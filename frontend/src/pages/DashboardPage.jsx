import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Loader2,
  Receipt,
  Languages,
  Car,
  Clock,
  Calculator,
  Bot,
  FolderOpen,
  FileText,
  Activity,
  CircleDot,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  CalendarCheck,
  Plus,
  Sun,
  Moon,
  Sunrise,
  CheckSquare,
  Square,
  Trash2,
  Target,
} from 'lucide-react';
import api from '../api/client';
import ExchangeRateCard from '../components/Dashboard/ExchangeRateCard';
import AIInsightsCard from '../components/Dashboard/AIInsightsCard';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatRelativeTime(isoStr) {
  if (!isoStr) return '-';
  const d = new Date(isoStr);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHrs = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffMin < 1) return 'Chiar acum';
  if (diffMin < 60) return `${diffMin} min in urma`;
  if (diffHrs < 24) return `${diffHrs}h in urma`;
  if (diffDays < 7) return `${diffDays}z in urma`;
  return d.toLocaleDateString('ro-RO', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function dayLabel(dateStr) {
  if (!dateStr) return '';
  // Parse YYYY-MM-DD as local time (not UTC) to avoid timezone offset shifting the day
  const parts = String(dateStr).split('T')[0].split('-');
  const d = parts.length === 3
    ? new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
    : new Date(dateStr);
  return d.toLocaleDateString('ro-RO', { weekday: 'short', day: 'numeric', month: 'short' });
}

// ---------------------------------------------------------------------------
// Summary Card
// ---------------------------------------------------------------------------

function SummaryCard({ icon: Icon, label, value, color, loading: isLoading, error, onRetry, onClick }) {
  return (
    <div onClick={!error ? onClick : undefined}
      className={`bg-gray-900 rounded-2xl shadow border ${error ? 'border-red-800/40' : 'border-gray-800'} p-5 flex items-start justify-between ${!error && onClick ? 'cursor-pointer hover:border-gray-600 transition-colors' : ''}`}>
      <div>
        <p className="text-xs text-gray-400 mb-1 uppercase tracking-wide">{label}</p>
        {isLoading ? (
          <div className="mt-1 space-y-2">
            <div className="animate-pulse bg-gray-700 rounded h-6 w-24" />
            <div className="animate-pulse bg-gray-700 rounded h-3 w-16" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 mt-1">
            <span className="text-sm text-red-400">Eroare la incarcare</span>
            {onRetry && (
              <button onClick={(e) => { e.stopPropagation(); onRetry(); }}
                className="p-1 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
                title="Reincearca">
                <RefreshCw size={14} />
              </button>
            )}
          </div>
        ) : (
          <p className="text-2xl font-bold text-gray-100">{value ?? '0'}</p>
        )}
      </div>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${error ? 'bg-red-600/50' : color}`}>
        <Icon size={22} className="text-white" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Activity Chart (CSS bars, no Recharts)
// ---------------------------------------------------------------------------

function ActivityChart({ data, lastWeekData, loading: isLoading }) {
  if (isLoading) {
    return (
      <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
        <h3 className="text-sm font-semibold text-gray-200 mb-4">Activitate Ultimele 7 Zile</h3>
        <div className="flex items-center justify-center h-48">
          <Loader2 size={24} className="animate-spin text-gray-600" />
        </div>
      </div>
    );
  }

  const hasComparison = Array.isArray(lastWeekData) && lastWeekData.length > 0;
  const allValues = [
    ...data.map((d) => d.count ?? d.total ?? 0),
    ...(hasComparison ? lastWeekData.map((d) => d.count ?? d.total ?? 0) : []),
  ];
  const maxCount = Math.max(1, ...allValues);

  return (
    <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-1">
        <Activity size={18} className="text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-200">Activitate Ultimele 7 Zile</h3>
      </div>
      {/* Legend */}
      {hasComparison && (
        <div className="flex items-center gap-4 mb-4 ml-7">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-blue-500" />
            <span className="text-[11px] text-gray-400">Saptamana curenta</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-gray-600 opacity-50" />
            <span className="text-[11px] text-gray-400">Saptamana anterioara</span>
          </div>
        </div>
      )}
      {!hasComparison && <div className="mb-4" />}
      {data.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-8">Nu exista date de activitate.</p>
      ) : (
        <div className="flex items-end gap-3 h-48">
          {data.map((item, idx) => {
            const value = item.count ?? item.total ?? 0;
            const pct = (value / maxCount) * 100;
            const lastVal = hasComparison ? (lastWeekData[idx]?.count ?? lastWeekData[idx]?.total ?? 0) : 0;
            const lastPct = hasComparison ? (lastVal / maxCount) * 100 : 0;
            return (
              <div key={idx} className="flex-1 flex flex-col items-center justify-end h-full">
                <span className="text-xs text-gray-400 mb-1 font-mono">{value}</span>
                <div className="w-full flex items-end justify-center gap-0.5" style={{ height: `${Math.max(pct, lastPct, 3)}%` }}>
                  {hasComparison && (
                    <div
                      className="w-[40%] rounded-t bg-gray-600 opacity-30 transition-all duration-500 min-h-[2px]"
                      style={{ height: maxCount > 0 ? `${Math.max((lastVal / Math.max(value, lastVal, 1)) * 100, 3)}%` : '3%' }}
                      title={`Sapt. anterioara: ${lastVal}`}
                    />
                  )}
                  <div
                    className={`${hasComparison ? 'w-[40%]' : 'w-full'} rounded-t-lg bg-gradient-to-t from-blue-600 to-blue-400 transition-all duration-500 min-h-[4px]`}
                    style={{ height: '100%' }}
                  />
                </div>
                <span className="text-[10px] text-gray-500 mt-2 text-center leading-tight">
                  {dayLabel(item.date || item.period)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Provider Status
// ---------------------------------------------------------------------------

function ProviderStatus({ providers, loading: isLoading }) {
  return (
    <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Bot size={18} className="text-purple-400" />
        <h3 className="text-sm font-semibold text-gray-200">Provideri AI</h3>
      </div>
      {isLoading ? (
        <div className="flex justify-center py-4">
          <Loader2 size={18} className="animate-spin text-gray-600" />
        </div>
      ) : providers.length === 0 ? (
        <p className="text-sm text-gray-500">Niciun provider gasit.</p>
      ) : (
        <div className="space-y-2.5">
          {providers.map((p, i) => (
            <div key={i} className="flex items-center gap-3">
              <CircleDot
                size={14}
                className={p.configured ? 'text-emerald-400' : 'text-gray-600'}
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-gray-200 font-medium truncate">{p.name}</p>
                <p className="text-[11px] text-gray-500 truncate">{p.model || 'N/A'}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quick Actions
// ---------------------------------------------------------------------------

const QUICK_ACTIONS = [
  { label: 'Calculator', path: '/upload', icon: Calculator, color: 'bg-blue-600 hover:bg-blue-500' },
  { label: 'Traducator', path: '/translator', icon: Languages, color: 'bg-emerald-600 hover:bg-emerald-500' },
  { label: 'Facturare', path: '/invoices', icon: Receipt, color: 'bg-amber-600 hover:bg-amber-500' },
  { label: 'Chat AI', path: '/ai-chat', icon: Bot, color: 'bg-purple-600 hover:bg-purple-500' },
  { label: 'Fisiere', path: '/files', icon: FolderOpen, color: 'bg-cyan-600 hover:bg-cyan-500' },
];

function QuickActions() {
  const navigate = useNavigate();

  return (
    <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <ArrowRight size={18} className="text-amber-400" />
        <h3 className="text-sm font-semibold text-gray-200">Acces Rapid</h3>
      </div>
      <div className="grid grid-cols-1 gap-2">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-colors ${action.color}`}
            >
              <Icon size={16} />
              {action.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Daily Goals Widget
// ---------------------------------------------------------------------------

function DailyGoals() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newGoal, setNewGoal] = useState('');
  const [adding, setAdding] = useState(false);

  const loadGoals = useCallback(async () => {
    try {
      const { data } = await api.get('/api/reports/dashboard/daily-goals');
      setGoals(Array.isArray(data) ? data : (data?.goals || []));
    } catch {
      // toast handles it
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadGoals(); }, [loadGoals]);

  const addGoal = async () => {
    const text = newGoal.trim();
    if (!text || adding) return;
    setAdding(true);
    try {
      await api.post('/api/reports/dashboard/daily-goals', JSON.stringify(text), {
        headers: { 'Content-Type': 'application/json' },
      });
      setNewGoal('');
      await loadGoals();
    } catch {
      // toast handles it
    } finally {
      setAdding(false);
    }
  };

  const toggleGoal = async (id, completed) => {
    try {
      await api.put(`/api/reports/dashboard/daily-goals/${id}`, { completed });
      setGoals((prev) => prev.map((g) => g.id === id ? { ...g, completed } : g));
    } catch {
      // toast handles it
    }
  };

  const deleteGoal = async (id) => {
    try {
      await api.delete(`/api/reports/dashboard/daily-goals/${id}`);
      setGoals((prev) => prev.filter((g) => g.id !== id));
    } catch {
      // toast handles it
    }
  };

  const completedCount = goals.filter((g) => g.completed).length;
  const totalCount = goals.length;
  const pct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Target size={18} className="text-blue-400" />
          <h3 className="text-sm font-semibold text-gray-200">Obiective Zilnice</h3>
        </div>
        <div className="flex justify-center py-4">
          <Loader2 size={18} className="animate-spin text-gray-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-3">
        <Target size={18} className="text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-200">Obiective Zilnice</h3>
        {totalCount > 0 && (
          <span className="ml-auto text-xs text-gray-500">{completedCount}/{totalCount} ({pct}%)</span>
        )}
      </div>

      {/* Progress bar */}
      {totalCount > 0 && (
        <div className="bg-gray-800 rounded-full h-2 mb-4 overflow-hidden">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      )}

      {/* Goals checklist */}
      {goals.length > 0 && (
        <div className="space-y-1.5 mb-3">
          {goals.map((goal) => (
            <div key={goal.id} className="flex items-center gap-2 group">
              <button
                onClick={() => toggleGoal(goal.id, !goal.completed)}
                className="shrink-0 text-gray-400 hover:text-blue-400 transition-colors"
              >
                {goal.completed
                  ? <CheckSquare size={16} className="text-blue-400" />
                  : <Square size={16} />
                }
              </button>
              <span className={`flex-1 text-sm ${goal.completed ? 'line-through text-gray-600' : 'text-gray-300'}`}>
                {goal.text || goal.title || goal.goal}
              </span>
              <button
                onClick={() => deleteGoal(goal.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-gray-600 hover:text-red-400 transition-all"
                title="Sterge"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add goal input */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={newGoal}
          onChange={(e) => setNewGoal(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') addGoal(); }}
          placeholder="Adauga obiectiv..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
        />
        <button
          onClick={addGoal}
          disabled={!newGoal.trim() || adding}
          className="p-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title="Adauga"
        >
          <Plus size={14} />
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// "Ziua Mea" (My Day) Section
// ---------------------------------------------------------------------------

function GreetingIcon({ hour }) {
  if (hour >= 5 && hour < 12) return <Sunrise size={28} className="text-amber-400" />;
  if (hour >= 12 && hour < 18) return <Sun size={28} className="text-yellow-400" />;
  return <Moon size={28} className="text-indigo-400" />;
}

function MyDaySection({ data, loading: isLoading, onNavigate }) {
  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 rounded-2xl shadow border border-gray-700 p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 size={28} className="animate-spin text-gray-500" />
          <span className="ml-3 text-gray-400">Se incarca rezumatul zilei...</span>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const currentHour = new Date().getHours();
  const dateFormatted = new Date().toLocaleDateString('ro-RO', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const overdueInvoices = data.invoices?.overdue?.length || 0;
  const itpOverdue = data.itp?.overdue_count || 0;
  const appointmentsToday = data.itp?.appointments_today?.length || 0;
  const itpExpiring7d = data.itp?.expiring_7_days || 0;
  const dueThisWeek = data.invoices?.due_this_week?.length || 0;
  const hasAlerts = overdueInvoices > 0 || itpOverdue > 0 || appointmentsToday > 0;

  const stats = data.quick_stats || {};

  return (
    <div className="space-y-4">
      {/* --- Greeting Banner --- */}
      <div className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 rounded-2xl shadow border border-gray-700 p-6">
        <div className="flex items-center gap-4">
          <GreetingIcon hour={currentHour} />
          <div>
            <h2 className="text-2xl font-bold text-gray-100">{data.greeting}</h2>
            <p className="text-sm text-gray-400 capitalize">{dateFormatted}</p>
          </div>
        </div>
      </div>

      {/* --- Daily Goals --- */}
      <DailyGoals />

      {/* --- Urgent Alerts Row --- */}
      {hasAlerts && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {overdueInvoices > 0 && (
            <button
              onClick={() => onNavigate('/invoices')}
              className="flex items-center gap-3 bg-red-950/60 border border-red-800/50 rounded-xl p-4 hover:bg-red-900/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-red-600/30 flex items-center justify-center shrink-0">
                <Receipt size={20} className="text-red-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-red-300">Facturi restante</p>
                <p className="text-xl font-bold text-red-400">{overdueInvoices}</p>
              </div>
            </button>
          )}
          {itpOverdue > 0 && (
            <button
              onClick={() => onNavigate('/itp')}
              className="flex items-center gap-3 bg-orange-950/60 border border-orange-800/50 rounded-xl p-4 hover:bg-orange-900/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-orange-600/30 flex items-center justify-center shrink-0">
                <Car size={20} className="text-orange-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-orange-300">ITP expirate</p>
                <p className="text-xl font-bold text-orange-400">{itpOverdue}</p>
              </div>
            </button>
          )}
          {appointmentsToday > 0 && (
            <button
              onClick={() => onNavigate('/itp')}
              className="flex items-center gap-3 bg-blue-950/60 border border-blue-800/50 rounded-xl p-4 hover:bg-blue-900/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-blue-600/30 flex items-center justify-center shrink-0">
                <CalendarCheck size={20} className="text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-blue-300">Programari azi</p>
                <p className="text-xl font-bold text-blue-400">{appointmentsToday}</p>
              </div>
            </button>
          )}
          {itpExpiring7d > 0 && (
            <button
              onClick={() => onNavigate('/itp')}
              className="flex items-center gap-3 bg-amber-950/60 border border-amber-800/50 rounded-xl p-4 hover:bg-amber-900/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-amber-600/30 flex items-center justify-center shrink-0">
                <AlertTriangle size={20} className="text-amber-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-amber-300">ITP expira 7 zile</p>
                <p className="text-xl font-bold text-amber-400">{itpExpiring7d}</p>
              </div>
            </button>
          )}
          {dueThisWeek > 0 && (
            <button
              onClick={() => onNavigate('/invoices')}
              className="flex items-center gap-3 bg-yellow-950/60 border border-yellow-800/50 rounded-xl p-4 hover:bg-yellow-900/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-yellow-600/30 flex items-center justify-center shrink-0">
                <Clock size={20} className="text-yellow-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-yellow-300">Scadente sapt.</p>
                <p className="text-xl font-bold text-yellow-400">{dueThisWeek}</p>
              </div>
            </button>
          )}
        </div>
      )}

      {/* --- Quick Actions Row --- */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button
          onClick={() => onNavigate('/invoices', { openCreate: true })}
          className="flex items-center gap-2 bg-blue-600/20 border border-blue-700/40 rounded-xl p-3 hover:bg-blue-600/30 transition-colors"
        >
          <Plus size={16} className="text-blue-400" />
          <span className="text-sm font-medium text-blue-300">Factura noua</span>
        </button>
        <button
          onClick={() => onNavigate('/itp')}
          className="flex items-center gap-2 bg-amber-600/20 border border-amber-700/40 rounded-xl p-3 hover:bg-amber-600/30 transition-colors"
        >
          <Plus size={16} className="text-amber-400" />
          <span className="text-sm font-medium text-amber-300">Inspectie noua</span>
        </button>
        <button
          onClick={() => onNavigate('/translator')}
          className="flex items-center gap-2 bg-emerald-600/20 border border-emerald-700/40 rounded-xl p-3 hover:bg-emerald-600/30 transition-colors"
        >
          <Languages size={16} className="text-emerald-400" />
          <span className="text-sm font-medium text-emerald-300">Traducere noua</span>
        </button>
        <button
          onClick={() => onNavigate('/upload')}
          className="flex items-center gap-2 bg-purple-600/20 border border-purple-700/40 rounded-xl p-3 hover:bg-purple-600/30 transition-colors"
        >
          <Calculator size={16} className="text-purple-400" />
          <span className="text-sm font-medium text-purple-300">Calcul pret</span>
        </button>
      </div>

      {/* --- This Month Summary --- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Receipt size={14} className="text-blue-400" />
            <span className="text-xs text-gray-500 uppercase">Facturi luna</span>
          </div>
          <p className="text-xl font-bold text-gray-100">{stats.invoices_this_month || 0}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={14} className="text-emerald-400" />
            <span className="text-xs text-gray-500 uppercase">Venit luna</span>
          </div>
          <p className="text-xl font-bold text-gray-100">
            {(stats.revenue_this_month || 0).toLocaleString('ro-RO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} RON
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Languages size={14} className="text-cyan-400" />
            <span className="text-xs text-gray-500 uppercase">Traduceri luna</span>
          </div>
          <p className="text-xl font-bold text-gray-100">{stats.translations_this_month || 0}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Car size={14} className="text-amber-400" />
            <span className="text-xs text-gray-500 uppercase">ITP luna</span>
          </div>
          <p className="text-xl font-bold text-gray-100">{stats.itp_this_month || 0}</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recent Activity (last 5 entries from activity-log)
// ---------------------------------------------------------------------------

const ACTIVITY_FILTERS = [
  { id: 'all', label: 'Toate' },
  { id: 'calc', label: 'Calculator', prefix: 'calc' },
  { id: 'translator', label: 'Translator', prefix: 'translat' },
  { id: 'invoice', label: 'Facturare', prefix: 'invoice' },
  { id: 'itp', label: 'ITP', prefix: 'itp' },
];

function RecentActivityList({ entries, loading: isLoading }) {
  const [filter, setFilter] = useState('all');

  const filtered = useMemo(() => {
    if (filter === 'all') return entries;
    const f = ACTIVITY_FILTERS.find((t) => t.id === filter);
    if (!f || !f.prefix) return entries;
    return entries.filter(
      (e) => e.action && e.action.toLowerCase().startsWith(f.prefix)
    );
  }, [entries, filter]);

  return (
    <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <FileText size={18} className="text-cyan-400" />
        <h3 className="text-sm font-semibold text-gray-200">Activitate Recenta</h3>
      </div>
      {/* Filter pills (R4-34) */}
      <div className="flex gap-1.5 mb-4 flex-wrap">
        {ACTIVITY_FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              filter === f.id
                ? 'bg-blue-600/30 text-blue-300 border border-blue-500/40'
                : 'bg-gray-800 text-gray-400 border border-gray-700 hover:text-gray-200 hover:bg-gray-700'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
      {isLoading ? (
        <div className="flex justify-center py-6">
          <Loader2 size={18} className="animate-spin text-gray-600" />
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-4">
          {filter === 'all' ? 'Nicio activitate inregistrata.' : 'Nicio activitate pentru acest modul.'}
        </p>
      ) : (
        <div className="space-y-2">
          {filtered.map((entry, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 rounded-xl bg-gray-800/50 hover:bg-gray-800 transition-colors"
            >
              <Activity size={14} className="text-gray-500 mt-0.5 shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-medium text-blue-400 uppercase">
                    {entry.action || 'actiune'}
                  </span>
                  {entry.status && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                        entry.status === 'success'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : entry.status === 'error'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-gray-700 text-gray-400'
                      }`}
                    >
                      {entry.status}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-300 truncate">{entry.summary || '-'}</p>
              </div>
              <span className="text-[11px] text-gray-500 shrink-0 whitespace-nowrap">
                {formatRelativeTime(entry.timestamp)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Dashboard Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Summary card data
  const [invoiceCount, setInvoiceCount] = useState(0);
  const [translationCount, setTranslationCount] = useState(0);
  const [itpActiveCount, setItpActiveCount] = useState(0);
  const [uptimeStr, setUptimeStr] = useState('-');

  // Per-card error tracking (R4-33)
  const [statsError, setStatsError] = useState(false);
  const [uptimeError, setUptimeError] = useState(false);

  // Chart + providers + recent
  const [chartData, setChartData] = useState([]);
  const [providers, setProviders] = useState([]);
  const [recentEntries, setRecentEntries] = useState([]);

  // Per-section loading
  const [chartLoading, setChartLoading] = useState(true);
  const [providersLoading, setProvidersLoading] = useState(true);
  const [recentLoading, setRecentLoading] = useState(true);

  // R3-29: Additional dashboard widgets
  const [receivable, setReceivable] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(true);

  // AXA E: "Ziua Mea" (My Day) data
  const [myDay, setMyDay] = useState(null);
  const [myDayLoading, setMyDayLoading] = useState(true);

  // Weekly comparison data
  const [lastWeekData, setLastWeekData] = useState([]);

  const navigate = useNavigate();

  const fetchAll = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);

    try {
      const results = await Promise.allSettled([
        // 0 - quick-stats (replaces: invoice/list, activity-log?translator, itp/list)
        api.get('/api/reports/dashboard/quick-stats'),
        // 1 - system info (uptime)
        api.get('/api/reports/system-info'),
        // 2 - timeline (chart)
        api.get('/api/reports/timeline/stats', { params: { group_by: 'day', days: 7 } }),
        // 3 - AI providers
        api.get('/api/ai/providers'),
        // 4 - recent activity
        api.get('/api/activity-log', { params: { limit: 5 } }),
        // 5 - receivable (R3-29)
        api.get('/api/reports/dashboard/receivable'),
        // 6 - alerts (R3-29)
        api.get('/api/reports/dashboard/alerts'),
        // 7 - my-day (AXA E)
        api.get('/api/reports/dashboard/my-day'),
        // 8 - weekly comparison
        api.get('/api/reports/dashboard/weekly-comparison'),
      ]);

      // 0 - Quick stats (invoices, translations, ITP — single call)
      if (results[0].status === 'fulfilled') {
        const d = results[0].value?.data;
        setInvoiceCount(d?.invoices_this_month ?? 0);
        setTranslationCount(d?.translations_this_month ?? 0);
        setItpActiveCount(d?.itp_this_month ?? 0);
        setStatsError(false);
      } else {
        setStatsError(true);
      }

      // 1 - Uptime
      if (results[1].status === 'fulfilled') {
        const d = results[1].value?.data;
        const up = d?.uptime || d?.system_uptime || d?.uptime_string || '-';
        setUptimeStr(typeof up === 'string' ? up : '-');
        setUptimeError(false);
      } else {
        setUptimeError(true);
      }

      // 2 - Chart
      setChartLoading(false);
      if (results[2].status === 'fulfilled') {
        const d = results[2].value?.data;
        const timeline = Array.isArray(d) ? d : (d?.stats || d?.timeline || d?.data || []);
        setChartData(timeline);
      }

      // 3 - Providers
      setProvidersLoading(false);
      if (results[3].status === 'fulfilled') {
        const d = results[3].value?.data;
        const list = Array.isArray(d) ? d : (d?.providers || []);
        setProviders(list);
      }

      // 4 - Recent
      setRecentLoading(false);
      if (results[4].status === 'fulfilled') {
        const d = results[4].value?.data;
        const entries = d?.entries || (Array.isArray(d) ? d : []);
        setRecentEntries(entries);
      }

      // 5 - Receivable (R3-29)
      if (results[5]?.status === 'fulfilled') {
        setReceivable(results[5].value?.data);
      }

      // 6 - Alerts (R3-29)
      setAlertsLoading(false);
      if (results[6]?.status === 'fulfilled') {
        const d = results[6].value?.data;
        setAlerts(d?.alerts || (Array.isArray(d) ? d : []));
      }

      // 7 - My Day (AXA E)
      setMyDayLoading(false);
      if (results[7]?.status === 'fulfilled') {
        setMyDay(results[7].value?.data || null);
      }

      // 8 - Weekly comparison (graceful fallback — if fails, lastWeekData stays empty)
      if (results[8]?.status === 'fulfilled') {
        const wc = results[8].value?.data;
        setLastWeekData(wc?.last_week || []);
        // If the endpoint provides this_week, use it for chart instead
        if (Array.isArray(wc?.this_week) && wc.this_week.length > 0) {
          setChartData(wc.this_week);
        }
      }
    } catch {
      // toast handles it — individual cards show fallback values
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(() => fetchAll(), 300000); // auto-refresh every 5 minutes
    return () => clearInterval(interval);
  }, [fetchAll]);

  // ---------- Render ----------

  return (
    <div className="space-y-6 bg-gray-950 min-h-full">
      {/* ---------- Header Row ---------- */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">Panou Principal</h1>
        <button
          onClick={() => fetchAll(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Se actualizeaza...' : 'Actualizeaza'}
        </button>
      </div>

      {/* ---------- Ziua Mea (My Day) ---------- */}
      <MyDaySection
        data={myDay}
        loading={myDayLoading}
        onNavigate={(path, state) => navigate(path, { state })}
      />

      {/* ---------- Summary Cards ---------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          icon={Receipt}
          label="Total Facturi"
          value={invoiceCount}
          color="bg-blue-600/80"
          loading={loading}
          error={statsError}
          onRetry={() => fetchAll(true)}
        />
        <SummaryCard
          icon={Languages}
          label="Total Traduceri"
          value={translationCount}
          color="bg-emerald-600/80"
          loading={loading}
          error={statsError}
          onRetry={() => fetchAll(true)}
        />
        <SummaryCard
          icon={Car}
          label="ITP Active"
          value={itpActiveCount}
          color="bg-amber-600/80"
          loading={loading}
          error={statsError}
          onRetry={() => fetchAll(true)}
        />
        <SummaryCard
          icon={Clock}
          label="Uptime Sistem"
          value={uptimeStr}
          color="bg-purple-600/80"
          loading={loading}
          error={uptimeError}
          onRetry={() => fetchAll(true)}
        />
      </div>

      {/* ---------- Alerts + Receivable Row (R3-29) ---------- */}
      {(alerts.length > 0 || (receivable && receivable.total_receivable > 0)) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {receivable && receivable.total_receivable > 0 && (
            <div className="bg-gray-900 rounded-2xl shadow border border-amber-800/30 p-5">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign size={18} className="text-amber-400" />
                <h3 className="text-sm font-semibold text-gray-200">De incasat</h3>
              </div>
              <p className="text-2xl font-bold text-amber-400">{receivable.total_receivable?.toFixed(2)} RON</p>
              <p className="text-xs text-gray-500">{receivable.unpaid_count || 0} facturi neplatite</p>
            </div>
          )}
          {alerts.length > 0 && (
            <div className="bg-gray-900 rounded-2xl shadow border border-red-800/30 p-5">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={18} className="text-red-400" />
                <h3 className="text-sm font-semibold text-gray-200">Alerte ({alerts.length})</h3>
              </div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {alerts.slice(0, 5).map((a, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span className={`mt-0.5 w-2 h-2 rounded-full shrink-0 ${a.severity === 'critical' ? 'bg-red-500' : a.severity === 'warning' ? 'bg-amber-500' : 'bg-blue-500'}`} />
                    <span className="text-gray-300">{a.message || a.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------- Main Grid (3 columns desktop) ---------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1 — span 2: Activity Chart */}
        <div className="lg:col-span-2">
          <ActivityChart data={chartData} lastWeekData={lastWeekData} loading={chartLoading} />
        </div>

        {/* Column 2 — sidebar cards */}
        <div className="space-y-6">
          <ProviderStatus providers={providers} loading={providersLoading} />
          <QuickActions />
          <ExchangeRateCard />
          <AIInsightsCard />
        </div>
      </div>

      {/* ---------- Recent Activity (bottom) ---------- */}
      <RecentActivityList entries={recentEntries} loading={recentLoading} />
    </div>
  );
}
