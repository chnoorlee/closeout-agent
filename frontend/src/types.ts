export type RunStatus = "queued" | "running" | "completed" | "failed";
export type StageStatus = "waiting" | "active" | "completed" | "failed";
export type Verdict = "queued" | "verified" | "repaired" | "blocked";

export interface Health {
  status: string;
  service: string;
  model: string;
  framework: string;
  ai_mode: string;
  store: string;
  dispatcher: string;
  timestamp: string;
}

export interface Stage {
  id: string;
  label: string;
  status: StageStatus;
  summary: string;
}

export interface Requirement {
  id: string;
  title: string;
  source: string;
  evidence: string[];
  verdict: Verdict;
  confidence: number;
  action: string | null;
}

export interface TimelineEvent {
  id: string;
  stage: string;
  title: string;
  detail: string;
  actor: string;
  status: StageStatus;
  created_at: string;
}

export interface Artifact {
  id: string;
  name: string;
  media_type: string;
  size_bytes: number;
  sha256: string;
  source: string;
}

export interface Run {
  id: string;
  name: string;
  scenario: string;
  status: RunStatus;
  mode: string;
  model: string;
  framework: string;
  created_at: string;
  updated_at: string;
  stages: Stage[];
  artifacts: Artifact[];
  requirements: Requirement[];
  events: TimelineEvent[];
  metrics: {
    requirements: number;
    verified: number;
    repaired: number;
    blocked: number;
    evidence_coverage: number;
    autonomous_actions: number;
  };
  bundle_ready: boolean;
  bundle_sha256: string | null;
  error: string | null;
}
