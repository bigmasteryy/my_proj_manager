import { http, unwrap } from "./client";
import type {
  DashboardProject,
  ProjectSaveAsTemplatePayload,
  TemplateCreatePayload,
  TemplateDetail,
  TemplateGenerateProjectPayload,
  TemplateUpdatePayload,
  TemplateSummary
} from "../types/models";

export function getTemplates() {
  return unwrap<TemplateSummary[]>(http.get("/templates"));
}

export function getTemplateDetail(templateId: number) {
  return unwrap<TemplateDetail>(http.get(`/templates/${templateId}`));
}

export function createTemplate(payload: TemplateCreatePayload) {
  return unwrap<TemplateSummary>(http.post("/templates", payload));
}

export function updateTemplate(templateId: number, payload: TemplateUpdatePayload) {
  return unwrap<TemplateSummary>(http.put(`/templates/${templateId}`, payload));
}

export function deleteTemplate(templateId: number) {
  return unwrap(http.delete(`/templates/${templateId}`));
}

export function generateProjectFromTemplate(templateId: number, payload: TemplateGenerateProjectPayload) {
  return unwrap<DashboardProject>(http.post(`/templates/${templateId}/generate-project`, payload));
}

export function saveProjectAsTemplate(projectId: number, payload: ProjectSaveAsTemplatePayload) {
  return unwrap<TemplateSummary>(http.post(`/templates/projects/${projectId}/save-as-template`, payload));
}
