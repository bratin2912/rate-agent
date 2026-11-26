
import type { RatingResult } from "../../../../types/policy";

interface Props {
  rating: RatingResult;
}

export default function DecisionTrace({ rating }: Props) {
  const trace = rating.decision_trace ?? [];

  if (!trace.length) return null;

  return (
    <section className="result-section">
      <h3>Decision trace</h3>

      <div className="trace-list">
        {trace.map((step, index) => (
          <div className="trace-item" key={index}>
            <div className="trace-number">{index + 1}</div>
            <div>
              <strong>{step.rule || step.step || "Decision"}</strong>
              <p>
                {step.explanation || step.outcome || "No explanation returned."}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
