import { useState, useEffect } from 'react';
import { TrendingUp, RefreshCw } from 'lucide-react';
import api from '../../api/client';

export default function ExchangeRateCard() {
  const [rates, setRates] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchRates = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/api/reports/exchange-rates');
      setRates(data);
    } catch {
      setError('Nu s-a putut obține cursul BNR');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRates(); }, []);

  const main = rates?.key_rates || {};

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Curs BNR</h3>
        </div>
        <button onClick={fetchRates} disabled={loading}
          className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error ? (
        <p className="text-red-400 text-sm">{error}</p>
      ) : rates ? (
        <div className="space-y-2">
          {['EUR', 'USD', 'GBP', 'CHF'].map(c => main[c] != null && (
            <div key={c} className="flex justify-between items-center">
              <span className="text-slate-400 text-sm font-medium">{c}/RON</span>
              <span className="text-white font-mono text-base">{main[c].toFixed(4)}</span>
            </div>
          ))}
          {rates.date && (
            <p className="text-slate-500 text-xs mt-2 pt-2 border-t border-slate-700">
              Data: {rates.date} {rates.cached && '(cache)'}
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
