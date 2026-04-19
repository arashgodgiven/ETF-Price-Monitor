import { configureStore } from "@reduxjs/toolkit";
import { etfApi } from "@/features/etf/etfApiSlice";
import etfReducer from "@/features/etf/etfSlice";

export const store = configureStore({
  reducer: {
    etf: etfReducer,
    [etfApi.reducerPath]: etfApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(etfApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;