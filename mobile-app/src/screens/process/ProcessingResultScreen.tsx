import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import Icon from 'react-native-vector-icons/Ionicons';
import {ProcessStackParamList} from '@/navigation/types';
import {TaskCard, DecisionCard, RiskCard} from '@/components';
import {exportReportAsPdf} from '@/utils/exportReport';

type Props = NativeStackScreenProps<ProcessStackParamList, 'ProcessingResult'>;
type Tab = 'tasks' | 'decisions' | 'risks';

export default function ProcessingResultScreen({route, navigation}: Props) {
  const {result} = route.params;
  const [activeTab, setActiveTab] = useState<Tab>('tasks');
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportReportAsPdf({
        title: 'Text Processing Report',
        source: `Run ID: ${result.metadata.run_id}`,
        summary: result.summary,
        tasks: result.tasks,
        decisions: result.decisions,
        risks: result.risks,
      });
    } catch (e: any) {
      Alert.alert('Export Failed', e.message || 'Could not generate report.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>Summary</Text>
        <Text style={styles.summaryText}>{result.summary}</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['tasks', 'decisions', 'risks'] as Tab[]).map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}>
            <Text
              style={[
                styles.tabText,
                activeTab === tab && styles.activeTabText,
              ]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)} (
              {result[tab].length})
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentPadding}>
        {activeTab === 'tasks' &&
          (result.tasks.length > 0 ? (
            result.tasks.map(task => <TaskCard key={task.id} task={task} />)
          ) : (
            <EmptyTabMessage icon="checkmark-done-outline" label="No tasks found" />
          ))}

        {activeTab === 'decisions' &&
          (result.decisions.length > 0 ? (
            result.decisions.map(decision => (
              <DecisionCard key={decision.id} decision={decision} />
            ))
          ) : (
            <EmptyTabMessage icon="git-branch-outline" label="No decisions found" />
          ))}

        {activeTab === 'risks' &&
          (result.risks.length > 0 ? (
            result.risks.map(risk => <RiskCard key={risk.id} risk={risk} />)
          ) : (
            <EmptyTabMessage icon="shield-checkmark-outline" label="No risks found" />
          ))}
      </ScrollView>

      {/* Export */}
      <TouchableOpacity
        style={[styles.exportBar, exporting && styles.exportBarDisabled]}
        onPress={handleExport}
        disabled={exporting}>
        {exporting ? (
          <ActivityIndicator size="small" color="#FFFFFF" />
        ) : (
          <Icon name="download-outline" size={18} color="#FFFFFF" />
        )}
        <Text style={styles.exportBarText}>
          {exporting ? 'Generating PDF…' : 'Download Report'}
        </Text>
      </TouchableOpacity>

      {/* Bottom actions */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.closeButton}
          onPress={() => navigation.goBack()}>
          <Icon name="close-outline" size={20} color="#9CA3AF" />
          <Text style={styles.closeButtonText}>Close</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.newButton}
          onPress={() => navigation.popToTop()}>
          <Icon name="add-circle-outline" size={20} color="#3B82F6" />
          <Text style={styles.newButtonText}>New Session</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function EmptyTabMessage({icon, label}: {icon: string; label: string}) {
  return (
    <View style={emptyStyles.container}>
      <Icon name={icon} size={40} color="#374151" />
      <Text style={emptyStyles.text}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  summaryCard: {
    backgroundColor: '#1F2937',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 14,
    color: '#D1D5DB',
    lineHeight: 20,
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
    backgroundColor: '#1F2937',
  },
  activeTab: {
    backgroundColor: '#3B82F6',
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#9CA3AF',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  content: {
    flex: 1,
  },
  contentPadding: {
    padding: 16,
    paddingBottom: 8,
  },
  actions: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#1F2937',
  },
  closeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: 16,
    borderRightWidth: 1,
    borderRightColor: '#1F2937',
  },
  closeButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#9CA3AF',
  },
  newButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: 16,
  },
  newButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#3B82F6',
  },
  exportBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: '#3B82F6',
    padding: 14,
  },
  exportBarDisabled: {backgroundColor: '#1D4ED8', opacity: 0.7},
  exportBarText: {fontSize: 15, fontWeight: '700', color: '#FFFFFF'},
});

const emptyStyles = StyleSheet.create({
  container: {
    alignItems: 'center',
    paddingTop: 48,
    gap: 12,
  },
  text: {
    fontSize: 14,
    color: '#6B7280',
  },
});
