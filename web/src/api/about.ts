import { request } from "./http";

export type ProfileMetric = {
  value: string;
  label: string;
};

export type WorkExperience = {
  organization: string;
  role: string;
  period: string;
  summary: string;
  highlights: string[];
};

export type ProjectExperience = {
  name: string;
  role: string;
  period: string;
  summary: string;
  link_url: string | null;
  technologies: string[];
};

export type SkillItem = {
  name: string;
  icon_url: string;
};

export type SocialLink = {
  platform: string;
  label: string;
  url: string;
};

export type AboutProfile = {
  id: number;
  display_name: string;
  role: string;
  headline: string;
  bio: string;
  avatar_url: string;
  resume_url: string;
  resume_filename: string;
  status_text: string;
  email: string | null;
  location_name: string;
  location_longitude: number | null;
  location_latitude: number | null;
  metrics: ProfileMetric[];
  work_experiences: WorkExperience[];
  project_experiences: ProjectExperience[];
  skills: SkillItem[];
  social_links: SocialLink[];
  interests: string[];
  site_title: string;
  site_description: string;
  site_launched_at: string;
  site_stack: string[];
  site_repository_url: string | null;
  updated_at: string;
};

export async function fetchAboutProfile(): Promise<AboutProfile> {
  return request<AboutProfile>({ method: "GET", url: "/about-profile" });
}
