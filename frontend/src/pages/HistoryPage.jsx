import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
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
