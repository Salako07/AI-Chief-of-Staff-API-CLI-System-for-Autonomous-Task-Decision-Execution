import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import {Task, Decision, Risk} from '@/types/api';

export interface ExportData {
  title: string;
  source: string;
  summary: string;
  transcript?: string;
  tasks: Task[];
  decisions: Decision[];
  risks: Risk[];
}

const PRIORITY_COLOR: Record<string, string> = {
  high: '#EF4444',
  medium: '#F59E0B',
  low: '#10B981',
};

const SEVERITY_COLOR: Record<string, string> = {
  high: '#EF4444',
  medium: '#F59E0B',
  low: '#10B981',
};

function badge(label: string, color: string): string {
  return `<span style="display:inline-block;padding:2px 8px;border-radius:9999px;font-size:11px;font-weight:700;color:#fff;background:${color};text-transform:uppercase">${label}</span>`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function buildTasksHtml(tasks: Task[]): string {
  if (!tasks.length) return '<p style="color:#888">No tasks identified.</p>';
  return tasks
    .map(
      t => `
    <div style="margin-bottom:12px;padding:12px;background:#f9fafb;border-radius:8px;border-left:4px solid ${PRIORITY_COLOR[t.priority] ?? '#6B7280'}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <strong style="font-size:14px;color:#111827">${escapeHtml(t.title)}</strong>
        ${badge(t.priority, PRIORITY_COLOR[t.priority] ?? '#6B7280')}
      </div>
      <div style="font-size:12px;color:#6B7280;display:flex;gap:16px;flex-wrap:wrap">
        ${t.owner ? `<span>👤 ${escapeHtml(t.owner)}</span>` : ''}
        ${t.deadline ? `<span>📅 ${escapeHtml(t.deadline)}</span>` : ''}
        <span>Status: ${t.status}</span>
      </div>
    </div>`,
    )
    .join('');
}

function buildDecisionsHtml(decisions: Decision[]): string {
  if (!decisions.length) return '<p style="color:#888">No decisions recorded.</p>';
  return decisions
    .map(
      d => `
    <div style="margin-bottom:12px;padding:12px;background:#f9fafb;border-radius:8px;border-left:4px solid #3B82F6">
      <p style="font-size:14px;color:#111827;margin:0 0 6px">${escapeHtml(d.decision)}</p>
      <div style="font-size:12px;color:#6B7280;display:flex;gap:16px">
        ${d.made_by ? `<span>👤 ${escapeHtml(d.made_by)}</span>` : ''}
        <span>🕐 ${new Date(d.timestamp).toLocaleString()}</span>
      </div>
    </div>`,
    )
    .join('');
}

function buildRisksHtml(risks: Risk[]): string {
  if (!risks.length) return '<p style="color:#888">No risks identified.</p>';
  return risks
    .map(
      r => `
    <div style="margin-bottom:12px;padding:12px;background:#f9fafb;border-radius:8px;border-left:4px solid ${SEVERITY_COLOR[r.severity] ?? '#6B7280'}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
        <p style="font-size:14px;color:#111827;margin:0;flex:1;padding-right:12px">${escapeHtml(r.risk)}</p>
        ${badge(r.severity, SEVERITY_COLOR[r.severity] ?? '#6B7280')}
      </div>
      ${r.mitigation ? `<p style="font-size:12px;color:#6B7280;margin:4px 0 0">💡 ${escapeHtml(r.mitigation)}</p>` : ''}
    </div>`,
    )
    .join('');
}

function buildHtml(data: ExportData): string {
  const now = new Date().toLocaleString();
  const transcriptSection = data.transcript
    ? `
    <div style="margin-bottom:32px">
      <h2 style="font-size:16px;font-weight:700;color:#111827;border-bottom:2px solid #E5E7EB;padding-bottom:8px;margin-bottom:12px">📝 Transcript</h2>
      <div style="font-size:13px;color:#374151;line-height:1.7;white-space:pre-wrap;background:#f9fafb;padding:16px;border-radius:8px;font-family:monospace">${escapeHtml(data.transcript)}</div>
    </div>`
    : '';

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(data.title)}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, Helvetica, Arial, sans-serif; color: #111827; background: #fff; padding: 32px; max-width: 800px; margin: auto; }
  </style>
</head>
<body>

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:32px;padding-bottom:20px;border-bottom:3px solid #3B82F6">
    <div>
      <div style="font-size:11px;font-weight:700;color:#3B82F6;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px">AI Chief of Staff</div>
      <h1 style="font-size:22px;font-weight:800;color:#111827;line-height:1.2">${escapeHtml(data.title)}</h1>
      <div style="font-size:12px;color:#9CA3AF;margin-top:4px">Source: ${escapeHtml(data.source)}</div>
    </div>
    <div style="text-align:right;font-size:11px;color:#9CA3AF">
      <div>Generated</div>
      <div style="font-weight:600;color:#6B7280">${now}</div>
    </div>
  </div>

  <!-- Stats row -->
  <div style="display:flex;gap:12px;margin-bottom:32px">
    ${[
      {label: 'Tasks', count: data.tasks.length, color: '#3B82F6'},
      {label: 'Decisions', count: data.decisions.length, color: '#8B5CF6'},
      {label: 'Risks', count: data.risks.length, color: '#EF4444'},
    ]
      .map(
        s => `
      <div style="flex:1;background:#f9fafb;border-radius:10px;padding:14px;text-align:center;border-top:3px solid ${s.color}">
        <div style="font-size:28px;font-weight:800;color:${s.color}">${s.count}</div>
        <div style="font-size:12px;color:#6B7280;font-weight:600">${s.label}</div>
      </div>`,
      )
      .join('')}
  </div>

  <!-- Summary -->
  <div style="margin-bottom:32px">
    <h2 style="font-size:16px;font-weight:700;color:#111827;border-bottom:2px solid #E5E7EB;padding-bottom:8px;margin-bottom:12px">📋 Summary</h2>
    <p style="font-size:14px;color:#374151;line-height:1.7;background:#EFF6FF;padding:16px;border-radius:8px;border-left:4px solid #3B82F6">${escapeHtml(data.summary)}</p>
  </div>

  <!-- Transcript (optional) -->
  ${transcriptSection}

  <!-- Tasks -->
  <div style="margin-bottom:32px">
    <h2 style="font-size:16px;font-weight:700;color:#111827;border-bottom:2px solid #E5E7EB;padding-bottom:8px;margin-bottom:12px">✅ Action Items (${data.tasks.length})</h2>
    ${buildTasksHtml(data.tasks)}
  </div>

  <!-- Decisions -->
  <div style="margin-bottom:32px">
    <h2 style="font-size:16px;font-weight:700;color:#111827;border-bottom:2px solid #E5E7EB;padding-bottom:8px;margin-bottom:12px">🔵 Decisions Made (${data.decisions.length})</h2>
    ${buildDecisionsHtml(data.decisions)}
  </div>

  <!-- Risks -->
  <div style="margin-bottom:32px">
    <h2 style="font-size:16px;font-weight:700;color:#111827;border-bottom:2px solid #E5E7EB;padding-bottom:8px;margin-bottom:12px">⚠️ Risks Identified (${data.risks.length})</h2>
    ${buildRisksHtml(data.risks)}
  </div>

  <!-- Footer -->
  <div style="margin-top:48px;padding-top:16px;border-top:1px solid #E5E7EB;font-size:11px;color:#9CA3AF;text-align:center">
    Generated by AI Chief of Staff · ${now}
  </div>

</body>
</html>`;
}

export async function exportReportAsPdf(data: ExportData): Promise<void> {
  const html = buildHtml(data);
  const {uri} = await Print.printToFileAsync({html, base64: false});

  const canShare = await Sharing.isAvailableAsync();
  if (!canShare) {
    throw new Error('Sharing is not available on this device.');
  }

  const filename = `report_${Date.now()}.pdf`;
  await Sharing.shareAsync(uri, {
    mimeType: 'application/pdf',
    dialogTitle: 'Save or share report',
    UTI: 'com.adobe.pdf',
  });
}
