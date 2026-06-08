// Root App Navigator - Direct to Main (No Auth for now)

import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {MainNavigator} from './MainNavigator';

export function AppNavigator() {
  // Skip authentication for now - direct to main app
  return (
    <NavigationContainer>
      <MainNavigator />
    </NavigationContainer>
  );
}
