import React, { useState, useEffect, useCallback } from 'react';
import {
  Car, Plus, Trash2, Edit3, Save, X, Search, ChevronLeft, ChevronRight,
  BarChart3, PieChart as PieChartIcon, TrendingUp, AlertTriangle, Upload,
  Download, Loader2, FileSpreadsheet, Calendar, Receipt, History, CheckCircle, XCircle, Ban,
  Clock, UserCheck, UserX, Camera
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import apiClient from '../api/client';

const TABS = [
  { id: 'inspections', label: 'Inspectii', icon: Car },
  { id: 'appointments', label: 'Programari', icon: Calendar },
  { id: 'followup', label: 'Follow-up', icon: Clock },
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
  expiry_date: '', result: 'Admis', price: '', notes: '',
  owner_name: '', owner_phone: '', inspector_name: '', rejection_reasons: []
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
  // R3-36: Vehicle history
  const [vehicleHistory, setVehicleHistory] = useState(null);
  const [vhData, setVhData] = useState([]);
  const [vhLoading, setVhLoading] = useState(false);
  // R3-37: Rejection reasons
  const [rejectionReasons, setRejectionReasons] = useState([]);
  // Photos
  const [photos, setPhotos] = useState([]);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
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

  // R4-25: Check if rejection reasons are required but missing
  const rejectionMissing = form.result === 'Respins' && (!form.rejection_reasons || form.rejection_reasons.length === 0);

  const save = async () => {
    // R4-25: Block save if Respins without reasons
    if (rejectionMissing) return;
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
      owner_name: insp.owner_name || '',
      owner_phone: insp.owner_phone || '',
      inspector_name: insp.inspector_name || '',
      rejection_reasons: insp.rejection_reasons || [],
    });
    if (insp.result === 'Respins') loadRejectionReasons();
  };

  // R3-36: Vehicle history
  const showVehicleHistory = async (plate) => {
    setVehicleHistory(plate);
    setVhLoading(true);
    try {
      const { data } = await apiClient.get(`/api/itp/vehicle-history/${encodeURIComponent(plate)}`);
      setVhData(data?.inspections || data || []);
    } catch { setVhData([]); }
    setVhLoading(false);
    setPhotos([]);
  };

  // R3-37: Load rejection reasons
  const loadRejectionReasons = async () => {
    try {
      const { data } = await apiClient.get('/api/itp/rejection-reasons');
      setRejectionReasons(data?.reasons || data || []);
    } catch { setRejectionReasons(['Franare deficitara', 'Emisii depasire', 'Directie defecta', 'Suspensie uzata', 'Lichide sub minim', 'Anvelope uzate', 'Corp rugina', 'Lumini defecte']); }
  };

  // Photos
  const loadPhotos = async (inspectionId) => {
    try {
      const { data } = await apiClient.get(`/api/itp/inspections/${inspectionId}/photos`);
      setPhotos(data.photos || []);
    } catch { setPhotos([]); }
  };

  const uploadPhoto = async (inspectionId, file) => {
    setUploadingPhoto(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await apiClient.post(`/api/itp/inspections/${inspectionId}/photos`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await loadPhotos(inspectionId);
    } finally { setUploadingPhoto(false); }
  };

  const createInvoice = async (insp) => {
    try {
      const { data } = await apiClient.post(`/api/invoice/from-itp/${insp.id}`);
      alert(`Factura ${data.invoice_number || 'noua'} creata cu succes!`);
    } catch { /* toast handles it */ }
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
              <select value={form.result} onChange={e => { setForm({ ...form, result: e.target.value }); if (e.target.value === 'Respins') loadRejectionReasons(); }}
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
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Proprietar</label>
              <input value={form.owner_name} onChange={e => setForm({ ...form, owner_name: e.target.value })}
                placeholder="Nume proprietar"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Telefon proprietar</label>
              <input value={form.owner_phone} onChange={e => setForm({ ...form, owner_phone: e.target.value })}
                placeholder="07xx xxx xxx"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Inspector</label>
              <input value={form.inspector_name} onChange={e => setForm({ ...form, inspector_name: e.target.value })}
                placeholder="Nume inspector"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none" />
            </div>
          </div>
          {/* R3-37 + R4-25: Rejection reasons (visible + mandatory when Respins) */}
          {form.result === 'Respins' && (
            <div>
              <label className="text-xs text-slate-400 mb-1 block">
                Motive respingere <span className="text-red-400">*</span>
                {rejectionMissing && <span className="ml-2 text-red-400 font-medium">Selecteaza cel putin un motiv!</span>}
              </label>
              <div className={`flex flex-wrap gap-2 p-2 rounded-lg border ${rejectionMissing ? 'border-red-500 bg-red-900/10' : 'border-transparent'}`}>
                {(rejectionReasons.length > 0 ? rejectionReasons : ['Franare', 'Emisii', 'Directie', 'Suspensie', 'Lumini', 'Anvelope']).map(reason => (
                  <label key={reason} className="flex items-center gap-1.5 text-xs cursor-pointer">
                    <input type="checkbox"
                      checked={(form.rejection_reasons || []).includes(reason)}
                      onChange={e => {
                        const cur = form.rejection_reasons || [];
                        setForm({ ...form, rejection_reasons: e.target.checked ? [...cur, reason] : cur.filter(r => r !== reason) });
                      }}
                      className="rounded border-slate-600 accent-red-500" />
                    <span className="text-slate-300">{reason}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Observatii</label>
            <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} rows={2}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none resize-none" />
          </div>
          <div className="flex gap-2">
            <button onClick={save} disabled={rejectionMissing} className={`btn-primary px-4 py-1.5 text-sm flex items-center gap-1 ${rejectionMissing ? 'opacity-50 cursor-not-allowed' : ''}`}><Save className="w-3.5 h-3.5" /> Salveaza</button>
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
                        <button onClick={() => showVehicleHistory(insp.plate_number)} className="p-1.5 text-blue-400 hover:bg-blue-400/10 rounded" title="Istoric vehicul"><History className="w-3.5 h-3.5" /></button>
                        <button onClick={() => createInvoice(insp)} className="p-1.5 text-amber-400 hover:bg-amber-400/10 rounded" title="Creaza factura"><Receipt className="w-3.5 h-3.5" /></button>
                        <label className="p-1.5 text-emerald-400 hover:bg-emerald-400/10 rounded cursor-pointer" title="Adauga foto">
                          <Camera className="w-3.5 h-3.5" />
                          <input type="file" accept="image/*" className="hidden" disabled={uploadingPhoto}
                            onChange={e => e.target.files[0] && uploadPhoto(insp.id, e.target.files[0])} />
                        </label>
                        <button onClick={() => startEdit(insp)} className="p-1.5 text-slate-400 hover:bg-slate-700 rounded" title="Editeaza"><Edit3 className="w-3.5 h-3.5" /></button>
                        <button onClick={() => setDeleting(insp.id)} className="p-1.5 text-red-400 hover:bg-red-400/10 rounded" title="Sterge"><Trash2 className="w-3.5 h-3.5" /></button>
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

      {/* R3-36: Vehicle history modal */}
      {vehicleHistory && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end">
          <div className="bg-slate-900 w-full max-w-md h-full overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Istoric vehicul — {vehicleHistory}</h3>
              <button onClick={() => setVehicleHistory(null)} className="p-1.5 hover:bg-slate-800 rounded"><X className="w-4 h-4" /></button>
            </div>
            {vhLoading ? (
              <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-slate-500" /></div>
            ) : vhData.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">Nicio inspectie anterioara pentru acest vehicul.</p>
            ) : (
              <div className="space-y-2">
                {vhData.map((insp, i) => (
                  <div key={i} className="bg-slate-800 rounded-lg p-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-300">{insp.inspection_date}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${insp.result === 'Admis' ? 'bg-green-400/10 text-green-400' : 'bg-red-400/10 text-red-400'}`}>
                        {insp.result}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">Expirare: {insp.expiry_date} | Pret: {insp.price || '-'} RON</div>
                    {insp.notes && <div className="text-xs text-slate-600 mt-0.5">{insp.notes}</div>}
                    <button onClick={() => loadPhotos(insp.id)} className="text-xs text-blue-400 hover:text-blue-300 mt-1 flex items-center gap-1">
                      <Camera className="w-3 h-3" /> Fotografii
                    </button>
                  </div>
                ))}
              </div>
            )}
            {/* Fotografii Inspectie */}
            {photos.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-300 mb-2">Fotografii</h4>
                <div className="grid grid-cols-3 gap-2 mb-2">
                  {photos.map(p => (
                    <div key={p.id} className="relative group">
                      <img src={`/api/itp/photos/serve/${p.id}`} alt={p.filename}
                        className="w-full h-24 object-cover rounded-lg" />
                      <button onClick={() => { apiClient.delete(`/api/itp/inspections/${p.inspection_id}/photos/${p.id}`).then(() => loadPhotos(p.inspection_id)); }}
                        className="absolute top-1 right-1 bg-red-600 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition">
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ===== R4-24: FOLLOW-UP =====
function FollowUpTab() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await apiClient.get('/api/itp/followup/due-soon', { params: { days: 30 } });
        setVehicles(data || []);
      } catch { setVehicles([]); }
      setLoading(false);
    })();
  }, []);

  if (loading) return <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>;

  const getDaysColor = (days) => {
    if (days <= 0) return 'text-red-400 bg-red-400/10';
    if (days < 7) return 'text-red-400 bg-red-400/10';
    if (days <= 14) return 'text-yellow-400 bg-yellow-400/10';
    return 'text-emerald-400 bg-emerald-400/10';
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-400">Vehicule care necesita re-inspectie in urmatoarele 30 de zile (bazat pe ultima inspectie + 12 luni)</p>

      {vehicles.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Niciun vehicul nu necesita re-inspectie in curand</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-700">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-800/60 text-slate-400 text-xs">
                <th className="text-left p-3">Nr. Auto</th>
                <th className="text-left p-3">Proprietar</th>
                <th className="text-left p-3">Marca / Model</th>
                <th className="text-left p-3">Ultima Inspectie</th>
                <th className="text-left p-3">Urmatoarea</th>
                <th className="text-center p-3">Zile Ramase</th>
              </tr>
            </thead>
            <tbody>
              {vehicles.map((v, i) => (
                <tr key={i} className="border-t border-slate-700/50 hover:bg-slate-800/30 transition-colors">
                  <td className="p-3 text-white font-mono font-medium">{v.plate}</td>
                  <td className="p-3 text-slate-300">{v.owner_name || '-'}</td>
                  <td className="p-3 text-slate-300">{v.brand} {v.model}</td>
                  <td className="p-3 text-slate-400">{v.last_inspection_date}</td>
                  <td className="p-3 text-slate-400">{v.next_due_date}</td>
                  <td className="p-3 text-center">
                    <span className={`text-xs px-2 py-1 rounded font-medium ${getDaysColor(v.days_remaining)}`}>
                      {v.days_remaining <= 0 ? `Depasit (${Math.abs(v.days_remaining)} zile)` : `${v.days_remaining} zile`}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ===== STATISTICI =====
function StatsTab() {
  const [stats, setStats] = useState(null);
  const [noshowStats, setNoshowStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [statsRes, noshowRes] = await Promise.all([
          apiClient.get('/api/itp/statistics'),
          apiClient.get('/api/itp/stats/noshow-rate').catch(() => ({ data: null })),
        ]);
        setStats(statsRes.data);
        setNoshowStats(noshowRes.data);
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

      {/* R4-26: No-show rate stats */}
      {noshowStats && noshowStats.total_appointments > 0 && (
        <div className="bg-slate-800/40 rounded-lg p-4 lg:col-span-2">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <UserX className="w-4 h-4 text-red-400" /> Statistici Prezenta Programari
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-white">{noshowStats.total_appointments}</div>
              <div className="text-xs text-slate-400">Total programari</div>
            </div>
            <div className="bg-slate-900/60 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-emerald-400">{noshowStats.showed_up}</div>
              <div className="text-xs text-slate-400">Prezenti</div>
            </div>
            <div className="bg-slate-900/60 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-red-400">{noshowStats.no_shows}</div>
              <div className="text-xs text-slate-400">Neprezentari</div>
            </div>
            <div className="bg-slate-900/60 rounded-lg p-3 text-center">
              <div className={`text-2xl font-bold ${noshowStats.no_show_rate_percent > 20 ? 'text-red-400' : noshowStats.no_show_rate_percent > 10 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                {noshowStats.no_show_rate_percent}%
              </div>
              <div className="text-xs text-slate-400">Rata neprezentare</div>
            </div>
          </div>
        </div>
      )}
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
      const endpoint = format === 'xlsx' ? '/api/itp/export/excel' : '/api/itp/export/csv';
      const res = await apiClient.get(endpoint, {
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

const RO_MONTHS = ['Ianuarie','Februarie','Martie','Aprilie','Mai','Iunie','Iulie','August','Septembrie','Octombrie','Noiembrie','Decembrie'];

// ===== F5: PROGRAMARI =====
function AppointmentsTab() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const now = new Date();
  const [calendarMonth, setCalendarMonth] = useState({ year: now.getFullYear(), month: now.getMonth() });
  const [form, setForm] = useState({
    plate_number: '', owner_name: '', owner_phone: '',
    scheduled_date: new Date().toISOString().split('T')[0],
    scheduled_time: '08:00', duration_min: 30, notes: '',
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get('/api/itp/appointments');
      setAppointments(data || []);
    } catch { setAppointments([]); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    try {
      if (editing && editing !== 'new') {
        await apiClient.put(`/api/itp/appointments/${editing}`, form);
      } else {
        await apiClient.post('/api/itp/appointments', form);
      }
      setEditing(null);
      setForm({ plate_number: '', owner_name: '', owner_phone: '', scheduled_date: new Date().toISOString().split('T')[0], scheduled_time: '08:00', duration_min: 30, notes: '' });
      load();
    } catch { /* toast handles it */ }
  };

  const remove = async (id) => {
    try { await apiClient.delete(`/api/itp/appointments/${id}`); load(); } catch { /* toast handles it */ }
  };

  const updateStatus = async (id, status) => {
    try { await apiClient.put(`/api/itp/appointments/${id}`, { status }); load(); } catch { /* toast handles it */ }
  };

  // R4-26: Mark showed up / no-show
  const markShowup = async (id, showedUp) => {
    try { await apiClient.put(`/api/itp/appointments/${id}/mark-showup`, { showed_up: showedUp }); load(); } catch { /* toast handles it */ }
  };

  const statusColors = { scheduled: 'text-blue-400', confirmed: 'text-green-400', completed: 'text-gray-400', cancelled: 'text-red-400', no_show: 'text-yellow-400' };

  const prevMonth = () => setCalendarMonth(cm => {
    const d = new Date(cm.year, cm.month - 1, 1);
    return { year: d.getFullYear(), month: d.getMonth() };
  });
  const nextMonth = () => setCalendarMonth(cm => {
    const d = new Date(cm.year, cm.month + 1, 1);
    return { year: d.getFullYear(), month: d.getMonth() };
  });

  const visibleAppointments = appointments.filter(a => {
    if (!a.scheduled_date) return false;
    const d = new Date(a.scheduled_date);
    return d.getFullYear() === calendarMonth.year && d.getMonth() === calendarMonth.month;
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-base font-medium">Programari ITP</h3>
        <button onClick={() => { setEditing('new'); setForm({ plate_number: '', owner_name: '', owner_phone: '', scheduled_date: new Date().toISOString().split('T')[0], scheduled_time: '08:00', duration_min: 30, notes: '' }); }}
          className="flex items-center gap-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
          <Plus size={14} /> Programare noua
        </button>
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-center gap-3">
        <button onClick={prevMonth} className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors">
          <ChevronLeft size={18} />
        </button>
        <span className="text-sm font-medium text-white min-w-[120px] text-center">
          {RO_MONTHS[calendarMonth.month]} {calendarMonth.year}
        </span>
        <button onClick={nextMonth} className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors">
          <ChevronRight size={18} />
        </button>
      </div>

      {editing && (
        <div className="bg-gray-900 rounded-xl p-4 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <input value={form.plate_number} onChange={e => setForm(f => ({ ...f, plate_number: e.target.value }))} placeholder="Nr. inmatriculare *" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <input value={form.owner_name} onChange={e => setForm(f => ({ ...f, owner_name: e.target.value }))} placeholder="Proprietar" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <input value={form.owner_phone} onChange={e => setForm(f => ({ ...f, owner_phone: e.target.value }))} placeholder="Telefon" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <input type="date" value={form.scheduled_date} onChange={e => setForm(f => ({ ...f, scheduled_date: e.target.value }))} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <input type="time" value={form.scheduled_time} onChange={e => setForm(f => ({ ...f, scheduled_time: e.target.value }))} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <input type="number" value={form.duration_min} onChange={e => setForm(f => ({ ...f, duration_min: parseInt(e.target.value) || 30 }))} placeholder="Durata (min)" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <input value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Note" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm col-span-2" />
          </div>
          <div className="flex gap-2">
            <button onClick={save} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm flex items-center gap-1"><Save size={14} /> Salveaza</button>
            <button onClick={() => setEditing(null)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm"><X size={14} /></button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="animate-spin text-gray-500" size={24} /></div>
      ) : visibleAppointments.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {appointments.length === 0 ? 'Nicio programare' : `Nicio programare in ${RO_MONTHS[calendarMonth.month]} ${calendarMonth.year}`}
        </div>
      ) : (
        <div className="space-y-2">
          {visibleAppointments.map(a => (
            <div key={a.id} className="bg-gray-900 rounded-lg p-3 flex items-center gap-3">
              <div className="flex-1">
                <div className="font-medium text-sm">{a.plate_number} {a.owner_name && `— ${a.owner_name}`}</div>
                <div className="text-xs text-gray-400">{a.scheduled_date} la {a.scheduled_time} ({a.duration_min} min)</div>
                {a.notes && <div className="text-xs text-gray-500 mt-0.5">{a.notes}</div>}
              </div>
              <div className="flex flex-col items-end gap-0.5">
                <span className={`text-xs font-medium ${statusColors[a.status] || 'text-gray-400'}`}>{a.status}</span>
                {a.showed_up === 1 && <span className="text-[10px] text-emerald-400">Prezent</span>}
                {a.showed_up === 0 && a.showed_up !== null && <span className="text-[10px] text-red-400">Neprezentare</span>}
              </div>
              <div className="flex gap-1">
                {a.status === 'scheduled' && (
                  <button onClick={() => updateStatus(a.id, 'confirmed')} className="p-1.5 hover:bg-green-700/30 rounded text-green-400" title="Confirma">
                    <Car size={14} />
                  </button>
                )}
                {(a.status === 'scheduled' || a.status === 'confirmed') && (
                  <>
                    <button onClick={() => markShowup(a.id, true)} className="p-1.5 hover:bg-green-700/30 rounded text-emerald-400" title="S-a prezentat">
                      <UserCheck size={14} />
                    </button>
                    <button onClick={() => markShowup(a.id, false)} className="p-1.5 hover:bg-red-700/30 rounded text-red-400" title="Nu s-a prezentat">
                      <UserX size={14} />
                    </button>
                    <button onClick={() => updateStatus(a.id, 'cancelled')} className="p-1.5 hover:bg-red-700/30 rounded text-orange-400" title="Anuleaza">
                      <Ban size={14} />
                    </button>
                  </>
                )}
                <button onClick={() => { setEditing(a.id); setForm({ plate_number: a.plate_number, owner_name: a.owner_name || '', owner_phone: a.owner_phone || '', scheduled_date: a.scheduled_date, scheduled_time: a.scheduled_time, duration_min: a.duration_min, notes: a.notes || '' }); }}
                  className="p-1.5 hover:bg-gray-700 rounded text-gray-400"><Edit3 size={14} /></button>
                <button onClick={() => remove(a.id)} className="p-1.5 hover:bg-red-700/30 rounded text-red-400"><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== MAIN PAGE =====
export default function ITPPage() {
  const [activeTab, setActiveTab] = useState('inspections');

  const renderTab = () => {
    switch (activeTab) {
      case 'inspections': return <InspectionsTab />;
      case 'appointments': return <AppointmentsTab />;
      case 'followup': return <FollowUpTab />;
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
