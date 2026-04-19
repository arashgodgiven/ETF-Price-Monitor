export interface Constituent {
  stock_name: string;
  weight: number;
  latest_price: number | null;
}

export interface ETFSummary {
  id: string;
  name: string;
  constituents: Constituent[];
}

export interface PricePoint {
  date: string;
  price: number;
}

export interface ETFPriceHistory {
  etf_id: string;
  etf_name: string;
  series: PricePoint[];
}

export interface TopHolding {
  stock_name: string;
  weight: number;
  latest_price: number;
  holding_size: number;
}

export interface ETFTopHoldings {
  etf_id: string;
  etf_name: string;
  as_of_date: string;
  holdings: TopHolding[];
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  db: string;
}

export type UploadStatus = "idle" | "uploading" | "success" | "error";