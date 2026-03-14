"use client";

const TOKEN_KEY = "biometric_token";
const USER_KEY = "biometric_user";

export interface AuthUser {
  username: string;
  rol: string;
  token: string;
}

export function saveAuth(token: string, username: string, rol: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify({ username, rol }));
}

export function getAuth(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem(TOKEN_KEY);
  const userData = localStorage.getItem(USER_KEY);
  if (!token || !userData) return null;
  try {
    const user = JSON.parse(userData);
    return { token, username: user.username, rol: user.rol };
  } catch {
    return null;
  }
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return getAuth() !== null;
}
