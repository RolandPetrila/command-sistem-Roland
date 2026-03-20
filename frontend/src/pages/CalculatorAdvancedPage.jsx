import React, { useState, useEffect, useCallback } from 'react';
import { Calculator, Trash2, History, Copy, Check } from 'lucide-react';
import apiClient from '../api/client';

const FUNC_BUTTONS = [
  { label: 'sin', insert: 'sin(' },
  { label: 'cos', insert: 'cos(' },
  { label: 'tan', insert: 'tan(' },
  { label: 'sqrt', insert: 'sqrt(' },
  { label: 'pow', insert: 'pow(' },
  { label: 'log', insert: 'log(' },
  { label: '\u03C0', insert: 'pi' },
  { label: 'e', insert: 'e' },
  { label: '(', insert: '(' },
  { label: ')', insert: ')' },
  { label: '%', insert: '%' },
  { label: '^', insert: '**' },
];

export default function CalculatorAdvancedPage() {
  const [expression, setExpression] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const res = await apiClient.get('/api/tools/calc-history');
      setHistory((res.data.history || []).slice(0, 20));
    } catch {
      // toast handles it
    }
  };

  const calculate = useCallback(async () => {
    if (!expression.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.post('/api/tools/calculate', {
        expression: expression.trim(),
      });
      setResult(res.data.formatted);
      loadHistory();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare de calcul');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [expression]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      calculate();
    }
  };

  const insertFunc = (text) => {
    setExpression(prev => prev + text);
    setError('');
    setResult(null);
  };

  const clearAll = () => {
    setExpression('');
    setResult(null);
    setError('');
  };

  const clearHistory = async () => {
    try {
      await apiClient.delete('/api/tools/calc-history');
      setHistory([]);
    } catch {
      // toast handles it
    }
  };

  const copyResult = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const el = document.createElement('textarea');
      el.value = result;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const useFromHistory = (item) => {
    setExpression(item.expression);
    setResult(item.formatted);
    setError('');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Input Card */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Calculator className="w-5 h-5 text-primary-400" />
          Calculator Avansat
        </h2>

        {/* Expression Input */}
        <div className="relative mb-4">
          <input
            type="text"
            value={expression}
            onChange={(e) => {
              setExpression(e.target.value);
              setError('');
              setResult(null);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Introdu o expresie matematica (ex: sqrt(144) + pow(2,10))..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-4 text-white text-xl font-mono focus:border-primary-500 focus:outline-none transition-colors pr-20"
          />
          {expression && (
            <button
              onClick={clearAll}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-red-400 transition-colors text-sm px-2 py-1"
            >
              Sterge
            </button>
          )}
        </div>

        {/* Result */}
        {result !== null && !error && (
          <div className="bg-slate-800/60 rounded-lg p-4 mb-4 flex items-center justify-between">
            <div>
              <span className="text-sm text-slate-400">Rezultat:</span>
              <p className="text-2xl font-mono font-bold text-primary-400 mt-1">= {result}</p>
            </div>
            <button
              onClick={copyResult}
              className="p-2 text-slate-400 hover:text-primary-400 transition-colors"
              title="Copiaza rezultatul"
            >
              {copied ? <Check className="w-5 h-5 text-green-400" /> : <Copy className="w-5 h-5" />}
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3 mb-4">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Function Buttons */}
        <div className="mb-4">
          <span className="text-xs text-slate-500 mb-2 block">Functii rapide:</span>
          <div className="flex flex-wrap gap-2">
            {FUNC_BUTTONS.map((btn) => (
              <button
                key={btn.label}
                onClick={() => insertFunc(btn.insert)}
                className="px-3 py-2 bg-slate-700/60 hover:bg-slate-600 text-cyan-300 rounded-lg text-sm font-mono transition-colors active:scale-95"
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* Calculate Button */}
        <button
          onClick={calculate}
          disabled={loading || !expression.trim()}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold disabled:opacity-50"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Se calculeaza...
            </>
          ) : (
            <>
              <Calculator className="w-4 h-4" />
              Calculeaza
            </>
          )}
        </button>

        <p className="text-xs text-slate-500 mt-3 text-center">
          Suporta: +, -, *, /, paranteze, %, sqrt, pow, sin, cos, tan, log, pi, e, ** (putere)
        </p>
      </div>

      {/* History */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-md font-semibold text-white flex items-center gap-2">
            <History className="w-4 h-4 text-primary-400" />
            Ultimele calcule
          </h3>
          {history.length > 0 && (
            <button
              onClick={clearHistory}
              className="text-slate-500 hover:text-red-400 transition-colors flex items-center gap-1 text-sm"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Sterge tot
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className="text-center py-8">
            <History className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-500">Niciun calcul in istoric</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {history.map((item, i) => (
              <button
                key={i}
                onClick={() => useFromHistory(item)}
                className="w-full text-left bg-slate-800/40 hover:bg-slate-700/50 rounded-lg p-3 transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400 font-mono truncate group-hover:text-slate-300 flex-1 mr-4">
                    {item.expression}
                  </p>
                  <p className="text-sm text-primary-400 font-mono font-semibold whitespace-nowrap">
                    = {item.formatted}
                  </p>
                </div>
                {item.timestamp && (
                  <p className="text-[10px] text-slate-600 mt-1">{item.timestamp}</p>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
