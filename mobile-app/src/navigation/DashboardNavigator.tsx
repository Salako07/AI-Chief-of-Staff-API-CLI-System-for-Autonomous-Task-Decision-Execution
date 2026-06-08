// Dashboard Stack Navigator

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {DashboardStackParamList} from './types';

// Placeholder screens
import DashboardHomeScreen from '@/screens/dashboard/DashboardHomeScreen';
import VideoDetailsScreen from '@/screens/dashboard/VideoDetailsScreen';
import TranscriptionResultScreen from '@/screens/dashboard/TranscriptionResultScreen';
import TaskDetailsScreen from '@/screens/dashboard/TaskDetailsScreen';

const Stack = createStackNavigator<DashboardStackParamList>();

export function DashboardNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {backgroundColor: '#000000'},
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {fontWeight: '600'},
        contentStyle: {backgroundColor: '#000000'},
      }}>
      <Stack.Screen
        name="DashboardHome"
        component={DashboardHomeScreen}
        options={{title: 'Dashboard'}}
      />
      <Stack.Screen
        name="VideoDetails"
        component={VideoDetailsScreen}
        options={{title: 'Video Details'}}
      />
      <Stack.Screen
        name="TranscriptionResult"
        component={TranscriptionResultScreen}
        options={{title: 'Results'}}
      />
      <Stack.Screen
        name="TaskDetails"
        component={TaskDetailsScreen}
        options={{title: 'Task Details'}}
      />
    </Stack.Navigator>
  );
}
