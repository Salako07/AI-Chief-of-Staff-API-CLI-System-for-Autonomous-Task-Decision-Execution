// Video Card Component - For displaying video uploads

import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import {VideoMetadata} from '@/types/api';
import Icon from 'react-native-vector-icons/Ionicons';

interface VideoCardProps {
  video: VideoMetadata;
  onPress?: () => void;
}

export default function VideoCard({video, onPress}: VideoCardProps) {
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return 'Unknown';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10B981';
      case 'processing':
        return '#F59E0B';
      case 'failed':
        return '#EF4444';
      default:
        return '#9CA3AF';
    }
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={onPress ? 0.7 : 1}>
      <View style={styles.thumbnail}>
        <Icon name="videocam" size={32} color="#3B82F6" />
      </View>

      <View style={styles.content}>
        <Text style={styles.filename} numberOfLines={1}>
          {video.filename}
        </Text>

        <View style={styles.metadata}>
          <View style={styles.metaItem}>
            <Icon name="timer-outline" size={14} color="#9CA3AF" />
            <Text style={styles.metaText}>
              {formatDuration(video.duration_seconds)}
            </Text>
          </View>

          <View style={styles.metaItem}>
            <Icon name="document-outline" size={14} color="#9CA3AF" />
            <Text style={styles.metaText}>{formatFileSize(video.size_bytes)}</Text>
          </View>

          <View style={styles.metaItem}>
            <Icon name="calendar-outline" size={14} color="#9CA3AF" />
            <Text style={styles.metaText}>
              {new Date(video.created_at).toLocaleDateString()}
            </Text>
          </View>
        </View>

        {video.transcription_job && (
          <View
            style={[
              styles.statusBadge,
              {
                backgroundColor:
                  getStatusColor(video.transcription_job.status) + '20',
              },
            ]}>
            <Text
              style={[
                styles.statusText,
                {color: getStatusColor(video.transcription_job.status)},
              ]}>
              {video.transcription_job.status === 'completed'
                ? 'Processed'
                : video.transcription_job.status.charAt(0).toUpperCase() +
                  video.transcription_job.status.slice(1)}
            </Text>
          </View>
        )}
      </View>

      <Icon name="chevron-forward" size={20} color="#6B7280" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
    flexDirection: 'row',
    alignItems: 'center',
  },
  thumbnail: {
    width: 60,
    height: 60,
    backgroundColor: '#111827',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  content: {
    flex: 1,
  },
  filename: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  metadata: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 11,
    color: '#9CA3AF',
    marginLeft: 2,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
  },
});
