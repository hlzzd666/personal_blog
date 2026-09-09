import { request } from "./http";
import type {
  VisitorRecordFilters,
  VisitorRecordListResponse,
} from "../types/visitor-record";

export function fetchVisitorRecords(params: VisitorRecordFilters) {
  return request<VisitorRecordListResponse>({
    url: "/visitor-records",
    method: "GET",
    params,
  });
}

export function deleteVisitorRecord(id: number) {
  return request<{ id: number }>({
    url: `/visitor-records/${id}`,
    method: "DELETE",
  });
}

export function deleteVisitorRecords(visitedFrom?: string, visitedTo?: string) {
  return request<{ deleted_count: number }>({
    url: "/visitor-records",
    method: "DELETE",
    params: {
      visited_from: visitedFrom,
      visited_to: visitedTo,
    },
  });
}
