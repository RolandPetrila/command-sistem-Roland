import React, { useState } from 'react';
import { BarChart3, Loader2, Bot } from 'lucide-react';
import api from '../../api/client';

export default function CompetitorAnalysis({ price, pages, words, docType }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const loadAnalysis = async () => {
    if (analysis) {
      setExpanded(!expanded);
      return;
    }
    setLoading(true);
    setExpanded(true);
    try {
      const { data } = await api.post('/api/ai/compare-price', { price, pages, words, doc_type: docType });
      setAnalysis(data);
    } catch {
      setAnalysis({ analysis: 'Nu s-a putut genera comparația.' });
    }
    setLoading(false);
  };

  return (
    <div className="mt-3">
      <button onClick={loadAnalysis}
        className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors">
        {loading ? <Loader2 size={14} className="animate-spin" /> : <BarChart3 size={14} />}
        <span>Comparare piață AI</span>
      </button>
      {expanded && analysis && (
        <div className="mt-2 p-3 bg-blue-900/10 border border-blue-800/30 rounded-lg space-y-3">
          <p className="text-sm text-slate-300 leading-relaxed">{analysis.analysis}</p>

          {/* Competitor bars */}
          {analysis.competitors && analysis.competitors.length > 0 && (
            <div className="space-y-2">
              {analysis.competitors.map((comp, i) => {
                const maxPrice = Math.max(price, ...analysis.competitors.map(c => c.estimated_price || 0));
                const pct = maxPrice > 0 ? ((comp.estimated_price || 0) / maxPrice) * 100 : 0;
                const isYou = comp.name === 'Tu';
                return (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className={`w-24 truncate ${isYou ? 'text-green-400 font-medium' : 'text-gray-400'}`}>{comp.name}</span>
                    <div className="flex-1 h-4 bg-gray-800 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${isYou ? 'bg-green-500' : 'bg-blue-600/60'}`}
                        style={{ width: `${pct}%` }} />
                    </div>
                    <span className={`w-20 text-right ${isYou ? 'text-green-400 font-medium' : 'text-gray-400'}`}>
                      {(comp.estimated_price || 0).toFixed(0)} RON
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {analysis.suggestion && (
            <p className="text-xs text-yellow-400/80 border-t border-gray-800 pt-2">
              💡 {analysis.suggestion}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
