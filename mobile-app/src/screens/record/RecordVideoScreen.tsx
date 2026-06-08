import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import * as ImagePicker from 'expo-image-picker';
import Icon from 'react-native-vector-icons/Ionicons';
import {RecordStackParamList} from '@/navigation/types';
import {useUploadStore} from '@/stores/uploadStore';

type Props = NativeStackScreenProps<RecordStackParamList, 'RecordVideo'>;

export default function RecordVideoScreen({navigation}: Props) {
  const [isLoading, setIsLoading] = useState(false);
  const addUpload = useUploadStore(state => state.addUpload);

  const handlePickVideo = async (fromCamera: boolean) => {
    const permissionResult = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();

    if (!permissionResult.granted) {
      Alert.alert(
        'Permission Required',
        fromCamera
          ? 'Camera access is needed to record videos.'
          : 'Media library access is needed to upload videos.',
      );
      return;
    }

    setIsLoading(true);
    try {
      const result = fromCamera
        ? await ImagePicker.launchCameraAsync({
            mediaTypes: 'videos',
            videoMaxDuration: 300,
            allowsEditing: false,
          })
        : await ImagePicker.launchImageLibraryAsync({
            mediaTypes: 'videos',
            allowsEditing: false,
          });

      if (result.canceled || !result.assets?.[0]) {
        return;
      }

      const asset = result.assets[0];
      const uploadId = `upload_${Date.now()}`;
      const filename = asset.fileName ?? `video_${Date.now()}.mp4`;

      addUpload({
        id: uploadId,
        filename,
        fileUri: asset.uri,
        fileType: asset.mimeType ?? 'video/mp4',
        status: 'uploading',
        progress: 0,
      });

      navigation.navigate('UploadProgress', {mediaId: uploadId, filename});
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to pick video.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Icon name="videocam-outline" size={80} color="#3B82F6" />
      <Text style={styles.title}>Record or Upload Video</Text>
      <Text style={styles.description}>
        Record a meeting or upload an existing video to extract tasks, decisions,
        and risks with AI.
      </Text>

      {isLoading ? (
        <ActivityIndicator size="large" color="#3B82F6" style={styles.loader} />
      ) : (
        <View style={styles.buttons}>
          <TouchableOpacity
            style={styles.button}
            onPress={() => handlePickVideo(true)}>
            <Icon name="camera" size={24} color="#FFFFFF" />
            <Text style={styles.buttonText}>Record Video</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={() => handlePickVideo(false)}>
            <Icon name="cloud-upload-outline" size={24} color="#3B82F6" />
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>
              Upload File
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.meetingButton]}
            onPress={() => navigation.navigate('MeetingRecorder')}>
            <Icon name="mic" size={24} color="#FFFFFF" />
            <Text style={styles.buttonText}>Meeting Recorder</Text>
          </TouchableOpacity>
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
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 24,
    marginBottom: 12,
  },
  description: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    lineHeight: 20,
  },
  loader: {
    marginTop: 40,
  },
  buttons: {
    marginTop: 32,
    width: '100%',
    gap: 12,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#3B82F6',
  },
  secondaryButtonText: {
    color: '#3B82F6',
  },
  meetingButton: {
    backgroundColor: '#EF4444',
  },
});
