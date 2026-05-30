import { http, unwrap } from "./client";
import type {
  BrokerIssueDetail,
  BrokerIssuePayload,
  BrokerIssueStatusPayload,
  BrokerIssueSummary
} from "../types/models";

export function getBrokerIssues(params: {
  issue_type?: string;
  status?: string;
  priority?: string;
  broker_id?: number;
  keyword?: string;
}) {
  return unwrap<BrokerIssueSummary[]>(http.get("/broker-issues", { params }));
}

export function getBrokerIssueDetail(issueId: number) {
  return unwrap<BrokerIssueDetail>(http.get(`/broker-issues/${issueId}`));
}

export function createBrokerIssue(payload: BrokerIssuePayload) {
  return unwrap<{ id: number }>(http.post("/broker-issues", payload));
}

export function updateBrokerIssue(issueId: number, payload: BrokerIssuePayload) {
  return unwrap<{ id: number }>(http.put(`/broker-issues/${issueId}`, payload));
}

export function updateBrokerIssueStatus(issueId: number, statusId: number, payload: Omit<BrokerIssueStatusPayload, "broker_id">) {
  return unwrap<{ id: number }>(http.put(`/broker-issues/${issueId}/brokers/${statusId}`, payload));
}

export function deleteBrokerIssue(issueId: number) {
  return unwrap<{ id: number; deleted: boolean }>(http.delete(`/broker-issues/${issueId}`));
}
