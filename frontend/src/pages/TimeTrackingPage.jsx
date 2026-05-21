import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Clock, Play, Square, Trash2, Receipt, Filter, Calendar, Loader2, CheckSquare, ChevronDown, ChevronUp, X } from 'lucide-react';
import api from '../api/client';

function formatDuration(seconds) {
  if (!seconds || seconds < 0) return '00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function formatDurationHMS(seconds) {
  if (!seconds || seconds < 0) return '00:00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function TimeTrackingPage() {
  // Active timer
  const [activeTimer, setActiveTimer] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef(null);

  // Start form
  const [project, setProject] = useState('');
  const [description, setDescription] = useState('');
  const [clientId, setClientId] = useState('');

  // Entries
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [clients, setClients] = useState([]);

  // Filters
  const [filterClient, setFilterClient] = useState('');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');
  const [filterInvoiced, setFilterInvoiced] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Stats
  const [stats, setStats] = useState({ total_hours_today: 0, total_hours_week: 0, total_hours_month: 0 });

  // Invoice generation
  const [selectedEntries, setSelectedEntries] = useState(new Set());
  const [hourlyRate, setHourlyRate] = useState('');
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [generating, setGenerating] = useState(false);

  // Error
  const [error, setError] = useState('');

  // Load clients + active timer + entries + stats on mount
  useEffect(() => {
    loadAll();
  }, []);

  // Reload entries when filters change
  useEffect(() => {
    loadEntries();
  }, [filterClient, filterStartDate, filterEndDate, filterInvoiced]);

  // Live timer tick
  useEffect(() => {
    if (activeTimer) {
      const startTime = new Date(activeTimer.start_time).getTime();
      const tick = () => {
        const now = Date.now();
        setElapsed(Math.floor((now - startTime) / 1000));
      };
      tick();
      timerRef.current = setInterval(tick, 1000);
      return () => clearInterval(timerRef.current);
    } else {
      setElapsed(0);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, [activeTimer]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [activeRes, clientsRes, statsRes] = await Promise.allSettled([
        api.get('/api/time/active'),
        api.get('/api/invoice/clients'),
        api.get('/api/time/stats'),
      ]);
      if (activeRes.status === 'fulfilled' && activeRes.value.data?.id) {
        setActiveTimer(activeRes.value.data);
      }
      if (clientsRes.status === 'fulfilled') {
        setClients(Array.isArray(clientsRes.value.data) ? clientsRes.value.data : []);
      }
      if (statsRes.status === 'fulfilled' && statsRes.value.data) {
        setStats(statsRes.value.data);
      }
    } catch { /* toast handles it */ }
    await loadEntries();
    setLoading(false);
  };

  const loadEntries = async () => {
    try {
      const params = { limit: 100 };
      if (filterClient) params.client_id = filterClient;
      if (filterStartDate) params.start_date = filterStartDate;
      if (filterEndDate) params.end_date = filterEndDate;
      if (filterInvoiced === 'yes') params.invoiced = true;
      if (filterInvoiced === 'no') params.invoiced = false;
      const { data } = await api.get('/api/time/entries', { params });
      setEntries(Array.isArray(data) ? data : (data?.items || []));
    } catch { /* toast handles it */ }
  };

  const loadStats = async () => {
    try {
      const { data } = await api.get('/api/time/stats');
      if (data) setStats(data);
    } catch { /* toast handles it */ }
  };

  const handleStart = async () => {
    if (!project.trim()) {
      setError('Numele proiectului este obligatoriu');
      return;
    }
    setError('');
    try {
      const payload = { project: project.trim(), description: description.trim() };
      if (clientId) payload.client_id = parseInt(clientId);
      const { data } = await api.post('/api/time/start', payload);
      setActiveTimer(data);
      setProject('');
      setDescription('');
      setClientId('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la pornirea cronometrului');
    }
  };

  const handleStop = async () => {
    try {
      await api.post('/api/time/stop');
      setActiveTimer(null);
      setElapsed(0);
      await Promise.all([loadEntries(), loadStats()]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la oprirea cronometrului');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Stergi aceasta inregistrare?')) return;
    try {
      await api.delete(`/api/time/entries/${id}`);
      setEntries(prev => prev.filter(e => e.id !== id));
      setSelectedEntries(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      await loadStats();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la stergere');
    }
  };

  const toggleSelect = (id) => {
    setSelectedEntries(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedEntries.size === entries.length) {
      setSelectedEntries(new Set());
    } else {
      setSelectedEntries(new Set(entries.map(e => e.id)));
    }
  };

  const handleGenerateInvoice = async () => {
    if (selectedEntries.size === 0 || !hourlyRate) return;
    setGenerating(true);
    try {
      const { data } = await api.post('/api/time/to-invoice-items', {
        entry_ids: Array.from(selectedEntries),
        hourly_rate: parseFloat(hourlyRate),
      });
      setShowInvoiceModal(false);
      setSelectedEntries(new Set());
      setHourlyRate('');
      await loadEntries();
      alert(`${data?.items_created || selectedEntries.size} articole de factura generate cu succes!`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la generarea articolelor');
    }
    setGenerating(false);
  };

  const getClientName = useCallback((cid) => {
    if (!cid) return '-';
    const c = clients.find(cl => cl.id === cid);
    return c ? c.name : '-';
  }, [clients]);

  const clearFilters = () => {
    setFilterClient('');
    setFilterStartDate('');
    setFilterEndDate('');
    setFilterInvoiced('');
  };

  const hasActiveFilters = filterClient || filterStartDate || filterEndDate || filterInvoiced;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-400" size={28} />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Clock size={24} className="text-blue-400" />
        <h1 className="text-2xl font-bold">Time Tracking</h1>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-3 text-sm text-red-400 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="ml-2 p-1 hover:bg-red-900/30 rounded"><X size={14} /></button>
        </div>
      )}

      {/* Active Timer */}
      {activeTimer && (
        <div className="bg-blue-900/30 border border-blue-700 rounded-2xl shadow p-5 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <Clock size={22} className="text-blue-400 animate-pulse flex-shrink-0" />
            <div className="min-w-0">
              <div className="font-semibold text-lg text-white truncate">{activeTimer.project}</div>
              {activeTimer.description && (
                <div className="text-sm text-gray-400 truncate">{activeTimer.description}</div>
              )}
            </div>
          </div>
          <div className="text-3xl font-mono text-blue-300 font-bold tabular-nums">
            {formatDurationHMS(elapsed)}
          </div>
          <button onClick={handleStop}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition-colors">
            <Square size={16} /> Opreste
          </button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
          <div className="text-sm text-gray-400 mb-1">Astazi</div>
          <div className="text-2xl font-bold text-white">{stats.total_hours_today?.toFixed(1) || '0.0'}h</div>
        </div>
        <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
          <div className="text-sm text-gray-400 mb-1">Saptamana aceasta</div>
          <div className="text-2xl font-bold text-white">{stats.total_hours_week?.toFixed(1) || '0.0'}h</div>
        </div>
        <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
          <div className="text-sm text-gray-400 mb-1">Luna aceasta</div>
          <div className="text-2xl font-bold text-white">{stats.total_hours_month?.toFixed(1) || '0.0'}h</div>
        </div>
      </div>

      {/* Start Timer Form */}
      {!activeTimer && (
        <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Play size={18} className="text-green-400" /> Porneste cronometrul
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Proiect *</label>
              <input
                type="text"
                value={project}
                onChange={e => setProject(e.target.value)}
                placeholder="Numele proiectului"
                className="input-field w-full"
                onKeyDown={e => e.key === 'Enter' && handleStart()}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Client</label>
              <select
                value={clientId}
                onChange={e => setClientId(e.target.value)}
                className="input-field w-full"
              >
                <option value="">-- Fara client --</option>
                {clients.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button onClick={handleStart}
                className="btn-primary flex items-center gap-2 w-full justify-center">
                <Play size={16} /> Start
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Descriere</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Descriere activitate (optional)"
              className="input-field w-full h-20 resize-none"
            />
          </div>
        </div>
      )}

      {/* Entries Section */}
      <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Calendar size={18} className="text-gray-400" />
            Inregistrari recente
            <span className="text-sm text-gray-500 font-normal">({entries.length})</span>
          </h2>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowFilters(prev => !prev)}
              className={`btn-secondary flex items-center gap-1.5 text-sm ${hasActiveFilters ? 'border-blue-500 text-blue-400' : ''}`}>
              <Filter size={14} />
              Filtre
              {hasActiveFilters && <span className="w-2 h-2 rounded-full bg-blue-400" />}
              {showFilters ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            {selectedEntries.size > 0 && (
              <button onClick={() => setShowInvoiceModal(true)}
                className="btn-primary flex items-center gap-1.5 text-sm">
                <Receipt size={14} />
                Factureaza ({selectedEntries.size})
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4 p-4 bg-gray-800/50 rounded-xl">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Client</label>
              <select value={filterClient} onChange={e => setFilterClient(e.target.value)} className="input-field w-full text-sm">
                <option value="">Toti clientii</option>
                {clients.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">De la</label>
              <input type="date" value={filterStartDate} onChange={e => setFilterStartDate(e.target.value)} className="input-field w-full text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Pana la</label>
              <input type="date" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} className="input-field w-full text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Facturat</label>
              <select value={filterInvoiced} onChange={e => setFilterInvoiced(e.target.value)} className="input-field w-full text-sm">
                <option value="">Toate</option>
                <option value="yes">Da</option>
                <option value="no">Nu</option>
              </select>
            </div>
            {hasActiveFilters && (
              <div className="sm:col-span-4">
                <button onClick={clearFilters} className="text-xs text-gray-400 hover:text-white flex items-center gap-1">
                  <X size={12} /> Sterge filtrele
                </button>
              </div>
            )}
          </div>
        )}

        {/* Table */}
        {entries.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <Clock size={40} className="mx-auto mb-3 opacity-30" />
            <p>Nicio inregistrare gasita</p>
            {hasActiveFilters && <p className="text-sm mt-1">Incearca sa modifici filtrele</p>}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-800">
                  <th className="pb-2 pr-2 w-8">
                    <input
                      type="checkbox"
                      checked={selectedEntries.size === entries.length && entries.length > 0}
                      onChange={toggleSelectAll}
                      className="rounded border-gray-600"
                    />
                  </th>
                  <th className="pb-2 pr-4">Data</th>
                  <th className="pb-2 pr-4">Proiect</th>
                  <th className="pb-2 pr-4 hidden sm:table-cell">Descriere</th>
                  <th className="pb-2 pr-4">Client</th>
                  <th className="pb-2 pr-4">Durata</th>
                  <th className="pb-2 pr-4">Facturat</th>
                  <th className="pb-2 w-10"></th>
                </tr>
              </thead>
              <tbody>
                {entries.map(entry => (
                  <tr key={entry.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                    <td className="py-2.5 pr-2">
                      <input
                        type="checkbox"
                        checked={selectedEntries.has(entry.id)}
                        onChange={() => toggleSelect(entry.id)}
                        className="rounded border-gray-600"
                      />
                    </td>
                    <td className="py-2.5 pr-4 text-gray-300 whitespace-nowrap">
                      {entry.date || (entry.start_time && new Date(entry.start_time).toLocaleDateString('ro'))}
                    </td>
                    <td className="py-2.5 pr-4 text-white font-medium">{entry.project}</td>
                    <td className="py-2.5 pr-4 text-gray-400 hidden sm:table-cell max-w-xs truncate">
                      {entry.description || '-'}
                    </td>
                    <td className="py-2.5 pr-4 text-gray-300">{getClientName(entry.client_id)}</td>
                    <td className="py-2.5 pr-4 text-gray-300 font-mono tabular-nums">
                      {formatDuration(entry.duration_seconds)}
                    </td>
                    <td className="py-2.5 pr-4">
                      {entry.invoiced ? (
                        <span className="inline-flex items-center gap-1 text-xs text-green-400 bg-green-900/20 px-2 py-0.5 rounded-full">
                          <CheckSquare size={12} /> Da
                        </span>
                      ) : (
                        <span className="text-xs text-gray-500">Nu</span>
                      )}
                    </td>
                    <td className="py-2.5">
                      <button onClick={() => handleDelete(entry.id)}
                        className="p-1.5 hover:bg-red-900/30 rounded-lg text-gray-500 hover:text-red-400 transition-colors"
                        title="Sterge">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invoice Modal */}
      {showInvoiceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <Receipt size={18} className="text-blue-400" />
                <span className="font-medium">Genereaza articole factura</span>
              </div>
              <button onClick={() => setShowInvoiceModal(false)} className="p-1.5 hover:bg-gray-800 rounded-lg">
                <X size={16} />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <p className="text-sm text-gray-400">
                {selectedEntries.size} inregistrari selectate
              </p>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Tarif pe ora (RON)</label>
                <input
                  type="number"
                  value={hourlyRate}
                  onChange={e => setHourlyRate(e.target.value)}
                  placeholder="ex: 50"
                  className="input-field w-full"
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="flex gap-3">
                <button onClick={handleGenerateInvoice}
                  disabled={!hourlyRate || generating}
                  className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
                  {generating ? <Loader2 size={16} className="animate-spin" /> : <Receipt size={16} />}
                  Genereaza
                </button>
                <button onClick={() => setShowInvoiceModal(false)} className="btn-secondary flex-1">
                  Anuleaza
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
