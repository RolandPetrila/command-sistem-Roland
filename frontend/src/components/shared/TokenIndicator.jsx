import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import api from '../../api/client';

const PROVIDER_COLORS = {
  gemini: { bg: 'bg-blue-500', text: 'text-blue-400', label: 'Gemini' },
  openai: { bg: 'bg-green-500', text: 'text-green-400', label: 'OpenAI' },
  groq: { bg: 'bg-orange-500', text: 'text-orange-400', label: 'Groq' },
  deepl: { bg: 'bg-cyan-500', text: 'text-cyan-400', label: 'DeepL' },
  azure: { bg: 'bg-purple-500', text: 'text-purple-400', label: 'Azure' },
};

export default function TokenIndicator({ compact = false }) {
  const [usage, setUsage] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadUsage = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/api/ai/token-usage');
      setUsage(Array.isArray(data) ? data : []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => {
    loadUsage();
    const interval = setInterval(loadUsage, 60000); // refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (usage.length === 0 && !loading) return null;

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-xs">
        <Activity size={12} className="text-gray-500" />
        {usage.filter(u => u.configured).map(u => {
          const pct = u.percent_used || 0;
          const color = pct > 80 ? 'text-red-400' : pct > 50 ? 'text-yellow-400' : 'text-green-400';
          return (
            <span key={u.provider} className={`${color}`} title={`${u.provider}: ${u.today_requests || 0} req azi`}>
              {PROVIDER_COLORS[u.provider]?.label || u.provider}
              {u.daily_limit ? ` ${pct.toFixed(0)}%` : ''}
            </span>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Activity size={14} />
          <span>Utilizare provideri AI</span>
        </div>
        <button onClick={loadUsage} disabled={loading}
          className="p-1 hover:bg-gray-800 rounded transition-colors">
          <RefreshCw size={12} className={loading ? 'animate-spin text-blue-400' : 'text-gray-600'} />
        </button>
      </div>
      {usage.filter(u => u.configured).map(u => {
        const pct = u.percent_used || 0;
        const colors = PROVIDER_COLORS[u.provider] || { bg: 'bg-gray-500', text: 'text-gray-400', label: u.provider };
        const barColor = pct > 80 ? 'bg-red-500' : pct > 50 ? 'bg-yellow-500' : colors.bg;
        return (
          <div key={u.provider} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className={colors.text}>{colors.label}</span>
              <span className="text-gray-500">
                {u.today_requests || 0} req
                {u.daily_limit ? ` / ${u.daily_limit}` : ''}
                {u.monthly_chars_used ? ` | ${(u.monthly_chars_used / 1000).toFixed(0)}K chars` : ''}
              </span>
            </div>
            {u.daily_limit && (
              <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all ${barColor}`}
                  style={{ width: `${Math.min(100, pct)}%` }} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
