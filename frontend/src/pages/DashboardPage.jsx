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
  const d = new Date(dateStr);
  return d.toLocaleDateString('ro-RO', { weekday: 'short', day: 'numeric', month: 'short' });
}

// ---------------------------------------------------------------------------
// Summary Card
// ---------------------------------------------------------------------------

function SummaryCard({ icon: Icon, label, value, color, loading: isLoading }) {
  return (
    <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5 flex items-start justify-between">
      <div>
        <p className="text-xs text-gray-400 mb-1 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-gray-100">
          {isLoading ? (
            <Loader2 size={20} className="animate-spin text-gray-500" />
          ) : (
            value ?? '0'
          )}
        </p>
      </div>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Activity Chart (CSS bars, no Recharts)
// ---------------------------------------------------------------------------

function ActivityChart({ data, loading: isLoading }) {
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

  const maxCount = Math.max(1, ...data.map((d) => d.count ?? d.total ?? 0));

  return (
    <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-5">
        <Activity size={18} className="text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-200">Activitate Ultimele 7 Zile</h3>
      </div>
      {data.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-8">Nu exista date de activitate.</p>
      ) : (
        <div className="flex items-end gap-3 h-48">
          {data.map((item, idx) => {
            const value = item.count ?? item.total ?? 0;
            const pct = (value / maxCount) * 100;
            return (
              <div key={idx} className="flex-1 flex flex-col items-center justify-end h-full">
                <span className="text-xs text-gray-400 mb-1 font-mono">{value}</span>
                <div
                  className="w-full rounded-t-lg bg-gradient-to-t from-blue-600 to-blue-400 transition-all duration-500 min-h-[4px]"
                  style={{ height: `${Math.max(pct, 3)}%` }}
                />
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
// Recent Activity (last 5 entries from activity-log)
// ---------------------------------------------------------------------------

function RecentActivityList({ entries, loading: isLoading }) {
  return (
    <div className="bg-gray-900 rounded-2xl shadow border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <FileText size={18} className="text-cyan-400" />
        <h3 className="text-sm font-semibold text-gray-200">Activitate Recenta</h3>
      </div>
      {isLoading ? (
        <div className="flex justify-center py-6">
          <Loader2 size={18} className="animate-spin text-gray-600" />
        </div>
      ) : entries.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-4">Nicio activitate inregistrata.</p>
      ) : (
        <div className="space-y-2">
          {entries.map((entry, idx) => (
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

  // Chart + providers + recent
  const [chartData, setChartData] = useState([]);
  const [providers, setProviders] = useState([]);
  const [recentEntries, setRecentEntries] = useState([]);

  // Per-section loading
  const [chartLoading, setChartLoading] = useState(true);
  const [providersLoading, setProvidersLoading] = useState(true);
  const [recentLoading, setRecentLoading] = useState(true);

  const fetchAll = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);

    try {
      const results = await Promise.allSettled([
        // 0 - quick-stats (replaces: invoice/list, activity-log?translator, itp/list)
        api.get('/api/reports/dashboard/quick-stats').catch(() => ({ data: {} })),
        // 1 - system info (uptime)
        api.get('/api/reports/system-info').catch(() => ({ data: {} })),
        // 2 - timeline (chart)
        api.get('/api/reports/timeline/stats', { params: { group_by: 'day', days: 7 } }).catch(() => ({ data: [] })),
        // 3 - AI providers
        api.get('/api/ai/providers').catch(() => ({ data: [] })),
        // 4 - recent activity
        api.get('/api/activity-log', { params: { limit: 5 } }).catch(() => ({ data: { entries: [] } })),
      ]);

      // 0 - Quick stats (invoices, translations, ITP — single call)
      if (results[0].status === 'fulfilled') {
        const d = results[0].value?.data;
        setInvoiceCount(d?.invoices_this_month ?? 0);
        setTranslationCount(d?.translations_this_month ?? 0);
        setItpActiveCount(d?.itp_this_month ?? 0);
      }

      // 1 - Uptime
      if (results[1].status === 'fulfilled') {
        const d = results[1].value?.data;
        const up = d?.uptime || d?.system_uptime || d?.uptime_string || '-';
        setUptimeStr(typeof up === 'string' ? up : '-');
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-400" size={32} />
      </div>
    );
  }

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

      {/* ---------- Summary Cards ---------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          icon={Receipt}
          label="Total Facturi"
          value={invoiceCount}
          color="bg-blue-600/80"
        />
        <SummaryCard
          icon={Languages}
          label="Total Traduceri"
          value={translationCount}
          color="bg-emerald-600/80"
        />
        <SummaryCard
          icon={Car}
          label="ITP Active"
          value={itpActiveCount}
          color="bg-amber-600/80"
        />
        <SummaryCard
          icon={Clock}
          label="Uptime Sistem"
          value={uptimeStr}
          color="bg-purple-600/80"
        />
      </div>

      {/* ---------- Main Grid (3 columns desktop) ---------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1 — span 2: Activity Chart */}
        <div className="lg:col-span-2">
          <ActivityChart data={chartData} loading={chartLoading} />
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
