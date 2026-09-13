import { request } from "./http";

export type GuestbookStatus = "pending" | "approved" | "rejected" | "spam" | "deleted";
export type GuestbookItem = {
  id: number;
  nickname: string;
  content: string;
  admin_reply: string;
  status: GuestbookStatus;
  risk_score: number;
  created_at: string;
  reviewed_at: string | null;
};
export type GuestbookManageList = { items: GuestbookItem[]; total: number; page: number; page_size: number; pending_count: number };

export function fetchManageGuestbook(params: Record<string, string | number | undefined> = {}) {
  return request<GuestbookManageList>({ url: "/guestbook/manage", method: "GET", params });
}
export function updateGuestbookStatus(id: number, status: GuestbookStatus, reason = "") {
  return request<GuestbookItem>({ url: `/guestbook/${id}/status`, method: "PATCH", data: { status, reason } });
}
export function updateGuestbookReply(id: number, admin_reply: string) {
  return request<GuestbookItem>({ url: `/guestbook/${id}/reply`, method: "PATCH", data: { admin_reply } });
}
