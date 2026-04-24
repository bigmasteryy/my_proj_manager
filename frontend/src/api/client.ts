import axios from "axios";
import { clearSession, getStoredToken } from "../utils/auth";

export const http = axios.create({
  baseURL: "/api/v1",
  timeout: 8000
});

http.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && window.location.pathname !== "/login") {
      clearSession();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export async function unwrap<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const response = await promise;
  return response.data.data;
}
