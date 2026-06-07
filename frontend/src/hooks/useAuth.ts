import { useCallback, useState } from "react";
import { login as apiLogin, logout as apiLogout } from "../api/auth";
import { getAuthToken } from "../api/client";

export function useAuth() {
  const [token, setToken] = useState<string | null>(getAuthToken());

  const login = useCallback(async (username: string, password: string) => {
    const newToken = await apiLogin(username, password);
    setToken(newToken);
    return newToken;
  }, []);

  const logout = useCallback(() => {
    apiLogout();
    setToken(null);
  }, []);

  return { token, isAuthenticated: Boolean(token), login, logout };
}
