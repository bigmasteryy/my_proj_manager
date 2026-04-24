import { http, unwrap } from "./client";

export function resetDemoData() {
  return unwrap(http.post("/system/reset-demo"));
}
