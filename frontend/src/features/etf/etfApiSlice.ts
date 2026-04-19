import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import type {
  ETFPriceHistory,
  ETFSummary,
  ETFTopHoldings,
  HealthStatus,
} from "@/types/etf";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const etfApi = createApi({
  reducerPath: "etfApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    credentials: "include",
  }),
  tagTypes: ["ETF", "Session"],
  endpoints: (builder) => ({
    // Health -------------------------------------------------
    getHealth: builder.query<HealthStatus, void>({
      query: () => "/health",
    }),

    // Session ETFs -------------------------------------------
    getSessionETFs: builder.query<ETFSummary[], void>({
      query: () => "/etf/session",
      providesTags: ["Session"],
    }),

    // Upload -------------------------------------------------
    uploadETF: builder.mutation<ETFSummary, File>({
      query:(file) => {
        const formData = new FormData();
        formData.append("file", file); // match backend routers/etf.py : "file: UploadFile = File(...)"
        return { url: "/etf/upload", method: "POST", body: formData};
      },
      invalidatesTags: ["Session"],
    }),

    // ETF Summary --------------------------------------------
    getETFSummary: builder.query<ETFSummary, string>({
      query: (etfId) => `/etf/${etfId}`,
      providesTags: (_result, _error, id) => [{ type: "ETF", id }],
    }),

    // Price History ------------------------------------------
    getPriceHistory: builder.query<
      ETFPriceHistory,
      { etfId: string; dateFrom?: string; dateTo?: string}
    >({
      query: ({ etfId, dateFrom, dateTo }) => {
        const params = new URLSearchParams();
        if (dateFrom) params.set("date_from", dateFrom);
        if (dateTo) params.set("date_to", dateTo);
        const qs = params.toString();
        return `/etf/${etfId}/price-history${qs ? `?${qs}` : ""}`;
      },
      providesTags: (_result, _error, { etfId }) => [
        { type: "ETF", id: `${etfId}-history`},
      ],
    }),

    // Top Holdings -------------------------------------------
    getTopHoldings: builder.query<
      ETFTopHoldings,
      { etfId: string; limit?: number }
    >({
      query: ({ etfId, limit = 5 }) =>
        `/etf/${etfId}/top-holdings?limit=${limit}`,
      providesTags: (_result, _error, { etfId }) => [
        { type: "ETF", id: `${etfId}-holdings` },
      ],
    }),
  }),
});

export const {
  useGetHealthQuery,
  useGetSessionETFsQuery,
  useUploadETFMutation,
  useGetETFSummaryQuery,
  useGetPriceHistoryQuery,
  useGetTopHoldingsQuery,
} = etfApi;