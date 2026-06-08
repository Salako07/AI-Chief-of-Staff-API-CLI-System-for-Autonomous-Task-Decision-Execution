// Authentication API

import apiClient from './client';
import {
  LoginRequest,
  SignupRequest,
  AuthResponse,
  User,
} from '@/types/api';

export const authApi = {
  // Login
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      '/api/v1/auth/login',
      credentials,
    );

    // Store tokens
    await apiClient.setToken(response.access_token, response.refresh_token);

    return response;
  },

  // Signup
  async signup(data: SignupRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      '/api/v1/auth/register',
      data,
    );

    // Store tokens
    await apiClient.setToken(response.access_token, response.refresh_token);

    return response;
  },

  // Logout
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout');
    } finally {
      await apiClient.clearTokens();
    }
  },

  // Get current user
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/api/v1/users/me');
  },

  // Update profile
  async updateProfile(data: Partial<User>): Promise<User> {
    return apiClient.put<User>('/api/v1/users/me', data);
  },
};

export default authApi;
