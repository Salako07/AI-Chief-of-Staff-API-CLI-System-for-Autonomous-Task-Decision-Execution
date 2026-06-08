// Navigation Types

import {NavigatorScreenParams} from '@react-navigation/native';
import {ProcessResult} from '@/types/api';

// Auth Stack
export type AuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  Signup: undefined;
};

// Main Tab Navigator
export type MainTabParamList = {
  Dashboard: undefined;
  Record: undefined;
  Process: undefined;
  Profile: undefined;
};

// Dashboard Stack
export type DashboardStackParamList = {
  DashboardHome: undefined;
  VideoDetails: {mediaId: string};
  TranscriptionResult: {jobId: string};
  TaskDetails: {taskId: string};
};

// Record Stack
export type RecordStackParamList = {
  RecordVideo: undefined;
  MeetingRecorder: undefined;
  UploadProgress: {mediaId: string; filename: string};
  ProcessingStatus: {jobId: string};
};

// Process Stack (Text input)
export type ProcessStackParamList = {
  TextInput: undefined;
  ProcessingResult: {runId: string; result: ProcessResult};
};

// Root Navigator
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
};

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
