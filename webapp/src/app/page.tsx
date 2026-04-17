'use client';

import { useState } from 'react';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';

export default function Home() {
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleDemo = async () => {
    if (!inputText.trim()) return;

    setIsProcessing(true);
    setResults(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: inputText,
          source: 'webapp_demo',
        }),
      });

      if (!response.ok) {
        throw new Error('Processing failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to process. Make sure the API is running on localhost:8000');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#262626_1px,transparent_1px),linear-gradient(to_bottom,#262626_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)]" />

        <div className="container-custom relative z-10 py-20">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 mb-8 bg-[#171717] border border-[#262626] rounded-full animate-fade-in">
              <div className="w-2 h-2 bg-[#E82127] rounded-full animate-pulse-subtle" />
              <span className="text-sm text-gray-300">AI-Powered Task Intelligence</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-6xl md:text-7xl font-bold mb-6 animate-fade-in" style={{ animationDelay: '100ms' }}>
              Your AI Chief
              <br />
              <span className="text-gradient-red">of Staff</span>
            </h1>

            {/* Subheading */}
            <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto animate-fade-in" style={{ animationDelay: '200ms' }}>
              Transform conversations into actionable tasks, decisions, and risk assessments.
              Built for developers, recruiters, and business owners.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16 animate-fade-in" style={{ animationDelay: '300ms' }}>
              <Button variant="primary" size="lg" onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}>
                Try Live Demo
              </Button>
              <Button variant="ghost" size="lg" onClick={() => window.open('http://localhost:8000/docs', '_blank')}>
                View API Docs
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto animate-fade-in" style={{ animationDelay: '400ms' }}>
              <div>
                <div className="text-4xl font-bold text-[#E82127]">99.9%</div>
                <div className="text-sm text-gray-500 mt-2">Accuracy</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-[#E82127]">&lt;2s</div>
                <div className="text-sm text-gray-500 mt-2">Response Time</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-[#E82127]">24/7</div>
                <div className="text-sm text-gray-500 mt-2">Availability</div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg
            className="w-6 h-6 text-gray-600"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" className="py-20 bg-[#0a0a0a]">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold mb-4">See It In Action</h2>
              <p className="text-gray-400">
                Paste your meeting notes, email thread, or any text. Watch AI extract tasks, decisions, and risks.
              </p>
            </div>

            <Card className="mb-8">
              <textarea
                className="w-full h-48 bg-black border border-[#262626] rounded p-4 text-white placeholder-gray-600 focus:outline-none focus:border-[#E82127] resize-none"
                placeholder="Example: 'We discussed launching the new product Q2. John will handle marketing, Sarah owns engineering. Budget approved at $50k. Risk: tight timeline might impact quality.'"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isProcessing}
              />

              <div className="mt-6 flex justify-between items-center">
                <span className="text-sm text-gray-500">
                  {inputText.length} characters
                </span>
                <Button
                  variant="primary"
                  onClick={handleDemo}
                  isLoading={isProcessing}
                  disabled={!inputText.trim()}
                >
                  {isProcessing ? 'Processing...' : 'Analyze Text'}
                </Button>
              </div>
            </Card>

            {/* Results */}
            {results && (
              <div className="space-y-6 animate-fade-in">
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
                            <span className={`text-xs px-2 py-1 rounded ${
                              risk.severity === 'high' ? 'bg-red-900/30 text-red-400' :
                              risk.severity === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                              'bg-blue-900/30 text-blue-400'
                            }`}>
                              {risk.severity || 'medium'}
                            </span>
                          </div>
                          {risk.mitigation && (
                            <div className="text-sm text-gray-500">Mitigation: {risk.mitigation}</div>
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
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="container-custom">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Why Choose AI Chief of Staff?</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Enterprise-grade AI processing with developer-friendly APIs
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card hover>
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold mb-3">Lightning Fast</h3>
              <p className="text-gray-400">
                Process thousands of words in under 2 seconds. Built on GPT-4o-mini for optimal speed and accuracy.
              </p>
            </Card>

            <Card hover>
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold mb-3">Precision Extraction</h3>
              <p className="text-gray-400">
                Advanced NLP extracts tasks, decisions, and risks with context-aware accuracy.
              </p>
            </Card>

            <Card hover>
              <div className="text-4xl mb-4">🔗</div>
              <h3 className="text-xl font-semibold mb-3">Powerful Integrations</h3>
              <p className="text-gray-400 mb-3">
                Connect your entire workflow: <span className="text-white font-medium">Zoom → Slack</span>, <span className="text-white font-medium">Google Meet → Notion</span>, and more.
              </p>
              <p className="text-sm text-gray-500">
                RESTful API • Webhooks • Real-time notifications
              </p>
            </Card>

            <Card hover>
              <div className="text-4xl mb-4">🎤</div>
              <h3 className="text-xl font-semibold mb-3">Media Support</h3>
              <p className="text-gray-400 mb-4">
                Upload audio/video files. Automatic transcription via Whisper AI, then extract insights.
              </p>
              <a href="/upload" className="text-[#E82127] hover:underline text-sm font-medium">
                Try Media Upload →
              </a>
            </Card>

            <Card hover>
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-3">Real-time Analytics</h3>
              <p className="text-gray-400">
                Track processing history, view trends, and monitor AI performance in your dashboard.
              </p>
            </Card>

            <Card hover>
              <div className="text-4xl mb-4">🔒</div>
              <h3 className="text-xl font-semibold mb-3">Secure & Reliable</h3>
              <p className="text-gray-400">
                Enterprise security standards. Your data is encrypted and never stored long-term.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-[#0a0a0a]">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Workflow?</h2>
            <p className="text-xl text-gray-400 mb-8">
              Join developers, recruiters, and business owners using AI Chief of Staff.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="primary" size="lg" onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}>
                Get Started Free
              </Button>
              <Button variant="ghost" size="lg" onClick={() => window.open('http://localhost:8000/docs', '_blank')}>
                Explore API
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-[#262626]">
        <div className="container-custom">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-gray-500 mb-4 md:mb-0">
              © 2026 AI Chief of Staff. Built by <span className="text-[#E82127] font-semibold">Salako Olamide</span>
            </div>
            <div className="flex gap-6">
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-white transition-colors">
                API Docs
              </a>
              <a href="#demo" className="text-gray-500 hover:text-white transition-colors">
                Demo
              </a>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-white transition-colors">
                GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
