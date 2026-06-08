// Upload Store - Zustand State Management for Video Uploads

import {create} from 'zustand';
import {MediaUploadResponse, TranscriptionStatus} from '@/types/api';
import {mediaApi} from '@/api';

export interface UploadItem {
  id: string;
  mediaId?: string;
  filename: string;
  fileUri: string;
  fileType: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: string;
  uploadedAt?: string;
  jobId?: string;
  transcriptionStatus?: TranscriptionStatus;
}

interface UploadState {
  uploads: UploadItem[];
  activeUploadId: string | null;

  // Actions
  addUpload: (item: UploadItem) => void;
  updateUpload: (id: string, updates: Partial<UploadItem>) => void;
  removeUpload: (id: string) => void;
  setActiveUpload: (id: string | null) => void;
  clearCompleted: () => void;

  // Upload operations
  uploadVideo: (
    file: {uri: string; type: string; name: string},
    onProgress?: (progress: number) => void,
  ) => Promise<MediaUploadResponse>;

  startTranscription: (mediaId: string, uploadId: string) => Promise<void>;
  pollTranscriptionStatus: (
    jobId: string,
    uploadId: string,
  ) => Promise<void>;
}

export const useUploadStore = create<UploadState>((set, get) => ({
  uploads: [],
  activeUploadId: null,

  addUpload: (item: UploadItem) => {
    set(state => ({
      uploads: [item, ...state.uploads],
      activeUploadId: item.id,
    }));
  },

  updateUpload: (id: string, updates: Partial<UploadItem>) => {
    set(state => ({
      uploads: state.uploads.map(upload =>
        upload.id === id ? {...upload, ...updates} : upload,
      ),
    }));
  },

  removeUpload: (id: string) => {
    set(state => ({
      uploads: state.uploads.filter(upload => upload.id !== id),
      activeUploadId:
        state.activeUploadId === id ? null : state.activeUploadId,
    }));
  },

  setActiveUpload: (id: string | null) => {
    set({activeUploadId: id});
  },

  clearCompleted: () => {
    set(state => ({
      uploads: state.uploads.filter(
        upload => upload.status !== 'completed' && upload.status !== 'failed',
      ),
    }));
  },

  uploadVideo: async (
    file: {uri: string; type: string; name: string},
    onProgress?: (progress: number) => void,
  ) => {
    try {
      const response = await mediaApi.uploadMedia(file, onProgress);
      return response;
    } catch (error: any) {
      throw new Error(error.message || 'Upload failed');
    }
  },

  startTranscription: async (mediaId: string, uploadId: string) => {
    try {
      const job = await mediaApi.startTranscription(mediaId);
      get().updateUpload(uploadId, {
        status: 'processing',
        jobId: job.job_id,
        progress: 0,
      });

      // Start polling in background
      get().pollTranscriptionStatus(job.job_id, uploadId);
    } catch (error: any) {
      get().updateUpload(uploadId, {
        status: 'failed',
        error: error.message || 'Failed to start transcription',
      });
      throw error;
    }
  },

  pollTranscriptionStatus: async (jobId: string, uploadId: string) => {
    try {
      await mediaApi.pollTranscriptionStatus(jobId, status => {
        get().updateUpload(uploadId, {
          progress: status.progress,
          transcriptionStatus: status,
        });
      });

      // Completed
      get().updateUpload(uploadId, {
        status: 'completed',
        progress: 100,
      });
    } catch (error: any) {
      get().updateUpload(uploadId, {
        status: 'failed',
        error: error.message || 'Transcription failed',
      });
    }
  },
}));
