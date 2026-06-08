import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {DashboardStackParamList} from '@/navigation/types';
import {useResultsStore} from '@/stores/resultsStore';
import {TaskCard, DecisionCard, RiskCard} from '@/components';
import Icon from 'react-native-vector-icons/Ionicons';
import {exportReportAsPdf} from '@/utils/exportReport';

type Props = NativeStackScreenProps<DashboardStackParamList, 'TranscriptionResult'>;

export default function TranscriptionResultScreen({route, navigation}: Props) {
  const {jobId} = route.params;
  const {getResultByJobId, fetchResult, isLoading, error} = useResultsStore();
  const [activeTab, setActiveTab] = useState<'tasks' | 'decisions' | 'risks'>('tasks');
  const [exporting, setExporting] = useState(false);

  const result = getResultByJobId(jobId);

  useEffect(() => {
    if (!result) {
      fetchResult(jobId);
    }
  }, [jobId, result]);

  // Add export button to the navigation header
  useEffect(() => {
    if (!result) return;
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={handleExport}
          disabled={exporting}
          style={{marginRight: 8, padding: 4}}>
          {exporting ? (
            <ActivityIndicator size="small" color="#3B82F6" />
          ) : (
            <Icon name="download-outline" size={24} color="#3B82F6" />
          )}
        </TouchableOpacity>
      ),
    });
  }, [result, exporting]);

  const handleExport = async () => {
    if (!result) return;
    setExporting(true);
    try {
      await exportReportAsPdf({
        title: 'Meeting / Call Report',
        source: `Job ID: ${result.job_id}`,
        summary: result.summary,
        transcript: result.transcription,
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

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading results...</Text>
      </View>
    );
  }

  if (error || !result) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle-outline" size={48} color="#EF4444" />
        <Text style={styles.errorText}>{error || 'Failed to load results'}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>Summary</Text>
        <Text style={styles.summaryText}>{result.summary}</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['tasks', 'decisions', 'risks'] as const).map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}>
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)} ({result[tab].length})
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.content} contentContainerStyle={styles.contentPadding}>
        {activeTab === 'tasks' &&
          result.tasks.map(task => <TaskCard key={task.id} task={task} />)}
        {activeTab === 'decisions' &&
          result.decisions.map(d => <DecisionCard key={d.id} decision={d} />)}
        {activeTab === 'risks' &&
          result.risks.map(r => <RiskCard key={r.id} risk={r} />)}
      </ScrollView>

      {/* Export bar */}
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
          {exporting ? 'Generating PDF…' : 'Download Report + Transcript'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#000000'},
  loadingContainer: {
    flex: 1,
    backgroundColor: '#000000',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {marginTop: 16, fontSize: 16, color: '#9CA3AF'},
  errorContainer: {
    flex: 1,
    backgroundColor: '#000000',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  errorText: {marginTop: 16, fontSize: 16, color: '#EF4444', textAlign: 'center'},
  summaryCard: {
    backgroundColor: '#1F2937',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  summaryTitle: {fontSize: 16, fontWeight: '600', color: '#FFFFFF', marginBottom: 8},
  summaryText: {fontSize: 14, color: '#D1D5DB', lineHeight: 20},
  tabs: {flexDirection: 'row', paddingHorizontal: 16, gap: 8},
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
    backgroundColor: '#1F2937',
  },
  activeTab: {backgroundColor: '#3B82F6'},
  tabText: {fontSize: 13, fontWeight: '600', color: '#9CA3AF'},
  activeTabText: {color: '#FFFFFF'},
  content: {flex: 1},
  contentPadding: {padding: 16},
  exportBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: '#3B82F6',
    padding: 16,
  },
  exportBarDisabled: {backgroundColor: '#1D4ED8', opacity: 0.7},
  exportBarText: {fontSize: 15, fontWeight: '700', color: '#FFFFFF'},
});
