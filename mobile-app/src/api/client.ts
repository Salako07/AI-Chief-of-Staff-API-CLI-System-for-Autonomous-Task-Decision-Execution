// API Client - AI Chief of Staff Mobile App

import axios, {AxiosInstance, AxiosRequestConfig, AxiosError} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {ApiError} from '@/types/api';

// API Base URL - Updated for iPhone testing
// Your computer's IP: 172.20.10.2 (from Wi-Fi adapter)
// Make sure your iPhone is on the same Wi-Fi network
const API_BASE_URL = __DEV__
  ? 'http://172.20.10.2:8000' // Your computer's IP for real device testing
  : 'https://api.yourcompany.com'; // Production

// Storage keys
const TOKEN_KEY = '@ai_chief_token';
const REFRESH_TOKEN_KEY = '@ai_chief_refresh_token';

class APIClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token (DISABLED FOR NOW - NO AUTH)
    this.client.interceptors.request.use(
      async config => {
        // Skip auth for now
        // if (!this.accessToken) {
        //   this.accessToken = await this.getStoredToken();
        // }
        // if (this.accessToken) {
        //   config.headers.Authorization = `Bearer ${this.accessToken}`;
        // }
        return config;
      },
      error => Promise.reject(error),
    );

    // Response interceptor for error handling (AUTH DISABLED)
    this.client.interceptors.response.use(
      response => response,
      async (error: AxiosError<ApiError>) => {
        // Skip auth handling for now
        // if (error.response?.status === 401) {
        //   const refreshed = await this.refreshAccessToken();
        //   if (refreshed && error.config) {
        //     return this.client.request(error.config);
        //   } else {
        //     await this.clearTokens();
        //   }
        // }

        return Promise.reject(this.handleError(error));
      },
    );
  }

  // Token management
  async setToken(accessToken: string, refreshToken?: string): Promise<void> {
    this.accessToken = accessToken;
    await AsyncStorage.setItem(TOKEN_KEY, accessToken);
    if (refreshToken) {
      await AsyncStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
  }

  async getStoredToken(): Promise<string | null> {
    return AsyncStorage.getItem(TOKEN_KEY);
  }

  async clearTokens(): Promise<void> {
    this.accessToken = null;
    await AsyncStorage.multiRemove([TOKEN_KEY, REFRESH_TOKEN_KEY]);
  }

  async refreshAccessToken(): Promise<boolean> {
    try {
      const refreshToken = await AsyncStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refreshToken) return false;

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/auth/refresh`,
        {refresh_token: refreshToken},
      );

      const {access_token, refresh_token} = response.data;
      await this.setToken(access_token, refresh_token);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  // Error handler
  private handleError(error: AxiosError<ApiError>): Error {
    if (error.response) {
      // Server responded with error
      const message =
        error.response.data?.detail || `Error: ${error.response.status}`;
      return new Error(message);
    } else if (error.request) {
      // No response received
      return new Error('Network error. Please check your connection.');
    } else {
      // Request setup error
      return new Error(error.message || 'An unexpected error occurred');
    }
  }

  // Generic request methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // File upload with progress
  async uploadFile<T>(
    url: string,
    formData: FormData,
    onProgress?: (progress: number) => void,
  ): Promise<T> {
    const response = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: progressEvent => {
        if (onProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          onProgress(Math.round(progress));
        }
      },
    });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health');
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
