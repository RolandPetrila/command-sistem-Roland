import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Wifi, WifiOff } from 'lucide-react';
import { checkHealth } from '../../api/client';

export default function Header({ pageTitles }) {
  const location = useLocation();
  const [connected, setConnected] = useState(false);

  const pageTitle = pageTitles[location.pathname] || 'Calculator Preț Traduceri';

  useEffect(() => {
    let mounted = true;

    const check = async () => {
      const ok = await checkHealth();
      if (mounted) setConnected(ok);
    };

    check();
    const interval = setInterval(check, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-14 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between px-6 shrink-0 backdrop-blur-sm">
      <h2 className="text-lg font-semibold text-slate-100">{pageTitle}</h2>

      <div className="flex items-center gap-3">
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
            connected
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              : 'bg-red-500/15 text-red-400 border border-red-500/30'
          }`}
        >
          {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
          <span>{connected ? 'Backend conectat' : 'Backend deconectat'}</span>
          <span
            className={`w-2 h-2 rounded-full ${
              connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
            }`}
          />
        </div>
      </div>
    </header>
  );
}
