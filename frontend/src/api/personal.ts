import { http, unwrap } from "./client";
import type {
  WeeklyReport,
  PersonalTaskCompletePayload,
  PersonalTaskCreatePayload,
  PersonalRiskItem,
  PersonalTaskItem,
  PersonalTaskUpdatePayload
} from "../types/models";

export function getPersonalTasks(
  categoryOrParams?: string | { category?: string; parent_task_id?: number }
) {
  const params =
    typeof categoryOrParams === "string"
      ? { category: categoryOrParams }
      : (categoryOrParams || {});
  return unwrap<PersonalTaskItem[]>(http.get("/personal/tasks", { params }));
}

export function getPersonalHistory(params: {
  category?: string;
  parent_task_id?: number;
  keyword?: string;
  start_date?: string;
  end_date?: string;
}) {
  return unwrap<PersonalTaskItem[]>(http.get("/personal/history", { params }));
}

export function getPersonalRisks() {
  return unwrap<PersonalRiskItem[]>(http.get("/personal/risks"));
}

export function getPersonalWeeklyReport(category?: string) {
  return unwrap<WeeklyReport>(http.get("/personal/reports/weekly", { params: { category } }));
}

export function createPersonalTask(payload: PersonalTaskCreatePayload) {
  return unwrap<PersonalTaskItem>(http.post("/personal/tasks", payload));
}

export function updatePersonalTask(taskId: number, payload: PersonalTaskUpdatePayload) {
  return unwrap<PersonalTaskItem>(http.put(`/personal/tasks/${taskId}`, payload));
}

export function completePersonalTask(taskId: number, payload: PersonalTaskCompletePayload) {
  return unwrap<PersonalTaskItem>(http.post(`/personal/tasks/${taskId}/complete`, payload));
}

export function deletePersonalTask(taskId: number) {
  return unwrap(http.delete(`/personal/tasks/${taskId}`));
}

export function sortPersonalTasks(orderedIds: number[]) {
  return unwrap(http.post("/personal/tasks/sort", { ordered_ids: orderedIds }));
}

export function resetDailyTasks() {
  return unwrap(http.post("/personal/tasks/reset-daily"));
}
