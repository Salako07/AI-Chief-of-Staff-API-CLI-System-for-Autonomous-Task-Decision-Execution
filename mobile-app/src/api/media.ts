// Media API - Video/Audio Upload and Transcription

import apiClient from './client';
import {
  MediaUploadResponse,
  TranscriptionJob,
  TranscriptionStatus,
  TranscriptionResult,
  VideoMetadata,
  PresignedUrlResponse,
} from '@/types/api';

export const mediaApi = {
  // Upload video/audio file
  async uploadMedia(
    file: {uri: string; type: string; name: string},
    onProgress?: (progress: number) => void,
  ): Promise<MediaUploadResponse> {
    const formData = new FormData();
    formData.append('file', {
      uri: file.uri,
      type: file.type,
      name: file.name,
    } as any);

    return apiClient.uploadFile<MediaUploadResponse>(
      '/api/v1/media/upload',
      formData,
      onProgress,
    );
  },

  // Start transcription
  async startTranscription(mediaId: string): Promise<TranscriptionJob> {
    return apiClient.post<TranscriptionJob>(
      `/api/v1/media/transcribe/${mediaId}`,
    );
  },

  // Get transcription status
  async getTranscriptionStatus(jobId: string): Promise<TranscriptionStatus> {
    return apiClient.get<TranscriptionStatus>(
      `/api/v1/media/status/${jobId}`,
    );
  },

  // Get transcription result
  async getTranscriptionResult(jobId: string): Promise<TranscriptionResult> {
    return apiClient.get<TranscriptionResult>(
      `/api/v1/media/result/${jobId}`,
    );
  },

  // Get video metadata
  async getVideoMetadata(mediaId: string): Promise<VideoMetadata> {
    return apiClient.get<VideoMetadata>(
      `/api/v1/media/video/${mediaId}/metadata`,
    );
  },

  // Get presigned URL for video playback
  async getVideoUrl(
    mediaId: string,
    expiration: number = 3600,
  ): Promise<PresignedUrlResponse> {
    return apiClient.get<PresignedUrlResponse>(
      `/api/v1/media/video/${mediaId}/url?expiration=${expiration}`,
    );
  },

  // Delete video
  async deleteVideo(mediaId: string): Promise<void> {
    return apiClient.delete(`/api/v1/media/video/${mediaId}`);
  },

  // Poll transcription status until complete
  async pollTranscriptionStatus(
    jobId: string,
    onProgress?: (status: TranscriptionStatus) => void,
    interval: number = 2000,
  ): Promise<TranscriptionResult> {
    return new Promise((resolve, reject) => {
      const poll = setInterval(async () => {
        try {
          const status = await this.getTranscriptionStatus(jobId);

          if (onProgress) {
            onProgress(status);
          }

          if (status.status === 'completed') {
            clearInterval(poll);
            const result = await this.getTranscriptionResult(jobId);
            resolve(result);
          } else if (status.status === 'failed') {
            clearInterval(poll);
            reject(
              new Error(status.error_message || 'Transcription failed'),
            );
          }
        } catch (error) {
          clearInterval(poll);
          reject(error);
        }
      }, interval);

      // Timeout after 10 minutes
      setTimeout(() => {
        clearInterval(poll);
        reject(new Error('Transcription timeout'));
      }, 10 * 60 * 1000);
    });
  },
};

export default mediaApi;
