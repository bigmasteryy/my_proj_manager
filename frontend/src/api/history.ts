import { http, unwrap } from "./client";
import type { HistoryLogItem } from "../types/models";

export interface HistoryQuery {
  broker_id?: number;
  project_id?: number;
  start_date?: string;
  end_date?: string;
  keyword?: string;
}

export function getHistoryLogs(params: HistoryQuery) {
  return unwrap<HistoryLogItem[]>(http.get("/history/logs", { params }));
}
