import { request } from "./http";
import type { SiteSettings } from "../types/site";

export type ImageUploadResult = {
  url: string;
  filename: string;
  content_type: string;
  size: number;
};

export type FileUploadResult = ImageUploadResult & {
  original_filename: string;
};

export async function fetchSiteSettings(): Promise<SiteSettings> {
  return request<SiteSettings>({
    method: "GET",
    url: "/site-settings",
  });
}

export async function updateSiteSettings(payload: SiteSettings): Promise<SiteSettings> {
  return request<SiteSettings>({
    method: "PUT",
    url: "/site-settings",
    data: payload,
  });
}

export async function uploadImage(file: File): Promise<ImageUploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  return request<ImageUploadResult>({
    method: "POST",
    url: "/media/images",
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 30000,
  });
}

export async function uploadResume(file: File): Promise<FileUploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  return request<FileUploadResult>({
    method: "POST",
    url: "/media/resumes",
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 30000,
  });
}
