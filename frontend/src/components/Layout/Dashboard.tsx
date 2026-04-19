import { useAppSelector } from "@/app/hooks";
import { selectSelectedETFId } from "@/features/etf/etfSlice";
import { PriceChart } from "@/components/PriceChart/PriceChart";
import { TopHoldingsChart } from "@/components/TopHoldingsChart/TopHoldingsChart";
import { HoldingsTable } from "@/components/HoldingsTable/HoldingsTable";
import styles from "./Dashboard.module.css";

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
    </main>
  );
}