import React, { useState, useEffect } from 'react';
import { Bot, Loader2, RefreshCw } from 'lucide-react';
import api from '../../api/client';

export default function AIInsightsCard() {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadInsights = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/api/ai/dashboard-insights');
      setInsights(data);
    } catch (err) {
      setError('Nu s-au putut genera insight-urile AI');
    }
    setLoading(false);
  };

  useEffect(() => { loadInsights(); }, []);

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bot size={18} className="text-purple-400" />
          <h3 className="font-semibold text-sm">Insight-uri AI</h3>
          {insights?.cached && <span className="text-xs text-gray-600">(cached)</span>}
        </div>
        <button onClick={loadInsights} disabled={loading}
          className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors">
          <RefreshCw size={14} className={loading ? 'animate-spin text-purple-400' : 'text-gray-500'} />
        </button>
      </div>

      {loading && !insights && (
        <div className="flex items-center gap-2 py-4 justify-center text-gray-500 text-sm">
          <Loader2 size={16} className="animate-spin" /> Generez analiză...
        </div>
      )}

      {error && !insights && (
        <p className="text-xs text-gray-500 py-2">{error}</p>
      )}

      {insights?.insights && (
        <div className="space-y-2">
          {(Array.isArray(insights.insights) ? insights.insights : [insights.insights]).map((insight, i) => (
            <div key={i} className="text-sm text-slate-300 flex gap-2">
              <span className="text-purple-400 shrink-0">•</span>
              <span>{insight}</span>
            </div>
          ))}
          {insights.generated_at && (
            <p className="text-xs text-gray-600 mt-2">
              Generat: {new Date(insights.generated_at).toLocaleString('ro')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
