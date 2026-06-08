import React, {useEffect, useRef} from 'react';
import {View, Text, StyleSheet, Alert} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import Icon from 'react-native-vector-icons/Ionicons';
import {RecordStackParamList} from '@/navigation/types';
import {useUploadStore} from '@/stores/uploadStore';
import {ProgressBar} from '@/components';

type Props = NativeStackScreenProps<RecordStackParamList, 'UploadProgress'>;

export default function UploadProgressScreen({route, navigation}: Props) {
  const {mediaId: uploadId, filename} = route.params;
  const started = useRef(false);

  const upload = useUploadStore(state =>
    state.uploads.find(u => u.id === uploadId),
  );
  const uploadVideo = useUploadStore(state => state.uploadVideo);
  const updateUpload = useUploadStore(state => state.updateUpload);
  const startTranscription = useUploadStore(state => state.startTranscription);

  useEffect(() => {
    if (started.current || !upload) return;
    started.current = true;

    const run = async () => {
      try {
        const response = await uploadVideo(
          {uri: upload.fileUri, type: upload.fileType, name: upload.filename},
          progress => updateUpload(uploadId, {progress}),
        );

        updateUpload(uploadId, {
          status: 'processing',
          mediaId: response.media_id,
          progress: 100,
        });

        await startTranscription(response.media_id, uploadId);

        const refreshed = useUploadStore
          .getState()
          .uploads.find(u => u.id === uploadId);
        if (refreshed?.jobId) {
          navigation.replace('ProcessingStatus', {jobId: refreshed.jobId});
        }
      } catch (error: any) {
        Alert.alert('Upload Failed', error.message || 'Could not upload file.', [
          {text: 'OK', onPress: () => navigation.goBack()},
        ]);
      }
    };

    run();
  }, []);

  const progress = upload?.progress ?? 0;
  const isUploading = (upload?.progress ?? 0) < 100 || upload?.status === 'uploading';

  return (
    <View style={styles.container}>
      <Icon
        name={isUploading ? 'cloud-upload' : 'checkmark-circle'}
        size={64}
        color={isUploading ? '#3B82F6' : '#10B981'}
      />
      <Text style={styles.title}>
        {isUploading ? 'Uploading Video' : 'Upload Complete'}
      </Text>
      <Text style={styles.filename}>{filename}</Text>

      <View style={styles.progressContainer}>
        <ProgressBar progress={progress} />
        <Text style={styles.progressText}>{Math.round(progress)}%</Text>
      </View>

      <Text style={styles.statusText}>
        {isUploading
          ? 'Uploading to server...'
          : 'Starting transcription...'}
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
    marginTop: 16,
    marginBottom: 8,
  },
  filename: {
    fontSize: 14,
    color: '#9CA3AF',
    marginBottom: 32,
  },
  progressContainer: {
    width: '100%',
    marginBottom: 16,
  },
  progressText: {
    fontSize: 14,
    color: '#3B82F6',
    textAlign: 'center',
    marginTop: 8,
  },
  statusText: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
  },
});
