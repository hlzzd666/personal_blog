import { request } from "./http";
import type { AboutProfile, AboutProfilePayload } from "../types/about";

export async function fetchAboutProfile(): Promise<AboutProfile> {
  return request<AboutProfile>({
    method: "GET",
    url: "/about-profile",
  });
}

export async function updateAboutProfile(payload: AboutProfilePayload): Promise<AboutProfile> {
  return request<AboutProfile>({
    method: "PUT",
    url: "/about-profile",
    data: payload,
  });
}
