import React, { useState, useEffect, useCallback } from 'react';
import {
  Car, Plus, Trash2, Edit3, Save, X, Search, ChevronLeft, ChevronRight,
  BarChart3, PieChart as PieChartIcon, TrendingUp, AlertTriangle, Upload,
  Download, Loader2, FileSpreadsheet, Calendar
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import apiClient from '../api/client';

const TABS = [
  { id: 'inspections', label: 'Inspectii', icon: Car },
  { id: 'stats', label: 'Statistici', icon: BarChart3 },
  { id: 'expiring', label: 'Expirari', icon: AlertTriangle },
  { id: 'import-export', label: 'Import/Export', icon: FileSpreadsheet },
];

const FUEL_TYPES = ['Benzina', 'Diesel', 'GPL', 'Electric', 'Hybrid'];
const RESULTS = ['Admis', 'Respins'];
const PIE_COLORS = ['#6366f1', '#22d3ee', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

const emptyForm = {
  plate_number: '', vin: '', brand: '', model: '', year: new Date().getFullYear(),
  fuel_type: 'Benzina', inspection_date: new Date().toISOString().split('T')[0],
  expiry_date: '', result: 'Admis', price: '', notes: ''
};

// ===== INSPECTII =====
function InspectionsTab() {
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...emptyForm });
  const [deleting, setDeleting] = useState(null);
  const perPage = 10;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/itp/inspections', {
        params: { search, page, per_page: perPage }
      });
      setInspections(res.data.inspections || res.data.items || res.data || []);
      setTotalPages(res.data.total_pages || Math.ceil((res.data.total || 0) / perPage) || 1);
    } catch { setInspections([]); }
    setLoading(false);
  }, [search, page]);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    try {
      const payload = { ...form, price: form.price ? parseFloat(form.price) : 0, year: parseInt(form.year) };
      if (editing && editing !== 'new') {
        await apiClient.put(`/api/itp/inspections/${editing}`, payload);
      } else {
        await apiClient.post('/api/itp/inspections', payload);
      }
      setEditing(null);
      setForm({ ...emptyForm });
      load();
    } catch { /* toast handles it */ }
  };

  const remove = async (id) => {
    try {
      await apiClient.delete(`/api/itp/inspections/${id}`);
      setDeleting(null);
      load();
    } catch { /* toast handles it */ }
  };

  const startEdit = (insp) => {
    setEditing(insp.id);
    setForm({
      plate_number: insp.plate_number || '',
      vin: insp.vin || '',
      brand: insp.brand || '',
      model: insp.model || '',
      year: insp.year || new Date().getFullYear(),
      fuel_type: insp.fuel_type || 'Benzina',
      inspection_date: insp.inspection_date || '',
      expiry_date: insp.expiry_date || '',
      result: insp.result || 'Admis',
      price: insp.price || '',
      notes: insp.notes || '',
    });
  };

  return (
    <div className="space-y-4">
      {/* Search + Add */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Cauta dupa numar, marca, model..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
        </div>
        <button onClick={() => { setEditing('new'); setForm({ ...emptyForm }); }}
          className="btn-primary flex items-center gap-2 px-4 py-2 text-sm">
          <Plus className="w-4 h-4" /> Adauga ITP
        </button>
      </div>

      {/* Edit Form */}
      {editing && (
        <div className="bg-slate-800/60 rounded-lg p-4 border border-slate-700 space-y-3">
          <h3 className="text-sm font-semibold text-white">{editing === 'new' ? 'Adauga Inspectie Noua' : 'Editeaza Inspectia'}</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { key: 'plate_number', label: 'Numar Inmatriculare', placeholder: 'B 123 ABC' },
              { key: 'vin', label: 'VIN (serie sasiu)', placeholder: '17 caractere' },
              { key: 'brand', label: 'Marca', placeholder: 'Dacia' },
              { key: 'model', label: 'Model', placeholder: 'Logan' },
            ].map(f => (
              <div key={f.key}>
                <label className="text-xs text-slate-400 mb-1 block">{f.label}</label>
                <input value={form[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })}
                  placeholder={f.placeholder}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
              </div>
            ))}
            <div>
              <label className="text-xs text-slate-400 mb-1 block">An Fabricatie</label>
              <input type="number" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Combustibil</label>
              <select value={form.fuel_type} onChange={e => setForm({ ...form, fuel_type: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none">
                {FUEL_TYPES.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Data Inspectie</label>
              <input type="date" value={form.inspection_date} onChange={e => setForm({ ...form, inspection_date: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Data Expirare</label>
              <input type="date" value={form.expiry_date} onChange={e => setForm({ ...form, expiry_date: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Rezultat</label>
              <select value={form.result} onChange={e => setForm({ ...form, result: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none">
                {RESULTS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Pret (RON)</label>
              <input type="number" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })}
                placeholder="0" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Observatii</label>
            <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} rows={2}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none resize-none" />
          </div>
          <div className="flex gap-2">
            <button onClick={save} className="btn-primary px-4 py-1.5 text-sm flex items-center gap-1"><Save className="w-3.5 h-3.5" /> Salveaza</button>
            <button onClick={() => setEditing(null)} className="btn-secondary px-4 py-1.5 text-sm flex items-center gap-1"><X className="w-3.5 h-3.5" /> Anuleaza</button>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      {deleting && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-4 flex items-center justify-between">
          <p className="text-sm text-red-300">Sigur stergi aceasta inspectie?</p>
          <div className="flex gap-2">
            <button onClick={() => remove(deleting)} className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm text-white">Da, sterge</button>
            <button onClick={() => setDeleting(null)} className="px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white">Anuleaza</button>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : inspections.length === 0 ? (
        <div className="text-center py-12">
          <Car className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">{search ? 'Niciun rezultat pentru cautare' : 'Nicio inspectie inregistrata'}</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-800/60 text-slate-400 text-xs">
                  <th className="text-left p-3">Nr. Auto</th>
                  <th className="text-left p-3">Marca / Model</th>
                  <th className="text-left p-3">An</th>
                  <th className="text-left p-3">Combustibil</th>
                  <th className="text-left p-3">Data ITP</th>
                  <th className="text-left p-3">Expirare</th>
                  <th className="text-left p-3">Rezultat</th>
                  <th className="text-right p-3">Pret</th>
                  <th className="text-right p-3">Actiuni</th>
                </tr>
              </thead>
              <tbody>
                {inspections.map(insp => (
                  <tr key={insp.id} className="border-t border-slate-700/50 hover:bg-slate-800/30 transition-colors">
                    <td className="p-3 text-white font-mono font-medium">{insp.plate_number}</td>
                    <td className="p-3 text-slate-300">{insp.brand} {insp.model}</td>
                    <td className="p-3 text-slate-400">{insp.year}</td>
                    <td className="p-3 text-slate-400">{insp.fuel_type}</td>
                    <td className="p-3 text-slate-400">{insp.inspection_date}</td>
                    <td className="p-3 text-slate-400">{insp.expiry_date}</td>
                    <td className="p-3">
                      <span className={`text-xs px-2 py-0.5 rounded ${insp.result === 'Admis' ? 'bg-green-400/10 text-green-400' : 'bg-red-400/10 text-red-400'}`}>
                        {insp.result}
                      </span>
                    </td>
                    <td className="p-3 text-right text-primary-400 font-mono">{insp.price ? `${insp.price} RON` : '-'}</td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => startEdit(insp)} className="p-1.5 text-slate-400 hover:bg-slate-700 rounded"><Edit3 className="w-3.5 h-3.5" /></button>
                        <button onClick={() => setDeleting(insp.id)} className="p-1.5 text-red-400 hover:bg-red-400/10 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">Pagina {page} din {totalPages}</span>
            <div className="flex gap-1">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
                className="p-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded text-slate-400"><ChevronLeft className="w-4 h-4" /></button>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                className="p-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded text-slate-400"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ===== STATISTICI =====
function StatsTab() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/api/itp/statistics');
        setStats(res.data);
      } catch { setStats(null); }
      setLoading(false);
    })();
  }, []);

  if (loading) return <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>;
  if (!stats) return <div className="text-center py-12"><BarChart3 className="w-10 h-10 text-slate-600 mx-auto mb-2" /><p className="text-sm text-slate-500">Nu sunt date suficiente pentru statistici</p></div>;

  const monthlyData = stats.monthly_inspections || [];
  const brandsData = stats.top_brands || [];
  const revenueData = stats.monthly_revenue || [];
  const fuelData = stats.fuel_distribution || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Monthly inspections */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-primary-400" /> Inspectii pe Luna
        </h3>
        {monthlyData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : <p className="text-sm text-slate-500 text-center py-8">Fara date</p>}
      </div>

      {/* Top brands */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <PieChartIcon className="w-4 h-4 text-cyan-400" /> Top Marci
        </h3>
        {brandsData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={brandsData} dataKey="count" nameKey="brand" cx="50%" cy="50%" outerRadius={90} label={({ brand, percent }) => `${brand} ${(percent * 100).toFixed(0)}%`}>
                {brandsData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        ) : <p className="text-sm text-slate-500 text-center py-8">Fara date</p>}
      </div>

      {/* Monthly revenue */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-green-400" /> Venituri Lunare (RON)
        </h3>
        {revenueData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
            </LineChart>
          </ResponsiveContainer>
        ) : <p className="text-sm text-slate-500 text-center py-8">Fara date</p>}
      </div>

      {/* Fuel distribution */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <PieChartIcon className="w-4 h-4 text-yellow-400" /> Distributie Combustibil
        </h3>
        {fuelData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={fuelData} dataKey="count" nameKey="fuel_type" cx="50%" cy="50%" outerRadius={90} label={({ fuel_type, percent }) => `${fuel_type} ${(percent * 100).toFixed(0)}%`}>
                {fuelData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : <p className="text-sm text-slate-500 text-center py-8">Fara date</p>}
      </div>
    </div>
  );
}

// ===== EXPIRARI =====
function ExpiringTab() {
  const [expiring, setExpiring] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/api/itp/expiring', { params: { days: 30 } });
        setExpiring(res.data.inspections || res.data || []);
      } catch { setExpiring([]); }
      setLoading(false);
    })();
  }, []);

  if (loading) return <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>;

  const getDaysColor = (days) => {
    if (days <= 0) return 'text-red-400 bg-red-400/10';
    if (days <= 7) return 'text-orange-400 bg-orange-400/10';
    if (days <= 14) return 'text-yellow-400 bg-yellow-400/10';
    return 'text-emerald-400 bg-emerald-400/10';
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-400">Vehicule cu ITP-ul care expira in urmatoarele 30 de zile</p>

      {expiring.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Niciun vehicul cu ITP expirand in curand</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-700">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-800/60 text-slate-400 text-xs">
                <th className="text-left p-3">Nr. Auto</th>
                <th className="text-left p-3">Marca / Model</th>
                <th className="text-left p-3">Expirare</th>
                <th className="text-center p-3">Zile Ramase</th>
                <th className="text-left p-3">Observatii</th>
              </tr>
            </thead>
            <tbody>
              {expiring.map(insp => {
                const daysLeft = insp.days_remaining != null ? insp.days_remaining :
                  Math.ceil((new Date(insp.expiry_date) - new Date()) / (1000 * 60 * 60 * 24));
                return (
                  <tr key={insp.id} className="border-t border-slate-700/50 hover:bg-slate-800/30 transition-colors">
                    <td className="p-3 text-white font-mono font-medium">{insp.plate_number}</td>
                    <td className="p-3 text-slate-300">{insp.brand} {insp.model}</td>
                    <td className="p-3 text-slate-400">{insp.expiry_date}</td>
                    <td className="p-3 text-center">
                      <span className={`text-xs px-2 py-1 rounded font-medium ${getDaysColor(daysLeft)}`}>
                        {daysLeft <= 0 ? `Expirat (${Math.abs(daysLeft)} zile)` : `${daysLeft} zile`}
                      </span>
                    </td>
                    <td className="p-3 text-slate-500 text-xs">{insp.notes || '-'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ===== IMPORT / EXPORT =====
function ImportExportTab() {
  const [importLoading, setImportLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportLoading(true);
    setMessage('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post('/api/itp/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage(`Import reusit: ${res.data.imported || 0} inregistrari adaugate.`);
    } catch (err) {
      setMessage(`Eroare import: ${err.response?.data?.detail || err.message}`);
    }
    setImportLoading(false);
    e.target.value = '';
  };

  const handleExport = async (format) => {
    setExportLoading(true);
    try {
      const res = await apiClient.get('/api/itp/export', {
        params: { format },
        responseType: 'blob',
      });
      const url = URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `itp_export.${format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setMessage(`Eroare export: ${err.response?.data?.detail || err.message}`);
    }
    setExportLoading(false);
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-400">Importa sau exporta date ITP in format CSV sau Excel</p>

      {message && (
        <div className={`rounded-lg p-3 text-sm ${message.startsWith('Eroare') ? 'bg-red-900/20 border border-red-800/30 text-red-300' : 'bg-green-900/20 border border-green-800/30 text-green-300'}`}>
          {message}
        </div>
      )}

      {/* Import */}
      <div className="bg-slate-800/40 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Upload className="w-4 h-4 text-blue-400" /> Import Date
        </h3>
        <p className="text-xs text-slate-400 mb-4">Incarca un fisier CSV sau Excel cu date ITP. Coloanele trebuie sa corespunda: plate_number, vin, brand, model, year, fuel_type, inspection_date, expiry_date, result, price, notes</p>
        <label className="btn-primary inline-flex items-center gap-2 px-4 py-2 text-sm cursor-pointer">
          {importLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          {importLoading ? 'Se importa...' : 'Alege Fisier CSV/Excel'}
          <input type="file" accept=".csv,.xlsx,.xls" onChange={handleImport} className="hidden" />
        </label>
      </div>

      {/* Export */}
      <div className="bg-slate-800/40 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Download className="w-4 h-4 text-green-400" /> Export Date
        </h3>
        <p className="text-xs text-slate-400 mb-4">Descarca toate datele ITP intr-un fisier</p>
        <div className="flex gap-3">
          <button onClick={() => handleExport('csv')} disabled={exportLoading}
            className="btn-primary flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-50">
            <Download className="w-4 h-4" /> Export CSV
          </button>
          <button onClick={() => handleExport('xlsx')} disabled={exportLoading}
            className="btn-secondary flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-50">
            <FileSpreadsheet className="w-4 h-4" /> Export Excel
          </button>
        </div>
      </div>
    </div>
  );
}

// ===== MAIN PAGE =====
export default function ITPPage() {
  const [activeTab, setActiveTab] = useState('inspections');

  const renderTab = () => {
    switch (activeTab) {
      case 'inspections': return <InspectionsTab />;
      case 'stats': return <StatsTab />;
      case 'expiring': return <ExpiringTab />;
      case 'import-export': return <ImportExportTab />;
      default: return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
          <Car className="w-5 h-5 text-primary-400" />
          Gestiune ITP
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
