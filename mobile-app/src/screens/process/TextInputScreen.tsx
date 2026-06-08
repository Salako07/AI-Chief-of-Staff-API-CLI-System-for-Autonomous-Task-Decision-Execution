import React, {useState} from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import Icon from 'react-native-vector-icons/Ionicons';
import {ProcessStackParamList} from '@/navigation/types';
import {textApi} from '@/api';

type Props = NativeStackScreenProps<ProcessStackParamList, 'TextInput'>;

export default function TextInputScreen({navigation}: Props) {
  const [text, setText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleProcess = async () => {
    if (!text.trim()) return;
    setIsProcessing(true);
    try {
      const result = await textApi.processText(text.trim());
      setText(''); // clear so next session starts fresh
      navigation.navigate('ProcessingResult', {
        runId: result.metadata.run_id,
        result,
      });
    } catch (error: any) {
      Alert.alert(
        'Processing Failed',
        error.message || 'Could not process text. Check your connection.',
      );
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Icon name="document-text-outline" size={48} color="#3B82F6" />
          <Text style={styles.title}>Process Text</Text>
          <Text style={styles.description}>
            Paste meeting notes, transcripts, or any text to extract actionable
            insights
          </Text>
        </View>

        <TextInput
          style={styles.textInput}
          placeholder="Paste your text here..."
          placeholderTextColor="#6B7280"
          multiline
          value={text}
          onChangeText={setText}
          textAlignVertical="top"
          editable={!isProcessing}
        />

        <View style={styles.charCount}>
          <Text style={styles.charCountText}>{text.length} characters</Text>
        </View>

        <TouchableOpacity
          style={[
            styles.processButton,
            (!text.trim() || isProcessing) && styles.disabledButton,
          ]}
          onPress={handleProcess}
          disabled={!text.trim() || isProcessing}>
          {isProcessing ? (
            <>
              <ActivityIndicator size="small" color="#FFFFFF" />
              <Text style={styles.processButtonText}>Processing...</Text>
            </>
          ) : (
            <>
              <Text style={styles.processButtonText}>Process Text</Text>
              <Icon name="arrow-forward" size={20} color="#FFFFFF" />
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 16,
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  textInput: {
    backgroundColor: '#1F2937',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#FFFFFF',
    minHeight: 200,
    marginBottom: 8,
  },
  charCount: {
    alignItems: 'flex-end',
    marginBottom: 16,
  },
  charCountText: {
    fontSize: 12,
    color: '#6B7280',
  },
  processButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  processButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  disabledButton: {
    opacity: 0.4,
  },
});
