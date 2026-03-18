import React, { useState } from 'react';
import { ArrowUpDown, Eye, Trash2 } from 'lucide-react';
import ConfidenceBadge from '../Price/ConfidenceBadge';

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function HistoryTable({ entries, onDelete, onView }) {
  const [sortKey, setSortKey] = useState('date');
  const [sortDir, setSortDir] = useState('desc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sorted = [...(entries || [])].sort((a, b) => {
    let va = a[sortKey];
    let vb = b[sortKey];
    if (sortKey === 'date') {
      va = new Date(va || 0).getTime();
      vb = new Date(vb || 0).getTime();
    }
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    if (va < vb) return sortDir === 'asc' ? -1 : 1;
    if (va > vb) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  const columns = [
    { key: 'date', label: 'Data' },
    { key: 'filename', label: 'Fișier' },
    { key: 'market_price', label: 'Preț piață' },
    { key: 'invoice_price', label: 'Preț facturat' },
    { key: 'invoice_percent', label: '%' },
    { key: 'confidence', label: 'Încredere' },
  ];

  if (!entries || entries.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-slate-400">Nu există calcule în istoric.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-4 py-3 cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    <ArrowUpDown size={12} className={sortKey === col.key ? 'text-primary-400' : 'text-slate-600'} />
                  </div>
                </th>
              ))}
              <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider px-4 py-3">
                Acțiuni
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((entry, idx) => (
              <tr
                key={entry.id || idx}
                className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
              >
                <td className="px-4 py-3 text-sm text-slate-300">{formatDate(entry.date)}</td>
                <td className="px-4 py-3 text-sm text-slate-200 font-medium max-w-[200px] truncate">
                  {entry.filename || '-'}
                </td>
                <td className="px-4 py-3 text-sm text-slate-200 font-semibold">
                  {Number(entry.market_price || 0).toFixed(2)} RON
                </td>
                <td className="px-4 py-3 text-sm text-emerald-400 font-semibold">
                  {Number(entry.invoice_price || 0).toFixed(2)} RON
                </td>
                <td className="px-4 py-3 text-sm text-slate-300">
                  {entry.invoice_percent || 75}%
                </td>
                <td className="px-4 py-3">
                  <ConfidenceBadge confidence={entry.confidence || 0} />
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    {onView && (
                      <button
                        onClick={() => onView(entry)}
                        className="p-1.5 text-slate-400 hover:text-primary-400 rounded-lg hover:bg-slate-800 transition-colors"
                        title="Vizualizează"
                      >
                        <Eye size={16} />
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => onDelete(entry.id)}
                        className="p-1.5 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-800 transition-colors"
                        title="Șterge"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
