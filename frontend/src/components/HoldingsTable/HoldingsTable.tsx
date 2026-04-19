import { useState, useMemo } from "react";
import { useGetETFSummaryQuery } from "@/features/etf/etfApiSlice";
import { formatCurrency, formatPercent } from "@/utils/formatters";
import styles from "./HoldingsTable.module.css";

interface Props {
  etfId: string;
}

type SortField = "stock_name" | "weight" | "latest_price";
type SortDirection = "asc" | "desc" | "none";

interface SortState {
  field: SortField | null;
  direction: SortDirection;
}

function SortIcon({ direction }: { direction: SortDirection }) {
  if (direction === "asc") return <span className={styles.sortActive}>↑</span>;
  if (direction === "desc") return <span className={styles.sortActive}>↓</span>;
  return <span className={styles.sortIdle}>↕</span>;
}

export function HoldingsTable({ etfId }: Props) {
  const { data, isLoading, isError } = useGetETFSummaryQuery(etfId);
  const [sort, setSort] = useState<SortState>({ field: null, direction: "none" });

  const handleSort = (field: SortField) => {
    setSort((prev) => {
      if (prev.field === field) {
        if (prev.direction === "none") return { field, direction: "asc" };
        if (prev.direction === "asc") return { field, direction: "desc" };
        return { field: null, direction: "none" };
      }
      return { field, direction: "asc" };
    });
  };

  const sortedConstituents = useMemo(() => {
    if (!data?.constituents) return [];
    if (!sort.field || sort.direction === "none") return data.constituents;

    return [...data.constituents].sort((a, b) => {
      const field = sort.field as SortField;

      let aVal: string | number;
      let bVal: string | number;

      if (field === "stock_name") {
        aVal = a.stock_name;
        bVal = b.stock_name;
      } else if (field === "weight") {
        aVal = a.weight;
        bVal = b.weight;
      } else {
        aVal = a.latest_price ?? -Infinity;
        bVal = b.latest_price ?? -Infinity;
      }

      if (aVal < bVal) return sort.direction === "asc" ? -1 : 1;
      if (aVal > bVal) return sort.direction === "asc" ? 1 : -1;
      return 0;
    });
  }, [data?.constituents, sort]);

  if (isLoading) return <div className={styles.state}>Loading constituents…</div>;
  if (isError || !data)
    return <div className={styles.stateError}>Failed to load constituents.</div>;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <h2 className={styles.title}>Constituents: {data.name} </h2>
        <span className={styles.badge}>{data.constituents.length} holdings</span>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th
                className={`${styles.sortable} ${sort.field === "stock_name" ? styles.sorted : ""}`}
                onClick={() => handleSort("stock_name")}
              >
                <span className={styles.thInner}>
                  Ticker
                  <SortIcon direction={sort.field === "stock_name" ? sort.direction : "none"} />
                </span>
              </th>
              <th
                className={`${styles.right} ${styles.sortable} ${sort.field === "weight" ? styles.sorted : ""}`}
                onClick={() => handleSort("weight")}
              >
                <span className={`${styles.thInner}`}>
                  Weight
                  <SortIcon direction={sort.field === "weight" ? sort.direction : "none"} />
                </span>
              </th>
              <th
                className={`${styles.right} ${styles.sortable} ${sort.field === "latest_price" ? styles.sorted : ""}`}
                onClick={() => handleSort("latest_price")}
              >
                <span className={`${styles.thInner}`}>
                  Latest Close
                  <SortIcon direction={sort.field === "latest_price" ? sort.direction : "none"} />
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedConstituents.map((c) => (
              <tr key={c.stock_name}>
                <td>
                  <span className={styles.ticker}>{c.stock_name}</span>
                </td>
                <td className={styles.right}>{formatPercent(c.weight)}</td>
                <td className={styles.right}>
                  {c.latest_price != null
                    ? formatCurrency(c.latest_price)
                    : <span className={styles.na}>N/A</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}