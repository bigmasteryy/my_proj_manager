import { http, unwrap } from "./client";
import type { AuthUser, LoginPayload, LoginResponse } from "../types/models";

export function login(payload: LoginPayload) {
  return unwrap<LoginResponse>(http.post("/auth/login", payload));
}

export function getCurrentUserProfile() {
  return unwrap<AuthUser>(http.get("/auth/me"));
}

export function logout() {
  return unwrap<{ logout: boolean }>(http.post("/auth/logout"));
}
