import { useState } from 'react';
import { Hash } from 'lucide-react';

const BASES = [
  { label: 'Binar (2)', base: 2 },
  { label: 'Octal (8)', base: 8 },
  { label: 'Zecimal (10)', base: 10 },
  { label: 'Hexazecimal (16)', base: 16 },
];

export default function NumberConverterPage() {
  const [input, setInput] = useState('');
  const [fromBase, setFromBase] = useState(10);
  const [error, setError] = useState('');

  const parsed = (() => {
    if (!input.trim()) return null;
    try {
      const n = parseInt(input.trim(), fromBase);
      if (isNaN(n)) throw new Error('NaN');
      return n;
    } catch {
      return null;
    }
  })();

  const handleInput = (val) => {
    setInput(val);
    setError('');
    if (val.trim()) {
      const n = parseInt(val.trim(), fromBase);
      if (isNaN(n)) setError(`"${val}" nu este valid în baza ${fromBase}`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Hash className="w-6 h-6 text-indigo-400" />
        <h1 className="text-2xl font-bold text-white">Convertor Numere</h1>
      </div>

      <div className="bg-slate-800 rounded-xl p-6 space-y-4 border border-slate-700">
        <div className="space-y-2">
          <label className="text-sm text-slate-400">Număr de convertit</label>
          <input
            type="text"
            value={input}
            onChange={e => handleInput(e.target.value)}
            placeholder="Introdu un număr..."
            className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg text-white text-lg font-mono focus:border-indigo-500 focus:outline-none"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm text-slate-400">Baza sursă</label>
          <div className="flex gap-2 flex-wrap">
            {BASES.map(b => (
              <button
                key={b.base}
                onClick={() => { setFromBase(b.base); handleInput(input); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  fromBase === b.base
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {parsed !== null && (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-sm text-slate-400 mb-4">Rezultate conversie</h2>
          <div className="space-y-3">
            {BASES.map(b => (
              <div key={b.base} className="flex items-center justify-between p-3 bg-slate-900 rounded-lg">
                <span className="text-slate-400 text-sm">{b.label}</span>
                <span className="font-mono text-lg text-white select-all">
                  {parsed.toString(b.base).toUpperCase()}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between p-3 bg-slate-900 rounded-lg">
              <span className="text-slate-400 text-sm">ASCII</span>
              <span className="font-mono text-lg text-white select-all">
                {parsed >= 32 && parsed <= 126 ? String.fromCharCode(parsed) : '—'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
