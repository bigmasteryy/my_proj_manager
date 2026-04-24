import { http, unwrap } from "./client";
import type { DashboardOverview, DashboardProject } from "../types/models";

export function getDashboardOverview() {
  return unwrap<DashboardOverview>(http.get("/dashboard/overview"));
}

export function getDashboardProjects() {
  return unwrap<DashboardProject[]>(http.get("/dashboard/projects"));
}
