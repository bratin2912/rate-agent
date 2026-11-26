
import type { VehicleDetails as Vehicle } from "../../../../types/policy";

interface Props {
  vehicle?: Vehicle;
}

export default function VehicleDetails({ vehicle = {} }: Props) {
  const fields = [
    ["Registration number", vehicle.registration_number],
    ["Make", vehicle.make],
    ["Model", vehicle.model],
    ["Fuel type", vehicle.fuel_type],
    ["Engine CC", vehicle.engine_cc],
    ["Manufacture year", vehicle.manufacture_year],
    ["Vehicle age", vehicle.vehicle_age],
    ["RTO code", vehicle.rto_code],
    ["Vehicle category", vehicle.vehicle_category],
  ];

  return (
    <section className="result-section">
      <h3>Vehicle information</h3>
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
