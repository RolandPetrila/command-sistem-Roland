import React from 'react';
import { Search, Filter, X } from 'lucide-react';

export default function HistoryFilters({ filters, onChange, onReset }) {
  const update = (key, value) => {
    onChange({ ...filters, [key]: value });
  };

  const hasFilters = filters.search || filters.fileType || filters.minPrice || filters.maxPrice || filters.minConfidence;

  return (
    <div className="card mb-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-300">Filtre</h3>
        </div>
        {hasFilters && (
          <button
            onClick={onReset}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-400 transition-colors"
          >
            <X size={12} />
            Resetează filtre
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Search */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Caută fișier..."
            value={filters.search || ''}
            onChange={(e) => update('search', e.target.value)}
            className="input-field w-full pl-8 text-sm"
          />
        </div>

        {/* File Type */}
        <select
          value={filters.fileType || ''}
          onChange={(e) => update('fileType', e.target.value)}
          className="input-field text-sm"
        >
          <option value="">Toate tipurile</option>
          <option value="pdf">PDF</option>
          <option value="docx">DOCX</option>
        </select>

        {/* Min Price */}
        <input
          type="number"
          placeholder="Preț min (RON)"
          value={filters.minPrice || ''}
          onChange={(e) => update('minPrice', e.target.value)}
          className="input-field text-sm"
        />

        {/* Max Price */}
        <input
          type="number"
          placeholder="Preț max (RON)"
          value={filters.maxPrice || ''}
          onChange={(e) => update('maxPrice', e.target.value)}
          className="input-field text-sm"
        />

        {/* Confidence */}
        <select
          value={filters.minConfidence || ''}
          onChange={(e) => update('minConfidence', e.target.value)}
          className="input-field text-sm"
        >
          <option value="">Orice încredere</option>
          <option value="90">Ridicată (&ge;90%)</option>
          <option value="70">Medie (&ge;70%)</option>
          <option value="0">Scăzută (toate)</option>
        </select>
      </div>
    </div>
  );
}
