// Dashboard Home Screen

import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {DashboardStackParamList} from '@/navigation/types';
import {useResultsStore} from '@/stores/resultsStore';
import {TaskCard, EmptyState} from '@/components';
import Icon from 'react-native-vector-icons/Ionicons';

type Props = NativeStackScreenProps<DashboardStackParamList, 'DashboardHome'>;

export default function DashboardHomeScreen({navigation}: Props) {
  const {results, getAllTasks, getAllDecisions, getAllRisks} = useResultsStore();
  const [refreshing, setRefreshing] = useState(false);

  const tasks = getAllTasks();
  const decisions = getAllDecisions();
  const risks = getAllRisks();

  const pendingTasks = tasks.filter(t => t.status === 'pending');
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
  const highPriorityTasks = tasks.filter(t => t.priority === 'high');

  const onRefresh = async () => {
    setRefreshing(true);
    // TODO: Fetch latest data from API
    setTimeout(() => setRefreshing(false), 1000);
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor="#3B82F6"
        />
      }>
      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        <StatCard
          icon="checkbox-outline"
          label="Total Tasks"
          value={tasks.length}
          color="#3B82F6"
        />
        <StatCard
          icon="bulb-outline"
          label="Decisions"
          value={decisions.length}
          color="#F59E0B"
        />
        <StatCard
          icon="alert-circle-outline"
          label="Risks"
          value={risks.length}
          color="#EF4444"
        />
        <StatCard
          icon="videocam-outline"
          label="Uploads"
          value={results.length}
          color="#10B981"
        />
      </View>

      {/* Quick Stats */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Overview</Text>
        <View style={styles.quickStats}>
          <QuickStat label="Pending" value={pendingTasks.length} />
          <QuickStat label="In Progress" value={inProgressTasks.length} />
          <QuickStat label="High Priority" value={highPriorityTasks.length} />
        </View>
      </View>

      {/* Recent Tasks */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Tasks</Text>
          <TouchableOpacity>
            <Text style={styles.seeAllText}>See All</Text>
          </TouchableOpacity>
        </View>

        {tasks.length === 0 ? (
          <EmptyState
            icon="clipboard-outline"
            title="No Tasks Yet"
            description="Upload a video or process text to extract tasks"
          />
        ) : (
          <View>
            {tasks.slice(0, 5).map(task => (
              <TaskCard
                key={task.id}
                task={task}
                onPress={() =>
                  navigation.navigate('TaskDetails', {taskId: task.id})
                }
              />
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: string;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <View style={[styles.statCard, {borderLeftColor: color}]}>
      <Icon name={icon} size={24} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function QuickStat({label, value}: {label: string; value: number}) {
  return (
    <View style={styles.quickStat}>
      <Text style={styles.quickStatValue}>{value}</Text>
      <Text style={styles.quickStatLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  content: {
    padding: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    minWidth: '47%',
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#374151',
    borderLeftWidth: 4,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  seeAllText: {
    fontSize: 14,
    color: '#3B82F6',
    fontWeight: '600',
  },
  quickStats: {
    flexDirection: 'row',
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#374151',
    justifyContent: 'space-around',
  },
  quickStat: {
    alignItems: 'center',
  },
  quickStatValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  quickStatLabel: {
    fontSize: 12,
    color: '#9CA3AF',
  },
});
