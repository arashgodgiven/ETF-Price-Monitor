import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
prices_df = pd.read_csv(DATA_DIR / "bankofmontreal-e134q-1arsjzss-prices.csv", parse_dates=["DATE"], index_col="DATE")

def parse_etf(file_bytes: bytes) -> pd.DataFrame:
    from io import BytesIO
    etf_df = pd.read_csv(BytesIO(file_bytes))
    etf_df.columns = etf_df.columns.str.strip()
    return etf_df

def get_constituents(etf_df: pd.DataFrame) -> list:
    latest_prices = prices_df.iloc[-1]
    result = []
    for _, row in etf_df.iterrows():
        name = row["name"]
        weight = row["weight"]
        latest_price = latest_prices.get(name, None)
        result.append({
            "name": name,
            "weight": weight,
            "latest_price": round(float(latest_price), 2) if latest_price is not None else None
        })
    return result

def get_etf_price_series(etf_df: pd.DataFrame) -> dict:
    constituents = etf_df.set_index("name")["weight"].to_dict()
    valid = {k: v for k, v in constituents.items() if k in prices_df.columns}
    filtered = prices_df[list(valid.keys())]
    weights = pd.Series(valid)
    etf_prices = filtered.mul(weights).sum(axis=1)
    return {
        "dates": etf_prices.index.strftime("%Y-%m-%d").tolist(),
        "prices": [round(p, 4) for p in etf_prices.tolist()]
    }

def get_top_holdings(etf_df: pd.DataFrame, top_n: int = 5) -> list:
    latest_prices = prices_df.iloc[-1]
    holdings =[]
    for _, row in etf_df.iterrows():
        name = row["name"]
        weight = row["weight"]
        price = latest_prices.get(name, None)
        if price is not None:
            holding_size = round(float(weight) * float(price), 4)
            holdings.append({
                "name": name,
                "weight": weight,
                "latest_price": round(float(price), 2),
                "holding_size": holding_size
            })
    return sorted(holdings, key=lambda x: x["holding_size"], reverse=True)[:top_n]