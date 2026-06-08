// Risk Card Component

import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import {Risk} from '@/types/api';
import Icon from 'react-native-vector-icons/Ionicons';

interface RiskCardProps {
  risk: Risk;
  onPress?: () => void;
}

export default function RiskCard({risk, onPress}: RiskCardProps) {
  const severityColors = {
    low: '#10B981',
    medium: '#F59E0B',
    high: '#EF4444',
  };

  const severityIcons = {
    low: 'alert-circle-outline',
    medium: 'warning-outline',
    high: 'alert-outline',
  };

  return (
    <TouchableOpacity
      style={[
        styles.card,
        {borderLeftColor: severityColors[risk.severity]},
      ]}
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={onPress ? 0.7 : 1}>
      <View style={styles.header}>
        <Icon
          name={severityIcons[risk.severity]}
          size={20}
          color={severityColors[risk.severity]}
        />
        <View
          style={[
            styles.severityBadge,
            {backgroundColor: severityColors[risk.severity] + '20'},
          ]}>
          <Text
            style={[
              styles.severityText,
              {color: severityColors[risk.severity]},
            ]}>
            {risk.severity.charAt(0).toUpperCase() + risk.severity.slice(1)}{' '}
            Risk
          </Text>
        </View>
      </View>

      <Text style={styles.riskText}>{risk.risk}</Text>

      {risk.mitigation && (
        <View style={styles.mitigationContainer}>
          <View style={styles.mitigationHeader}>
            <Icon name="shield-checkmark-outline" size={16} color="#10B981" />
            <Text style={styles.mitigationLabel}>Mitigation</Text>
          </View>
          <Text style={styles.mitigationText}>{risk.mitigation}</Text>
        </View>
      )}
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
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  severityBadge: {
    marginLeft: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  severityText: {
    fontSize: 12,
    fontWeight: '600',
  },
  riskText: {
    fontSize: 15,
    color: '#FFFFFF',
    marginBottom: 12,
    lineHeight: 22,
  },
  mitigationContainer: {
    backgroundColor: '#111827',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#10B981',
  },
  mitigationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  mitigationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#10B981',
    marginLeft: 6,
  },
  mitigationText: {
    fontSize: 13,
    color: '#D1D5DB',
    lineHeight: 20,
  },
});
