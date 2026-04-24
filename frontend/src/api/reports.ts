import { http, unwrap } from "./client";
import type { WeeklyReport } from "../types/models";

export interface ReportQuery {
  broker_id?: number;
  owner_name?: string;
}

export function getWeeklyReportPreview(params: ReportQuery = {}) {
  return unwrap<WeeklyReport>(http.get("/reports/weekly/preview", { params }));
}
