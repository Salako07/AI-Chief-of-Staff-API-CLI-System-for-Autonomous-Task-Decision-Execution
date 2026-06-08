import React, {useEffect, useRef, useState} from 'react';
import {View, Text, StyleSheet, ActivityIndicator, Alert} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {RecordStackParamList} from '@/navigation/types';
import {mediaApi} from '@/api';
import {ProgressBar} from '@/components';

type Props = NativeStackScreenProps<RecordStackParamList, 'ProcessingStatus'>;

const STATUS_MESSAGES: Record<string, string> = {
  queued: 'Waiting in queue...',
  processing: 'Transcribing audio with AI...',
  completed: 'Transcription complete!',
  failed: 'Processing failed.',
};

export default function ProcessingStatusScreen({route, navigation}: Props) {
  const {jobId} = route.params;
  const started = useRef(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('Starting...');

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const run = async () => {
      try {
        await mediaApi.pollTranscriptionStatus(jobId, status => {
          setProgress(status.progress ?? 0);
          setStatusMessage(STATUS_MESSAGES[status.status] ?? 'Processing...');
        });

        // Reset Record stack to root so tapping the tab again lands on RecordVideo
        navigation.popToTop();
        // Then switch to Dashboard and show the result
        navigation.getParent()?.navigate('Dashboard', {
          screen: 'TranscriptionResult',
          params: {jobId},
        });
      } catch (error: any) {
        Alert.alert(
          'Processing Failed',
          error.message || 'Could not process video.',
          [{text: 'OK', onPress: () => navigation.popToTop()}],
        );
      }
    };

    run();
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#3B82F6" />
      <Text style={styles.title}>Processing Video</Text>
      <Text style={styles.subtitle}>Extracting insights with AI...</Text>

      <View style={styles.progressContainer}>
        <ProgressBar progress={progress} showPercentage={false} />
        <Text style={styles.statusText}>{statusMessage}</Text>
      </View>

      <Text style={styles.hint}>
        This may take a few minutes depending on video length.
      </Text>
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
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 24,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    marginBottom: 32,
  },
  progressContainer: {
    width: '100%',
    marginBottom: 24,
  },
  statusText: {
    fontSize: 14,
    color: '#3B82F6',
    marginTop: 12,
    textAlign: 'center',
  },
  hint: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
  },
});
