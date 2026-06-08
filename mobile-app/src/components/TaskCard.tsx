// Task Card Component

import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import {Task} from '@/types/api';
import Icon from 'react-native-vector-icons/Ionicons';

interface TaskCardProps {
  task: Task;
  onPress?: () => void;
  showStatus?: boolean;
}

export default function TaskCard({
  task,
  onPress,
  showStatus = true,
}: TaskCardProps) {
  const priorityColors = {
    low: '#10B981',
    medium: '#F59E0B',
    high: '#EF4444',
  };

  const statusIcons = {
    pending: 'ellipse-outline',
    in_progress: 'play-circle-outline',
    completed: 'checkmark-circle',
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={onPress ? 0.7 : 1}>
      <View style={styles.header}>
        <View style={styles.priorityBadge}>
          <View
            style={[
              styles.priorityDot,
              {backgroundColor: priorityColors[task.priority]},
            ]}
          />
          <Text style={styles.priorityText}>
            {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
          </Text>
        </View>

        {showStatus && (
          <View style={styles.statusBadge}>
            <Icon
              name={statusIcons[task.status]}
              size={16}
              color={
                task.status === 'completed' ? '#10B981' : '#9CA3AF'
              }
            />
            <Text style={styles.statusText}>
              {task.status === 'in_progress' ? 'In Progress' : task.status.charAt(0).toUpperCase() + task.status.slice(1)}
            </Text>
          </View>
        )}
      </View>

      <Text style={styles.title}>{task.title}</Text>

      <View style={styles.footer}>
        {task.owner && (
          <View style={styles.footerItem}>
            <Icon name="person-outline" size={14} color="#9CA3AF" />
            <Text style={styles.footerText}>{task.owner}</Text>
          </View>
        )}

        {task.deadline && (
          <View style={styles.footerItem}>
            <Icon name="calendar-outline" size={14} color="#9CA3AF" />
            <Text style={styles.footerText}>
              {new Date(task.deadline).toLocaleDateString()}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  priorityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111827',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginLeft: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
    lineHeight: 22,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  footerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  footerText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginLeft: 4,
  },
});
