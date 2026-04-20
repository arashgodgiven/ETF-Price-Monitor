import { useState, useMemo, useRef, useEffect } from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useGetETFSummaryQuery } from "@/features/etf/etfApiSlice";
import { formatCurrency, formatPercent } from "@/utils/formatters";
import type { Constituent } from "@/types/etf";
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

interface TextFilter {
  value: string;
}

interface RangeFilter {
  min: string;
  max: string;
}

interface FilterState {
  stock_name: TextFilter;
  weight: RangeFilter;
  latest_price: RangeFilter;
}

interface SearchOpenState {
  stock_name: boolean;
  weight: boolean;
  latest_price: boolean;
}

interface ColumnVisibility {
  stock_name: boolean;
  weight: boolean;
  latest_price: boolean;
}

const EMPTY_FILTERS: FilterState = {
  stock_name: { value: "" },
  weight: { min: "", max: "" },
  latest_price: { min: "", max: "" },
};

function SortIcon({ direction }: { direction: SortDirection }) {
  if (direction === "asc") return <span className={styles.sortActive}>↑</span>;
  if (direction === "desc") return <span className={styles.sortActive}>↓</span>;
  return <span className={styles.sortIdle}>↕</span>;
}

function SearchIconButton({
  active,
  onClick,
}: {
  active: boolean;
  onClick: (e: React.MouseEvent) => void;
}) {
  return (
    <button
      className={`${styles.searchBtn} ${active ? styles.searchBtnActive : ""}`}
      onClick={onClick}
      title="Filter this column"
    >
      🔍
    </button>
  );
}

// ── Draggable row ──────────────────────────────────────────
function SortableRow({
  constituent,
  colVisible,
}: {
  constituent: Constituent;
  colVisible: ColumnVisibility;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: constituent.stock_name });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    background: isDragging ? "var(--color-primary-subtle)" : undefined,
  };

  return (
    <tr ref={setNodeRef} style={style}>
      <td className={styles.dragCell}>
        <button
          className={styles.dragHandle}
          {...attributes}
          {...listeners}
          title="Drag to reorder"
        >
          ⠿
        </button>
      </td>
      <td>
        {colVisible.stock_name && (
          <span className={styles.stock_name}>{constituent.stock_name}</span>
        )}
      </td>
      <td className={styles.right}>
        {colVisible.weight && formatPercent(constituent.weight)}
      </td>
      <td className={styles.right}>
        {colVisible.latest_price &&
          (constituent.latest_price != null ? (
            formatCurrency(constituent.latest_price)
          ) : (
            <span className={styles.na}>N/A</span>
          ))}
      </td>
    </tr>
  );
}

