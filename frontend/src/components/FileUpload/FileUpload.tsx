import { useRef, useState, type DragEvent, type ChangeEvent } from "react";
import { useAppDispatch } from "@/app/hooks";
import { selectETF } from "@/features/etf/etfSlice";
import { useUploadETFMutation } from "@/features/etf/etfApiSlice";
import styles from "./FileUpload.module.css";

export function FileUpload() {
  const dispatch = useAppDispatch();
  const [uploadETF, { isLoading, error }] = useUploadETFMutation();
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      alert("Only .csv files are accepted.");
      return;
    }
    try {
      const result = await uploadETF(file).unwrap();
      dispatch(selectETF(result.id));
    } catch {
      // Error is surfaced via RTK Query's `error` state below
    }
  };

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value=""; // Reset input so re-uploading the same file triggers onChange
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const getErrorMessage = (): string | null => {
    if (!error) return null;
    if ("data" in error) {
      const data = error.data as { error?: string };
      return data?.error ?? "Upload failed!";
    }
    return "Network error! Please try again.";
  };

  return (
    <div className={styles.wrapper}>
      <div
        className={`${styles.dropzone} ${isDragging ? styles.dragging : ""} ${isLoading ? styles.loading : ""}`}
          onClick={() => inputRef.current?.click()}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={() => setIsDragging(false)}
          role="button"
          tabIndex={0}
          aria-label="Upload an ETF CSV file"
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            onChange={onInputChange}
            className={styles.hiddenInput}
            aria-hidden="true"
          />

          {isLoading? (
            <div className={styles.uploading}>
              <span className={styles.spinner} aria-hidden="true" />
              <span>Uploading...</span>
            </div>
          ) : (
            <>
              <div className={styles.icon} aria-hidden="true">📂</div>
              <p className={styles.primaryText}>
                Drop ETF CSV here or <span className={styles.link}>browse</span>
              </p>
              <p className={styles.secondaryText}>
                Expects columns: <code>name</code>, <code>weight</code>
              </p>
            </>
          )}
      </div>

      {getErrorMessage() && (
        <p className={styles.error} role="alert">
          {getErrorMessage()}
        </p>
      )}
    </div>
  );
}