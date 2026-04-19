import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useGetTopHoldingsQuery } from "@/features/etf/etfApiSlice";
import { formatCurrency, formatDate, formatPercent } from "@/utils/formatters";
import styles from "./TopHoldingsChart.module.css";

interface Props {
  etfId: string;
  limit?: number;
}

const BAR_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

export function TopHoldingsChart({ etfId, limit = 5 }: Props) {
  const { data, isLoading, isError } = useGetTopHoldingsQuery({ etfId, limit });

  if (isLoading) return <div className={styles.state}>Loading top holdings…</div>;
  if (isError || !data)
    return <div className={styles.stateError}>Failed to load top holdings.</div>;

  const chartData = data.holdings.map((h) => ({
    stock_name: h.stock_name,
    holding_size: h.holding_size,
    weight: h.weight,
    latest_price: h.latest_price,
  }));

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>
            {data.etf_name} — Top {limit} Holdings
          </h2>
          <p className={styles.subtitle}>As of {formatDate(data.as_of_date)}</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="var(--color-border-subtle)"
          />
          <XAxis
            dataKey="stock_name"
            tick={{ fontSize: 13, fill: "var(--color-text-secondary)", fontWeight: 600 }}
            tickLine={false}
            axisLine={{ stroke: "var(--color-border)" }}
          />
          <YAxis
            tickFormatter={(v) => formatCurrency(v)}
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            tickLine={false}
            axisLine={false}
            width={70}
          />
          <Tooltip
            cursor={{ fill: "var(--color-surface-hover)" }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload;
              return (
                <div className={styles.tooltip}>
                  <p className={styles.tooltipStockName}>{d.stock_name}</p>
                  <p>Holding size: <strong>{formatCurrency(d.holding_size)}</strong></p>
                  <p>Weight: <strong>{formatPercent(d.weight)}</strong></p>
                  <p>Latest price: <strong>{formatCurrency(d.latest_price)}</strong></p>
                </div>
              );
            }}
          />
          <Bar dataKey="holding_size" radius={[4, 4, 0, 0]} maxBarSize={64}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
