
import { useState } from "react";

import { policyApi } from "../../../../api/policyApi";
import type { PolicyAnalysisResponse } from "../../../../types/policy";

import PolicyUpload from "../../../components/upload/PolicyUpload";
import PolicySummary from "../components/PolicySummary";
import VehicleDetails from "../components/VehicleDetails";
import PremiumBreakup from "../components/PremiumBreakup";
import CommissionResult from "../components/CommissionResult";
import DecisionTrace from "../components/DecisionTrace";

export default function PolicyAnalysisPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PolicyAnalysisResponse | null>(null);
  const [error, setError] = useState("");

  async function handleUpload(file: File) {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await policyApi.analyze(file);
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to process the policy."
      );
    } finally {
      setLoading(false);
    }
  }

  function resetAnalysis() {
    setResult(null);
    setError("");
  }

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <p className="eyebrow">MOTOR INSURANCE</p>
          <h1>Policy Rating Workspace</h1>
          <p className="subtitle">
            Extract policy information and evaluate insurer commission grids.
          </p>
        </div>

        {result && (
          <button className="secondary-button" onClick={resetAnalysis}>
            + New analysis
          </button>
        )}
      </div>

      {!result ? (
        <PolicyUpload loading={loading} onUpload={handleUpload} />
      ) : (
        <div className="results-container">
          <PolicySummary result={result} />

          <section className="result-section">
            <h3>Insurer and policy details</h3>
            <div className="details-grid">
              <div className="detail-item">
                <span>Current insurer</span>
                <strong>{result.policy.insurer?.current_insurer ?? "Not available"}</strong>
              </div>
              <div className="detail-item">
                <span>Previous insurer</span>
                <strong>{result.policy.insurer?.previous_insurer ?? "Not available"}</strong>
              </div>
              <div className="detail-item">
                <span>Business type</span>
                <strong>{result.policy.insurer?.business_type ?? "Not available"}</strong>
              </div>
              <div className="detail-item">
                <span>Policy type</span>
                <strong>{result.policy.policy_type ?? "Not available"}</strong>
              </div>
              <div className="detail-item">
                <span>NCB</span>
                <strong>
                  {result.policy.ncb_percentage == null
                    ? "Not available"
                    : `${result.policy.ncb_percentage}%`}
                </strong>
              </div>
              <div className="detail-item">
                <span>Policy number</span>
                <strong>{result.policy.policy_number ?? "Not available"}</strong>
              </div>
            </div>
          </section>

          <VehicleDetails vehicle={result.policy.vehicle} />

          <PremiumBreakup premium={result.policy.premium} />

          <CommissionResult rating={result.rating} />

          <DecisionTrace rating={result.rating} />

          {result.rating.matched_records?.length ? (
            <section className="result-section">
              <h3>Matched grid records</h3>
              {result.rating.matched_records.map((record, index) => (
                <pre className="json-block" key={index}>
                  {JSON.stringify(record, null, 2)}
                </pre>
              ))}
            </section>
          ) : null}

          <details className="raw-data">
            <summary>View complete API response</summary>
            <pre className="json-block">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );
}
