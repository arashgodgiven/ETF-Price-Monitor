import { useAppDispatch, useAppSelector } from "@/app/hooks";
import { selectETF, selectSelectedETFId } from "@/features/etf/etfSlice";
import { useGetSessionETFsQuery } from "@/features/etf/etfApiSlice";
import { FileUpload } from "@/components/FileUpload/FileUpload";
import styles from "./Sidebar.module.css";

export function Sidebar() {
  const dispatch = useAppDispatch();
  const selectedId = useAppSelector(selectSelectedETFId);
  const { data: etfs, isLoading } = useGetSessionETFsQuery();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.logo}>📈</span>
        <span className={styles.brandName}>ETF Monitor</span>
      </div>

      <div className={styles.section}>
        <p className={styles.sectionLabel}>Upload ETF</p>
        <FileUpload />
      </div>

      <div className={styles.section}>
        <p className={styles.sectionLabel}>This Session</p>

        {isLoading && (
          <p className={styles.hint}>Loading…</p>
        )}

        {!isLoading && (!etfs || etfs.length === 0) && (
          <p className={styles.hint}>No ETFs uploaded yet.</p>
        )}

        <ul className={styles.etfList}>
          {etfs?.map((etf) => (
            <li key={etf.id}>
              <button
                className={`${styles.etfBtn} ${selectedId === etf.id ? styles.active : ""}`}
                onClick={() => dispatch(selectETF(etf.id))}
              >
                <span className={styles.etfName}>{etf.name}</span>
                <span className={styles.etfMeta}>
                  {etf.constituents.length} holdings
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className={styles.footer}>
        <span className={styles.footerText}>BMO Capital Markets</span>
        <span className={styles.footerText}>Data Cognition Team</span>
      </div>
    </aside>
  );
}
