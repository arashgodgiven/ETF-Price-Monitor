import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { RootState } from "@/app/store";

interface ETFState {
  selectedETFId: string | null;
  selectedStockName: string | null;
}

const initialState: ETFState = {
  selectedETFId: null,
  selectedStockName: null,
};

export const etfSlice = createSlice({
  name: "etf",
  initialState,
  reducers: {
    selectETF: (state, action: PayloadAction<string>) => {
      state.selectedETFId = action.payload;
      state.selectedStockName = null; // clear stock when ETF changes
    },
    clearSelectedETF: (state) => {
      state.selectedETFId = null;
      state.selectedStockName = null;
    },
    selectStock: (state, action: PayloadAction<string>) => {
      state.selectedStockName = action.payload;
    },
    clearSelectedStock: (state) => {
      state.selectedStockName = null;
    },
  },
});

export const {
  selectETF,
  clearSelectedETF,
  selectStock,
  clearSelectedStock,
} = etfSlice.actions;

export const selectSelectedETFId = (state: RootState) =>
  state.etf.selectedETFId;

export const selectSelectedStockName = (state: RootState) =>
  state.etf.selectedStockName;

export default etfSlice.reducer;