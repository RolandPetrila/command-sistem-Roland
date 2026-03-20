import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Wifi, WifiOff, Sun, Moon, Keyboard, AlertTriangle, X, RefreshCw } from 'lucide-react';
import apiClient, { checkHealth } from '../../api/client';
import { useTheme } from '../../hooks/useTheme';
import { SHORTCUTS } from '../../hooks/useHotkeys';
import NetworkSpeedIndicator from './NetworkSpeedIndicator';

function ShortcutsModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-96 max-w-[90vw] shadow-2xl" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-semibold text-white mb-4">Scurtaturi Tastatura</h3>
        <div className="space-y-2">
          {SHORTCUTS.map((s, i) => (
            <div key={i} className="flex items-center justify-between py-1.5 border-b border-gray-800 last:border-0">
              <span className="text-sm text-gray-300">{s.label}</span>
              <kbd className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400 font-mono">
                {s.ctrl ? 'Ctrl+' : ''}{s.shift ? 'Shift+' : ''}{s.key.toUpperCase()}
              </kbd>
            </div>
          ))}
        </div>
        <button onClick={onClose}
          className="mt-4 w-full py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors">
          Inchide (Esc)
        </button>
      </div>
    </div>
  );
}

function DiagnosticsPanel({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data: d } = await apiClient.get('/api/diagnostics');
      setData(d);
    } catch { setData(null); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const allErrors = [
    ...(data?.recent_api_errors || []).map(e => ({ ...e, source: 'API' })),
    ...(data?.recent_frontend_errors || []).map(e => ({ ...e, source: 'Frontend' })),
  ].sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, 30);

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div className="w-full max-w-lg bg-gray-900 border-l border-gray-700 shadow-2xl h-full overflow-y-auto"
        onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-400" /> Diagnostice
          </h3>
          <div className="flex items-center gap-2">
            <button onClick={load} className="p-1.5 rounded hover:bg-gray-800 text-gray-400" title="Reincarca">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
            <button onClick={onClose} className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
              <X size={16} />
            </button>
          </div>
        </div>

        {data && (
          <div className="p-4 space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-gray-800 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-white">{data.request_stats.total_requests}</div>
                <div className="text-xs text-gray-400">Requests</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3 text-center">
                <div className={`text-2xl font-bold ${data.request_stats.total_errors > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {data.request_stats.total_errors}
                </div>
                <div className="text-xs text-gray-400">Erori</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-blue-400">{data.request_stats.uptime_human}</div>
                <div className="text-xs text-gray-400">Uptime</div>
              </div>
            </div>

            {/* Slow requests */}
            {data.request_stats.slow_requests.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-amber-400 mb-2">Requests lente (&gt;2s)</h4>
                {data.request_stats.slow_requests.map((r, i) => (
                  <div key={i} className="text-xs text-gray-400 py-1 border-b border-gray-800">
                    {r.method} {r.path} — {r.duration_ms}ms (status {r.status})
                  </div>
                ))}
              </div>
            )}

            {/* Error log */}
            <div>
              <h4 className="text-sm font-medium text-red-400 mb-2">
                Erori recente ({allErrors.length})
              </h4>
              {allErrors.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">Nicio eroare inregistrata</p>
              ) : (
                <div className="space-y-2">
                  {allErrors.map((e, i) => (
                    <div key={i} className="bg-gray-800 rounded-lg p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          e.source === 'API' ? 'bg-red-500/20 text-red-400' : 'bg-orange-500/20 text-orange-400'
                        }`}>{e.source}</span>
                        <span className="text-gray-500">
                          {new Date(e.timestamp).toLocaleString('ro-RO', { hour: '2-digit', minute: '2-digit', second: '2-digit', day: '2-digit', month: '2-digit' })}
                        </span>
                      </div>
                      <div className="text-gray-300 font-medium">{e.summary}</div>
                      {e.details?.response_body && (
                        <div className="text-gray-500 break-all bg-gray-900 rounded p-1.5 mt-1">
                          {e.details.response_body.slice(0, 200)}
                        </div>
                      )}
                      {e.details?.user_agent && (
                        <div className="text-gray-600 truncate">
                          {e.details.user_agent.includes('Android') ? 'Android' :
                           e.details.user_agent.includes('Windows') ? 'PC Windows' : 'Alt dispozitiv'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* System info */}
            <div className="text-xs text-gray-500 border-t border-gray-800 pt-3 space-y-1">
              <div>Disk: {data.system.disk_free_gb} GB liber / {data.system.disk_total_gb} GB ({data.system.disk_used_pct} folosit)</div>
              <div>Module: {data.system.modules_loaded} | Python {data.system.python_version} | v{data.system.server_version}</div>
            </div>
          </div>
        )}

        {loading && !data && (
          <div className="flex items-center justify-center h-32">
            <RefreshCw size={24} className="animate-spin text-gray-500" />
          </div>
        )}
      </div>
    </div>
  );
}

export default function Header({ pageTitles, showShortcuts, onToggleShortcuts }) {
  const location = useLocation();
  const [connected, setConnected] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const [showDiag, setShowDiag] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const pageTitle = pageTitles[location.pathname] || 'Calculator Pret Traduceri';

  useEffect(() => {
    let mounted = true;

    const check = async () => {
      const ok = await checkHealth();
      if (mounted) setConnected(ok);
      // Also fetch error count
      try {
        const { data } = await apiClient.get('/api/diagnostics');
        if (mounted) setErrorCount(data.request_stats.total_errors);
      } catch { /* ignore */ }
    };

    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <>
      <header className="h-14 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between px-6 pl-14 lg:pl-6 shrink-0 backdrop-blur-sm">
        <h2 className="text-lg font-semibold text-slate-100 truncate">{pageTitle}</h2>

        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <button onClick={toggleTheme}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title={theme === 'dark' ? 'Treci la tema deschisa' : 'Treci la tema inchisa'}>
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {/* Shortcuts help */}
          <button onClick={onToggleShortcuts}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Scurtaturi tastatura (Ctrl+/)">
            <Keyboard size={16} />
          </button>

          {/* Network speed indicator */}
          <NetworkSpeedIndicator />

          {/* Diagnostics button */}
          <button onClick={() => setShowDiag(v => !v)}
            className={`relative p-2 rounded-lg transition-colors ${
              errorCount > 0
                ? 'text-amber-400 hover:text-amber-300 hover:bg-amber-500/10'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
            title={`Diagnostice (${errorCount} erori)`}>
            <AlertTriangle size={16} />
            {errorCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 flex items-center justify-center px-1 bg-red-500 text-white text-[10px] font-bold rounded-full">
                {errorCount > 99 ? '99+' : errorCount}
              </span>
            )}
          </button>

          {/* Connection status */}
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
              connected
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'bg-red-500/15 text-red-400 border border-red-500/30'
            }`}
          >
            {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
            <span className="hidden sm:inline">{connected ? 'Conectat' : 'Deconectat'}</span>
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
              }`}
            />
          </div>
        </div>
      </header>
      {showShortcuts && <ShortcutsModal onClose={onToggleShortcuts} />}
      {showDiag && <DiagnosticsPanel onClose={() => setShowDiag(false)} />}
    </>
  );
}
