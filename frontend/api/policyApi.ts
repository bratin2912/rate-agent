import { apiRequest } from "./client";
import type { PolicyAnalysisResponse } from "../types/policy";

export const policyApi = {
  async analyze(file: File): Promise<PolicyAnalysisResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return apiRequest<PolicyAnalysisResponse>(
      "/api/v1/policies/extract",
      {
        method: "POST",
        body: formData,
      }
    );
  },
};
