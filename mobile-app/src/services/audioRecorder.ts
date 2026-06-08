import {Audio} from 'expo-av';
import {Platform} from 'react-native';

export type RecorderState = 'idle' | 'recording' | 'paused' | 'stopped';

export interface RecordingResult {
  uri: string;
  durationMs: number;
  filename: string;
}

class AudioRecorderService {
  private recording: Audio.Recording | null = null;
  private state: RecorderState = 'idle';
  private startTime: number | null = null;

  async requestPermissions(): Promise<boolean> {
    const {granted} = await Audio.requestPermissionsAsync();
    return granted;
  }

  async startRecording(): Promise<void> {
    if (this.state === 'recording') return;

    const granted = await this.requestPermissions();
    if (!granted) throw new Error('Microphone permission denied.');

    // Configure audio session for background recording
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      staysActiveInBackground: true,
      playsInSilentModeIOS: true,
      shouldDuckAndroid: false,
      playThroughEarpieceAndroid: false,
    });

    this.recording = new Audio.Recording();

    await this.recording.prepareToRecordAsync({
      android: {
        extension: '.m4a',
        outputFormat: Audio.AndroidOutputFormat.MPEG_4,
        audioEncoder: Audio.AndroidAudioEncoder.AAC,
        sampleRate: 44100,
        numberOfChannels: 1,
        bitRate: 128000,
      },
      ios: {
        extension: '.m4a',
        audioQuality: Audio.IOSAudioQuality.HIGH,
        sampleRate: 44100,
        numberOfChannels: 1,
        bitRate: 128000,
        linearPCMBitDepth: 16,
        linearPCMIsBigEndian: false,
        linearPCMIsFloat: false,
      },
      web: {mimeType: 'audio/webm', bitsPerSecond: 128000},
    });

    await this.recording.startAsync();
    this.state = 'recording';
    this.startTime = Date.now();
  }

  async pauseRecording(): Promise<void> {
    if (this.state !== 'recording' || !this.recording) return;
    await this.recording.pauseAsync();
    this.state = 'paused';
  }

  async resumeRecording(): Promise<void> {
    if (this.state !== 'paused' || !this.recording) return;
    await this.recording.startAsync();
    this.state = 'recording';
  }

  async stopRecording(): Promise<RecordingResult> {
    if (!this.recording || this.state === 'idle') {
      throw new Error('No active recording.');
    }

    await this.recording.stopAndUnloadAsync();
    const uri = this.recording.getURI();
    if (!uri) throw new Error('Recording URI not available.');

    const status = await this.recording.getStatusAsync();
    const durationMs = status.durationMillis ?? 0;

    // Reset audio mode so other audio (music, calls) can resume normally
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      staysActiveInBackground: false,
      playsInSilentModeIOS: false,
    });

    this.recording = null;
    this.state = 'stopped';
    this.startTime = null;

    const filename = `meeting_${Date.now()}.m4a`;
    return {uri, durationMs, filename};
  }

  async cancelRecording(): Promise<void> {
    if (!this.recording) return;
    try {
      await this.recording.stopAndUnloadAsync();
    } catch {}
    this.recording = null;
    this.state = 'idle';
    this.startTime = null;

    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      staysActiveInBackground: false,
      playsInSilentModeIOS: false,
    });
  }

  getState(): RecorderState {
    return this.state;
  }

  getElapsedMs(): number {
    if (!this.startTime || this.state === 'idle') return 0;
    return Date.now() - this.startTime;
  }

  isRecording(): boolean {
    return this.state === 'recording';
  }
}

// Singleton — one recording session at a time
export const audioRecorder = new AudioRecorderService();
