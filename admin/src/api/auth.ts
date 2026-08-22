import { request } from "./http";

export type AdminSession = {
  username: string;
  logged_in_at: string;
  expires_at: string;
};

export type AdminLoginPayload = {
  username: string;
  password: string;
};

export async function loginAdmin(payload: AdminLoginPayload): Promise<AdminSession> {
  return request<AdminSession>({
    method: "POST",
    url: "/auth/login",
    data: payload,
  });
}

export async function fetchCurrentAdmin(): Promise<AdminSession> {
  return request<AdminSession>({
    method: "GET",
    url: "/auth/me",
  });
}

export async function logoutAdmin(): Promise<void> {
  await request<{ logged_out: boolean }>({
    method: "POST",
    url: "/auth/logout",
  });
}
