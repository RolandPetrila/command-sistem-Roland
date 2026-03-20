import React, { useState, useEffect } from 'react';
import { Save, Loader2, CheckCircle2 } from 'lucide-react';
import { getSettings, updateSettings } from '../../api/client';

export default function InvoicePercent() {
  const [percent, setPercent] = useState(75);
  const [savedPercent, setSavedPercent] = useState(75);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSettings()
      .then((data) => {
        const val = data.invoice_percent ?? 75;
        setPercent(val);
        setSavedPercent(val);
      })
      .catch(() => { /* toast handles it */ })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await updateSettings({ invoice_percent: percent });
      setSavedPercent(percent);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Invoice percent save error:', err);
    } finally {
      setSaving(false);
    }
  };

  const hasChanged = percent !== savedPercent;

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-8">
        <Loader2 className="animate-spin text-primary-400" size={20} />
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-slate-200 mb-4">Procent Facturare</h3>
      <p className="text-sm text-slate-400 mb-6">
        Procentul aplicat la prețul pieței pentru a calcula prețul facturat clientului.
        Valoarea salvată curentă: <span className="font-medium text-slate-300">{savedPercent}%</span>
      </p>

      <div className="bg-slate-800/60 rounded-lg p-5">
        <div className="flex items-center gap-4 mb-4">
          <input
            type="range"
            min={1}
            max={100}
            value={percent}
            onChange={(e) => setPercent(Number(e.target.value))}
            className="flex-1 h-2 rounded-full appearance-none cursor-pointer
              [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
              [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-500
              [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:cursor-pointer
              bg-gradient-to-r from-slate-700 to-primary-600"
          />
          <div className="flex items-center gap-1">
            <input
              type="number"
              min={1}
              max={100}
              value={percent}
              onChange={(e) => setPercent(Math.min(100, Math.max(1, Number(e.target.value) || 1)))}
              className="w-20 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-center text-white font-semibold focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <span className="text-slate-400 font-medium">%</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Exemplu: preț piață 100 RON = facturat{' '}
            <span className="text-emerald-400 font-semibold">{percent} RON</span>
          </div>
          <button
            onClick={handleSave}
            disabled={saving || !hasChanged}
            className="btn-primary flex items-center gap-2"
          >
            {saving ? (
              <Loader2 size={16} className="animate-spin" />
            ) : saved ? (
              <CheckCircle2 size={16} />
            ) : (
              <Save size={16} />
            )}
            {saving ? 'Se salvează...' : saved ? 'Salvat!' : 'Salvează'}
          </button>
        </div>
      </div>
    </div>
  );
}
