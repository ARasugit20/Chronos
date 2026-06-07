import { apiClient, setAuthToken } from "./client";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(username: string, password: string): Promise<string> {
  const params = new URLSearchParams();
  params.append("username", username);
  params.append("password", password);
  const { data } = await apiClient.post<TokenResponse>("/api/v1/auth/token", params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  setAuthToken(data.access_token);
  return data.access_token;
}

export function logout(): void {
  setAuthToken(null);
}
