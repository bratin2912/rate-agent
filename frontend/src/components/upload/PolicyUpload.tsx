
import { useRef, useState } from "react";

interface PolicyUploadProps {
  loading: boolean;
  onUpload: (file: File) => void;
}

export default function PolicyUpload({
  loading,
  onUpload,
}: PolicyUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  function selectFile(selected?: File) {
    if (!selected) return;

    setError("");

    if (
      selected.type !== "application/pdf" &&
      !selected.name.toLowerCase().endsWith(".pdf")
    ) {
      setFile(null);
      setError("Only PDF files are supported.");
      return;
    }

    if (selected.size > 15 * 1024 * 1024) {
      setFile(null);
      setError("Maximum file size is 15 MB.");
      return;
    }

    setFile(selected);
  }

  function submit() {
    if (file && !loading) {
      onUpload(file);
    }
  }

  return (
    <div className="upload-card">
      <div className="upload-heading">
        <div>
          <h2>Upload policy document</h2>
          <p>Select a motor insurance policy PDF to analyse.</p>
        </div>
        <span className="file-badge">PDF ONLY</span>
      </div>

      <div
        className={`drop-zone ${file ? "has-file" : ""}`}
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            inputRef.current?.click();
          }
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          selectFile(event.dataTransfer.files[0]);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          hidden
          onChange={(event) => selectFile(event.target.files?.[0])}
        />

        <div className="upload-icon">↑</div>
        <h3>{file ? file.name : "Drop your PDF here"}</h3>
        <p>
          {file
            ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
            : "or click to browse files"}
        </p>
        <span className="file-limit">Maximum file size: 15 MB</span>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="upload-footer">
        <span>✓ Secure document processing</span>
        <button
          className="primary-button"
          disabled={!file || loading}
          onClick={submit}
        >
          {loading ? "Analysing..." : "Analyse policy →"}
        </button>
      </div>

      {loading && (
        <div className="processing-message">
          <div className="spinner" />
          Uploading and analysing your policy...
        </div>
      )}
    </div>
  );
}
