import React, { useState, useEffect, useCallback } from 'react';
import {
  Zap, Clock, Link2, Activity, Send, HeartPulse,
  Plus, Trash2, Play, Pause, Edit3, Save, X, RefreshCw,
  ExternalLink, HardDrive, Database, Cpu, CheckCircle, XCircle,
  Loader2, ChevronDown, ChevronUp
} from 'lucide-react';
import apiClient from '../api/client';

const TABS = [
  { id: 'tasks', label: 'Sarcini Programate', icon: Clock },
  { id: 'shortcuts', label: 'Scurtaturi', icon: Link2 },
  { id: 'uptime', label: 'Monitorizare Uptime', icon: Activity },
  { id: 'api-tester', label: 'API Tester', icon: Send },
  { id: 'health', label: 'Sanatate Sistem', icon: HeartPulse },
];

// ===== SARCINI PROGRAMATE =====
function ScheduledTasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', cron: '*/5 * * * *', action_type: 'http', action_config: '{}', enabled: true });

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/automations/tasks');
      setTasks(res.data.tasks || res.data || []);
    } catch {
      setTasks([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const saveTask = async () => {
    try {
      if (editing && editing !== 'new') {
        await apiClient.put(`/api/automations/tasks/${editing}`, form);
      } else {
        await apiClient.post('/api/automations/tasks', form);
      }
      setEditing(null);
      setForm({ name: '', cron: '*/5 * * * *', action_type: 'http', action_config: '{}', enabled: true });
      loadTasks();
    } catch { /* toast handles it */ }
  };

  const deleteTask = async (id) => {
    if (!confirm('Stergi aceasta sarcina?')) return;
    try {
      await apiClient.delete(`/api/automations/tasks/${id}`);
      loadTasks();
    } catch { /* toast handles it */ }
  };

  const runTask = async (id) => {
    try {
      await apiClient.post(`/api/automations/tasks/${id}/run`);
      loadTasks();
    } catch { /* toast handles it */ }
  };

  const startEdit = (task) => {
    setEditing(task.id);
    setForm({
      name: task.name || '',
      cron: task.cron || '*/5 * * * *',
      action_type: task.action_type || 'http',
      action_config: typeof task.action_config === 'string' ? task.action_config : JSON.stringify(task.action_config || {}),
      enabled: task.enabled !== false,
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">Gestioneaza sarcini automate cu expresii cron</p>
        <button
          onClick={() => { setEditing('new'); setForm({ name: '', cron: '*/5 * * * *', action_type: 'http', action_config: '{}', enabled: true }); }}
          className="btn-primary flex items-center gap-2 px-3 py-1.5 text-sm"
        >
          <Plus className="w-4 h-4" /> Adauga Sarcina
        </button>
      </div>

      {/* Edit form */}
      {editing && (
        <div className="bg-slate-800/60 rounded-lg p-4 space-y-3 border border-slate-700">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Nume</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" placeholder="Backup zilnic" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Expresie Cron</label>
              <input value={form.cron} onChange={e => setForm({ ...form, cron: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-primary-500 focus:outline-none" placeholder="*/5 * * * *" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Tip Actiune</label>
              <select value={form.action_type} onChange={e => setForm({ ...form, action_type: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none">
                <option value="http">HTTP Request</option>
                <option value="backup">Backup</option>
                <option value="cleanup">Curatare</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <label className="flex items-center gap-2 cursor-pointer bg-slate-900 rounded-lg px-3 py-2 border border-slate-700">
                <input type="checkbox" checked={form.enabled} onChange={e => setForm({ ...form, enabled: e.target.checked })}
                  className="rounded border-slate-600" />
                <span className="text-sm text-slate-300">Activ</span>
              </label>
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Configuratie (JSON)</label>
            <textarea value={form.action_config} onChange={e => setForm({ ...form, action_config: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-primary-500 focus:outline-none resize-none h-20" placeholder='{"url": "http://localhost:8000/api/health"}' />
          </div>
          <div className="flex gap-2">
            <button onClick={saveTask} className="btn-primary px-4 py-1.5 text-sm flex items-center gap-1">
              <Save className="w-3.5 h-3.5" /> Salveaza
            </button>
            <button onClick={() => setEditing(null)} className="btn-secondary px-4 py-1.5 text-sm flex items-center gap-1">
              <X className="w-3.5 h-3.5" /> Anuleaza
            </button>
          </div>
        </div>
      )}

      {/* Tasks list */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Nicio sarcina programata</p>
        </div>
      ) : (
        <div className="space-y-2">
          {tasks.map(task => (
            <div key={task.id} className="bg-slate-800/40 rounded-lg p-4 flex items-center justify-between group">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${task.enabled !== false ? 'bg-green-400' : 'bg-slate-500'}`} />
                  <span className="text-sm text-white font-medium">{task.name || 'Sarcina fara nume'}</span>
                  <span className="text-xs text-slate-500 font-mono bg-slate-900 px-2 py-0.5 rounded">{task.cron}</span>
                </div>
                {task.last_run && <p className="text-[10px] text-slate-500 mt-1">Ultima rulare: {task.last_run}</p>}
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => runTask(task.id)} className="p-1.5 text-green-400 hover:bg-green-400/10 rounded" title="Ruleaza acum">
                  <Play className="w-3.5 h-3.5" />
                </button>
                <button onClick={() => startEdit(task)} className="p-1.5 text-slate-400 hover:bg-slate-700 rounded" title="Editeaza">
                  <Edit3 className="w-3.5 h-3.5" />
                </button>
                <button onClick={() => deleteTask(task.id)} className="p-1.5 text-red-400 hover:bg-red-400/10 rounded" title="Sterge">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== SCURTATURI =====
function Shortcuts() {
  const [shortcuts, setShortcuts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', url: '', icon: 'link', category: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/automations/shortcuts');
      setShortcuts(res.data.shortcuts || res.data || []);
    } catch { setShortcuts([]); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    try {
      if (editing && editing !== 'new') {
        await apiClient.put(`/api/automations/shortcuts/${editing}`, form);
      } else {
        await apiClient.post('/api/automations/shortcuts', form);
      }
      setEditing(null);
      setForm({ name: '', url: '', icon: 'link', category: '' });
      load();
    } catch { /* toast handles it */ }
  };

  const remove = async (id) => {
    if (!confirm('Stergi aceasta scurtatura?')) return;
    try { await apiClient.delete(`/api/automations/shortcuts/${id}`); load(); } catch { /* toast handles it */ }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">Acces rapid la link-uri si comenzi frecvente</p>
        <button onClick={() => { setEditing('new'); setForm({ name: '', url: '', icon: 'link', category: '' }); }}
          className="btn-primary flex items-center gap-2 px-3 py-1.5 text-sm">
          <Plus className="w-4 h-4" /> Adauga Scurtatura
        </button>
      </div>

      {editing && (
        <div className="bg-slate-800/60 rounded-lg p-4 space-y-3 border border-slate-700">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Nume</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" placeholder="Google" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">URL / Comanda</label>
              <input value={form.url} onChange={e => setForm({ ...form, url: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" placeholder="https://google.com" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Categorie</label>
              <input value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" placeholder="Productivitate" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Icon</label>
              <input value={form.icon} onChange={e => setForm({ ...form, icon: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" placeholder="link" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={save} className="btn-primary px-4 py-1.5 text-sm flex items-center gap-1"><Save className="w-3.5 h-3.5" /> Salveaza</button>
            <button onClick={() => setEditing(null)} className="btn-secondary px-4 py-1.5 text-sm flex items-center gap-1"><X className="w-3.5 h-3.5" /> Anuleaza</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : shortcuts.length === 0 ? (
        <div className="text-center py-12">
          <Link2 className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Nicio scurtatura adaugata</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {shortcuts.map(s => (
            <div key={s.id} className="bg-slate-800/40 rounded-lg p-4 flex flex-col items-center text-center group relative">
              <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => { setEditing(s.id); setForm({ name: s.name, url: s.url, icon: s.icon || 'link', category: s.category || '' }); }}
                  className="p-1 text-slate-400 hover:bg-slate-700 rounded"><Edit3 className="w-3 h-3" /></button>
                <button onClick={() => remove(s.id)} className="p-1 text-red-400 hover:bg-red-400/10 rounded"><Trash2 className="w-3 h-3" /></button>
              </div>
              <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center mb-2">
                <ExternalLink className="w-5 h-5 text-primary-400" />
              </div>
              <p className="text-sm text-white font-medium truncate w-full">{s.name}</p>
              {s.category && <p className="text-[10px] text-slate-500 mt-0.5">{s.category}</p>}
              <a href={s.url} target="_blank" rel="noopener noreferrer"
                className="mt-2 text-xs text-primary-400 hover:text-primary-300 transition-colors">Deschide</a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== UPTIME MONITOR =====
function UptimeMonitor() {
  const [monitors, setMonitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newUrl, setNewUrl] = useState('');
  const [newName, setNewName] = useState('');
  const [checking, setChecking] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/automations/uptime');
      setMonitors(res.data.monitors || res.data || []);
    } catch { setMonitors([]); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const addMonitor = async () => {
    if (!newUrl.trim()) return;
    try {
      await apiClient.post('/api/automations/uptime', { name: newName || newUrl, url: newUrl });
      setNewUrl(''); setNewName('');
      load();
    } catch { /* toast handles it */ }
  };

  const checkNow = async (id) => {
    setChecking(id);
    try { await apiClient.post(`/api/automations/uptime/${id}/check`); load(); } catch { /* toast handles it */ }
    setChecking(null);
  };

  const remove = async (id) => {
    if (!confirm('Stergi acest monitor?')) return;
    try { await apiClient.delete(`/api/automations/uptime/${id}`); load(); } catch { /* toast handles it */ }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-400">Monitorizeaza disponibilitatea URL-urilor importante</p>

      {/* Add monitor */}
      <div className="flex gap-2">
        <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Nume (optional)"
          className="w-40 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
        <input value={newUrl} onChange={e => setNewUrl(e.target.value)} placeholder="https://example.com"
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none"
          onKeyDown={e => e.key === 'Enter' && addMonitor()} />
        <button onClick={addMonitor} disabled={!newUrl.trim()} className="btn-primary px-4 py-2 text-sm flex items-center gap-1 disabled:opacity-50">
          <Plus className="w-4 h-4" /> Adauga
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : monitors.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Niciun URL monitorizat</p>
        </div>
      ) : (
        <div className="space-y-2">
          {monitors.map(m => (
            <div key={m.id} className="bg-slate-800/40 rounded-lg overflow-hidden">
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {m.status === 'up' ? <CheckCircle className="w-5 h-5 text-green-400 shrink-0" /> :
                   m.status === 'down' ? <XCircle className="w-5 h-5 text-red-400 shrink-0" /> :
                   <Activity className="w-5 h-5 text-slate-500 shrink-0" />}
                  <div className="min-w-0">
                    <p className="text-sm text-white font-medium truncate">{m.name || m.url}</p>
                    <p className="text-[10px] text-slate-500 truncate">{m.url}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {m.latency_ms != null && (
                    <span className={`text-xs font-mono px-2 py-0.5 rounded ${m.latency_ms < 300 ? 'text-green-400 bg-green-400/10' : m.latency_ms < 1000 ? 'text-yellow-400 bg-yellow-400/10' : 'text-red-400 bg-red-400/10'}`}>
                      {m.latency_ms}ms
                    </span>
                  )}
                  <div className="flex items-center gap-1">
                    <button onClick={() => checkNow(m.id)} className="p-1.5 text-slate-400 hover:bg-slate-700 rounded" title="Verifica acum">
                      {checking === m.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                    </button>
                    <button onClick={() => setExpanded(expanded === m.id ? null : m.id)} className="p-1.5 text-slate-400 hover:bg-slate-700 rounded">
                      {expanded === m.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                    <button onClick={() => remove(m.id)} className="p-1.5 text-red-400 hover:bg-red-400/10 rounded" title="Sterge">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
              {expanded === m.id && m.history && (
                <div className="border-t border-slate-700 p-3 bg-slate-900/40">
                  <p className="text-xs text-slate-400 mb-2">Istoric verificari:</p>
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {(m.history || []).map((h, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">{h.timestamp}</span>
                        <span className={h.status === 'up' ? 'text-green-400' : 'text-red-400'}>{h.status} ({h.latency_ms}ms)</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== API TESTER =====
function ApiTester() {
  const [method, setMethod] = useState('GET');
  const [url, setUrl] = useState('');
  const [headers, setHeaders] = useState('{\n  "Content-Type": "application/json"\n}');
  const [body, setBody] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timing, setTiming] = useState(null);

  const sendRequest = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResponse(null);
    setTiming(null);

    const start = performance.now();
    try {
      let parsedHeaders = {};
      try { parsedHeaders = JSON.parse(headers); } catch { /* toast handles it */ }

      let parsedBody = undefined;
      if (['POST', 'PUT', 'PATCH'].includes(method) && body.trim()) {
        try { parsedBody = JSON.parse(body); } catch { parsedBody = body; }
      }

      const res = await apiClient.post('/api/automations/api-test', {
        method, url, headers: parsedHeaders, body: parsedBody,
      });

      const elapsed = Math.round(performance.now() - start);
      setTiming(elapsed);
      setResponse(res.data);
    } catch (err) {
      const elapsed = Math.round(performance.now() - start);
      setTiming(elapsed);
      setResponse({
        status: err.response?.status || 0,
        status_text: err.response?.statusText || 'Eroare de conexiune',
        headers: err.response?.headers || {},
        body: err.response?.data || { error: err.message },
      });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-400">Testeaza endpoint-uri API direct din interfata</p>

      {/* Request builder */}
      <div className="flex gap-2">
        <select value={method} onChange={e => setMethod(e.target.value)}
          className="w-28 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-primary-500 focus:outline-none">
          {['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://api.example.com/endpoint"
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-primary-500 focus:outline-none"
          onKeyDown={e => e.key === 'Enter' && sendRequest()} />
        <button onClick={sendRequest} disabled={loading || !url.trim()}
          className="btn-primary px-6 py-2 text-sm flex items-center gap-2 disabled:opacity-50">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Trimite
        </button>
      </div>

      {/* Headers & Body */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Headers (JSON)</label>
          <textarea value={headers} onChange={e => setHeaders(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-primary-500 focus:outline-none resize-none h-32" />
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Body (JSON) {!['POST', 'PUT', 'PATCH'].includes(method) && <span className="text-slate-600">— nu se aplica la {method}</span>}</label>
          <textarea value={body} onChange={e => setBody(e.target.value)}
            disabled={!['POST', 'PUT', 'PATCH'].includes(method)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-primary-500 focus:outline-none resize-none h-32 disabled:opacity-40" />
        </div>
      </div>

      {/* Response */}
      {response && (
        <div className="bg-slate-800/60 rounded-lg border border-slate-700 overflow-hidden">
          <div className="p-3 border-b border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`text-sm font-mono font-bold ${response.status >= 200 && response.status < 300 ? 'text-green-400' : response.status >= 400 ? 'text-red-400' : 'text-yellow-400'}`}>
                {response.status} {response.status_text}
              </span>
            </div>
            {timing && <span className="text-xs text-slate-500 font-mono">{timing}ms</span>}
          </div>
          {response.response_headers && (
            <div className="p-3 border-b border-slate-700">
              <p className="text-xs text-slate-400 mb-1">Headers raspuns:</p>
              <pre className="text-xs text-slate-300 font-mono max-h-24 overflow-y-auto whitespace-pre-wrap">
                {typeof response.response_headers === 'string' ? response.response_headers : JSON.stringify(response.response_headers, null, 2)}
              </pre>
            </div>
          )}
          <div className="p-3">
            <p className="text-xs text-slate-400 mb-1">Body raspuns:</p>
            <pre className="text-xs text-slate-300 font-mono max-h-64 overflow-y-auto whitespace-pre-wrap bg-slate-900/50 rounded p-3">
              {typeof response.body === 'string' ? response.body : JSON.stringify(response.body, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

// ===== HEALTH =====
function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/automations/health');
      setHealth(res.data);
    } catch {
      try {
        const res = await apiClient.get('/api/health');
        setHealth(res.data);
      } catch { setHealth(null); }
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>;
  if (!health) return <div className="text-center py-12"><HeartPulse className="w-10 h-10 text-slate-600 mx-auto mb-2" /><p className="text-sm text-slate-500">Nu s-au putut incarca datele</p></div>;

  const cards = [
    { icon: HardDrive, label: 'Spatiu Disc', value: health.disk_usage || health.disk || 'N/A', sub: health.disk_total ? `Total: ${health.disk_total}` : null, color: 'text-blue-400' },
    { icon: Cpu, label: 'Memorie', value: health.memory_usage || health.memory || 'N/A', sub: health.memory_total ? `Total: ${health.memory_total}` : null, color: 'text-purple-400' },
    { icon: Database, label: 'Dimensiune DB', value: health.db_size || 'N/A', sub: null, color: 'text-cyan-400' },
    { icon: Clock, label: 'Uptime', value: health.uptime || 'N/A', sub: null, color: 'text-green-400' },
    { icon: Zap, label: 'Module Active', value: health.module_count || health.modules || 'N/A', sub: null, color: 'text-yellow-400' },
    { icon: HeartPulse, label: 'Status', value: health.status || 'OK', sub: health.version ? `v${health.version}` : null, color: 'text-emerald-400' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">Informatii despre starea generala a sistemului</p>
        <button onClick={load} className="btn-secondary px-3 py-1.5 text-sm flex items-center gap-1">
          <RefreshCw className="w-3.5 h-3.5" /> Actualizeaza
        </button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card, i) => (
          <div key={i} className="bg-slate-800/40 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <card.icon className={`w-4 h-4 ${card.color}`} />
              <span className="text-xs text-slate-400">{card.label}</span>
            </div>
            <p className="text-lg font-semibold text-white">{card.value}</p>
            {card.sub && <p className="text-[10px] text-slate-500 mt-1">{card.sub}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}

// ===== MAIN PAGE =====
export default function AutomationsPage() {
  const [activeTab, setActiveTab] = useState('tasks');

  const renderTab = () => {
    switch (activeTab) {
      case 'tasks': return <ScheduledTasks />;
      case 'shortcuts': return <Shortcuts />;
      case 'uptime': return <UptimeMonitor />;
      case 'api-tester': return <ApiTester />;
      case 'health': return <SystemHealth />;
      default: return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary-400" />
          Automatizari
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
