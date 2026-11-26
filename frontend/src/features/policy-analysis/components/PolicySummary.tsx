
import type { PolicyAnalysisResponse } from "../../../../types/policy";

interface Props {
  result: PolicyAnalysisResponse;
}

export default function PolicySummary({ result }: Props) {
  return (
    <>
      <div className="success-banner">
        <div className="success-icon">✓</div>
        <div>
          <strong>Policy processing completed</strong>
          <p>{result.filename}</p>
        </div>
        <span className="success-status">{result.status.toUpperCase()}</span>
      </div>

      <div className="summary-grid">
        <div className="summary-card">
          <span>Document ID</span>
          <strong>#{result.document_id}</strong>
        </div>
        <div className="summary-card">
          <span>Analysis ID</span>
          <strong>#{result.analysis_id}</strong>
        </div>
        <div className="summary-card">
          <span>Current insurer</span>
          <strong>{result.policy.insurer?.current_insurer || "Not available"}</strong>
        </div>
        <div className="summary-card">
          <span>Rating status</span>
          <strong>{result.rating.status || "Not available"}</strong>
        </div>
      </div>
    </>
  );
}
