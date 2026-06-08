// Text Processing API

import apiClient from './client';
import {ProcessResult} from '@/types/api';

export const textApi = {
  // Process text input
  async processText(text: string, source: string = 'mobile'): Promise<ProcessResult> {
    return apiClient.post<ProcessResult>('/api/v1/process', {
      text,
      source,
    });
  },

  // Get task status (for Celery task tracking if needed)
  async getTaskStatus(taskId: string): Promise<any> {
    return apiClient.get(`/api/v1/task-status/${taskId}`);
  },
};

export default textApi;
