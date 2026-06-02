import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 15_000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
);
