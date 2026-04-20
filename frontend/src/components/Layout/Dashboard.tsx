import { useAppSelector } from "@/app/hooks";
import { formatCurrency, formatDate } from "@/utils/formatters";
import { selectSelectedETFId } from "@/features/etf/etfSlice";
import { useGetETFSummaryQuery, useGetPriceHistoryQuery } from "@/features/etf/etfApiSlice";
import { PriceChart } from "@/components/PriceChart/PriceChart";
import { TopHoldingsChart } from "@/components/TopHoldingsChart/TopHoldingsChart";
import { HoldingsTable } from "@/components/HoldingsTable/HoldingsTable";
import styles from "./Dashboard.module.css";

function ETFHeader({ etfId }: { etfId: string }) {
  const { data } = useGetETFSummaryQuery(etfId);
  const { data: history } = useGetPriceHistoryQuery({ etfId });

  if (!data) return null;

  const series = history?.series ?? [];
  const prices = series.map((p) => p.price);
  const latestPrice = prices[prices.length - 1];
  const highestPrice = prices.length ? Math.max(...prices) : null;
  const lowestPrice = prices.length ? Math.min(...prices) : null;
  const dateFrom = series[0]?.date;
  const dateTo = series[series.length - 1]?.date;

  return (
    <div className={styles.etfHeader}>
      <div className={styles.etfHeaderLeft}>
        <div className={styles.etfIconBadge}>📈</div>
        <div>
          <h1 className={styles.etfName}>{data.name}</h1>
          <p className={styles.etfMeta}>
            {dateFrom && dateTo
              ? `${formatDate(dateFrom)} → ${formatDate(dateTo)}`
              : "Loading date range…"}
          </p>
        </div>
      </div>
      <div className={styles.etfHeaderRight}>
        <div className={styles.etfStat}>
          <span className={styles.etfStatLabel}>Latest Price</span>
          <span className={styles.etfStatValue}>
            {latestPrice != null ? formatCurrency(latestPrice) : "—"}
          </span>
        </div>
        <div className={styles.etfStatDivider} />
        <div className={styles.etfStat}>
          <span className={styles.etfStatLabel}>Highest Price</span>
          <span className={`${styles.etfStatValue} ${styles.etfStatHigh}`}>
            {highestPrice != null ? formatCurrency(highestPrice) : "—"}
          </span>
        </div>
        <div className={styles.etfStatDivider} />
        <div className={styles.etfStat}>
          <span className={styles.etfStatLabel}>Lowest Price</span>
          <span className={`${styles.etfStatValue} ${styles.etfStatLow}`}>
            {lowestPrice != null ? formatCurrency(lowestPrice) : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

export function Dashboard() {
  const etfId = useAppSelector(selectSelectedETFId);

  if (!etfId) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyInner}>
          <span className={styles.emptyIcon}>📊</span>
          <h1 className={styles.emptyTitle}>ETF Price Monitor</h1>
          <p className={styles.emptyText}>
            Upload an ETF CSV from the sidebar to get started.
          </p>
          <p className={styles.emptyHint}>
            File must contain <code>name</code> and <code>weight</code> columns.
          </p>
        </div>
      </div>
    );
  }

  return (
    <main className={styles.dashboard}>
      <div className={styles.content}>
        <ETFHeader etfId={etfId} />
        <div className={styles.grid}>
          <section className={`${styles.card} ${styles.fullWidth}`}>
            <PriceChart etfId={etfId} />
          </section>
          <section className={styles.card}>
            <TopHoldingsChart etfId={etfId} limit={5} />
          </section>
          <section className={styles.card}>
            <HoldingsTable etfId={etfId} />
          </section>
        </div>
      </div>
    </main>
  );
}