import { useState } from "react";
import ETFTable from "./components/ETFTable";
import PriceChart from "./components/PriceChart";
import HoldingsChart from "./components/HoldingsChart";

function App() {
  // const [constituents, setConstituents] = useState([]);
  // const [etfName, setEtfName] = useState("");
  // const [priceData, setPriceData] = useState(null);
  // const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(false);

  const [etfs, setEtfs] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleUpload = async (e) => {
    // const file = e.target.files[0]; //Grabs the first selected file from the event. how to make sure not more than one file is selected
    
    const files = Array.from(e.target.files);
    if (files.length > 5) {
      alert("Please upload a maximum of 5 files.");
      return;
    }
    
    if (!files) return;

    setLoading(true);

    // const uploadFile = async (url, file) => {
    //   const formData = new FormData();
    //   formData.append("file", file);
    //   const res = await fetch(url, {method: "POST", body: formData });
    //   return res.json();
    // };
  
    const results = await Promise.all(
      files.map(async (file) => {

        const sendFile = async (url) => {
          const formData = new FormData();
          formData.append("file", file);
          const res = await fetch(url, { method: "POST", body: formData });
          return res.json();
        };

        const [uploadData, pricesData, holdingsData] = await Promise.all([//why send all three together
          // uploadFile("http://localhost:8000/api/etf/upload"),
          // uploadFile("http://localhost:8000/api/etf/prices"),
          // uploadFile("http://localhost:8000/api/etf/holdings"),
          sendFile("http://localhost:8000/api/etf/upload"),
          sendFile("http://localhost:8000/api/etf/prices"),
          sendFile("http://localhost:8000/api/etf/holdings"),
        ]);
      
        const rawName = uploadData.etf_name;
        const cleanName = rawName.includes("-")
          ? rawName.split("-").pop()
          : rawName;

        return {
          etfName: cleanName,
          constituents: uploadData.constituents,
          priceData: pricesData,
          holdings: holdingsData,
        };
      })
    );
    

    // setEtfName(uploadData.etf_name);
    // setConstituents(uploadsData.constituents);
    // setPriceData(pricesData);
    // setHoldings(holdingsData);
    setLoading(false);

    setEtfs(results);
    setCurrentIndex(0);
  };

  const current = etfs[currentIndex];

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "2rem" }}>
      <h1>ETF Price Monitor</h1>

      <input type="file" accept=".csv" multiple onChange={handleUpload} />

      {loading && <p>Loading...</p>}

      {etfs.length > 0 && (
        <div>
          {/* Navigation arrows */}
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", margin: "1rem 0" }}>
            <button
              onClick={() => setCurrentIndex(i => i - 1)}
              disabled={currentIndex === 0}
            >
              ←
            </button>
            <span>{current.etfName} — {currentIndex + 1} / {etfs.length}</span>
            <button
              onClick={() => setCurrentIndex(i => i + 1)}
              disabled={currentIndex === etfs.length - 1}
            >
              →
            </button>
          </div>

          {/* All three visuals for current ETF */}
          <ETFTable constituents={current.constituents} />
          <PriceChart priceData={current.priceData} />
          <HoldingsChart holdings={current.holdings} />
        </div>
      )}

      {/* {etfName && <h2>{etfName}</h2>}

      {constituents.length > 0 && <ETFTable constituents={constituents} />}

      {priceData && <PriceChart priceData={priceData} />}

      {holdings.length > 0 && <HoldingsChart holdings={holdings} />} */}
    </div>
  );
}

export default App;