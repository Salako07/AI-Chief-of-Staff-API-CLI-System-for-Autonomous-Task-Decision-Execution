// Decision Card Component

import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import {Decision} from '@/types/api';
import Icon from 'react-native-vector-icons/Ionicons';

interface DecisionCardProps {
  decision: Decision;
  onPress?: () => void;
}

export default function DecisionCard({decision, onPress}: DecisionCardProps) {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={onPress ? 0.7 : 1}>
      <View style={styles.header}>
        <Icon name="bulb" size={20} color="#F59E0B" />
        <Text style={styles.badge}>Decision</Text>
      </View>

      <Text style={styles.decision}>{decision.decision}</Text>

      <View style={styles.footer}>
        {decision.made_by && (
          <View style={styles.footerItem}>
            <Icon name="person-outline" size={14} color="#9CA3AF" />
            <Text style={styles.footerText}>Made by {decision.made_by}</Text>
          </View>
        )}

        <View style={styles.footerItem}>
          <Icon name="time-outline" size={14} color="#9CA3AF" />
          <Text style={styles.footerText}>
            {new Date(decision.timestamp).toLocaleDateString()}
          </Text>
        </View>
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
    borderLeftWidth: 4,
    borderLeftColor: '#F59E0B',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  badge: {
    fontSize: 12,
    fontWeight: '600',
    color: '#F59E0B',
    marginLeft: 8,
    backgroundColor: '#78350F',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  decision: {
    fontSize: 15,
    color: '#FFFFFF',
    marginBottom: 12,
    lineHeight: 22,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    flexWrap: 'wrap',
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
