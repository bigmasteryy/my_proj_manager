import { http, unwrap } from "./client";
import type {
  BrokerCreatePayload,
  BrokerDetail,
  BrokerEntrustSiteItem,
  BrokerEntrustSitePayload,
  BrokerFeaturedUpdatePayload,
  BrokerOverview,
  BrokerServerItem,
  BrokerServerPayload,
  BrokerSummary,
  BrokerUpdatePayload
} from "../types/models";

export function getBrokers() {
  return unwrap<BrokerSummary[]>(http.get("/brokers"));
}

export function getBrokerOverview() {
  return unwrap<BrokerOverview>(http.get("/brokers/overview"));
}

export function updateBrokerFeatured(payload: BrokerFeaturedUpdatePayload) {
  return unwrap<{ brokerIds: number[] }>(http.post("/brokers/overview/featured", payload));
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

export function getBrokerDetail(brokerId: number) {
  return unwrap<BrokerDetail>(http.get(`/brokers/${brokerId}`));
}

export function createBrokerServer(brokerId: number, payload: BrokerServerPayload) {
  return unwrap<BrokerServerItem>(http.post(`/brokers/${brokerId}/servers`, payload));
}

export function updateBrokerServer(serverId: number, payload: BrokerServerPayload) {
  return unwrap<BrokerServerItem>(http.put(`/brokers/servers/${serverId}`, payload));
}

export function deleteBrokerServer(serverId: number) {
  return unwrap<{ id: number; deleted: boolean }>(http.delete(`/brokers/servers/${serverId}`));
}

export function createBrokerEntrustSite(brokerId: number, payload: BrokerEntrustSitePayload) {
  return unwrap<BrokerEntrustSiteItem>(http.post(`/brokers/${brokerId}/entrust-sites`, payload));
}

export function updateBrokerEntrustSite(siteId: number, payload: BrokerEntrustSitePayload) {
  return unwrap<BrokerEntrustSiteItem>(http.put(`/brokers/entrust-sites/${siteId}`, payload));
}

export function deleteBrokerEntrustSite(siteId: number) {
  return unwrap<{ id: number; deleted: boolean }>(http.delete(`/brokers/entrust-sites/${siteId}`));
}
