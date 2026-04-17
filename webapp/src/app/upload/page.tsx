'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import Link from 'next/link';

interface UploadResponse {
  media_id: string;
  filename: string;
  size_bytes: number;
  mime_type: string;
  status: string;
}

interface TranscriptionJob {
  job_id: string;
  media_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
}

interface JobStatus {
  job_id: string;
  media_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  transcription_length?: number;
  processing_time_ms?: number;
  error_message?: string;
}

interface TranscriptionResult {
  job_id: string;
  run_id: string;
  media_id: string;
  transcription: string;
  tasks: any[];
  decisions: any[];
  risks: any[];
  summary: string;
  processing_time_ms: number;
}

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [results, setResults] = useState<TranscriptionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const handleFileSelect = (file: File) => {
    // Validate file type
    const validTypes = [
      'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/ogg',
      'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo'
    ];

    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|ogg|mp4|mov|avi)$/i)) {
      setError('Invalid file type. Please upload audio (MP3, WAV, M4A, OGG) or video (MP4, MOV, AVI) files.');
      return;
    }

    // Validate file size (100MB max)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File too large. Maximum size is 100MB.');
      return;
    }

    setSelectedFile(file);
    setError(null);
    setResults(null);
    setJobStatus(null);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDuration = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${seconds}s`;
  };

  const pollJobStatus = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/media/status/${jobId}`);
      if (!response.ok) throw new Error('Failed to get job status');

      const status: JobStatus = await response.json();
      setJobStatus(status);

      if (status.status === 'completed') {
        // Stop polling
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }

        // Get results
        const resultResponse = await fetch(`http://localhost:8000/api/v1/media/result/${jobId}`);
        if (!resultResponse.ok) throw new Error('Failed to get results');

        const result: TranscriptionResult = await resultResponse.json();
        setResults(result);
        setIsUploading(false);
      } else if (status.status === 'failed') {
        // Stop polling
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }

        setError(status.error_message || 'Transcription failed');
        setIsUploading(false);
      }
    } catch (err) {
      console.error('Error polling status:', err);
      setError('Failed to check job status. Is the API running?');
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      setIsUploading(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    setResults(null);
    setJobStatus(null);

    try {
      // Step 1: Upload file
      const formData = new FormData();
      formData.append('file', selectedFile);

      setUploadProgress(10);

      console.log('Uploading file:', selectedFile.name, 'Size:', selectedFile.size, 'Type:', selectedFile.type);

      const uploadResponse = await fetch('http://localhost:8000/api/v1/media/upload', {
        method: 'POST',
        body: formData,
        mode: 'cors',
      });

      console.log('Upload response status:', uploadResponse.status);

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text();
        console.error('Upload error response:', errorText);
        try {
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.detail || `Upload failed with status ${uploadResponse.status}`);
        } catch {
          throw new Error(`Upload failed with status ${uploadResponse.status}: ${errorText}`);
        }
      }

      const uploadData: UploadResponse = await uploadResponse.json();
      console.log('Upload successful:', uploadData);
      setUploadProgress(30);

      // Step 2: Start transcription
      const transcribeResponse = await fetch(
        `http://localhost:8000/api/v1/media/transcribe/${uploadData.media_id}`,
        { method: 'POST' }
      );

      if (!transcribeResponse.ok) {
        throw new Error('Failed to start transcription');
      }

      const transcribeData: TranscriptionJob = await transcribeResponse.json();
      setUploadProgress(50);

      // Step 3: Poll for status
      setJobStatus({
        job_id: transcribeData.job_id,
        media_id: transcribeData.media_id,
        status: 'queued',
        progress: 50,
      });

      // Start polling every 2 seconds
      pollIntervalRef.current = setInterval(() => {
        pollJobStatus(transcribeData.job_id);
      }, 2000);

      // Initial status check
      pollJobStatus(transcribeData.job_id);

    } catch (err: any) {
      console.error('Upload error:', err);
      const errorMessage = err.message || 'Unknown error';
      setError(`Upload failed: ${errorMessage}. Make sure the API is running on localhost:8000`);
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResults(null);
    setJobStatus(null);
    setError(null);
    setUploadProgress(0);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-[#262626] py-4">
        <div className="container-custom flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold">
            AI Chief <span className="text-[#E82127]">of Staff</span>
          </Link>
          <nav className="flex gap-6">
            <Link href="/" className="text-gray-400 hover:text-white transition-colors">
              Home
            </Link>
            <Link href="/upload" className="text-white font-medium">
              Upload Media
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
            >
              API Docs
            </a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="py-20">
        <div className="container-custom max-w-4xl">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4">
              Upload Audio or Video
            </h1>
            <p className="text-xl text-gray-400">
              Automatically transcribe and extract insights from your media files
            </p>
          </div>

          {/* Upload Area */}
          {!results && (
            <Card className="mb-8">
              <div
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
                  isDragging
                    ? 'border-[#E82127] bg-[#E82127]/5'
                    : 'border-[#404040] hover:border-[#606060]'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*,video/*,.mp3,.wav,.m4a,.ogg,.mp4,.mov,.avi"
                  onChange={handleFileInputChange}
                  className="hidden"
                />

                {!selectedFile ? (
                  <>
                    <div className="text-6xl mb-4">🎤</div>
                    <h3 className="text-xl font-semibold mb-2">
                      Drop your media file here
                    </h3>
                    <p className="text-gray-500 mb-6">
                      or click to browse
                    </p>
                    <Button
                      variant="secondary"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      Choose File
                    </Button>
                    <p className="text-sm text-gray-600 mt-4">
                      Supports: MP3, WAV, M4A, OGG, MP4, MOV, AVI (max 100MB)
                    </p>
                  </>
                ) : (
                  <>
                    <div className="text-6xl mb-4">
                      {selectedFile.type.startsWith('audio/') ? '🎵' : '🎬'}
                    </div>
                    <h3 className="text-xl font-semibold mb-2">{selectedFile.name}</h3>
                    <p className="text-gray-500 mb-6">{formatFileSize(selectedFile.size)}</p>
                    <div className="flex gap-4 justify-center">
                      <Button
                        variant="primary"
                        onClick={handleUpload}
                        isLoading={isUploading}
                        disabled={isUploading}
                      >
                        {isUploading ? 'Processing...' : 'Upload & Transcribe'}
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={handleReset}
                        disabled={isUploading}
                      >
                        Change File
                      </Button>
                    </div>
                  </>
                )}
              </div>

              {/* Progress Bar */}
              {isUploading && jobStatus && (
                <div className="mt-6">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-400">
                      {jobStatus.status === 'queued' && 'Queued for processing...'}
                      {jobStatus.status === 'processing' && 'Transcribing and analyzing...'}
                      {jobStatus.status === 'completed' && 'Complete!'}
                      {jobStatus.status === 'failed' && 'Failed'}
                    </span>
                    <span className="text-sm text-gray-400">{jobStatus.progress}%</span>
                  </div>
                  <div className="w-full bg-[#262626] rounded-full h-2">
                    <div
                      className="bg-[#E82127] h-2 rounded-full transition-all duration-500"
                      style={{ width: `${jobStatus.progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="mt-6 p-4 bg-red-900/20 border border-red-900/50 rounded text-red-400">
                  {error}
                </div>
              )}
            </Card>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-6 animate-fade-in">
              {/* Header with Reset Button */}
              <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold">Results</h2>
                <Button variant="ghost" onClick={handleReset}>
                  Upload Another File
                </Button>
              </div>

              {/* Processing Time */}
              <Card>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-500">Processing Time</div>
                    <div className="text-2xl font-bold text-[#E82127]">
                      {formatDuration(results.processing_time_ms)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Transcription Length</div>
                    <div className="text-2xl font-bold">
                      {results.transcription.length.toLocaleString()} chars
                    </div>
                  </div>
                </div>
              </Card>

              {/* Transcription */}
              <Card>
                <h3 className="text-xl font-semibold mb-4">Transcription</h3>
                <div className="p-4 bg-black rounded border border-[#262626] max-h-64 overflow-y-auto">
                  <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {results.transcription}
                  </p>
                </div>
              </Card>

              {/* Tasks */}
              {results.tasks && results.tasks.length > 0 && (
                <Card>
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <span className="text-[#E82127]">✓</span> Tasks Extracted
                  </h3>
                  <div className="space-y-3">
                    {results.tasks.map((task: any, i: number) => (
                      <div key={i} className="p-3 bg-black rounded border border-[#262626]">
                        <div className="font-medium">{task.title}</div>
                        {task.owner && (
                          <div className="text-sm text-gray-500 mt-1">Owner: {task.owner}</div>
                        )}
                        {task.deadline && (
                          <div className="text-sm text-gray-500">Deadline: {task.deadline}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Decisions */}
              {results.decisions && results.decisions.length > 0 && (
                <Card>
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <span className="text-[#E82127]">◆</span> Decisions Made
                  </h3>
                  <div className="space-y-3">
                    {results.decisions.map((decision: any, i: number) => (
                      <div key={i} className="p-3 bg-black rounded border border-[#262626]">
                        <div className="font-medium">{decision.decision}</div>
                        {decision.made_by && (
                          <div className="text-sm text-gray-500 mt-1">By: {decision.made_by}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Risks */}
              {results.risks && results.risks.length > 0 && (
                <Card>
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <span className="text-[#E82127]">⚠</span> Risks Identified
                  </h3>
                  <div className="space-y-3">
                    {results.risks.map((risk: any, i: number) => (
                      <div key={i} className="p-3 bg-black rounded border border-[#262626]">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-medium">{risk.risk}</div>
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              risk.severity === 'high'
                                ? 'bg-red-900/30 text-red-400'
                                : risk.severity === 'medium'
                                ? 'bg-yellow-900/30 text-yellow-400'
                                : 'bg-blue-900/30 text-blue-400'
                            }`}
                          >
                            {risk.severity || 'medium'}
                          </span>
                        </div>
                        {risk.mitigation && (
                          <div className="text-sm text-gray-500">
                            Mitigation: {risk.mitigation}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Summary */}
              {results.summary && (
                <Card>
                  <h3 className="text-xl font-semibold mb-4">Summary</h3>
                  <p className="text-gray-300 leading-relaxed">{results.summary}</p>
                </Card>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 border-t border-[#262626] mt-20">
        <div className="container-custom">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-gray-500 mb-4 md:mb-0">
              © 2026 AI Chief of Staff. Built by <span className="text-[#E82127] font-semibold">Salako Olamide</span>
            </div>
            <div className="flex gap-6">
              <Link href="/" className="text-gray-500 hover:text-white transition-colors">
                Home
              </Link>
              <Link href="/upload" className="text-gray-500 hover:text-white transition-colors">
                Upload
              </Link>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-500 hover:text-white transition-colors"
              >
                API Docs
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
