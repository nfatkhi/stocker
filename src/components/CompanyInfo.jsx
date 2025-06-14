// src/components/CompanyInfo.jsx
export default function CompanyInfo({ info }) {
  return (
    <div className="mt-6 border p-4 rounded shadow">
      <h2 className="text-xl font-semibold mb-2">{info.name} ({info.ticker})</h2>
      <p><strong>Exchange:</strong> {info.exchange}</p>
      <p><strong>Industry:</strong> {info.finnhubIndustry}</p>
      <p><strong>Market Cap:</strong> ${Number(info.marketCapitalization).toLocaleString()}M</p>
      <p><strong>Current Price:</strong> ${info.currentPrice}</p>
      <p><strong>P/E Ratio:</strong> {info.peRatio}</p>
      <p><strong>52-Week High:</strong> ${info.high52}</p>
      <p><strong>52-Week Low:</strong> ${info.low52}</p>
    </div>
  );
}

