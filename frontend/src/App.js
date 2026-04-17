import { useState } from "react";
import ETFTable from "./components/ETFTable";
import PriceChart from "./components/PriceChart";
import HoldingsChart from "./components/HoldingsChart";

function App() {
  const [constituents, setConstituents] = useState([]);
  const [etfName, setEtfName] = useState("");
  const [priceData, setPriceData] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e) => {
    const file = e.target.files[0]; //Grabs the first selected file from the event. how to make sure not more than one file is selected
    if (!file) return;

    setLoading(true);

    const uploadFile = async (url) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(url, {method: "POST", body: formData });
      return res.json();
    };

    const [uploadData, pricesData, holdingsData] = await Promise.all([//why send all three together
      uploadFile("http://localhost:8000/api/etf/upload"),
      uploadFile("http://localhost:8000/api/etf/prices"),
      uploadFile("http://localhost:8000/api/etf/holdings"),
    ]);

    setEtfName(uploadData.etf_name);
    setConstituents(uploadData.constituents);
    setPriceData(pricesData);
    setHoldings(holdingsData);
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "2rem" }}>
      <h1>ETF Price Monitor</h1>

      <input type="file" accept=".csv" onChange={handleUpload} />

      {loading && <p>Loading...</p>}

      {etfName && <h2>{etfName}</h2>}

      {constituents.length > 0 && <ETFTable constituents={constituents} />}

      {priceData && <PriceChart priceData={priceData} />}

      {holdings.length > 0 && <HoldingsChart holdings={holdings} />}
    </div>
  );
}

export default App;