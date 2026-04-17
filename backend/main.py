from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from services.etf_service import (
  parse_etf,
  get_constituents,
  get_etf_price_series,
  get_top_holdings
)

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.post("/api/etf/upload")
async def upload_etf(file: UploadFile = File(...)):
  contents = await file.read()
  etf_df = parse_etf(contents)
  constituents = get_constituents(etf_df)
  return {
    "etf_name": file.filename.replace(".csv", ""),
    "constituents": get_constituents
  }

@app.post("/api/etf/prices")
async def etf_prices(file: UploadFile = File(...)):
  contents = await file.read()
  etf_df = parse_etf(contents)
  return get_etf_price_series(etf_df)

@app.post("/api/etf/holdings")
async def etf_holdings(file: UploadFile = File(...)):
  contents = await file.read()
  etf_df = parse_etf(contents)
  return get_top_holdings(etf_df)
