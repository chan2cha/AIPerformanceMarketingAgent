export type Organization = { id: string; name: string; role: "owner" | "admin" | "member" };

export type Me = {
  id: string;
  email: string;
  name: string | null;
  organizations: Organization[];
};

export type Brand = {
  id: string;
  organization_id: string;
  name: string;
  website: string | null;
  industry: string | null;
  description: string | null;
  target_customer: string | null;
  brand_tone: string | null;
  created_at: string;
  updated_at: string;
};

export type Competitor = {
  id: string;
  organization_id: string;
  brand_id: string;
  name: string;
  website: string | null;
  created_at: string;
};

export type Analysis = {
  id: string;
  creative_id: string;
  job_id: string;
  status: string;
  summary: string;
  hook: string | null;
  offer: string | null;
  cta: string | null;
  angle: string | null;
  emotional_triggers: string[];
  visual_elements: string[];
  strengths: string[];
  weaknesses: string[];
  tags: string[];
  confidence: number;
  provider: string;
  model: string;
  prompt_version: string;
  schema_version: string;
  created_at: string;
};

export type Creative = {
  id: string;
  organization_id: string;
  brand_id: string;
  competitor_id: string | null;
  created_by_user_id: string | null;
  ownership_type: "own" | "competitor" | "market";
  source: string;
  source_external_id: string | null;
  source_url: string | null;
  media_type: "image" | "video" | "carousel" | "text";
  title: string | null;
  body: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CreativeDetail = Creative & { analyses: Analysis[] };

export type CollectionSource = {
  id: string;
  organization_id: string;
  brand_id: string;
  competitor_id: string | null;
  platform: "meta_ad_library" | "tiktok_creative_center";
  scope: "competitor" | "industry";
  external_identifier: string | null;
  country_code: string;
  language_code: string | null;
  keywords: string[];
  status: "active" | "paused";
  sync_interval_hours: number;
  next_sync_at: string | null;
  last_attempt_at: string | null;
  last_sync_at: string | null;
  last_error_code: string | null;
  created_at: string;
  updated_at: string;
};

export type Job = {
  id: string;
  organization_id: string;
  job_type: string;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
  progress: number;
  target_type: string;
  target_id: string;
  attempts: number;
  error_code: string | null;
  error_message: string | null;
};

export type UsageSummary = {
  period: { from: string | null; to: string | null };
  estimated_cost_usd: string;
  calls: number;
  by_task: { task: string; calls: number; estimated_cost_usd: string }[];
};
