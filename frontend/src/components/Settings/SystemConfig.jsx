import React, { useState, useEffect } from 'react';
import { Save, Loader2, CheckCircle2, Info } from 'lucide-react';
import { getSettings, updateSettings } from '../../api/client';

const CONFIG_FIELDS = [
  {
    key: 'validation_threshold',
    label: 'Prag validare preț',
    description: 'Diferența maximă acceptată între metode (procent)',
    type: 'number',
    min: 0,
    max: 100,
    suffix: '%',
  },
  {
    key: 'reference_dir',
    label: 'Director fișiere reper',
    description: 'Calea către directorul cu fișiere de referință pentru calibrare',
    type: 'text',
  },
  {
    key: 'min_confidence',
    label: 'Încredere minimă acceptată',
    description: 'Sub acest prag se afișează avertisment',
    type: 'number',
    min: 0,
    max: 100,
    suffix: '%',
  },
  {
    key: 'ocr_enabled',
    label: 'OCR activat',
    description: 'Activează analiza documentelor scanate',
    type: 'toggle',
  },
];

export default function SystemConfig() {
  const [settings, setSettings] = useState({});
  const [original, setOriginal] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSettings()
      .then((data) => {
        setSettings(data);
        setOriginal(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await updateSettings(settings);
      setOriginal(settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // Handle gracefully
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = JSON.stringify(settings) !== JSON.stringify(original);

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-8">
        <Loader2 className="animate-spin text-primary-400" size={20} />
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-slate-200 mb-4">Configurare Sistem</h3>

      <div className="space-y-5">
        {CONFIG_FIELDS.map((field) => (
          <div key={field.key} className="bg-slate-800/40 rounded-lg p-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <label className="text-sm font-medium text-slate-300">{field.label}</label>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                  <Info size={10} />
                  {field.description}
                </p>
              </div>

              {field.type === 'toggle' ? (
                <button
                  onClick={() => handleChange(field.key, !settings[field.key])}
                  className={`w-11 h-6 rounded-full transition-colors duration-200 relative ${
                    settings[field.key] ? 'bg-primary-600' : 'bg-slate-700'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${
                      settings[field.key] ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              ) : field.type === 'number' ? (
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    min={field.min}
                    max={field.max}
                    value={settings[field.key] ?? ''}
                    onChange={(e) => handleChange(field.key, Number(e.target.value))}
                    className="w-24 input-field text-sm text-right"
                  />
                  {field.suffix && <span className="text-xs text-slate-500">{field.suffix}</span>}
                </div>
              ) : (
                <input
                  type="text"
                  value={settings[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  className="input-field text-sm w-64"
                />
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end mt-6">
        <button
          onClick={handleSave}
          disabled={saving || !hasChanges}
          className="btn-primary flex items-center gap-2"
        >
          {saving ? (
            <Loader2 size={16} className="animate-spin" />
          ) : saved ? (
            <CheckCircle2 size={16} />
          ) : (
            <Save size={16} />
          )}
          {saving ? 'Se salvează...' : saved ? 'Salvat!' : 'Salvează configurația'}
        </button>
      </div>
    </div>
  );
}
