import React, { useState, useEffect, useCallback } from 'react';
import {
  FileBarChart, HardDrive, Database, Clock, Activity, BookOpen,
  Bookmark, Download, Plus, Trash2, Edit3, Save, X, Search,
  Loader2, RefreshCw, ExternalLink, Cpu, FolderOpen, Tag,
  SmilePlus
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import apiClient from '../api/client';

const TABS = [
  { id: 'system', label: 'Sistem', icon: HardDrive },
  { id: 'timeline', label: 'Timeline', icon: Activity },
  { id: 'journal', label: 'Jurnal', icon: BookOpen },
  { id: 'bookmarks', label: 'Semne de carte', icon: Bookmark },
  { id: 'export', label: 'Export', icon: Download },
];

const MOODS = ['😊', '😐', '😔', '😤', '🎉', '💡', '🔥', '❤️'];

// ===== SISTEM =====
function SystemTab() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/reports/system');
      setInfo(res.data);
    } catch {
      try {
        const res = await apiClient.get('/api/health');
        setInfo(res.data);
      } catch { setInfo(null); }
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>;
  if (!info) return <div className="text-center py-12"><HardDrive className="w-10 h-10 text-slate-600 mx-auto mb-2" /><p className="text-sm text-slate-500">Nu s-au putut incarca datele de sistem</p></div>;

  const diskPercent = info.disk_used_percent || (info.disk_used && info.disk_total ? Math.round((parseFloat(info.disk_used) / parseFloat(info.disk_total)) * 100) : null);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">Informatii despre sistemul curent</p>
        <button onClick={load} className="btn-secondary px-3 py-1.5 text-sm flex items-center gap-1">
          <RefreshCw className="w-3.5 h-3.5" /> Actualizeaza
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Disk usage */}
        <div className="bg-slate-800/40 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <HardDrive className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-slate-400">Spatiu Disc</span>
          </div>
          {diskPercent != null && (
            <div className="mb-2">
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all ${diskPercent > 90 ? 'bg-red-500' : diskPercent > 70 ? 'bg-yellow-500' : 'bg-blue-500'}`}
                  style={{ width: `${Math.min(diskPercent, 100)}%` }} />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[10px] text-slate-500">{info.disk_used || 'N/A'} folosit</span>
                <span className="text-[10px] text-slate-500">{diskPercent}%</span>
              </div>
            </div>
          )}
          <p className="text-lg font-semibold text-white">{info.disk_total || info.disk_usage || 'N/A'}</p>
        </div>

        {/* DB size */}
        <div className="bg-slate-800/40 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-slate-400">Dimensiune DB</span>
          </div>
          <p className="text-lg font-semibold text-white">{info.db_size || 'N/A'}</p>
        </div>

        {/* Upload folder */}
        <div className="bg-slate-800/40 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <FolderOpen className="w-4 h-4 text-yellow-400" />
            <span className="text-xs text-slate-400">Folder Upload</span>
          </div>
          <p className="text-lg font-semibold text-white">{info.upload_folder_size || info.uploads_size || 'N/A'}</p>
        </div>

        {/* Python version */}
        <div className="bg-slate-800/40 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Cpu className="w-4 h-4 text-green-400" />
            <span className="text-xs text-slate-400">Python</span>
          </div>
          <p className="text-lg font-semibold text-white">{info.python_version || 'N/A'}</p>
        </div>

        {/* OS */}
        <div className="bg-slate-800/40 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span className="text-xs text-slate-400">Sistem Operare</span>
          </div>
          <p className="text-lg font-semibold text-white">{info.os || info.platform || 'N/A'}</p>
        </div>

        {/* Modules */}
        <div className="bg-slate-800/40 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-orange-400" />
            <span className="text-xs text-slate-400">Module Active</span>
          </div>
          <p className="text-lg font-semibold text-white">{info.module_count || info.modules || 'N/A'}</p>
        </div>
      </div>
    </div>
  );
}

// ===== TIMELINE =====
function TimelineTab() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [chartData, setChartData] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 50 };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await apiClient.get('/api/reports/timeline', { params });
      const items = res.data.activities || res.data || [];
      setActivities(items);

      // Build chart data
      const dayCounts = {};
      items.forEach(a => {
        const day = (a.timestamp || a.created_at || '').split('T')[0] || (a.timestamp || a.created_at || '').split(' ')[0];
        if (day) dayCounts[day] = (dayCounts[day] || 0) + 1;
      });
      setChartData(Object.entries(dayCounts).sort().map(([day, count]) => ({ day, count })));
    } catch {
      setActivities([]);
      setChartData([]);
    }
    setLoading(false);
  }, [dateFrom, dateTo]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-3 items-end">
        <div>
          <label className="text-xs text-slate-400 mb-1 block">De la</label>
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Pana la</label>
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
        </div>
        <button onClick={load} className="btn-secondary px-3 py-2 text-sm flex items-center gap-1">
          <RefreshCw className="w-3.5 h-3.5" /> Filtreaza
        </button>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="bg-slate-800/40 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Activitate pe zi</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="day" stroke="#94a3b8" tick={{ fontSize: 10 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Timeline */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : activities.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Nicio activitate inregistrata</p>
        </div>
      ) : (
        <div className="space-y-1 relative">
          <div className="absolute left-5 top-0 bottom-0 w-px bg-slate-700" />
          {activities.map((a, i) => (
            <div key={a.id || i} className="flex gap-4 relative">
              <div className="w-10 flex items-start justify-center pt-3 z-10">
                <div className="w-2.5 h-2.5 rounded-full bg-primary-500 ring-4 ring-slate-900" />
              </div>
              <div className="flex-1 bg-slate-800/40 rounded-lg p-3 mb-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-white">{a.action || a.description || a.message || 'Activitate'}</p>
                  <span className="text-[10px] text-slate-500 whitespace-nowrap ml-2">{a.timestamp || a.created_at || ''}</span>
                </div>
                {a.details && <p className="text-xs text-slate-400 mt-1">{typeof a.details === 'string' ? a.details : JSON.stringify(a.details)}</p>}
                {a.page && <span className="text-[10px] text-slate-600 mt-0.5 block">{a.page}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== JURNAL =====
function JournalTab() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ title: '', content: '', mood: '', tags: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/reports/journal');
      setEntries(res.data.entries || res.data || []);
    } catch { setEntries([]); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    try {
      const payload = { ...form, tags: form.tags.split(',').map(t => t.trim()).filter(Boolean) };
      if (editing && editing !== 'new') {
        await apiClient.put(`/api/reports/journal/${editing}`, payload);
      } else {
        await apiClient.post('/api/reports/journal', payload);
      }
      setEditing(null);
      setForm({ title: '', content: '', mood: '', tags: '' });
      load();
    } catch { /* toast handles it */ }
  };

  const remove = async (id) => {
    if (!confirm('Stergi aceasta intrare?')) return;
    try { await apiClient.delete(`/api/reports/journal/${id}`); load(); } catch { /* toast handles it */ }
  };

  const startEdit = (entry) => {
    setEditing(entry.id);
    setForm({
      title: entry.title || '',
      content: entry.content || '',
      mood: entry.mood || '',
      tags: Array.isArray(entry.tags) ? entry.tags.join(', ') : (entry.tags || ''),
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">Jurnal personal — ganduri, idei, reflectii</p>
        <button onClick={() => { setEditing('new'); setForm({ title: '', content: '', mood: '', tags: '' }); }}
          className="btn-primary flex items-center gap-2 px-3 py-1.5 text-sm">
          <Plus className="w-4 h-4" /> Intrare Noua
        </button>
      </div>

      {/* Edit form */}
      {editing && (
        <div className="bg-slate-800/60 rounded-lg p-4 space-y-3 border border-slate-700">
          <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
            placeholder="Titlu intrare..." className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
          <textarea value={form.content} onChange={e => setForm({ ...form, content: e.target.value })}
            placeholder="Scrie aici..." rows={5} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none resize-none" />
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block flex items-center gap-1"><SmilePlus className="w-3 h-3" /> Dispozitie</label>
              <div className="flex gap-1">
                {MOODS.map(m => (
                  <button key={m} onClick={() => setForm({ ...form, mood: m })}
                    className={`w-8 h-8 rounded-lg text-lg flex items-center justify-center transition-all ${form.mood === m ? 'bg-primary-600/30 ring-2 ring-primary-500 scale-110' : 'bg-slate-800 hover:bg-slate-700'}`}>
                    {m}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-1">
              <label className="text-xs text-slate-400 mb-1 block flex items-center gap-1"><Tag className="w-3 h-3" /> Tag-uri (separate prin virgula)</label>
              <input value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })}
                placeholder="personal, idei, proiect" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={save} className="btn-primary px-4 py-1.5 text-sm flex items-center gap-1"><Save className="w-3.5 h-3.5" /> Salveaza</button>
            <button onClick={() => setEditing(null)} className="btn-secondary px-4 py-1.5 text-sm flex items-center gap-1"><X className="w-3.5 h-3.5" /> Anuleaza</button>
          </div>
        </div>
      )}

      {/* Entries list */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12">
          <BookOpen className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Nicio intrare in jurnal</p>
        </div>
      ) : (
        <div className="space-y-3">
          {entries.map(entry => (
            <div key={entry.id} className="bg-slate-800/40 rounded-lg p-4 group">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {entry.mood && <span className="text-lg">{entry.mood}</span>}
                  <h4 className="text-sm font-semibold text-white">{entry.title || 'Fara titlu'}</h4>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => startEdit(entry)} className="p-1.5 text-slate-400 hover:bg-slate-700 rounded"><Edit3 className="w-3.5 h-3.5" /></button>
                  <button onClick={() => remove(entry.id)} className="p-1.5 text-red-400 hover:bg-red-400/10 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              </div>
              <p className="text-sm text-slate-300 mt-2 whitespace-pre-wrap line-clamp-3">{entry.content}</p>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-[10px] text-slate-500">{entry.created_at || entry.date || ''}</span>
                {entry.tags && (Array.isArray(entry.tags) ? entry.tags : [entry.tags]).map((tag, i) => (
                  <span key={i} className="text-[10px] text-primary-400 bg-primary-600/10 px-1.5 py-0.5 rounded">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== SEMNE DE CARTE =====
function BookmarksTab() {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ title: '', url: '', category: '', description: '' });
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/reports/bookmarks', { params: search ? { search } : {} });
      setBookmarks(res.data.bookmarks || res.data || []);
    } catch { setBookmarks([]); }
    setLoading(false);
  }, [search]);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    try {
      if (editing && editing !== 'new') {
        await apiClient.put(`/api/reports/bookmarks/${editing}`, form);
      } else {
        await apiClient.post('/api/reports/bookmarks', form);
      }
      setEditing(null);
      setForm({ title: '', url: '', category: '', description: '' });
      load();
    } catch { /* toast handles it */ }
  };

  const remove = async (id) => {
    if (!confirm('Stergi acest semn de carte?')) return;
    try { await apiClient.delete(`/api/reports/bookmarks/${id}`); load(); } catch { /* toast handles it */ }
  };

  // Group by category
  const grouped = {};
  bookmarks.forEach(b => {
    const cat = b.category || 'Necategorizate';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(b);
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Cauta semne de carte..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
        </div>
        <button onClick={() => { setEditing('new'); setForm({ title: '', url: '', category: '', description: '' }); }}
          className="btn-primary flex items-center gap-2 px-3 py-1.5 text-sm">
          <Plus className="w-4 h-4" /> Adauga
        </button>
      </div>

      {/* Edit form */}
      {editing && (
        <div className="bg-slate-800/60 rounded-lg p-4 space-y-3 border border-slate-700">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Titlu</label>
              <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
                placeholder="Google" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">URL</label>
              <input value={form.url} onChange={e => setForm({ ...form, url: e.target.value })}
                placeholder="https://google.com" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Categorie</label>
              <input value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}
                placeholder="Utile" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Descriere</label>
              <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
                placeholder="Motor de cautare" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={save} className="btn-primary px-4 py-1.5 text-sm flex items-center gap-1"><Save className="w-3.5 h-3.5" /> Salveaza</button>
            <button onClick={() => setEditing(null)} className="btn-secondary px-4 py-1.5 text-sm flex items-center gap-1"><X className="w-3.5 h-3.5" /> Anuleaza</button>
          </div>
        </div>
      )}

      {/* Bookmarks by category */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : bookmarks.length === 0 ? (
        <div className="text-center py-12">
          <Bookmark className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">{search ? 'Niciun rezultat' : 'Niciun semn de carte'}</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category}>
              <h4 className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-2">{category}</h4>
              <div className="space-y-2">
                {items.map(b => (
                  <div key={b.id} className="bg-slate-800/40 rounded-lg p-3 flex items-center justify-between group hover:bg-slate-800/60 transition-colors">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <Bookmark className="w-4 h-4 text-primary-400 shrink-0" />
                      <div className="min-w-0">
                        <a href={b.url} target="_blank" rel="noopener noreferrer"
                          className="text-sm text-white hover:text-primary-400 transition-colors font-medium truncate block">
                          {b.title}
                        </a>
                        {b.description && <p className="text-[10px] text-slate-500 truncate">{b.description}</p>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <a href={b.url} target="_blank" rel="noopener noreferrer" className="p-1.5 text-slate-400 hover:bg-slate-700 rounded"><ExternalLink className="w-3.5 h-3.5" /></a>
                      <button onClick={() => { setEditing(b.id); setForm({ title: b.title, url: b.url, category: b.category || '', description: b.description || '' }); }}
                        className="p-1.5 text-slate-400 hover:bg-slate-700 rounded"><Edit3 className="w-3.5 h-3.5" /></button>
                      <button onClick={() => remove(b.id)} className="p-1.5 text-red-400 hover:bg-red-400/10 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== EXPORT =====
function ExportTab() {
  const [exporting, setExporting] = useState(false);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/api/reports/export-stats');
        setStats(res.data);
      } catch { setStats(null); }
      setLoading(false);
    })();
  }, []);

  const exportAll = async () => {
    setExporting(true);
    try {
      const res = await apiClient.get('/api/reports/export', { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `command_center_export_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch { /* toast handles it */ }
    setExporting(false);
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-400">Exporta toate datele intr-un fisier JSON pentru backup</p>

      {/* Stats */}
      {loading ? (
        <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 text-primary-400 animate-spin" /></div>
      ) : stats && (
        <div className="bg-slate-800/40 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Statistici Fisiere</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.entries(stats).map(([key, value]) => (
              <div key={key} className="bg-slate-900/40 rounded-lg p-3 text-center">
                <p className="text-xs text-slate-400 capitalize">{key.replace(/_/g, ' ')}</p>
                <p className="text-lg font-semibold text-white mt-1">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Export button */}
      <div className="bg-slate-800/40 rounded-lg p-6 text-center">
        <Download className="w-12 h-12 text-primary-400 mx-auto mb-3 opacity-60" />
        <h3 className="text-sm font-semibold text-white mb-2">Export Complet Date</h3>
        <p className="text-xs text-slate-400 mb-4">Descarca toate datele (jurnal, semne de carte, setari, istoric) intr-un fisier JSON</p>
        <button onClick={exportAll} disabled={exporting}
          className="btn-primary flex items-center gap-2 px-6 py-2.5 text-sm mx-auto disabled:opacity-50">
          {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          {exporting ? 'Se exporta...' : 'Descarca Export JSON'}
        </button>
      </div>
    </div>
  );
}

// ===== MAIN PAGE =====
export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('system');

  const renderTab = () => {
    switch (activeTab) {
      case 'system': return <SystemTab />;
      case 'timeline': return <TimelineTab />;
      case 'journal': return <JournalTab />;
      case 'bookmarks': return <BookmarksTab />;
      case 'export': return <ExportTab />;
      default: return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
          <FileBarChart className="w-5 h-5 text-primary-400" />
          Rapoarte
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
