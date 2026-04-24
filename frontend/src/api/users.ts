import { http, unwrap } from "./client";
import type { AuthUser, UserCreatePayload, UserResetPasswordPayload, UserUpdatePayload } from "../types/models";

export function getUsers() {
  return unwrap<AuthUser[]>(http.get("/users"));
}

export function createUser(payload: UserCreatePayload) {
  return unwrap<AuthUser>(http.post("/users", payload));
}

export function updateUser(userId: number, payload: UserUpdatePayload) {
  return unwrap<AuthUser>(http.put(`/users/${userId}`, payload));
}

export function resetUserPassword(userId: number, payload: UserResetPasswordPayload) {
  return unwrap<AuthUser>(http.post(`/users/${userId}/reset-password`, payload));
}

export function deleteUser(userId: number) {
  return unwrap(http.delete(`/users/${userId}`));
}
