# test/xbrl_explorer.py - Standalone XBRL data exploration script

import sys
import os

# Add parent directory to path to import edgar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from edgar import Company, set_identity
except ImportError:
    print("❌ EdgarTools not installed. Install with: pip install edgartools")
    sys.exit(1)

def explore_xbrl_raw_data(ticker: str = "MSFT", max_facts_to_show: int = 100):
    """Explore raw XBRL data structure to understand how to access it"""
    print(f"\n🔍 EXPLORING RAW XBRL DATA for {ticker}")
    print("=" * 70)
    
    try:
        # Set identity (required by SEC)
        set_identity('nfatpro@gmail.com')
        
        # Get company
        company = Company(ticker)
        print(f"📊 Company: {company.name}")
        
        # Get latest 10-Q filing
        filings = company.get_filings(form='10-Q').head(1)
        if not filings:
            print("❌ No quarterly filings found")
            return
        
        filing = filings[0]
        print(f"📄 Latest filing: {filing.form} dated {filing.filing_date}")
        
        # Get XBRL data
        print(f"\n🔍 Getting XBRL data...")
        xbrl = filing.xbrl()
        
        if not xbrl:
            print("❌ No XBRL data available")
            return
        
        print(f"✅ XBRL object created: {type(xbrl)}")
        
        # Explore XBRL object structure
        print(f"\n📋 XBRL Object Analysis:")
        print(f"   Type: {type(xbrl)}")
        print(f"   Dir: {[attr for attr in dir(xbrl) if not attr.startswith('_')][:10]}...")
        
        if hasattr(xbrl, '__dict__'):
            attrs = list(xbrl.__dict__.keys())
            print(f"   Attributes: {attrs}")
        
        # Explore facts
        if hasattr(xbrl, 'facts'):
            facts = xbrl.facts
            print(f"\n📊 Facts Analysis:")
            print(f"   Facts type: {type(facts)}")
            print(f"   Facts dir: {[attr for attr in dir(facts) if not attr.startswith('_')][:10]}...")
            
            if hasattr(facts, '__len__'):
                print(f"   Facts length: {len(facts)}")
            
            # Try different ways to access facts
            print(f"\n🔍 Testing Facts Access Methods:")
            
            # Method 1: Try to iterate
            print(f"   🧪 Method 1: Direct iteration")
            try:
                count = 0
                for fact in facts:
                    if count >= 5:  # Just show first 5
                        break
                    print(f"      {count+1}. {fact} (type: {type(fact)})")
                    count += 1
                if count > 0:
                    print(f"      ... iteration works, showing first {count}")
                else:
                    print(f"      ❌ No facts found via iteration")
            except Exception as e:
                print(f"      ❌ Iteration failed: {e}")
            
            # Method 2: Try keys() if it exists
            print(f"\n   🧪 Method 2: facts.keys()")
            try:
                if hasattr(facts, 'keys'):
                    keys = list(facts.keys())
                    print(f"      ✅ Keys available: {len(keys)} total")
                    print(f"      First 10 keys: {keys[:10]}")
                    
                    # Try to access a fact by key
                    if keys:
                        test_key = keys[0]
                        test_value = facts[test_key] if hasattr(facts, '__getitem__') else facts.get(test_key)
                        print(f"      Test access facts['{test_key}']: {type(test_value)}")
                        
                        # If it's a fact object, explore it
                        if test_value:
                            print(f"      Test fact attributes: {[attr for attr in dir(test_value) if not attr.startswith('_')][:5]}...")
                            if hasattr(test_value, 'value'):
                                print(f"      Test fact value: {test_value.value} (type: {type(test_value.value)})")
                            if hasattr(test_value, 'concept'):
                                print(f"      Test fact concept: {test_value.concept}")
                else:
                    print(f"      ❌ No keys() method")
            except Exception as e:
                print(f"      ❌ Keys access failed: {e}")
            
            # Method 3: Try get() method
            print(f"\n   🧪 Method 3: facts.get()")
            try:
                if hasattr(facts, 'get'):
                    # Try some common concept names
                    test_concepts = ['Revenues', 'Revenue', 'us-gaap:Revenues', 'NetIncomeLoss']
                    for concept in test_concepts:
                        result = facts.get(concept)
                        if result:
                            print(f"      ✅ facts.get('{concept}'): {type(result)}")
                            if hasattr(result, 'value'):
                                print(f"         Value: {result.value}")
                        else:
                            print(f"      ❌ facts.get('{concept}'): None")
                else:
                    print(f"      ❌ No get() method")
            except Exception as e:
                print(f"      ❌ Get method failed: {e}")
            
            # Method 4: Try filter() method (if it's a FactsView)
            print(f"\n   🧪 Method 4: facts.filter()")
            try:
                if hasattr(facts, 'filter'):
                    # Try filtering for revenue-related concepts
                    revenue_filter = facts.filter(concept='Revenues')
                    print(f"      facts.filter(concept='Revenues'): {type(revenue_filter)}")
                    if hasattr(revenue_filter, '__len__'):
                        print(f"      Filtered results count: {len(revenue_filter)}")
                    
                    # Try iteration on filtered results
                    try:
                        for i, fact in enumerate(revenue_filter):
                            if i >= 3:  # Show first 3
                                break
                            print(f"         {i+1}. {fact}")
                            if hasattr(fact, 'value'):
                                print(f"            Value: {fact.value}")
                    except Exception as fe:
                        print(f"         ❌ Filter iteration failed: {fe}")
                        
                else:
                    print(f"      ❌ No filter() method")
            except Exception as e:
                print(f"      ❌ Filter method failed: {e}")
        
        # Explore other potential data sources
        print(f"\n🔍 Other XBRL Data Sources:")
        
        # Check for financial statements
        statements_to_check = [
            'income_statement', 'income', 'balance_sheet', 'balance', 
            'cash_flow_statement', 'cash_flow', 'statements'
        ]
        
        for stmt_name in statements_to_check:
            if hasattr(xbrl, stmt_name):
                stmt = getattr(xbrl, stmt_name)
                print(f"   ✅ Found {stmt_name}: {type(stmt)}")
                if hasattr(stmt, '__len__'):
                    try:
                        print(f"      Length: {len(stmt)}")
                    except:
                        pass
                if hasattr(stmt, 'keys'):
                    try:
                        keys = list(stmt.keys())[:5]
                        print(f"      Keys sample: {keys}")
                    except:
                        pass
        
        # Try direct concept access on XBRL object
        print(f"\n🔍 Direct XBRL Concept Access:")
        test_concepts = [
            'Revenues', 'Revenue', 'NetIncomeLoss', 'Assets', 
            'NetCashProvidedByUsedInOperatingActivities'
        ]
        
        for concept in test_concepts:
            if hasattr(xbrl, concept):
                value = getattr(xbrl, concept)
                print(f"   ✅ xbrl.{concept}: {type(value)}")
                if hasattr(value, 'value'):
                    print(f"      Value: {value.value}")
            else:
                print(f"   ❌ xbrl.{concept}: Not found")
        
    except Exception as e:
        print(f"❌ Exploration error: {e}")
        import traceback
        traceback.print_exc()

