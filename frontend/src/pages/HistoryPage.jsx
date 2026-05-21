import React, { useState, useEffect, useMemo } from 'react';
import { Loader2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import HistoryFilters from '../components/History/HistoryFilters';
import HistoryTable from '../components/History/HistoryTable';
import { getHistory, deleteHistoryEntry } from '../api/client';

const DEFAULT_FILTERS = {
  search: '',
  fileType: '',
  minPrice: '',
  maxPrice: '',
  minConfidence: '',
};

export default function HistoryPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const fetchHistory = async () => {
    try {
      const data = await getHistory();
      setEntries(Array.isArray(data) ? data : (data.items || data.entries || []));
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id) => {
    try {
      await deleteHistoryEntry(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      console.error('Eroare la ștergerea înregistrării:', err);
      alert('Nu s-a putut șterge înregistrarea. Încercați din nou.');
    }
  };

  // Price trend chart data
  const chartData = useMemo(() =>
    entries
      .filter(e => e.market_price > 0)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      .map(e => ({
        date: new Date(e.created_at).toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit' }),
        price: Math.round(e.market_price),
        file: e.filename,
      })),
    [entries]
  );

  // Apply filters
  const filtered = entries.filter((entry) => {
    if (filters.search) {
      const s = filters.search.toLowerCase();
      if (!(entry.filename || '').toLowerCase().includes(s)) return false;
    }
    if (filters.fileType) {
      const ext = (entry.filename || '').split('.').pop().toLowerCase();
      if (ext !== filters.fileType) return false;
    }
    if (filters.minPrice && Number(entry.market_price) < Number(filters.minPrice)) return false;
    if (filters.maxPrice && Number(entry.market_price) > Number(filters.maxPrice)) return false;
    if (filters.minConfidence && Number(entry.confidence) < Number(filters.minConfidence)) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary-400" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {chartData.length > 2 && (
        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-4 mb-6">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Evolutie Preturi</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} unit=" RON" />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }} />
              <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} name="Pret" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <HistoryFilters
        filters={filters}
        onChange={setFilters}
        onReset={() => setFilters(DEFAULT_FILTERS)}
      />
      <HistoryTable entries={filtered} onDelete={handleDelete} />
      {filtered.length > 0 && (
        <p className="text-xs text-slate-500 text-center">
          Se afișează {filtered.length} din {entries.length} înregistrări
        </p>
      )}
    </div>
  );
}
