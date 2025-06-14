// src/App.jsx
import { useState } from "react";
import SearchBar from "./components/SearchBar";
import CompanyInfo from "./components/CompanyInfo";
import PriceChart from "./components/PriceChart";
import axios from "axios";

const API_KEY = import.meta.env.VITE_FINNHUB_API_KEY;

export default function App() {
  const [ticker, setTicker] = useState("");
  const [companyInfo, setCompanyInfo] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [error, setError] = useState(null);

  const fetchStockData = async (symbol) => {
    try {
      setError(null);
      setCompanyInfo(null);
      setPriceData([]);

      const [profileRes, quoteRes, candleRes] = await Promise.all([
        axios.get(`https://finnhub.io/api/v1/stock/profile2`, {
          params: { symbol, token: API_KEY },
        }),
        axios.get(`https://finnhub.io/api/v1/quote`, {
          params: { symbol, token: API_KEY },
        }),
        axios.get(`https://finnhub.io/api/v1/stock/candle`, {
          params: {
            symbol,
            resolution: "D",
            from: Math.floor((Date.now() - 30 * 24 * 60 * 60 * 1000) / 1000),
            to: Math.floor(Date.now() / 1000),
            token: API_KEY,
          },
        }),
      ]);

      if (!profileRes.data.name) throw new Error("Invalid symbol");

      setCompanyInfo({
        ...profileRes.data,
        currentPrice: quoteRes.data.c,
        peRatio: quoteRes.data.pe || "N/A",
        high52: quoteRes.data.h,
        low52: quoteRes.data.l,
      });

      if (candleRes.data.s !== "ok") throw new Error("No price data available");

      const formattedPrices = candleRes.data.t.map((timestamp, i) => ({
        date: new Date(timestamp * 1000).toLocaleDateString(),
        price: candleRes.data.c[i],
      }));

      setPriceData(formattedPrices);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    }
  };

  const handleSearch = (symbol) => {
    setTicker(symbol.toUpperCase());
    fetchStockData(symbol.toUpperCase());
  };

  return (
    <div className="p-6 max-w-3xl mx-auto font-sans">
      <h1 className="text-3xl font-bold mb-6">📊 Stocker</h1>
      <SearchBar onSearch={handleSearch} />
      {error && <div className="text-red-500 mt-4">{error}</div>}
      {companyInfo && <CompanyInfo info={companyInfo} />}
      {priceData.length > 0 && <PriceChart data={priceData} />}
    </div>
  );
}
