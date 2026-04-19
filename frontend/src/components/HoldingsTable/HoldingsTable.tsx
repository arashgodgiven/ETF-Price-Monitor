import { useGetETFSummaryQuery } from "@/features/etf/etfApiSlice";
import { formatCurrency, formatPercent} from "@/utils/formatters";
import styles from "./HoldingsTable.module.css";

interface Props {
  etfId: string;
}

export function HoldingsTable({ etfId }: Props) {
  const { data, isLoading, isError } = useGetETFSummaryQuery(etfId);

  if (isLoading) return <div className={styles.state}>Loading constituents...</div>;
  if (isError || !data)
    return <div className={styles.stateError}>Failed to load constituents.</div>;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <h2 className={styles.title}>Constituents: {data.name}</h2>
        <span className={styles.badge}>{data.constituents.length} holdings</span>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Ticker</th>
              <th className={styles.right}>Weight</th>
              <th className={styles.right}>Latest Close</th>
            </tr>
          </thead>
          <tbody>
            {data.constituents.map((c) =>(
              <tr key={c.stock_name}>
                <td>
                  <span className={styles.stock_name}>{c.stock_name}</span>
                </td>
                <td className={styles.right}>{formatPercent(c.weight)}</td>
                <td className={styles.right}>
                  {c.latest_price != null ? formatCurrency(c.latest_price) : <span className={styles.na}>N/A</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}