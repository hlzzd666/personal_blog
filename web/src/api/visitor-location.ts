import { request } from "./http";

export type VisitorLocation = {
  ip: string;
  city: string | null;
  region: string | null;
  country: string | null;
  location_available: boolean;
  owner_location_name: string | null;
  distance_km: number | null;
};

export async function fetchVisitorLocation() {
  return request<VisitorLocation>({ url: "/visitor-location", method: "GET" });
}
