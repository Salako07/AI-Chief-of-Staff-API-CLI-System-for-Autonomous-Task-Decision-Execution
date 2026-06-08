// Record Stack Navigator - Video Recording Flow

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {RecordStackParamList} from './types';

import RecordVideoScreen from '@/screens/record/RecordVideoScreen';
import MeetingRecorderScreen from '@/screens/record/MeetingRecorderScreen';
import UploadProgressScreen from '@/screens/record/UploadProgressScreen';
import ProcessingStatusScreen from '@/screens/record/ProcessingStatusScreen';

const Stack = createStackNavigator<RecordStackParamList>();

export function RecordNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {backgroundColor: '#000000'},
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {fontWeight: '600'},
        contentStyle: {backgroundColor: '#000000'},
      }}>
      <Stack.Screen
        name="RecordVideo"
        component={RecordVideoScreen}
        options={{title: 'Record Video'}}
      />
      <Stack.Screen
        name="MeetingRecorder"
        component={MeetingRecorderScreen}
        options={{title: 'Meeting Recorder'}}
      />
      <Stack.Screen
        name="UploadProgress"
        component={UploadProgressScreen}
        options={{
          title: 'Uploading',
          headerBackVisible: false, // Prevent back during upload
        }}
      />
      <Stack.Screen
        name="ProcessingStatus"
        component={ProcessingStatusScreen}
        options={{
          title: 'Processing',
          headerBackVisible: false, // Prevent back during processing
        }}
      />
    </Stack.Navigator>
  );
}
