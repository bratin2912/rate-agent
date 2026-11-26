
import type { RatingResult } from "../../../../types/policy";

interface Props {
  rating: RatingResult;
}

export default function CommissionResult({ rating }: Props) {
  const commission = rating.commission ?? {};

  return (
    <section className="result-section">
      <h3>Commission evaluation</h3>

      <div className="commission-grid">
        <div className="commission-card">
          <span>OD commission</span>
          <strong>
            {commission.od_rate_percent == null
              ? "Not calculated"
              : `${commission.od_rate_percent}%`}
          </strong>
          <small>Own damage</small>
        </div>

        <div className="commission-card">
          <span>TP commission</span>
          <strong>
            {commission.tp_rate_percent == null
              ? "Not calculated"
              : `${commission.tp_rate_percent}%`}
          </strong>
          <small>Third party</small>
        </div>
      </div>

      <p className="rating-explanation">
        {commission.reason || "No commission calculation explanation returned."}
      </p>

      {rating.warnings?.map((warning, index) => (
        <div className="warning-message" key={index}>
          {warning}
        </div>
      ))}
    </section>
  );
}