def explore_multiple_companies():
    """Test with multiple companies to see if there are patterns"""
    companies = ["MSFT", "AAPL", "O", "GOOGL"]
    
    print(f"\n🧪 TESTING MULTIPLE COMPANIES")
    print("=" * 50)
    
    for ticker in companies:
        print(f"\n--- {ticker} ---")
        try:
            # Just get basic XBRL structure info
            set_identity('nfatpro@gmail.com')
            company = Company(ticker)
            filings = company.get_filings(form='10-Q').head(1)
            
            if filings:
                filing = filings[0]
                xbrl = filing.xbrl()
                
                if xbrl and hasattr(xbrl, 'facts'):
                    facts = xbrl.facts
                    print(f"   ✅ XBRL Facts: {type(facts)}, length: {len(facts) if hasattr(facts, '__len__') else 'unknown'}")
                    
                    # Try to find any revenue-like concept
                    if hasattr(facts, 'keys'):
                        keys = list(facts.keys())
                        revenue_keys = [k for k in keys if 'revenue' in k.lower() or 'income' in k.lower()][:3]
                        print(f"   📈 Revenue-like keys: {revenue_keys}")
                    
                else:
                    print(f"   ❌ No XBRL or facts")
            else:
                print(f"   ❌ No filings")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 XBRL Raw Data Explorer")
    print("=" * 40)
    
    # Test with Microsoft first (has many facts)
    explore_xbrl_raw_data("MSFT")
    
    # Test with multiple companies
    explore_multiple_companies()
    
    print(f"\n✅ Exploration completed!")
    print(f"\n💡 Based on the results above, we can determine:")
    print(f"   1. How to properly access XBRL facts")
    print(f"   2. What the actual concept names are")
    print(f"   3. How to extract values from fact objects")
    print(f"   4. Whether the structure is consistent across companies")