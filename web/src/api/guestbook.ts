import { request } from "./http";

export type GuestbookItem = {
  id: number;
  nickname: string;
  content: string;
  admin_reply: string;
  created_at: string;
};

export type GuestbookList = {
  items: GuestbookItem[];
  total: number;
  page: number;
  page_size: number;
};

export function fetchGuestbook(page = 1, pageSize = 20) {
  return request<GuestbookList>({ url: "/guestbook", method: "GET", params: { page, page_size: pageSize } });
}

export function submitGuestbook(payload: { nickname: string; content: string; honeypot?: string }) {
  return request<{ id: number; status: string }>({ url: "/guestbook", method: "POST", data: payload });
}
