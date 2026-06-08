import React, {useCallback, useEffect, useRef, useState} from 'react';
import {
  Alert,
  Animated,
  AppState,
  AppStateStatus,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useFocusEffect} from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import {RecordStackParamList} from '@/navigation/types';
import {audioRecorder} from '@/services/audioRecorder';
import {useUploadStore} from '@/stores/uploadStore';
import {mediaApi} from '@/api';

type Props = NativeStackScreenProps<RecordStackParamList, 'MeetingRecorder'>;

type ScreenState = 'ready' | 'recording' | 'paused' | 'processing';

function formatDuration(ms: number): string {
  const totalSecs = Math.floor(ms / 1000);
  const h = Math.floor(totalSecs / 3600);
  const m = Math.floor((totalSecs % 3600) / 60);
  const s = totalSecs % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

export default function MeetingRecorderScreen({navigation}: Props) {
  const [screenState, setScreenState] = useState<ScreenState>('ready');
  const [elapsedMs, setElapsedMs] = useState(0);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const addUpload = useUploadStore(s => s.addUpload);
  const uploadVideo = useUploadStore(s => s.uploadVideo);
  const updateUpload = useUploadStore(s => s.updateUpload);

  // Pulsing animation while recording
  useEffect(() => {
    let anim: Animated.CompositeAnimation;
    if (screenState === 'recording') {
      anim = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {toValue: 1.3, duration: 700, useNativeDriver: true}),
          Animated.timing(pulseAnim, {toValue: 1, duration: 700, useNativeDriver: true}),
        ]),
      );
      anim.start();
    } else {
      pulseAnim.setValue(1);
    }
    return () => anim?.stop();
  }, [screenState]);

  // Elapsed timer tick
  useEffect(() => {
    if (screenState === 'recording') {
      timerRef.current = setInterval(() => {
        setElapsedMs(audioRecorder.getElapsedMs());
      }, 500);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [screenState]);

  // Cancel recording if user navigates away mid-session
  useFocusEffect(
    useCallback(() => {
      return () => {
        if (audioRecorder.isRecording()) {
          audioRecorder.cancelRecording();
        }
      };
    }, []),
  );

  // On Android: watch AppState to detect when a call ends and app resumes
  useEffect(() => {
    if (Platform.OS !== 'android') return;
    const sub = AppState.addEventListener('change', (next: AppStateStatus) => {
      // App came back to foreground while we were recording in background
      if (next === 'active' && screenState === 'recording') {
        // Prompt user: call ended? Stop and process?
        Alert.alert(
          'Back from background',
          'Your call or meeting may have ended. Stop recording and process now?',
          [
            {text: 'Keep Recording', style: 'cancel'},
            {text: 'Stop & Process', onPress: handleStop},
          ],
        );
      }
    });
    return () => sub.remove();
  }, [screenState]);

  const handleStart = async () => {
    try {
      await audioRecorder.startRecording();
      setScreenState('recording');
      setElapsedMs(0);
    } catch (e: any) {
      Alert.alert('Cannot Record', e.message);
    }
  };

  const handlePause = async () => {
    await audioRecorder.pauseRecording();
    setScreenState('paused');
  };

  const handleResume = async () => {
    await audioRecorder.resumeRecording();
    setScreenState('recording');
  };

  const handleStop = async () => {
    if (elapsedMs < 2000) {
      Alert.alert('Too short', 'Recording is too short to process.');
      return;
    }
    setScreenState('processing');
    try {
      const recordingResult = await audioRecorder.stopRecording();
      const uploadId = `upload_${Date.now()}`;

      addUpload({
        id: uploadId,
        filename: recordingResult.filename,
        fileUri: recordingResult.uri,
        fileType: 'audio/m4a',
        status: 'uploading',
        progress: 0,
      });

      // 1. Upload the audio file
      const uploadResponse = await uploadVideo(
        {uri: recordingResult.uri, type: 'audio/m4a', name: recordingResult.filename},
        progress => updateUpload(uploadId, {progress}),
      );

      updateUpload(uploadId, {
        status: 'processing',
        mediaId: uploadResponse.media_id,
        progress: 100,
      });

      // 2. Kick off transcription and get the jobId immediately
      const job = await mediaApi.startTranscription(uploadResponse.media_id);

      updateUpload(uploadId, {jobId: job.job_id});

      // 3. Hand off to ProcessingStatus — it polls until done, then navigates to results
      navigation.replace('ProcessingStatus', {jobId: job.job_id});
    } catch (e: any) {
      Alert.alert('Upload Failed', e.message || 'Could not process recording.');
      setScreenState('ready');
      setElapsedMs(0);
    }
  };

  const handleCancel = () => {
    Alert.alert('Cancel Recording', 'Discard this recording?', [
      {text: 'Keep Recording', style: 'cancel'},
      {
        text: 'Discard',
        style: 'destructive',
        onPress: async () => {
          await audioRecorder.cancelRecording();
          setScreenState('ready');
          setElapsedMs(0);
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      {/* Header hint */}
      <View style={styles.hintBox}>
        <Icon name="information-circle-outline" size={16} color="#3B82F6" />
        <Text style={styles.hintText}>
          {Platform.OS === 'android'
            ? 'Start recording, then switch to your call app. Recording continues in the background.'
            : 'Start recording, then put the call on speaker and minimize this app.'}
        </Text>
      </View>

      {/* Mic visualizer */}
      <View style={styles.visualizerContainer}>
        <Animated.View
          style={[styles.pulseRing, {transform: [{scale: pulseAnim}]}]}
        />
        <View
          style={[
            styles.micCircle,
            screenState === 'recording' && styles.micCircleActive,
            screenState === 'paused' && styles.micCirclePaused,
          ]}>
          <Icon
            name={screenState === 'paused' ? 'pause' : 'mic'}
            size={48}
            color="#FFFFFF"
          />
        </View>
      </View>

      {/* Timer */}
      <Text style={styles.timer}>{formatDuration(elapsedMs)}</Text>
      <Text style={styles.statusLabel}>
        {screenState === 'ready' && 'Ready to record'}
        {screenState === 'recording' && 'Recording…'}
        {screenState === 'paused' && 'Paused'}
        {screenState === 'processing' && 'Uploading & processing…'}
      </Text>

      {/* Controls */}
      {screenState === 'ready' && (
        <TouchableOpacity style={styles.startButton} onPress={handleStart}>
          <Icon name="mic" size={24} color="#FFFFFF" />
          <Text style={styles.startButtonText}>Start Recording</Text>
        </TouchableOpacity>
      )}

      {(screenState === 'recording' || screenState === 'paused') && (
        <View style={styles.controls}>
          <TouchableOpacity style={styles.cancelButton} onPress={handleCancel}>
            <Icon name="trash-outline" size={22} color="#EF4444" />
            <Text style={styles.cancelButtonText}>Discard</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.pauseButton}
            onPress={screenState === 'recording' ? handlePause : handleResume}>
            <Icon
              name={screenState === 'recording' ? 'pause' : 'play'}
              size={22}
              color="#FFFFFF"
            />
            <Text style={styles.pauseButtonText}>
              {screenState === 'recording' ? 'Pause' : 'Resume'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.stopButton} onPress={handleStop}>
            <Icon name="stop-circle" size={22} color="#FFFFFF" />
            <Text style={styles.stopButtonText}>Stop & Process</Text>
          </TouchableOpacity>
        </View>
      )}

      {screenState === 'processing' && (
        <View style={styles.processingRow}>
          <Icon name="cloud-upload-outline" size={20} color="#3B82F6" />
          <Text style={styles.processingText}>
            Uploading audio for transcription…
          </Text>
        </View>
      )}

      {/* Background recording note */}
      {screenState === 'recording' && (
        <View style={styles.backgroundNote}>
          <Icon name="checkmark-circle" size={14} color="#10B981" />
          <Text style={styles.backgroundNoteText}>
            Recording continues while app is in background
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  hintBox: {
    position: 'absolute',
    top: 16,
    left: 16,
    right: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#1F2937',
    borderRadius: 10,
    padding: 12,
    gap: 8,
  },
  hintText: {
    flex: 1,
    fontSize: 13,
    color: '#9CA3AF',
    lineHeight: 18,
  },
  visualizerContainer: {
    width: 160,
    height: 160,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
  },
  pulseRing: {
    position: 'absolute',
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: 'rgba(59, 130, 246, 0.15)',
  },
  micCircle: {
    width: 112,
    height: 112,
    borderRadius: 56,
    backgroundColor: '#1F2937',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#374151',
  },
  micCircleActive: {
    backgroundColor: '#EF4444',
    borderColor: '#DC2626',
  },
  micCirclePaused: {
    backgroundColor: '#F59E0B',
    borderColor: '#D97706',
  },
  timer: {
    fontSize: 48,
    fontWeight: '700',
    color: '#FFFFFF',
    fontVariant: ['tabular-nums'],
    letterSpacing: 2,
    marginBottom: 8,
  },
  statusLabel: {
    fontSize: 15,
    color: '#9CA3AF',
    marginBottom: 40,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EF4444',
    paddingVertical: 18,
    paddingHorizontal: 48,
    borderRadius: 50,
    gap: 10,
  },
  startButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  controls: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  cancelButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#EF4444',
    gap: 4,
  },
  cancelButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#EF4444',
  },
  pauseButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#374151',
    gap: 4,
  },
  pauseButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  stopButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#3B82F6',
    gap: 6,
  },
  stopButtonText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  processingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 8,
  },
  processingText: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  backgroundNote: {
    position: 'absolute',
    bottom: 32,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  backgroundNoteText: {
    fontSize: 12,
    color: '#10B981',
  },
});
