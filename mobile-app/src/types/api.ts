// API Types - AI Chief of Staff Mobile App

export interface Task {
  id: string;
  title: string;
  owner?: string;
  deadline?: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed';
}

export interface Decision {
  id: string;
  decision: string;
  made_by?: string;
  timestamp: string;
}

export interface Risk {
  id: string;
  risk: string;
  severity: 'low' | 'medium' | 'high';
  mitigation?: string;
}

export interface AgentMetadata {
  source: string;
  processed_at: string;
  run_id: string;
}

export interface ProcessResult {
  tasks: Task[];
  decisions: Decision[];
  risks: Risk[];
  summary: string;
  metadata: AgentMetadata;
}

export interface MediaUploadResponse {
  media_id: string;
  filename: string;
  size_bytes: number;
  duration_seconds?: number;
  mime_type: string;
  status: string;
  created_at: string;
}

export interface TranscriptionJob {
  job_id: string;
  media_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
}

export interface TranscriptionStatus {
  job_id: string;
  media_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  transcription_length?: number;
  processing_time_ms?: number;
  error_message?: string;
}

export interface TranscriptionResult {
  job_id: string;
  run_id: string;
  media_id: string;
  transcription: string;
  tasks: Task[];
  decisions: Decision[];
  risks: Risk[];
  summary: string;
  processing_time_ms: number;
}

export interface VideoMetadata {
  media_id: string;
  filename: string;
  size_bytes: number;
  size_mb: number;
  mime_type: string;
  duration_seconds?: number;
  status: string;
  storage_type: 'local' | 'spaces';
  storage_location: string;
  created_at: string;
  updated_at: string;
  transcription_job?: {
    id: string;
    status: string;
    created_at: string;
    completed_at?: string;
  };
}

export interface PresignedUrlResponse {
  media_id: string;
  presigned_url: string;
  expires_in_seconds: number;
  storage_type: string;
  filename: string;
}

// Authentication Types (to be added to backend)
export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  avatar_url?: string;
}

export interface UserStats {
  total_uploads: number;
  total_tasks: number;
  total_decisions: number;
  total_risks: number;
  processing_time_total_ms: number;
}

// API Error Response
export interface ApiError {
  detail: string;
  status_code: number;
}
