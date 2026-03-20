import React, { useState, useCallback, useEffect } from 'react';
import { Calculator, History, Trash2, CornerDownLeft } from 'lucide-react';
import apiClient from '../api/client';

const BUTTONS = [
  ['(', ')', '%', 'C'],
  ['7', '8', '9', '/'],
  ['4', '5', '6', '*'],
  ['1', '2', '3', '-'],
  ['0', '.', '=', '+'],
];

const SCIENTIFIC_ROW_1 = ['sin', 'cos', 'tan', 'sqrt'];
const SCIENTIFIC_ROW_2 = ['pow', 'log', 'pi', 'e'];

export default function CalculatorPage() {
  const [display, setDisplay] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(false);

  // Incarca istoricul la mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const res = await apiClient.get('/api/tools/calc-history');
      setHistory(res.data.history || []);
    } catch {
      // toast handles it
    }
  };

  const calculate = useCallback(async () => {
    if (!display.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.post('/api/tools/calculate', {
        expression: display,
      });
      setResult(res.data.formatted);
      setDisplay(res.data.formatted);
      // Refresh history
      loadHistory();
    } catch (err) {
      const detail = err.response?.data?.detail || 'Eroare de calcul';
      setError(detail);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [display]);

  const handleButton = useCallback((btn) => {
    setError('');
    if (btn === 'C') {
      setDisplay('');
      setResult(null);
      return;
    }
    if (btn === '=') {
      calculate();
      return;
    }
    // Functii stiintifice — adauga cu paranteza
    if (['sin', 'cos', 'tan', 'sqrt', 'pow', 'log'].includes(btn)) {
      setDisplay(prev => prev + btn + '(');
      setResult(null);
      return;
    }
    // Constante
    if (btn === 'pi' || btn === 'e') {
      setDisplay(prev => prev + btn);
      setResult(null);
      return;
    }
    setDisplay(prev => prev + btn);
    setResult(null);
  }, [calculate]);

  // Keyboard support
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        calculate();
      } else if (e.key === 'Escape') {
        setDisplay('');
        setResult(null);
        setError('');
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [calculate]);

  const clearHistory = async () => {
    try {
      await apiClient.delete('/api/tools/calc-history');
      setHistory([]);
    } catch {
      // toast handles it
    }
  };

  const useFromHistory = (item) => {
    setDisplay(item.expression);
    setResult(item.formatted);
    setError('');
  };

  const btnClass = (btn) => {
    const base = 'rounded-lg font-semibold text-sm h-12 transition-all duration-150 active:scale-95 focus:outline-none focus:ring-2 focus:ring-primary-500';
    if (btn === '=') return `${base} bg-primary-600 hover:bg-primary-500 text-white col-span-1`;
    if (btn === 'C') return `${base} bg-red-600/80 hover:bg-red-500 text-white`;
    if (['+', '-', '*', '/', '%', '(', ')'].includes(btn)) return `${base} bg-slate-600 hover:bg-slate-500 text-primary-300`;
    return `${base} bg-slate-700 hover:bg-slate-600 text-white`;
  };

  const sciBtnClass = 'rounded-lg font-medium text-xs h-10 bg-slate-700/60 hover:bg-slate-600 text-cyan-300 transition-all duration-150 active:scale-95 focus:outline-none';

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Calculator className="w-5 h-5 text-primary-400" />
          Calculator Avansat
        </h2>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="btn-secondary flex items-center gap-2 px-3 py-1.5 text-sm"
        >
          <History className="w-4 h-4" />
          {showHistory ? 'Ascunde Istoric' : 'Istoric'}
          {history.length > 0 && (
            <span className="bg-primary-600 text-white text-xs px-1.5 py-0.5 rounded-full">
              {history.length}
            </span>
          )}
        </button>
      </div>

      <div className="flex gap-4">
        {/* Calculator */}
        <div className="flex-1 card p-4">
          {/* Display */}
          <div className="bg-slate-900 rounded-lg p-4 mb-4 min-h-[80px] flex flex-col justify-end">
            <input
              type="text"
              value={display}
              onChange={(e) => {
                setDisplay(e.target.value);
                setResult(null);
                setError('');
              }}
              placeholder="Introdu expresia..."
              className="w-full bg-transparent text-right text-xl text-white font-mono focus:outline-none placeholder-slate-600"
            />
            {error && (
              <p className="text-right text-red-400 text-xs mt-1">{error}</p>
            )}
            {result !== null && !error && (
              <p className="text-right text-primary-400 text-sm mt-1 font-mono">
                = {result}
              </p>
            )}
          </div>

          {/* Scientific functions */}
          <div className="grid grid-cols-4 gap-1.5 mb-2">
            {SCIENTIFIC_ROW_1.map(btn => (
              <button key={btn} onClick={() => handleButton(btn)} className={sciBtnClass}>
                {btn}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-4 gap-1.5 mb-3">
            {SCIENTIFIC_ROW_2.map(btn => (
              <button key={btn} onClick={() => handleButton(btn)} className={sciBtnClass}>
                {btn === 'pi' ? '\u03C0' : btn}
              </button>
            ))}
          </div>

          {/* Main buttons */}
          <div className="grid grid-cols-4 gap-2">
            {BUTTONS.flat().map((btn, i) => (
              <button
                key={`${btn}-${i}`}
                onClick={() => handleButton(btn)}
                disabled={loading}
                className={btnClass(btn)}
              >
                {btn === '=' ? <CornerDownLeft className="w-4 h-4 mx-auto" /> : btn}
              </button>
            ))}
          </div>

          {/* Info */}
          <p className="text-xs text-slate-500 mt-3 text-center">
            Suporta: +, -, *, /, paranteze, %, sqrt, pow, sin, cos, tan, log, pi, e
          </p>
        </div>

        {/* History sidebar */}
        {showHistory && (
          <div className="w-64 card p-4 max-h-[500px] flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Istoric</h3>
              {history.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="text-slate-500 hover:text-red-400 transition-colors"
                  title="Sterge istoricul"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            <div className="flex-1 overflow-y-auto space-y-2">
              {history.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">
                  Niciun calcul inca
                </p>
              ) : (
                history.map((item, i) => (
                  <button
                    key={i}
                    onClick={() => useFromHistory(item)}
                    className="w-full text-left bg-slate-800/50 hover:bg-slate-700/50 rounded-lg p-2 transition-colors group"
                  >
                    <p className="text-xs text-slate-400 font-mono truncate group-hover:text-slate-300">
                      {item.expression}
                    </p>
                    <p className="text-sm text-primary-400 font-mono font-semibold">
                      = {item.formatted}
                    </p>
                    <p className="text-[10px] text-slate-600 mt-0.5">
                      {item.timestamp}
                    </p>
                  </button>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
