
import type { PremiumBreakup as Premium } from "../../../../types/policy";

interface Props {
  premium?: Premium;
}

export default function PremiumBreakup({ premium = {} }: Props) {
  const fields = [
    ["Own damage premium", premium.own_damage_premium],
    ["Third-party premium", premium.third_party_premium],
    ["Add-on premium", premium.add_on_premium],
    ["Net premium", premium.net_premium],
    ["GST", premium.gst],
    ["Total premium", premium.total_premium],
  ];

  return (
    <section className="result-section">
      <h3>Premium breakup</h3>
      <div className="details-grid">
        {fields.map(([name, data]) => (
          <div className="detail-item" key={name}>
            <span>{name}</span>
            <strong>{data ?? "Not available"}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
