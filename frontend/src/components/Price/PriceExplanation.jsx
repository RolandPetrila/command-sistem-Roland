import React, { useState } from 'react';
import { Bot, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import api from '../../api/client';

export default function PriceExplanation({ calculationId, features, price, confidence }) {
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [provider, setProvider] = useState('');

  const loadExplanation = async () => {
    if (explanation) {
      setExpanded(!expanded);
      return;
    }
    setLoading(true);
    setExpanded(true);
    try {
      const payload = calculationId
        ? { calculation_id: calculationId }
        : { features, price, confidence };
      const { data } = await api.post('/api/ai/explain-price', payload);
      setExplanation(data.explanation || '');
      setProvider(data.provider || '');
    } catch {
      setExplanation('Nu s-a putut genera explicația.');
    }
    setLoading(false);
  };

  return (
    <div className="mt-3">
      <button onClick={loadExplanation}
        className="flex items-center gap-2 text-sm text-purple-400 hover:text-purple-300 transition-colors">
        {loading ? <Loader2 size={14} className="animate-spin" /> : <Bot size={14} />}
        <span>Explicație AI preț</span>
        {explanation && (expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
      </button>
      {expanded && explanation && (
        <div className="mt-2 p-3 bg-purple-900/10 border border-purple-800/30 rounded-lg text-sm text-slate-300 leading-relaxed">
          {explanation}
          {provider && <span className="block mt-1 text-xs text-gray-500">via {provider}</span>}
        </div>
      )}
    </div>
  );
}
