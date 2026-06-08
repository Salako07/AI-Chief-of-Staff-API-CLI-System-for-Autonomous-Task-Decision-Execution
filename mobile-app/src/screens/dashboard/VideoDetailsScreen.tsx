// Video Details Screen - Placeholder

import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {DashboardStackParamList} from '@/navigation/types';

type Props = NativeStackScreenProps<DashboardStackParamList, 'VideoDetails'>;

export default function VideoDetailsScreen({route}: Props) {
  const {mediaId} = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.text}>Video Details Screen</Text>
      <Text style={styles.subtext}>Media ID: {mediaId}</Text>
      <Text style={styles.placeholder}>
        Implementation: Display video metadata, playback, and transcription
        results
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
  text: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  subtext: {
    fontSize: 14,
    color: '#9CA3AF',
    marginBottom: 16,
  },
  placeholder: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
