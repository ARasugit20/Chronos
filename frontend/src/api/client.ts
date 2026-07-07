import axios from "axios";
import { resolveApiBaseUrl } from "./config";

const TOKEN_KEY = "chronos_token";

export const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 15_000,
});

const stored = localStorage.getItem(TOKEN_KEY);
if (stored) {
  apiClient.defaults.headers.common.Authorization = `Bearer ${stored}`;
}

export function setAuthToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    localStorage.removeItem(TOKEN_KEY);
    delete apiClient.defaults.headers.common.Authorization;
  }
}

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
);
