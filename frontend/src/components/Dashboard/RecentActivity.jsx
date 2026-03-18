import React from 'react';
import { Clock, FileText, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ConfidenceBadge from '../Price/ConfidenceBadge';

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHrs = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'Chiar acum';
  if (diffMin < 60) return `Acum ${diffMin} min`;
  if (diffHrs < 24) return `Acum ${diffHrs} ore`;
  if (diffDays < 7) return `Acum ${diffDays} zile`;
  return d.toLocaleDateString('ro-RO');
}

export default function RecentActivity({ entries }) {
  const navigate = useNavigate();
  const recent = (entries || []).slice(0, 5);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock size={16} className="text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-300">Activitate Recentă</h3>
        </div>
        {entries && entries.length > 5 && (
          <button
            onClick={() => navigate('/history')}
            className="flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
          >
            Vezi tot <ArrowRight size={12} />
          </button>
        )}
      </div>

      {recent.length === 0 ? (
        <div className="text-center py-8">
          <FileText size={32} className="text-slate-700 mx-auto mb-2" />
          <p className="text-sm text-slate-400">Nu există calcule recente.</p>
          <button
            onClick={() => navigate('/upload')}
            className="btn-primary mt-3 text-sm"
          >
            Calculează primul preț
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {recent.map((entry, idx) => (
            <div
              key={entry.id || idx}
              className="flex items-center justify-between p-3 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <FileText size={16} className="text-slate-500 shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm text-slate-200 font-medium truncate">
                    {entry.filename || 'Fișier necunoscut'}
                  </p>
                  <p className="text-xs text-slate-500">{formatDate(entry.date)}</p>
                </div>
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-200">
                    {Number(entry.market_price || 0).toFixed(2)} RON
                  </p>
                  <p className="text-xs text-emerald-400">
                    {Number(entry.invoice_price || 0).toFixed(2)} RON facturat
                  </p>
                </div>
                <ConfidenceBadge confidence={entry.confidence || 0} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
