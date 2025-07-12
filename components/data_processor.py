# components/data_processor.py - Clean dataset processor with event integration

import json
import os
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import io
import threading
import time

# Event system integration
from core.event_system import (
    get_global_event_bus,
    EventType,
    Event,
    create_data_event,
    create_error_event,
    create_loading_event
)


class DataProcessor:
    """Clean dataset processor that converts raw XBRL cache to analysis-ready datasets"""
    
    def __init__(self, cache_dir: str = "data/cache", auto_subscribe_events: bool = True):
        self.cache_dir = cache_dir
        self.processing_status = {}
        self.last_processed = {}
        
        # Event system integration
        self.event_bus = get_global_event_bus()
        self.auto_process = auto_subscribe_events
        
        # Core financial concepts that work across most companies
        self.financial_concepts = {
            'revenue': ['Revenue', 'Revenues', 'SalesRevenueNet', 'PropertyIncome', 'RentalIncome', 'TotalRevenues'],
            'net_income': ['NetIncomeLoss', 'NetIncome', 'ProfitLoss', 'IncomeLossFromContinuingOperations'],
            'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByOperatingActivities'],
            'total_assets': ['Assets', 'TotalAssets'],
            'total_liabilities': ['Liabilities', 'TotalLiabilities'],
            'stockholders_equity': ['StockholdersEquity', 'ShareholdersEquity', 'TotalEquity'],
            'shares_outstanding': ['CommonStockSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic']
        }
        
        # Subscribe to cache events for automatic processing
        if auto_subscribe_events:
            self._setup_event_subscriptions()
        
        # Publish processor ready event
        self.event_bus.publish(self._create_processor_event(
            EventType.COMPONENT_READY,
            component='DataProcessor',
            auto_process=auto_subscribe_events
        ))
        
        print(f"📊 Data Processor initialized: {self.cache_dir}")
        print(f"   🔄 Auto-process on cache updates: {auto_subscribe_events}")
    
    def _setup_event_subscriptions(self):
        """Subscribe to cache events for automatic processing"""
        # Process when cache is updated
        self.event_bus.subscribe(EventType.CACHE_UPDATED, self._on_cache_updated)
        
        # Process when new ticker is added to cache
        self.event_bus.subscribe(EventType.TICKER_ADDED_TO_CACHE, self._on_ticker_added)
        
        print("   📡 Subscribed to cache events for auto-processing")
    
    def _on_cache_updated(self, event: Event):
        """Handle cache update events"""
        ticker = event.data.get('ticker')
        new_quarters = event.data.get('new_quarters', 0)
        
        if ticker and new_quarters > 0:
            print(f"🔄 Auto-processing {ticker} (cache updated with {new_quarters} new quarters)")
            
            # Process in background thread to avoid blocking
            def background_process():
                success, message, df = self.process_ticker_dataset(ticker, force_refresh=True)
                
                if success:
                    # Publish successful processing event
                    self.event_bus.publish(self._create_processor_event(
                        EventType.DATA_FETCH_COMPLETED,
                        ticker=ticker,
                        quarters_processed=len(df) if df is not None else 0,
                        trigger='cache_update',
                        auto_processed=True
                    ))
                    print(f"✅ Auto-processed {ticker} dataset")
                else:
                    # Publish error event
                    self.event_bus.publish(create_error_event(
                        f"Auto-processing failed for {ticker}: {message}",
                        source='data_processor'
                    ))
                    print(f"❌ Auto-processing failed for {ticker}: {message}")
            
            # Run in background thread
            threading.Thread(target=background_process, daemon=True).start()
    
    def _on_ticker_added(self, event: Event):
        """Handle new ticker added to cache events"""
        ticker = event.data.get('ticker')
        quarters_cached = event.data.get('quarters_cached', 0)
        
        if ticker and quarters_cached > 0:
            print(f"🔄 Auto-processing new ticker {ticker} ({quarters_cached} quarters cached)")
            
            # Process in background thread
            def background_process():
                success, message, df = self.process_ticker_dataset(ticker, force_refresh=True)
                
                if success:
                    self.event_bus.publish(self._create_processor_event(
                        EventType.DATA_FETCH_COMPLETED,
                        ticker=ticker,
                        quarters_processed=len(df) if df is not None else 0,
                        trigger='new_ticker',
                        auto_processed=True
                    ))
                    print(f"✅ Auto-processed new ticker {ticker} dataset")
                else:
                    self.event_bus.publish(create_error_event(
                        f"Auto-processing failed for new ticker {ticker}: {message}",
                        source='data_processor'
                    ))
                    print(f"❌ Auto-processing failed for new ticker {ticker}: {message}")
            
            threading.Thread(target=background_process, daemon=True).start()
    
    def _create_processor_event(self, event_type: EventType, ticker: str = None, **extra_data) -> Event:
        """Helper to create processor events with consistent source"""
        data = {'ticker': ticker, **extra_data}
        return Event(type=event_type, data=data, source='data_processor')
    
    def should_process_dataset(self, ticker: str) -> bool:
        """
        Intelligent check if dataset needs processing
        
        Returns True if:
        - Dataset doesn't exist
        - Dataset is older than raw cache files
        - Dataset is corrupted/empty
        """
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        dataset_file = os.path.join(ticker_dir, f"{ticker}_dataset.csv")
        
        if not os.path.exists(dataset_file):
            return True  # Dataset doesn't exist
        
        try:
            # Check if dataset is older than raw cache files
            dataset_time = os.path.getmtime(dataset_file)
            raw_files = [f for f in os.listdir(ticker_dir) 
                        if f.endswith('.json') and f != 'metadata.json']
            
            if raw_files:
                newest_raw = max(os.path.getmtime(os.path.join(ticker_dir, f)) 
                               for f in raw_files)
                if dataset_time < newest_raw:
                    return True  # Dataset is stale
            
            # Check if dataset is valid (not empty/corrupted)
            df = pd.read_csv(dataset_file)
            if df.empty:
                return True  # Dataset is empty
                
        except Exception:
            return True  # Dataset is corrupted or unreadable
        
        return False  # Dataset is current and valid
    
    def process_ticker_dataset(self, ticker: str, force_refresh: bool = False) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Process a ticker's raw XBRL data into clean dataset
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Force reprocessing even if dataset exists
            
        Returns:
            Tuple of (success, message, dataframe)
        """
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            error_msg = f"No cached data found for {ticker}"
            self.event_bus.publish(create_error_event(
                error_msg, 
                source='data_processor',
                ticker=ticker,
                operation='dataset_processing'
            ))
            return False, error_msg, None
        
        # Publish processing started event
        self.event_bus.publish(self._create_processor_event(
            EventType.DATA_FETCH_STARTED,
            ticker=ticker,
            operation='dataset_processing',
            force_refresh=force_refresh
        ))
        
        dataset_file = os.path.join(ticker_dir, f"{ticker}_dataset.csv")
        
        # Check if dataset already exists and is recent
        if not force_refresh and not self.should_process_dataset(ticker):
            try:
                # Dataset is up to date, load and return
                df = pd.read_csv(dataset_file)
                
                # Publish data loaded event
                self.event_bus.publish(self._create_processor_event(
                    EventType.DATA_RECEIVED,
                    ticker=ticker,
                    quarters_loaded=len(df),
                    data_source='existing_dataset',
                    up_to_date=True
                ))
                
                return True, f"Dataset loaded (up to date) - {len(df)} quarters", df
            except Exception as e:
                # If loading fails, fall through to reprocessing
                self.event_bus.publish(create_error_event(
                    f"Failed to load existing dataset for {ticker}: {str(e)}",
                    source='data_processor',
                    ticker=ticker
                ))
        
        # Process the data
        try:
            self.processing_status[ticker] = "Processing..."
            
            # Publish progress event
            self.event_bus.publish(self._create_processor_event(
                EventType.ANALYSIS_STARTED,
                ticker=ticker,
                operation='financial_extraction'
            ))
            
            df = self._create_clean_dataset(ticker_dir, ticker)
            
            if df.empty:
                error_msg = "No valid financial data could be extracted"
                self.processing_status[ticker] = "No data extracted"
                
                self.event_bus.publish(create_error_event(
                    f"{ticker}: {error_msg}",
                    source='data_processor',
                    ticker=ticker,
                    operation='financial_extraction'
                ))
                
                return False, error_msg, None
            
            # Save the dataset
            self._save_dataset(ticker_dir, ticker, df)
            
            self.processing_status[ticker] = f"Completed - {len(df)} quarters"
            self.last_processed[ticker] = datetime.now().isoformat()
            
            # Publish successful completion events
            self.event_bus.publish(self._create_processor_event(
                EventType.ANALYSIS_COMPLETED,
                ticker=ticker,
                quarters_processed=len(df),
                operation='financial_extraction',
                success=True
            ))
            
            self.event_bus.publish(self._create_processor_event(
                EventType.DATA_RECEIVED,
                ticker=ticker,
                quarters_loaded=len(df),
                data_source='newly_processed',
                processing_time=datetime.now().isoformat()
            ))
            
            return True, f"Dataset created - {len(df)} quarters processed", df
            
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.processing_status[ticker] = f"Error: {str(e)}"
            
            self.event_bus.publish(create_error_event(
                f"{ticker}: {error_msg}",
                source='data_processor',
                ticker=ticker,
                operation='dataset_processing'
            ))
            
            return False, error_msg, None
    
    def _create_clean_dataset(self, ticker_dir: str, ticker: str) -> pd.DataFrame:
        """Create clean dataset from raw XBRL files"""
        quarter_files = [f for f in os.listdir(ticker_dir) 
                        if f.endswith('.json') and f != 'metadata.json']
        
        if not quarter_files:
            return pd.DataFrame()
        
        all_quarters = []
        processed_count = 0
        
        for quarter_file in quarter_files:
            quarter_data = self._process_quarter_file(ticker_dir, quarter_file, ticker)
            if quarter_data:
                all_quarters.append(quarter_data)
                processed_count += 1
                
                # Publish progress for each quarter processed
                self.event_bus.publish(self._create_processor_event(
                    EventType.PROGRESS_UPDATED,
                    ticker=ticker,
                    quarters_processed=processed_count,
                    total_quarters=len(quarter_files),
                    current_quarter=quarter_data.get('period_label', 'Unknown')
                ))
        
        if not all_quarters:
            return pd.DataFrame()
        
        # Convert to DataFrame and sort by date (most recent first)
        df = pd.DataFrame(all_quarters)
        df = df.sort_values('filing_date', ascending=False)
        
        # Add calculated fields
        df = self._add_calculated_metrics(df)
        
        return df
    
    def _process_quarter_file(self, ticker_dir: str, quarter_file: str, ticker: str) -> Optional[Dict]:
        """Process a single quarter file"""
        file_path = os.path.join(ticker_dir, quarter_file)
        
        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
            
            # Basic quarter information
            quarter_data = {
                'ticker': ticker,
                'filing_date': raw_data.get('filing_date', ''),
                'quarter': self._extract_quarter(raw_data.get('filing_date', '')),
                'year': self._extract_year(raw_data.get('filing_date', '')),
                'form_type': raw_data.get('form_type', '10-Q'),
                'period_label': f"{self._extract_quarter(raw_data.get('filing_date', ''))} {self._extract_year(raw_data.get('filing_date', ''))}",
                'extraction_success': raw_data.get('extraction_success', False),
                'total_facts': raw_data.get('total_facts_count', 0)
            }
            
            # Extract financial metrics
            if raw_data.get('facts_json'):
                try:
                    facts_df = pd.read_json(io.StringIO(raw_data['facts_json']))
                    financials = self._extract_financial_metrics(facts_df)
                    quarter_data.update(financials)
                    
                    # Publish financial data extraction event
                    self.event_bus.publish(self._create_processor_event(
                        EventType.FINANCIAL_DATA_EXTRACTED,
                        ticker=ticker,
                        quarter=quarter_data['quarter'],
                        year=quarter_data['year'],
                        metrics_extracted=len([k for k, v in financials.items() if v is not None and not k.endswith('_concept')]),
                        success=True
                    ))
                    
                except Exception as e:
                    # If facts processing fails, still return basic info
                    quarter_data['processing_error'] = str(e)
                    
                    self.event_bus.publish(self._create_processor_event(
                        EventType.FINANCIAL_DATA_EXTRACTION_FAILED,
                        ticker=ticker,
                        quarter=quarter_data['quarter'],
                        year=quarter_data['year'],
                        error=str(e)
                    ))
            
            return quarter_data
            
        except Exception as e:
            print(f"   ⚠️ Error processing {quarter_file}: {e}")
            return None
    
    def _extract_financial_metrics(self, facts_df: pd.DataFrame) -> Dict:
        """Extract financial metrics from facts DataFrame"""
        metrics = {}
        
        # Extract core financial metrics
        for metric_name, concept_list in self.financial_concepts.items():
            value = self._find_concept_value(facts_df, concept_list)
            metrics[metric_name] = value
            
            # Also store which concept was used (for debugging)
            concept_used = self._find_concept_name(facts_df, concept_list)
            metrics[f"{metric_name}_concept"] = concept_used
        
        # Add some common derived metrics
        metrics['free_cash_flow'] = metrics.get('operating_cash_flow')  # Simplified
        
        return metrics
    
    def _find_concept_value(self, facts_df: pd.DataFrame, concept_list: List[str]) -> Optional[float]:
        """Find numeric value for a financial concept"""
        for concept in concept_list:
            # Case-insensitive search for concept
            matches = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            
            if len(matches) > 0:
                # Try to get a valid numeric value
                for _, row in matches.iterrows():
                    value = self._extract_numeric_value(row)
                    if value is not None:
                        return value
        
        return None
    
    def _find_concept_name(self, facts_df: pd.DataFrame, concept_list: List[str]) -> Optional[str]:
        """Find the actual concept name that was used"""
        for concept in concept_list:
            matches = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(matches) > 0:
                return matches.iloc[0]['concept']
        return None
    
    def _extract_numeric_value(self, row: pd.Series) -> Optional[float]:
        """Extract numeric value from a fact row"""
        for field in ['value', 'numeric_value', 'amount']:
            value = row.get(field)
            if value is not None:
                try:
                    if isinstance(value, str):
                        # Clean string formatting
                        clean_value = value.replace(',', '').replace('$', '').replace('%', '')
                        return float(clean_value)
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _add_calculated_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated metrics to the dataset"""
        df = df.copy()
        
        # Revenue in millions for easier reading
        if 'revenue' in df.columns:
            df['revenue_millions'] = df['revenue'].apply(
                lambda x: round(x / 1000000, 1) if pd.notna(x) and x != 0 else None
            )
        
        # Operating cash flow in millions
        if 'operating_cash_flow' in df.columns:
            df['ocf_millions'] = df['operating_cash_flow'].apply(
                lambda x: round(x / 1000000, 1) if pd.notna(x) and x != 0 else None
            )
        
        # Simple ratios (if we have the data)
        if 'net_income' in df.columns and 'total_assets' in df.columns:
            df['return_on_assets'] = df.apply(
                lambda row: row['net_income'] / row['total_assets'] 
                if pd.notna(row['net_income']) and pd.notna(row['total_assets']) and row['total_assets'] != 0 
                else None, axis=1
            )
        
        if 'total_liabilities' in df.columns and 'total_assets' in df.columns:
            df['debt_to_assets'] = df.apply(
                lambda row: row['total_liabilities'] / row['total_assets']
                if pd.notna(row['total_liabilities']) and pd.notna(row['total_assets']) and row['total_assets'] != 0
                else None, axis=1
            )
        
        return df
    
    def _save_dataset(self, ticker_dir: str, ticker: str, df: pd.DataFrame):
        """Save clean dataset to ticker directory"""
        # Publish file save started event
        self.event_bus.publish(self._create_processor_event(
            EventType.FILE_SAVED,
            ticker=ticker,
            operation='dataset_save_started',
            quarters_count=len(df)
        ))
        
        # Save as CSV (easy to open in Excel)
        csv_file = os.path.join(ticker_dir, f"{ticker}_dataset.csv")
        df.to_csv(csv_file, index=False)
        
        # Save as JSON (preserves data types)
        json_file = os.path.join(ticker_dir, f"{ticker}_dataset.json")
        df.to_json(json_file, orient='records', indent=2, date_format='iso')
        
        # Create a summary file with key metrics
        summary_file = os.path.join(ticker_dir, f"{ticker}_summary.json")
        summary = {
            'ticker': ticker,
            'last_processed': datetime.now().isoformat(),
            'quarters_count': len(df),
            'date_range': {
                'earliest': df['filing_date'].min(),
                'latest': df['filing_date'].max()
            },
            'data_availability': {
                'revenue': df['revenue'].notna().sum(),
                'net_income': df['net_income'].notna().sum(),
                'operating_cash_flow': df['operating_cash_flow'].notna().sum(),
                'total_assets': df['total_assets'].notna().sum()
            },
            'recent_quarter': self._get_recent_quarter_summary(df)
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Publish dataset saved event
        self.event_bus.publish(self._create_processor_event(
            EventType.FILE_SAVED,
            ticker=ticker,
            operation='dataset_save_completed',
            files_saved=['CSV', 'JSON', 'Summary'],
            dataset_path=csv_file,
            summary=summary
        ))
    
    def _get_recent_quarter_summary(self, df: pd.DataFrame) -> Dict:
        """Get summary of most recent quarter"""
        if df.empty:
            return {}
        
        recent = df.iloc[0]  # Most recent (sorted by date desc)
        
        return {
            'period': recent.get('period_label', 'Unknown'),
            'filing_date': recent.get('filing_date', 'Unknown'),
            'revenue_millions': recent.get('revenue_millions'),
            'ocf_millions': recent.get('ocf_millions'),
            'total_assets_millions': round(recent.get('total_assets', 0) / 1000000, 1) if pd.notna(recent.get('total_assets')) else None
        }
    
    def _extract_quarter(self, filing_date: str) -> str:
        """Extract quarter from filing date"""
        try:
            date_obj = datetime.strptime(filing_date, '%Y-%m-%d')
            month = date_obj.month
            return f"Q{(month - 1) // 3 + 1}"
        except:
            return "Unknown"
    
    def _extract_year(self, filing_date: str) -> int:
        """Extract year from filing date"""
        try:
            return int(filing_date.split('-')[0])
        except:
            return 0
    
    def get_processing_status(self, ticker: str = None) -> Dict:
        """Get processing status for ticker(s)"""
        if ticker:
            ticker = ticker.upper()
            status_info = {
                'status': self.processing_status.get(ticker, 'Not processed'),
                'last_processed': self.last_processed.get(ticker),
                'dataset_exists': self._dataset_exists(ticker),
                'needs_processing': self.should_process_dataset(ticker)
            }
            
            # Publish status request event
            self.event_bus.publish(self._create_processor_event(
                EventType.STATUS_UPDATED,
                ticker=ticker,
                status_info=status_info,
                operation='status_check'
            ))
            
            return status_info
        else:
            return {
                'all_statuses': self.processing_status,
                'last_processed': self.last_processed,
                'total_processed': len(self.processing_status)
            }
    
    def _dataset_exists(self, ticker: str) -> bool:
        """Check if clean dataset exists for ticker"""
        ticker_dir = os.path.join(self.cache_dir, ticker.upper())
        dataset_file = os.path.join(ticker_dir, f"{ticker}_dataset.csv")
        return os.path.exists(dataset_file)
    
    def process_all_cached_tickers(self, background: bool = False) -> Dict:
        """Process all cached tickers"""
        tickers = self._get_cached_tickers()
        
        # Publish batch processing started event
        self.event_bus.publish(self._create_processor_event(
            EventType.ANALYSIS_STARTED,
            operation='batch_processing',
            total_tickers=len(tickers),
            background=background
        ))
        
        if background:
            # Run in background thread
            def background_process():
                self._process_all_background(tickers)
            
            thread = threading.Thread(target=background_process, daemon=True)
            thread.start()
            return {'message': 'Background processing started', 'thread_started': True, 'total_tickers': len(tickers)}
        else:
            return self._process_all_sync(tickers)
    
    def _process_all_sync(self, tickers: List[str]) -> Dict:
        """Process all tickers synchronously"""
        results = {'processed': 0, 'failed': 0, 'details': {}}
        
        for i, ticker in enumerate(tickers, 1):
            # Publish progress
            self.event_bus.publish(self._create_processor_event(
                EventType.PROGRESS_UPDATED,
                operation='batch_processing',
                tickers_processed=i-1,
                total_tickers=len(tickers),
                current_ticker=ticker
            ))
            
            success, message, df = self.process_ticker_dataset(ticker)
            results['details'][ticker] = {'success': success, 'message': message}
            
            if success:
                results['processed'] += 1
            else:
                results['failed'] += 1
        
        # Publish batch completion event
        self.event_bus.publish(self._create_processor_event(
            EventType.ANALYSIS_COMPLETED,
            operation='batch_processing',
            results=results,
            success=True
        ))
        
        return results
    
    def _process_all_background(self, tickers: List[str]):
        """Background processing of all tickers"""
        processed = 0
        failed = 0
        
        for ticker in tickers:
            try:
                # Publish progress
                self.event_bus.publish(self._create_processor_event(
                    EventType.PROGRESS_UPDATED,
                    operation='background_batch_processing',
                    tickers_processed=processed + failed,
                    total_tickers=len(tickers),
                    current_ticker=ticker
                ))
                
                success, message, df = self.process_ticker_dataset(ticker)
                if success:
                    processed += 1
                else:
                    failed += 1
                    
                time.sleep(0.1)  # Small delay to prevent overwhelming
                
            except Exception as e:
                self.processing_status[ticker] = f"Background error: {str(e)}"
                failed += 1
        
        # Publish background completion event
        self.event_bus.publish(self._create_processor_event(
            EventType.ANALYSIS_COMPLETED,
            operation='background_batch_processing',
            processed=processed,
            failed=failed,
            total_tickers=len(tickers),
            success=True
        ))
    
    def _get_cached_tickers(self) -> List[str]:
        """Get list of cached tickers"""
        if not os.path.exists(self.cache_dir):
            return []
        
        return [d for d in os.listdir(self.cache_dir) 
                if os.path.isdir(os.path.join(self.cache_dir, d)) and d != '__pycache__']
    
    def get_dataset_info(self, ticker: str) -> Dict:
        """Get information about a ticker's dataset"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        
        info = {
            'ticker': ticker,
            'cache_exists': os.path.exists(ticker_dir),
            'dataset_exists': False,
            'summary_exists': False,
            'last_updated': None,
            'quarters_count': 0,
            'needs_processing': True
        }
        
        if info['cache_exists']:
            dataset_file = os.path.join(ticker_dir, f"{ticker}_dataset.csv")
            summary_file = os.path.join(ticker_dir, f"{ticker}_summary.json")
            
            info['dataset_exists'] = os.path.exists(dataset_file)
            info['summary_exists'] = os.path.exists(summary_file)
            info['needs_processing'] = self.should_process_dataset(ticker)
            
            if info['dataset_exists']:
                try:
                    df = pd.read_csv(dataset_file)
                    info['quarters_count'] = len(df)
                    info['last_updated'] = datetime.fromtimestamp(os.path.getmtime(dataset_file)).isoformat()
                except:
                    pass
            
            if info['summary_exists']:
                try:
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                    info['summary'] = summary
                except:
                    pass
        
        # Publish dataset info event
        self.event_bus.publish(self._create_processor_event(
            EventType.STATUS_UPDATED,
            ticker=ticker,
            dataset_info=info,
            operation='dataset_info_check'
        ))
        
        return info


# Helper function to integrate with existing components
def start_background_dataset_processing(cache_dir: str = "data/cache"):
    """Start background processing of all datasets"""
    processor = DataProcessor(cache_dir)
    return processor.process_all_cached_tickers(background=True)


# Integration with cache manager - enhanced version
def process_ticker_on_cache_update(ticker: str, cache_dir: str = "data/cache"):
    """Process dataset when cache is updated (called by cache manager)"""
    processor = DataProcessor(cache_dir, auto_subscribe_events=False)  # Don't auto-subscribe to avoid loops
    success, message, df = processor.process_ticker_dataset(ticker, force_refresh=True)
    return success, message


# Main function to set up the integrated data processor
def create_integrated_data_processor(cache_dir: str = "data/cache") -> DataProcessor:
    """Create a data processor with full event integration"""
    return DataProcessor(cache_dir, auto_subscribe_events=True)


if __name__ == "__main__":
    # Test the integrated data processor
    print("🧪 Testing Integrated Data Processor")
    print("=" * 50)
    
    # Set up event monitoring
    from core.event_system import setup_comprehensive_monitoring
    cache_monitor, edgar_monitor = setup_comprehensive_monitoring()
    
    # Create integrated data processor
    processor = DataProcessor("data/cache", auto_subscribe_events=True)
    
    # Test with sample ticker
    test_ticker = "AAPL"
    print(f"\n🔍 Testing dataset processing for {test_ticker}")
    
    try:
        # Check if processing is needed
        needs_processing = processor.should_process_dataset(test_ticker)
        print(f"   📊 Dataset needs processing: {needs_processing}")
        
        # Get dataset info
        dataset_info = processor.get_dataset_info(test_ticker)
        print(f"   📋 Dataset Info:")
        print(f"      Cache exists: {dataset_info['cache_exists']}")
        print(f"      Dataset exists: {dataset_info['dataset_exists']}")
        print(f"      Quarters: {dataset_info['quarters_count']}")
        print(f"      Needs processing: {dataset_info['needs_processing']}")
        
        # Process dataset if needed or force refresh
        if needs_processing or not dataset_info['dataset_exists']:
            print(f"\n🔄 Processing {test_ticker} dataset...")
            success, message, df = processor.process_ticker_dataset(test_ticker)
            
            if success and df is not None:
                print(f"   ✅ {message}")
                print(f"   📊 Dataset shape: {df.shape}")
                print(f"   📅 Date range: {df['filing_date'].min()} to {df['filing_date'].max()}")
                
                # Show some key metrics from recent quarter
                if not df.empty:
                    recent = df.iloc[0]
                    print(f"   💰 Recent metrics (Q{recent.get('quarter', '?')} {recent.get('year', '?')}):")
                    if pd.notna(recent.get('revenue_millions')):
                        print(f"      Revenue: ${recent.get('revenue_millions')}M")
                    if pd.notna(recent.get('ocf_millions')):
                        print(f"      Operating Cash Flow: ${recent.get('ocf_millions')}M")
            else:
                print(f"   ❌ {message}")
        else:
            print(f"   ✅ Dataset is up to date")
        
        # Show processing status
        status = processor.get_processing_status(test_ticker)
        print(f"\n📊 Processing Status:")
        print(f"   Status: {status['status']}")
        print(f"   Last processed: {status.get('last_processed', 'Never')}")
        print(f"   Dataset exists: {status['dataset_exists']}")
        print(f"   Needs processing: {status['needs_processing']}")
        
        # Test event monitoring
        recent_events = cache_monitor.get_recent_cache_events(3)
        print(f"\n📋 Recent Cache Events ({len(recent_events)}):")
        for event in recent_events:
            ticker_event = event.data.get('ticker', 'N/A')
            print(f"   {event.type.value}: {ticker_event}")
        
        print(f"\n✅ Integrated data processor test completed successfully!")
        
        # Test auto-processing simulation
        print(f"\n🧪 Testing auto-processing simulation...")
        print("   (Simulating cache update event)")
        
        # Manually trigger a cache update event to test auto-processing
        from core.event_system import create_cache_update_event
        test_event = create_cache_update_event(test_ticker, new_quarters=1, total_quarters=12)
        processor.event_bus.publish(test_event)
        
        # Give background processing a moment
        import time
        time.sleep(1)
        
        print("   ✅ Auto-processing trigger test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 All data processor integration tests completed!")