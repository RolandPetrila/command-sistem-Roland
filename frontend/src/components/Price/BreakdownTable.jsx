import React from 'react';
import {
  FileText,
  Type,
  Image,
  Table2,
  LayoutGrid,
  ScanLine,
  AlignLeft,
  Hash,
} from 'lucide-react';

const FEATURE_CONFIG = {
  page_count: { label: 'Pagini', icon: FileText },
  word_count: { label: 'Cuvinte total', icon: Type },
  words_per_page: { label: 'Cuvinte / pagină', icon: Hash },
  image_count: { label: 'Imagini', icon: Image },
  table_count: { label: 'Tabele', icon: Table2 },
  layout_complexity: { label: 'Complexitate layout', icon: LayoutGrid },
  is_scanned: { label: 'Document scanat (OCR)', icon: ScanLine },
  text_density: { label: 'Densitate text', icon: AlignLeft },
  // Legacy keys (in case backend sends these)
  pages: { label: 'Pagini', icon: FileText },
  words: { label: 'Cuvinte total', icon: Type },
  images: { label: 'Imagini', icon: Image },
  tables: { label: 'Tabele', icon: Table2 },
};

function formatValue(key, value) {
  if (typeof value === 'boolean') return value ? 'Da' : 'Nu';
  if (key === 'layout_complexity') {
    const labels = { low: 'Scăzută', medium: 'Medie', high: 'Ridicată' };
    return labels[value] || String(value);
  }
  if (key === 'text_density') {
    const labels = { low: 'Scăzută', medium: 'Medie', high: 'Ridicată' };
    return labels[value] || String(value);
  }
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toLocaleString('ro-RO') : value.toFixed(1);
  }
  return String(value);
}

export default function BreakdownTable({ breakdown }) {
  if (!breakdown || Object.keys(breakdown).length === 0) return null;

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Detalii Analiză Document</h3>
      <div className="space-y-1">
        {Object.entries(breakdown).map(([key, value]) => {
          const config = FEATURE_CONFIG[key];
          const Icon = config?.icon || FileText;
          const label = config?.label || key;

          return (
            <div
              key={key}
              className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Icon size={15} className="text-slate-500" />
                <span className="text-sm text-slate-300">{label}</span>
              </div>
              <span className="text-sm font-medium text-slate-100">{formatValue(key, value)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
