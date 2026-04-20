import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useState, useCallback, useEffect, useRef } from "react";
import { useGetPriceHistoryQuery, useGetStockPriceHistoryQuery } from "@/features/etf/etfApiSlice";
import { useAppDispatch, useAppSelector } from "@/app/hooks";
import { clearSelectedStock, selectSelectedStockName } from "@/features/etf/etfSlice";
import { formatCurrency, formatDate, formatShortDate } from "@/utils/formatters";
import type { PricePoint } from "@/types/etf";
import styles from "./PriceChart.module.css";

interface Props {
  etfId: string;
}

interface ZoomState {
  refAreaLeft: string | null;
  refAreaRight: string | null;
  isSelecting: boolean;
  zoomedFrom: string | null;
  zoomedTo: string | null;
}

const INITIAL_ZOOM: ZoomState = {
  refAreaLeft: null,
  refAreaRight: null,
  isSelecting: false,
  zoomedFrom: null,
  zoomedTo: null,
};

export function PriceChart({ etfId }: Props) {
  const dispatch = useAppDispatch();
  const selectedStockName = useAppSelector(selectSelectedStockName);
  const [zoom, setZoom] = useState<ZoomState>(INITIAL_ZOOM);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Reset zoom when switching between ETF and stock view
  useEffect(() => {
    setZoom(INITIAL_ZOOM);
  }, [selectedStockName, etfId]);

  // Scroll to chart when stock is selected
  useEffect(() => {
    if (selectedStockName && wrapperRef.current) {
      wrapperRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [selectedStockName]);

  const etfHistory = useGetPriceHistoryQuery(
    { etfId },
    { skip: !!selectedStockName }
  );

  const stockHistory = useGetStockPriceHistoryQuery(
    { stockName: selectedStockName ?? "" },
    { skip: !selectedStockName }
  );

  const { data, isLoading, isError } =
    selectedStockName ? stockHistory : etfHistory;

  const visibleData: PricePoint[] = (() => {
    if (!data?.series) return [];
    if (!zoom.zoomedFrom && !zoom.zoomedTo) return data.series;
    return data.series.filter(
      (p) =>
        (!zoom.zoomedFrom || p.date >= zoom.zoomedFrom) &&
        (!zoom.zoomedTo || p.date <= zoom.zoomedTo)
    );
  })();

  const handleMouseDown = useCallback((e: { activeLabel?: string }) => {
    if (!e.activeLabel) return;
    setZoom((z) => ({
      ...z,
      refAreaLeft: e.activeLabel!,
      refAreaRight: null,
      isSelecting: true,
    }));
  }, []);

  const handleMouseMove = useCallback(
    (e: { activeLabel?: string }) => {
      if (!zoom.isSelecting || !e.activeLabel) return;
      setZoom((z) => ({ ...z, refAreaRight: e.activeLabel! }));
    },
    [zoom.isSelecting]
  );

  const handleMouseUp = useCallback(() => {
    setZoom((z) => {
      if (!z.refAreaLeft || !z.refAreaRight) return INITIAL_ZOOM;
      const [from, to] = [z.refAreaLeft, z.refAreaRight].sort();
      return {
        refAreaLeft: null,
        refAreaRight: null,
        isSelecting: false,
        zoomedFrom: from,
        zoomedTo: to,
      };
    });
  }, []);

  const resetZoom = () => setZoom(INITIAL_ZOOM);
  const isZoomed = !!(zoom.zoomedFrom || zoom.zoomedTo);

  const priceMin = visibleData.length
    ? Math.min(...visibleData.map((p) => p.price)) * 0.995
    : undefined;
  const priceMax = visibleData.length
    ? Math.max(...visibleData.map((p) => p.price)) * 1.005
    : undefined;

  if (isLoading) return <div className={styles.state}>Loading price history…</div>;
  if (isError || !data)
    return <div className={styles.stateError}>Failed to load price history.</div>;

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <div className={styles.header}>
        <div>
          <div className={styles.titleRow}>
            <h2 className={styles.title}>
              {selectedStockName
                ? `${selectedStockName} — Price History`
                : `${data.etf_name} — Price History`}
            </h2>
            {selectedStockName && (
              <button
                className={styles.backBtn}
                onClick={() => dispatch(clearSelectedStock())}
              >
                ← Back to ETF
              </button>
            )}
          </div>
          <p className={styles.subtitle}>
            {data.series.length} trading days •{" "}
            {isZoomed ? (
              <span className={styles.zoomLabel}>
                {formatDate(zoom.zoomedFrom!)} → {formatDate(zoom.zoomedTo!)}
              </span>
            ) : (
              <span>
                {formatDate(data.series[0]?.date)} →{" "}
                {formatDate(data.series[data.series.length - 1]?.date)}
              </span>
            )}
          </p>
        </div>
        {isZoomed && (
          <button className={styles.resetBtn} onClick={resetZoom}>
            Reset zoom
          </button>
        )}
      </div>

      {!isZoomed && (
        <p className={styles.zoomHint}>Click and drag on the chart to zoom in</p>
      )}

      <ResponsiveContainer width="100%" height={320}>
        <AreaChart
          data={visibleData}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          style={{ cursor: zoom.isSelecting ? "crosshair" : "default" }}
        >
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.15} />
              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />

          <XAxis
            dataKey="date"
            tickFormatter={formatShortDate}
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--color-border)" }}
            minTickGap={40}
          />

          <YAxis
            domain={[priceMin ?? "auto", priceMax ?? "auto"]}
            tickFormatter={(v) => formatCurrency(v)}
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            tickLine={false}
            axisLine={false}
            width={75}
          />

          <Tooltip
            formatter={(value: number) => [formatCurrency(value), selectedStockName ?? "ETF Price"]}
            labelFormatter={(label: string) => formatDate(label)}
            contentStyle={{
              background: "var(--color-surface-elevated)",
              border: "1px solid var(--color-border)",
              borderRadius: "6px",
              fontSize: "13px",
            }}
          />

          <Area
            type="monotone"
            dataKey="price"
            stroke="var(--color-primary)"
            strokeWidth={2}
            fill="url(#priceGradient)"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
            isAnimationActive={!zoom.isSelecting}
          />

          {zoom.isSelecting && zoom.refAreaLeft && zoom.refAreaRight && (
            <ReferenceArea
              x1={zoom.refAreaLeft}
              x2={zoom.refAreaRight}
              fill="var(--color-primary)"
              fillOpacity={0.1}
              stroke="var(--color-primary)"
              strokeOpacity={0.4}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}