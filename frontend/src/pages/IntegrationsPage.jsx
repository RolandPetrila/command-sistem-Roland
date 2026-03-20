import React, { useState, useEffect, useCallback } from 'react';
import {
  Puzzle, Mail, HardDrive, CalendarDays, Github,
  CheckCircle, XCircle, AlertTriangle, RefreshCw, Send,
  Download, Upload, Plus, Search, Loader2, ExternalLink,
  FileText, Inbox, Clock
} from 'lucide-react';
import apiClient from '../api/client';

const TABS = [
  { id: 'gmail', label: 'Gmail', icon: Mail },
  { id: 'drive', label: 'Google Drive', icon: HardDrive },
  { id: 'calendar', label: 'Calendar', icon: CalendarDays },
  { id: 'github', label: 'GitHub', icon: Github },
];

function StatusBadge({ status }) {
  const config = {
    connected: { icon: CheckCircle, color: 'text-green-400 bg-green-400/10', label: 'Conectat' },
    error: { icon: AlertTriangle, color: 'text-yellow-400 bg-yellow-400/10', label: 'Eroare' },
    disconnected: { icon: XCircle, color: 'text-red-400 bg-red-400/10', label: 'Neconectat' },
  };
  const c = config[status] || config.disconnected;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${c.color}`}>
      <c.icon className="w-3.5 h-3.5" />
      {c.label}
    </span>
  );
}

// ===== GMAIL =====
function GmailTab() {
  const [status, setStatus] = useState('disconnected');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [emailForm, setEmailForm] = useState({ to: '', subject: '', body: '' });
  const [sendResult, setSendResult] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/api/integrations/gmail/status');
        setStatus(res.data.status || 'disconnected');
      } catch { setStatus('disconnected'); }
      try {
        const res = await apiClient.get('/api/integrations/gmail/messages', { params: { limit: 10 } });
        setMessages(res.data.messages || res.data || []);
      } catch { setMessages([]); }
      setLoading(false);
    })();
  }, []);

  const sendEmail = async () => {
    if (!emailForm.to || !emailForm.subject) return;
    setSending(true);
    setSendResult('');
    try {
      await apiClient.post('/api/integrations/gmail/send', emailForm);
      setSendResult('Email trimis cu succes!');
      setEmailForm({ to: '', subject: '', body: '' });
    } catch (err) {
      setSendResult(`Eroare: ${err.response?.data?.detail || err.message}`);
    }
    setSending(false);
  };

  return (
    <div className="space-y-6">
      {/* Status */}
      <div className="bg-slate-800/40 rounded-lg p-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Mail className="w-4 h-4 text-red-400" /> Gmail
          </h3>
          <p className="text-xs text-slate-500 mt-1">Integrare cu contul Gmail</p>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Recent messages */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Inbox className="w-4 h-4 text-slate-400" /> Mesaje Recente
        </h3>
        {loading ? (
          <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 text-primary-400 animate-spin" /></div>
        ) : messages.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-6">Niciun mesaj disponibil</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {messages.map((msg, i) => (
              <div key={msg.id || i} className="bg-slate-900/40 rounded-lg p-3 hover:bg-slate-900/60 transition-colors">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-white font-medium truncate flex-1">{msg.subject || '(fara subiect)'}</p>
                  <span className="text-[10px] text-slate-500 ml-2 whitespace-nowrap">{msg.date || msg.received_at || ''}</span>
                </div>
                <p className="text-xs text-slate-400 truncate mt-0.5">{msg.from || msg.sender || ''}</p>
                {msg.snippet && <p className="text-xs text-slate-500 mt-1 truncate">{msg.snippet}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Compose */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Send className="w-4 h-4 text-blue-400" /> Compune Email
        </h3>
        <div className="space-y-3">
          <input value={emailForm.to} onChange={e => setEmailForm({ ...emailForm, to: e.target.value })}
            placeholder="Destinatar (email)" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
          <input value={emailForm.subject} onChange={e => setEmailForm({ ...emailForm, subject: e.target.value })}
            placeholder="Subiect" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
          <textarea value={emailForm.body} onChange={e => setEmailForm({ ...emailForm, body: e.target.value })}
            placeholder="Mesaj..." rows={4} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none resize-none" />
          {sendResult && (
            <p className={`text-xs ${sendResult.startsWith('Eroare') ? 'text-red-400' : 'text-green-400'}`}>{sendResult}</p>
          )}
          <button onClick={sendEmail} disabled={sending || !emailForm.to || !emailForm.subject}
            className="btn-primary flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-50">
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {sending ? 'Se trimite...' : 'Trimite Email'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ===== GOOGLE DRIVE =====
function DriveTab() {
  const [status, setStatus] = useState('disconnected');
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/integrations/drive/status');
      setStatus(res.data.status || 'disconnected');
    } catch { setStatus('disconnected'); }
    try {
      const res = await apiClient.get('/api/integrations/drive/files', { params: { search, limit: 20 } });
      setFiles(res.data.files || res.data || []);
    } catch { setFiles([]); }
    setLoading(false);
  }, [search]);

  useEffect(() => { load(); }, [load]);

  const uploadFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await apiClient.post('/api/integrations/drive/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      load();
    } catch { /* toast handles it */ }
    setUploading(false);
    e.target.value = '';
  };

  const downloadFile = async (fileId, fileName) => {
    try {
      const res = await apiClient.get(`/api/integrations/drive/download/${fileId}`, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      link.click();
      URL.revokeObjectURL(url);
    } catch { /* toast handles it */ }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 rounded-lg p-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-yellow-400" /> Google Drive
          </h3>
          <p className="text-xs text-slate-500 mt-1">Acces la fisierele din Drive</p>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Search + Upload */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Cauta fisiere..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
        </div>
        <label className="btn-primary flex items-center gap-2 px-4 py-2 text-sm cursor-pointer">
          {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          Upload
          <input type="file" onChange={uploadFile} className="hidden" />
        </label>
      </div>

      {/* File list */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : files.length === 0 ? (
        <div className="text-center py-12">
          <HardDrive className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">{search ? 'Niciun fisier gasit' : 'Niciun fisier disponibil'}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {files.map(file => (
            <div key={file.id} className="bg-slate-800/40 rounded-lg p-3 flex items-center justify-between hover:bg-slate-800/60 transition-colors">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm text-white truncate">{file.name}</p>
                  <p className="text-[10px] text-slate-500">{file.size || ''} {file.modified_at ? `- ${file.modified_at}` : ''}</p>
                </div>
              </div>
              <button onClick={() => downloadFile(file.id, file.name)} className="p-1.5 text-slate-400 hover:bg-slate-700 rounded" title="Descarca">
                <Download className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== CALENDAR =====
function CalendarTab() {
  const [status, setStatus] = useState('disconnected');
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [eventForm, setEventForm] = useState({ summary: '', start: '', end: '' });
  const [createResult, setCreateResult] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/api/integrations/calendar/status');
        setStatus(res.data.status || 'disconnected');
      } catch { setStatus('disconnected'); }
      try {
        const res = await apiClient.get('/api/integrations/calendar/events', { params: { limit: 10 } });
        setEvents(res.data.events || res.data || []);
      } catch { setEvents([]); }
      setLoading(false);
    })();
  }, []);

  const createEvent = async () => {
    if (!eventForm.summary || !eventForm.start || !eventForm.end) return;
    setCreating(true);
    setCreateResult('');
    try {
      await apiClient.post('/api/integrations/calendar/events', eventForm);
      setCreateResult('Eveniment creat cu succes!');
      setEventForm({ summary: '', start: '', end: '' });
      const res = await apiClient.get('/api/integrations/calendar/events', { params: { limit: 10 } });
      setEvents(res.data.events || res.data || []);
    } catch (err) {
      setCreateResult(`Eroare: ${err.response?.data?.detail || err.message}`);
    }
    setCreating(false);
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 rounded-lg p-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <CalendarDays className="w-4 h-4 text-blue-400" /> Google Calendar
          </h3>
          <p className="text-xs text-slate-500 mt-1">Evenimente si programari</p>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Upcoming events */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-400" /> Evenimente Urmatoare
        </h3>
        {loading ? (
          <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 text-primary-400 animate-spin" /></div>
        ) : events.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-6">Niciun eveniment disponibil</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {events.map((evt, i) => (
              <div key={evt.id || i} className="bg-slate-900/40 rounded-lg p-3">
                <p className="text-sm text-white font-medium">{evt.summary || evt.title || '(fara titlu)'}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-slate-400">{evt.start || evt.start_time || ''}</span>
                  {(evt.end || evt.end_time) && <span className="text-xs text-slate-500">- {evt.end || evt.end_time}</span>}
                </div>
                {evt.location && <p className="text-xs text-slate-500 mt-0.5">{evt.location}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create event */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Plus className="w-4 h-4 text-green-400" /> Creeaza Eveniment
        </h3>
        <div className="space-y-3">
          <input value={eventForm.summary} onChange={e => setEventForm({ ...eventForm, summary: e.target.value })}
            placeholder="Titlu eveniment" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Inceput</label>
              <input type="datetime-local" value={eventForm.start} onChange={e => setEventForm({ ...eventForm, start: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Sfarsit</label>
              <input type="datetime-local" value={eventForm.end} onChange={e => setEventForm({ ...eventForm, end: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
          </div>
          {createResult && (
            <p className={`text-xs ${createResult.startsWith('Eroare') ? 'text-red-400' : 'text-green-400'}`}>{createResult}</p>
          )}
          <button onClick={createEvent} disabled={creating || !eventForm.summary || !eventForm.start || !eventForm.end}
            className="btn-primary flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-50">
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {creating ? 'Se creeaza...' : 'Creeaza Eveniment'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ===== GITHUB =====
function GithubTab() {
  const [status, setStatus] = useState('disconnected');
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [commits, setCommits] = useState([]);
  const [loadingCommits, setLoadingCommits] = useState(false);
  const [creating, setCreating] = useState(false);
  const [issueForm, setIssueForm] = useState({ title: '', body: '', repo: '' });
  const [createResult, setCreateResult] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/api/integrations/github/status');
        setStatus(res.data.status || 'disconnected');
      } catch { setStatus('disconnected'); }
      try {
        const res = await apiClient.get('/api/integrations/github/repos');
        setRepos(res.data.repos || res.data || []);
      } catch { setRepos([]); }
      setLoading(false);
    })();
  }, []);

  const loadCommits = async (repoName) => {
    setSelectedRepo(repoName);
    setLoadingCommits(true);
    try {
      const res = await apiClient.get(`/api/integrations/github/repos/${encodeURIComponent(repoName)}/commits`, { params: { limit: 10 } });
      setCommits(res.data.commits || res.data || []);
    } catch { setCommits([]); }
    setLoadingCommits(false);
  };

  const createIssue = async () => {
    if (!issueForm.title || !issueForm.repo) return;
    setCreating(true);
    setCreateResult('');
    try {
      await apiClient.post(`/api/integrations/github/repos/${encodeURIComponent(issueForm.repo)}/issues`, {
        title: issueForm.title, body: issueForm.body,
      });
      setCreateResult('Issue creat cu succes!');
      setIssueForm({ ...issueForm, title: '', body: '' });
    } catch (err) {
      setCreateResult(`Eroare: ${err.response?.data?.detail || err.message}`);
    }
    setCreating(false);
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 rounded-lg p-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Github className="w-4 h-4 text-slate-300" /> GitHub
          </h3>
          <p className="text-xs text-slate-500 mt-1">Repositoare si issues</p>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Repos */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Repositoare</h3>
        {loading ? (
          <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 text-primary-400 animate-spin" /></div>
        ) : repos.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-6">Niciun repositor disponibil</p>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {repos.map((repo, i) => (
              <button key={repo.name || i} onClick={() => loadCommits(repo.full_name || repo.name)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${selectedRepo === (repo.full_name || repo.name) ? 'bg-primary-600/20 border border-primary-500/30' : 'bg-slate-900/40 hover:bg-slate-900/60 border border-transparent'}`}>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-white font-medium">{repo.name}</p>
                  {repo.language && <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded">{repo.language}</span>}
                </div>
                {repo.description && <p className="text-xs text-slate-400 mt-0.5 truncate">{repo.description}</p>}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Commits */}
      {selectedRepo && (
        <div className="bg-slate-800/40 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Commit-uri recente: {selectedRepo}</h3>
          {loadingCommits ? (
            <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 text-primary-400 animate-spin" /></div>
          ) : commits.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-6">Niciun commit</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {commits.map((c, i) => (
                <div key={c.sha || i} className="bg-slate-900/40 rounded-lg p-3">
                  <p className="text-sm text-white truncate">{c.message || c.commit?.message || ''}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-[10px] text-slate-400 font-mono">{(c.sha || '').slice(0, 7)}</span>
                    <span className="text-[10px] text-slate-500">{c.author || c.commit?.author?.name || ''}</span>
                    <span className="text-[10px] text-slate-500">{c.date || c.commit?.author?.date || ''}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create issue */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Plus className="w-4 h-4 text-green-400" /> Creeaza Issue
        </h3>
        <div className="space-y-3">
          <select value={issueForm.repo} onChange={e => setIssueForm({ ...issueForm, repo: e.target.value })}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none">
            <option value="">Alege repositorul</option>
            {repos.map((r, i) => <option key={i} value={r.full_name || r.name}>{r.name}</option>)}
          </select>
          <input value={issueForm.title} onChange={e => setIssueForm({ ...issueForm, title: e.target.value })}
            placeholder="Titlu issue" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
          <textarea value={issueForm.body} onChange={e => setIssueForm({ ...issueForm, body: e.target.value })}
            placeholder="Descriere..." rows={3} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none resize-none" />
          {createResult && (
            <p className={`text-xs ${createResult.startsWith('Eroare') ? 'text-red-400' : 'text-green-400'}`}>{createResult}</p>
          )}
          <button onClick={createIssue} disabled={creating || !issueForm.title || !issueForm.repo}
            className="btn-primary flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-50">
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {creating ? 'Se creeaza...' : 'Creeaza Issue'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ===== MAIN PAGE =====
export default function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState('gmail');

  const renderTab = () => {
    switch (activeTab) {
      case 'gmail': return <GmailTab />;
      case 'drive': return <DriveTab />;
      case 'calendar': return <CalendarTab />;
      case 'github': return <GithubTab />;
      default: return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
          <Puzzle className="w-5 h-5 text-primary-400" />
          Integratii Externe
        </h2>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-800/60 rounded-lg p-1 mb-6 overflow-x-auto">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'bg-primary-600/20 text-primary-300 border border-primary-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 border border-transparent'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {renderTab()}
      </div>
    </div>
  );
}
