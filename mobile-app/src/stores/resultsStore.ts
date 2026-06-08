// Results Store - Zustand State Management for Processing Results

import {create} from 'zustand';
import {
  TranscriptionResult,
  Task,
  Decision,
  Risk,
  VideoMetadata,
} from '@/types/api';
import {mediaApi} from '@/api';

interface ResultsState {
  results: TranscriptionResult[];
  videos: Record<string, VideoMetadata>;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchResult: (jobId: string) => Promise<void>;
  fetchVideoMetadata: (mediaId: string) => Promise<void>;
  deleteVideo: (mediaId: string) => Promise<void>;
  clearError: () => void;

  // Selectors
  getResultByJobId: (jobId: string) => TranscriptionResult | undefined;
  getVideoByMediaId: (mediaId: string) => VideoMetadata | undefined;
  getAllTasks: () => Task[];
  getAllDecisions: () => Decision[];
  getAllRisks: () => Risk[];
}

export const useResultsStore = create<ResultsState>((set, get) => ({
  results: [],
  videos: {},
  isLoading: false,
  error: null,

  fetchResult: async (jobId: string) => {
    try {
      set({isLoading: true, error: null});
      const result = await mediaApi.getTranscriptionResult(jobId);

      set(state => ({
        results: [
          result,
          ...state.results.filter(r => r.job_id !== jobId),
        ],
        isLoading: false,
      }));
    } catch (error: any) {
      set({
        error: error.message || 'Failed to fetch result',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchVideoMetadata: async (mediaId: string) => {
    try {
      set({isLoading: true, error: null});
      const metadata = await mediaApi.getVideoMetadata(mediaId);

      set(state => ({
        videos: {
          ...state.videos,
          [mediaId]: metadata,
        },
        isLoading: false,
      }));
    } catch (error: any) {
      set({
        error: error.message || 'Failed to fetch video metadata',
        isLoading: false,
      });
      throw error;
    }
  },

  deleteVideo: async (mediaId: string) => {
    try {
      set({isLoading: true, error: null});
      await mediaApi.deleteVideo(mediaId);

      set(state => {
        const newVideos = {...state.videos};
        delete newVideos[mediaId];

        return {
          videos: newVideos,
          results: state.results.filter(r => r.media_id !== mediaId),
          isLoading: false,
        };
      });
    } catch (error: any) {
      set({
        error: error.message || 'Failed to delete video',
        isLoading: false,
      });
      throw error;
    }
  },

  clearError: () => set({error: null}),

  // Selectors
  getResultByJobId: (jobId: string) => {
    return get().results.find(r => r.job_id === jobId);
  },

  getVideoByMediaId: (mediaId: string) => {
    return get().videos[mediaId];
  },

  getAllTasks: () => {
    const results = get().results;
    return results.flatMap(r => r.tasks);
  },

  getAllDecisions: () => {
    const results = get().results;
    return results.flatMap(r => r.decisions);
  },

  getAllRisks: () => {
    const results = get().results;
    return results.flatMap(r => r.risks);
  },
}));
