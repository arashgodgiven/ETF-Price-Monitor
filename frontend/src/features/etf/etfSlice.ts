import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { RootState } from "@/app/store";

interface ETFState {
  selectedETFId: string | null;
}

const initialState: ETFState = {
  selectedETFId: null,
};

export const etfSlice = createSlice({
  name: "etf",
  initialState,
  reducers: {
    selectETF: (state, action: PayloadAction<string>) => {
      state.selectedETFId = action.payload;
    },
    clearSelectedETF: (state) => {
      state.selectedETFId = null;
    },
  },
});

export const { selectETF, clearSelectedETF } = etfSlice.actions;

export const selectSelectedETFId = (state: RootState) =>
  state.etf.selectedETFId;

export default etfSlice.reducer;