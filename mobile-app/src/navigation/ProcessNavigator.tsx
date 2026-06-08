// Process Stack Navigator - Text Processing Flow

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {ProcessStackParamList} from './types';

// Placeholder screens
import TextInputScreen from '@/screens/process/TextInputScreen';
import ProcessingResultScreen from '@/screens/process/ProcessingResultScreen';

const Stack = createStackNavigator<ProcessStackParamList>();

export function ProcessNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {backgroundColor: '#000000'},
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {fontWeight: '600'},
        contentStyle: {backgroundColor: '#000000'},
      }}>
      <Stack.Screen
        name="TextInput"
        component={TextInputScreen}
        options={{title: 'Process Text'}}
      />
      <Stack.Screen
        name="ProcessingResult"
        component={ProcessingResultScreen}
        options={{title: 'Results'}}
      />
    </Stack.Navigator>
  );
}
