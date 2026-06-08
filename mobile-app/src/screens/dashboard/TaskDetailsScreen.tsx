// Task Details Screen - Placeholder

import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {DashboardStackParamList} from '@/navigation/types';

type Props = NativeStackScreenProps<DashboardStackParamList, 'TaskDetails'>;

export default function TaskDetailsScreen({route}: Props) {
  const {taskId} = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.text}>Task Details Screen</Text>
      <Text style={styles.subtext}>Task ID: {taskId}</Text>
      <Text style={styles.placeholder}>
        Implementation: Display full task details, edit status, assign owner
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
