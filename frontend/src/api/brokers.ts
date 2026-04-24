import { http, unwrap } from "./client";
import type { BrokerCreatePayload, BrokerSummary, BrokerUpdatePayload } from "../types/models";

export function getBrokers() {
  return unwrap<BrokerSummary[]>(http.get("/brokers"));
}

export function createBroker(payload: BrokerCreatePayload) {
  return unwrap<BrokerSummary>(http.post("/brokers", payload));
}

export function updateBroker(brokerId: number, payload: BrokerUpdatePayload) {
  return unwrap<BrokerSummary>(http.put(`/brokers/${brokerId}`, payload));
}

export function deleteBroker(brokerId: number) {
  return unwrap(http.delete(`/brokers/${brokerId}`));
}
