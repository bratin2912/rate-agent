
export interface VehicleDetails {
  registration_number?: string | null;
  make?: string | null;
  model?: string | null;
  fuel_type?: string | null;
  engine_cc?: number | null;
  manufacture_year?: number | null;
  vehicle_age?: number | null;
  rto_code?: string | null;
  vehicle_category?: string | null;
}

export interface InsurerDetails {
  current_insurer?: string | null;
  previous_insurer?: string | null;
  business_type?: string | null;
}

export interface PremiumBreakup {
  own_damage_premium?: number | null;
  third_party_premium?: number | null;
  add_on_premium?: number | null;
  net_premium?: number | null;
  gst?: number | null;
  total_premium?: number | null;
}

export interface PolicyDetails {
  policy_number?: string | null;
  policy_type?: string | null;
  ncb_percentage?: number | null;
  vehicle?: VehicleDetails;
  insurer?: InsurerDetails;
  premium?: PremiumBreakup;
}

export interface CommissionResult {
  od_rate_percent?: number | null;
  tp_rate_percent?: number | null;
  status?: string;
  reason?: string;
}

export interface RatingResult {
  status?: string;
  commission?: CommissionResult;
  matched_records?: Array<Record<string, unknown>>;
  decision_trace?: Array<{
    step?: string;
    rule?: string;
    outcome?: string;
    explanation?: string;
  }>;
  warnings?: string[];
}

export interface PolicyAnalysisResponse {
  document_id: number | string;
  analysis_id: number | string;
  status: string;
  filename: string;
  policy: PolicyDetails;
  extraction: Record<string, unknown>;
  rating: RatingResult;
}