// ── Main component ─────────────────────────────────────────
export function HoldingsTable({ etfId }: Props) {
  const { data, isLoading, isError } = useGetETFSummaryQuery(etfId);

  const [sort, setSort] = useState<SortState>({ field: null, direction: "none" });
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [searchOpen, setSearchOpen] = useState<SearchOpenState>({
    stock_name: false,
    weight: false,
    latest_price: false,
  });
  const [colVisible, setColVisible] = useState<ColumnVisibility>({
    stock_name: true,
    weight: true,
    latest_price: true,
  });
  const [manualOrder, setManualOrder] = useState<string[] | null>(null);

  const stockNameInputRef = useRef<HTMLInputElement>(null);
  const weightMinRef = useRef<HTMLInputElement>(null);
  const priceMinRef = useRef<HTMLInputElement>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    })
  );

  // Reset manual order when ETF changes
  useEffect(() => {
    setManualOrder(null);
  }, [etfId]);

  useEffect(() => {
    if (searchOpen.stock_name) stockNameInputRef.current?.focus();
  }, [searchOpen.stock_name]);

  useEffect(() => {
    if (searchOpen.weight) weightMinRef.current?.focus();
  }, [searchOpen.weight]);

  useEffect(() => {
    if (searchOpen.latest_price) priceMinRef.current?.focus();
  }, [searchOpen.latest_price]);

  const toggleSearch = (field: keyof SearchOpenState, e: React.MouseEvent) => {
    e.stopPropagation();
    setSearchOpen((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const closeSearch = (field: keyof SearchOpenState, e: React.MouseEvent) => {
    e.stopPropagation();
    setSearchOpen((prev) => ({ ...prev, [field]: false }));
  };

  const clearAllFilters = () => {
    setFilters(EMPTY_FILTERS);
    setSearchOpen({ stock_name: false, weight: false, latest_price: false });
  };

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

  const toggleColumn = (col: keyof ColumnVisibility, e: React.MouseEvent) => {
    e.stopPropagation();
    setColVisible((prev) => ({ ...prev, [col]: !prev[col] }));
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    // Use the currently displayed (possibly sorted) order as the base
    const displayedOrder = processedConstituents.map((c) => c.stock_name);

    const oldIndex = displayedOrder.indexOf(active.id as string);
    const newIndex = displayedOrder.indexOf(over.id as string);

    const newOrder = arrayMove(displayedOrder, oldIndex, newIndex);

    // Reset sort — list is now manually ordered
    setSort({ field: null, direction: "none" });
    setManualOrder(newOrder);
  };

  const hasActiveFilter = (field: keyof FilterState): boolean => {
    if (field === "stock_name") return filters.stock_name.value.trim() !== "";
    const f = filters[field] as RangeFilter;
    return f.min.trim() !== "" || f.max.trim() !== "";
  };

  const anyFilterActive =
    hasActiveFilter("stock_name") ||
    hasActiveFilter("weight") ||
    hasActiveFilter("latest_price");

  const processedConstituents = useMemo(() => {
    if (!data?.constituents) return [];

    // Apply manual order first
    let rows = [...data.constituents];
    if (manualOrder) {
      rows.sort(
        (a, b) =>
          manualOrder.indexOf(a.stock_name) - manualOrder.indexOf(b.stock_name)
      );
    }

    // Text filter
    const stockNameFilter = filters.stock_name.value.trim().toLowerCase();
    if (stockNameFilter) {
      rows = rows.filter((r) =>
        r.stock_name.toLowerCase().includes(stockNameFilter)
      );
    }

    // Weight range filter
    const wMin = filters.weight.min.trim();
    const wMax = filters.weight.max.trim();
    if (wMin !== "") rows = rows.filter((r) => r.weight >= parseFloat(wMin) / 100);
    if (wMax !== "") rows = rows.filter((r) => r.weight <= parseFloat(wMax) / 100);

    // Price range filter
    const pMin = filters.latest_price.min.trim();
    const pMax = filters.latest_price.max.trim();
    if (pMin !== "")
      rows = rows.filter(
        (r) => r.latest_price != null && r.latest_price >= parseFloat(pMin)
      );
    if (pMax !== "")
      rows = rows.filter(
        (r) => r.latest_price != null && r.latest_price <= parseFloat(pMax)
      );

    // Column sort (overrides manual order)
    if (sort.field && sort.direction !== "none") {
      rows.sort((a, b) => {
        let aVal: string | number;
        let bVal: string | number;

        if (sort.field === "stock_name") {
          aVal = a.stock_name;
          bVal = b.stock_name;
        } else if (sort.field === "weight") {
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
    }

    return rows;
  }, [data?.constituents, filters, sort, manualOrder]);

  if (isLoading) return <div className={styles.state}>Loading constituents…</div>;
  if (isError || !data)
    return <div className={styles.stateError}>Failed to load constituents.</div>;

  const totalCount = data.constituents.length;
  const filteredCount = processedConstituents.length;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <h2 className={styles.title}>Constituents</h2>
        <span className={styles.badge}>{totalCount} holdings</span>
      </div>

      {anyFilterActive && (
        <div className={styles.filterBar}>
          <span className={styles.filterBarText}>
            🔍 Showing {filteredCount} of {totalCount} holdings
          </span>
          <button className={styles.clearBtn} onClick={clearAllFilters}>
            Clear all filters
          </button>
        </div>
      )}

      <div className={styles.tableWrapper}>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <table className={styles.table}>
            <thead>
              <tr>
                {/* Drag handle column */}
                <th className={styles.dragHeader}>
                  <button
                    className={styles.eyeBtn}
                    onClick={(e) => toggleColumn("stock_name", e)}
                    title={colVisible.stock_name ? "Hide stock column" : "Show stock column"}
                  >
                    {colVisible.stock_name ? "👁" : "◡"}
                  </button>
                </th>

                {/* Stock Name header */}
                <th
                  className={`${styles.sortable} ${sort.field === "stock_name" ? styles.sorted : ""}`}
                  onClick={() => !searchOpen.stock_name && handleSort("stock_name")}
                >
                  {searchOpen.stock_name ? (
                    <span className={styles.searchCell}>
                      <input
                        ref={stockNameInputRef}
                        className={styles.searchInput}
                        placeholder="Search stock…"
                        value={filters.stock_name.value}
                        onChange={(e) =>
                          setFilters((f) => ({
                            ...f,
                            stock_name: { value: e.target.value },
                          }))
                        }
                        onClick={(e) => e.stopPropagation()}
                      />
                      <button
                        className={styles.closeBtn}
                        onClick={(e) => closeSearch("stock_name", e)}
                      >
                        ✕
                      </button>
                    </span>
                  ) : (
                    <span className={styles.thInner}>
                      
                      Stock
                      <SortIcon
                        direction={sort.field === "stock_name" ? sort.direction : "none"}
                      />
                      <SearchIconButton
                        active={hasActiveFilter("stock_name")}
                        onClick={(e) => toggleSearch("stock_name", e)}
                      />
                    </span>
                  )}
                </th>

                {/* Weight header */}
                <th
                  className={`${styles.right} ${styles.sortable} ${sort.field === "weight" ? styles.sorted : ""}`}
                  onClick={() => !searchOpen.weight && handleSort("weight")}
                >
                  {searchOpen.weight ? (
                    <span className={styles.searchCell}>
                      <input
                        ref={weightMinRef}
                        className={styles.rangeInput}
                        placeholder="min %"
                        value={filters.weight.min}
                        onChange={(e) =>
                          setFilters((f) => ({
                            ...f,
                            weight: { ...f.weight, min: e.target.value },
                          }))
                        }
                        onClick={(e) => e.stopPropagation()}
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                      />
                      <span className={styles.rangeSep}>—</span>
                      <input
                        className={styles.rangeInput}
                        placeholder="max %"
                        value={filters.weight.max}
                        onChange={(e) =>
                          setFilters((f) => ({
                            ...f,
                            weight: { ...f.weight, max: e.target.value },
                          }))
                        }
                        onClick={(e) => e.stopPropagation()}
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                      />
                      <button
                        className={styles.closeBtn}
                        onClick={(e) => closeSearch("weight", e)}
                      >
                        ✕
                      </button>
                    </span>
                  ) : (
                    <span className={styles.thInner}>
                      <button
                        className={styles.eyeBtn}
                        onClick={(e) => toggleColumn("weight", e)}
                        title={colVisible.weight ? "Hide column" : "Show column"}
                      >
                        {colVisible.weight ? "👁" : "◡"}
                      </button>
                      Weight
                      <SortIcon
                        direction={sort.field === "weight" ? sort.direction : "none"}
                      />
                      <SearchIconButton
                        active={hasActiveFilter("weight")}
                        onClick={(e) => toggleSearch("weight", e)}
                      />
                    </span>
                  )}
                </th>

                {/* Latest Close header */}
                <th
                  className={`${styles.right} ${styles.sortable} ${sort.field === "latest_price" ? styles.sorted : ""}`}
                  onClick={() =>
                    !searchOpen.latest_price && handleSort("latest_price")
                  }
                >
                  {searchOpen.latest_price ? (
                    <span className={styles.searchCell}>
                      <input
                        ref={priceMinRef}
                        className={styles.rangeInput}
                        placeholder="min $"
                        value={filters.latest_price.min}
                        onChange={(e) =>
                          setFilters((f) => ({
                            ...f,
                            latest_price: {
                              ...f.latest_price,
                              min: e.target.value,
                            },
                          }))
                        }
                        onClick={(e) => e.stopPropagation()}
                        type="number"
                        step="0.01"
                        min="0"
                      />
                      <span className={styles.rangeSep}>—</span>
                      <input
                        className={styles.rangeInput}
                        placeholder="max $"
                        value={filters.latest_price.max}
                        onChange={(e) =>
                          setFilters((f) => ({
                            ...f,
                            latest_price: {
                              ...f.latest_price,
                              max: e.target.value,
                            },
                          }))
                        }
                        onClick={(e) => e.stopPropagation()}
                        type="number"
                        step="0.01"
                        min="0"
                      />
                      <button
                        className={styles.closeBtn}
                        onClick={(e) => closeSearch("latest_price", e)}
                      >
                        ✕
                      </button>
                    </span>
                  ) : (
                    <span className={styles.thInner}>
                      <button
                        className={styles.eyeBtn}
                        onClick={(e) => toggleColumn("latest_price", e)}
                        title={colVisible.latest_price ? "Hide column" : "Show column"}
                      >
                        {colVisible.latest_price ? "👁" : "◡"}
                      </button>
                      Latest Close
                      <SortIcon
                        direction={sort.field === "latest_price" ? sort.direction : "none"}
                      />
                      <SearchIconButton
                        active={hasActiveFilter("latest_price")}
                        onClick={(e) => toggleSearch("latest_price", e)}
                      />
                    </span>
                  )}
                </th>
              </tr>
            </thead>
            <tbody>
              <SortableContext
                items={processedConstituents.map((c) => c.stock_name)}
                strategy={verticalListSortingStrategy}
              >
                {processedConstituents.length === 0 ? (
                  <tr>
                    <td colSpan={4} className={styles.noResults}>
                      No holdings match the current filters.
                    </td>
                  </tr>
                ) : (
                  processedConstituents.map((c) => (
                    <SortableRow
                      key={c.stock_name}
                      constituent={c}
                      colVisible={colVisible}
                    />
                  ))
                )}
              </SortableContext>
            </tbody>
          </table>
        </DndContext>
      </div>
    </div>
  );
}