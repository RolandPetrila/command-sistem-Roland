import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity, Upload, Calculator, Settings, Trash2,
  Shield, CheckCircle, AlertCircle, Filter, RefreshCw,
} from 'lucide-react';
import { getActivityLog } from '../../api/client';

const ACTION_CONFIG = {
  upload:           { icon: Upload,      label: 'Upload',           color: 'text-blue-400' },
  calculate:        { icon: Calculator,  label: 'Calcul Preț',      color: 'text-emerald-400' },
  validate_price:   { icon: CheckCircle, label: 'Validare Preț',    color: 'text-green-400' },
  calibrate:        { icon: Shield,      label: 'Calibrare',        color: 'text-violet-400' },
  calibrate_revert: { icon: Shield,      label: 'Revert Calibrare', color: 'text-amber-400' },
  calibrate_reset:  { icon: Shield,      label: 'Reset Calibrare',  color: 'text-slate-400' },
  delete_history:   { icon: Trash2,      label: 'Ștergere',         color: 'text-red-400' },
  update_settings:  { icon: Settings,    label: 'Setări',           color: 'text-cyan-400' },
};

const STATUS_COLORS = {
  success:  'bg-emerald-500/20 text-emerald-400',
  error:    'bg-red-500/20 text-red-400',
  warning:  'bg-amber-500/20 text-amber-400',
  rejected: 'bg-red-500/20 text-red-400',
};

function formatRelativeTime(isoStr) {
  if (!isoStr) return '-';
  const d = new Date(isoStr);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHrs = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'Chiar acum';
  if (diffMin < 60) return `${diffMin} min în urmă`;
  if (diffHrs < 24) return `${diffHrs}h în urmă`;
  if (diffDays < 7) return `${diffDays}z în urmă`;
  return d.toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export default function ActivityLog() {
  const [entries, setEntries] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchLog = useCallback(async () => {
    try {
      const data = await getActivityLog(50, filter || null);
      setEntries(data.entries || []);
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchLog();
    const interval = setInterval(fetchLog, 30000);
    return () => clearInterval(interval);
  }, [fetchLog]);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-primary-400" />
          <h3 className="text-sm font-semibold text-slate-300">Jurnal Activitate</h3>
          <span className="text-xs text-slate-500">({entries.length} intrări)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Filter size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" />
            <select
              value={filter}
              onChange={(e) => { setFilter(e.target.value); setLoading(true); }}
              className="pl-6 pr-2 py-1 text-xs bg-slate-800 border border-slate-700 rounded text-slate-300 focus:outline-none focus:border-primary-500"
            >
              <option value="">Toate</option>
              <option value="upload">Upload</option>
              <option value="calculate">Calcul</option>
              <option value="calibrate">Calibrare</option>
              <option value="validate_price">Validare</option>
              <option value="update_settings">Setări</option>
              <option value="delete_history">Ștergere</option>
            </select>
          </div>
          <button
            onClick={() => { setLoading(true); fetchLog(); }}
            className="p-1 rounded hover:bg-slate-700 transition-colors"
            title="Reîmprospătare"
          >
            <RefreshCw size={14} className={`text-slate-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="text-center py-8">
          <Activity size={32} className="text-slate-700 mx-auto mb-2" />
          <p className="text-sm text-slate-400">
            {loading ? 'Se încarcă...' : 'Nu există activitate înregistrată.'}
          </p>
        </div>
      ) : (
        <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
          {entries.map((entry, idx) => {
            const config = ACTION_CONFIG[entry.action] || { icon: Activity, label: entry.action, color: 'text-slate-400' };
            const Icon = config.icon;
            const statusClass = STATUS_COLORS[entry.status] || 'bg-slate-500/20 text-slate-400';

            return (
              <div
                key={idx}
                className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
              >
                <div className={`shrink-0 ${config.color}`}>
                  <Icon size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-400">{config.label}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${statusClass}`}>
                      {entry.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 truncate">{entry.summary || '-'}</p>
                </div>
                <span className="text-xs text-slate-500 shrink-0 whitespace-nowrap">
                  {formatRelativeTime(entry.timestamp)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
