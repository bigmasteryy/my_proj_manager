import { http, unwrap } from "./client";
import type { ReminderItem } from "../types/models";

export function getReminders() {
  return unwrap<ReminderItem[]>(http.get("/reminders"));
}

export function handleReminder(reminderId: number) {
  return unwrap(http.post(`/reminders/${reminderId}/handle`, { note: "" }));
}

export function ignoreReminder(reminderId: number) {
  return unwrap(http.post(`/reminders/${reminderId}/ignore`, { note: "" }));
}
