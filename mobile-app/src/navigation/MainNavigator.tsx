// Main Tab Navigator - Authenticated User Interface

import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {MainTabParamList} from './types';
import Icon from 'react-native-vector-icons/Ionicons';

// Stack navigators for each tab
import {DashboardNavigator} from './DashboardNavigator';
import {RecordNavigator} from './RecordNavigator';
import {ProcessNavigator} from './ProcessNavigator';
import ProfileScreen from '@/screens/main/ProfileScreen';

const Tab = createBottomTabNavigator<MainTabParamList>();

export function MainNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#000000',
          borderTopColor: '#1F2937',
          borderTopWidth: 1,
          paddingBottom: 8,
          paddingTop: 8,
          height: 60,
        },
        tabBarActiveTintColor: '#3B82F6',
        tabBarInactiveTintColor: '#6B7280',
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
      }}>
      <Tab.Screen
        name="Dashboard"
        component={DashboardNavigator}
        options={{
          tabBarIcon: ({color, size}) => (
            <Icon name="grid-outline" size={size} color={color} />
          ),
          tabBarLabel: 'Dashboard',
        }}
      />
      <Tab.Screen
        name="Record"
        component={RecordNavigator}
        options={{
          tabBarIcon: ({color, size}) => (
            <Icon name="videocam-outline" size={size} color={color} />
          ),
          tabBarLabel: 'Record',
        }}
      />
      <Tab.Screen
        name="Process"
        component={ProcessNavigator}
        options={{
          tabBarIcon: ({color, size}) => (
            <Icon name="document-text-outline" size={size} color={color} />
          ),
          tabBarLabel: 'Text',
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({color, size}) => (
            <Icon name="person-outline" size={size} color={color} />
          ),
          tabBarLabel: 'Profile',
        }}
      />
    </Tab.Navigator>
  );
}
