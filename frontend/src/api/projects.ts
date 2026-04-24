import { http, unwrap } from "./client";
import type {
  DashboardProject,
  ProjectCreatePayload,
  ProjectDetail,
  ProjectLogUpdatePayload,
  ProjectUpdatePayload,
  ProjectLogCreatePayload,
  RiskCreatePayload,
  RiskUpdatePayload,
  TaskCreatePayload
  ,
  TaskUpdatePayload
} from "../types/models";

export interface ProjectListQuery {
  broker_id?: number;
  status?: string;
  keyword?: string;
  owner_name?: string;
}

export function getProjects(params: ProjectListQuery = {}) {
  return unwrap<DashboardProject[]>(http.get("/projects", { params }));
}

export function getProjectDetail(projectId: number) {
  return unwrap<ProjectDetail>(http.get(`/projects/${projectId}`));
}

export function createProject(payload: ProjectCreatePayload) {
  return unwrap<DashboardProject>(http.post("/projects", payload));
}

export function updateProject(projectId: number, payload: ProjectUpdatePayload) {
  return unwrap<DashboardProject>(http.put(`/projects/${projectId}`, payload));
}

export function deleteProject(projectId: number) {
  return unwrap(http.delete(`/projects/${projectId}`));
}

export function createTask(projectId: number, payload: TaskCreatePayload) {
  return unwrap(http.post(`/projects/${projectId}/tasks`, payload));
}

export function updateTask(taskId: number, payload: TaskUpdatePayload) {
  return unwrap(http.put(`/tasks/${taskId}`, payload));
}

export function deleteTask(taskId: number) {
  return unwrap(http.delete(`/tasks/${taskId}`));
}

export function createRisk(projectId: number, payload: RiskCreatePayload) {
  return unwrap(http.post(`/projects/${projectId}/risks`, payload));
}

export function updateRisk(riskId: number, payload: RiskUpdatePayload) {
  return unwrap(http.put(`/risks/${riskId}`, payload));
}

export function deleteRisk(riskId: number) {
  return unwrap(http.delete(`/risks/${riskId}`));
}

export function createProjectLog(projectId: number, payload: ProjectLogCreatePayload) {
  return unwrap(http.post(`/projects/${projectId}/logs`, payload));
}

export function updateProjectLog(logId: number, payload: ProjectLogUpdatePayload) {
  return unwrap(http.put(`/logs/${logId}`, payload));
}

export function deleteProjectLog(logId: number) {
  return unwrap(http.delete(`/logs/${logId}`));
}

export function updateTaskStatus(
  taskId: number,
  payload: Pick<TaskCreatePayload, "status" | "actual_action" | "completion_result">
) {
  return unwrap(http.post(`/tasks/${taskId}/status`, payload));
}

export function updateRiskStatus(
  riskId: number,
  payload: Pick<RiskCreatePayload, "status" | "action_plan">
) {
  return unwrap(http.post(`/risks/${riskId}/status`, payload));
}
