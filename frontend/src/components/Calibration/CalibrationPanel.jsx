import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Undo2,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
  Sliders,
  Save,
} from 'lucide-react';
import api, {
  getCalibrationStatus,
  triggerCalibration,
  revertCalibration,
  resetCalibration,
} from '../../api/client';

export default function CalibrationPanel({ onCalibrationChange }) {
  const [status, setStatus] = useState(null);
  const [calibrating, setCalibrating] = useState(false);
  const [reverting, setReverting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');
  const [comparison, setComparison] = useState(null);
  // F8: Interactive weight adjustment
  const [showWeights, setShowWeights] = useState(false);
  const [weights, setWeights] = useState({ base_rate: 30, word_rate: 40, similarity: 30 });
  const [savingWeights, setSavingWeights] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await getCalibrationStatus();
      setStatus(data);
      // Initialize weights from calibration data
      if (data?.calibration?.weights) {
        const w = data.calibration.weights;
        setWeights({
          base_rate: Math.round((w.base_rate || 0.3) * 100),
          word_rate: Math.round((w.word_rate || 0.4) * 100),
          similarity: Math.round((w.similarity || 0.3) * 100),
        });
      }
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const handleWeightChange = (key, val) => {
    const newVal = Math.max(10, Math.min(80, val));
    const remaining = 100 - newVal;
    const otherKeys = Object.keys(weights).filter(k => k !== key);
    const otherTotal = otherKeys.reduce((s, k) => s + weights[k], 0);
    const newWeights = { ...weights, [key]: newVal };
    if (otherTotal > 0) {
      otherKeys.forEach(k => {
        newWeights[k] = Math.max(10, Math.round(weights[k] / otherTotal * remaining));
      });
      // Fix rounding errors
      const diff = 100 - Object.values(newWeights).reduce((s, v) => s + v, 0);
      if (diff !== 0) newWeights[otherKeys[0]] += diff;
    }
    setWeights(newWeights);
  };

  const saveWeights = async () => {
    setSavingWeights(true);
    try {
      const result = await api.post('/api/calibrate/weights', {
        base_rate: weights.base_rate / 100,
        word_rate: weights.word_rate / 100,
        similarity: weights.similarity / 100,
      });
      setMessage(result.data.message || 'Ponderi salvate!');
      setMessageType('success');
      await fetchStatus();
      if (onCalibrationChange) onCalibrationChange();
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Eroare la salvare ponderi');
      setMessageType('error');
    } finally {
      setSavingWeights(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleCalibrate = async () => {
    setCalibrating(true);
    setMessage('');
    setComparison(null);
    try {
      const result = await triggerCalibration();

      if (result.comparison) {
        setComparison(result.comparison);
      }

      if (result.status === 'rejected') {
        setMessage(result.message || 'Calibrare respinsă — nu a trecut verificările.');
        setMessageType('warning');
      } else {
        setMessage(result.message || 'Calibrare completă!');
        setMessageType('success');
      }
      await fetchStatus();
      if (onCalibrationChange) onCalibrationChange();
    } catch (err) {
      const detail = err.response?.data?.detail || 'Eroare la calibrare. Verificați backend-ul.';
      setMessage(detail);
      setMessageType('error');
    } finally {
      setCalibrating(false);
    }
  };

  const handleRevert = async () => {
    setReverting(true);
    setMessage('');
    setComparison(null);
    try {
      const result = await revertCalibration();
      setMessage(result.message || 'Calibrare restaurată.');
      setMessageType('success');
      await fetchStatus();
      if (onCalibrationChange) onCalibrationChange();
    } catch (err) {
      setMessage('Eroare la restaurare.');
      setMessageType('error');
    } finally {
      setReverting(false);
    }
  };

  const handleReset = async () => {
    setReverting(true);
    setMessage('');
    setComparison(null);
    try {
      const result = await resetCalibration();
      setMessage(result.message || 'Resetat la valori implicite.');
      setMessageType('success');
      await fetchStatus();
      if (onCalibrationChange) onCalibrationChange();
    } catch {
      setMessage('Eroare la resetare.');
      setMessageType('error');
    } finally {
      setReverting(false);
    }
  };

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-primary-400" size={24} />
      </div>
    );
  }

  const lastCalibrated = status?.last_calibrated
    ? new Date(status.last_calibrated).toLocaleString('ro-RO')
    : 'Niciodată';

  const msgColors = {
    info: 'bg-primary-500/10 border-primary-500/20 text-primary-400',
    success: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    error: 'bg-red-500/10 border-red-500/20 text-red-400',
    warning: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
  };

  return (
    <div className="card">
      {/* Header with buttons */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h3 className="text-lg font-semibold text-slate-200">Stare Calibrare</h3>
        <div className="flex items-center gap-2">
          {/* Revert button */}
          {status?.has_backup && (
            <button
              onClick={handleRevert}
              disabled={reverting || calibrating}
              className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg
                bg-amber-500/10 border border-amber-500/30 text-amber-400
                hover:bg-amber-500/20 transition-colors disabled:opacity-50"
            >
              {reverting ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Undo2 size={14} />
              )}
              Revert
            </button>
          )}

          {/* Reset button */}
          {status?.is_calibrated && (
            <button
              onClick={handleReset}
              disabled={reverting || calibrating}
              className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg
                bg-slate-500/10 border border-slate-500/30 text-slate-400
                hover:bg-slate-500/20 transition-colors disabled:opacity-50"
            >
              <RotateCcw size={14} />
              Reset
            </button>
          )}

          {/* Calibrate button */}
          <button
            onClick={handleCalibrate}
            disabled={calibrating || reverting}
            className="btn-primary flex items-center gap-2"
          >
            {calibrating ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <RefreshCw size={16} />
            )}
            {calibrating ? 'Se calibrează...' : 'Recalibrează'}
          </button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        <div className="bg-slate-800/60 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Ultima calibrare</p>
          <p className="text-sm font-medium text-slate-200">{lastCalibrated}</p>
        </div>
        <div className="bg-slate-800/60 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Fișiere reper</p>
          <p className="text-sm font-medium text-slate-200">
            {status?.reference_count ?? '-'}
          </p>
        </div>
        <div className="bg-slate-800/60 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Acuratețe medie</p>
          <p className="text-sm font-medium text-slate-200">
            {status?.avg_accuracy != null ? `${(status.avg_accuracy * 100).toFixed(1)}%` : '-'}
          </p>
        </div>
      </div>

      {/* Status indicator */}
      <div
        className={`flex items-center gap-2 p-3 rounded-lg border ${
          status?.is_calibrated
            ? 'bg-emerald-500/10 border-emerald-500/20'
            : 'bg-amber-500/10 border-amber-500/20'
        }`}
      >
        {status?.is_calibrated ? (
          <CheckCircle2 size={16} className="text-emerald-400" />
        ) : (
          <AlertCircle size={16} className="text-amber-400" />
        )}
        <span className={`text-sm ${status?.is_calibrated ? 'text-emerald-400' : 'text-amber-400'}`}>
          {status?.is_calibrated
            ? 'Sistemul este calibrat'
            : 'Se folosesc valorile implicite (fără calibrare)'}
        </span>
      </div>

      {/* F8: Interactive weight sliders */}
      <div className="mt-4">
        <button onClick={() => setShowWeights(!showWeights)}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors">
          <Sliders size={14} /> Ajusteaza ponderi manual
        </button>
        {showWeights && (
          <div className="mt-3 bg-slate-800/60 rounded-lg p-4 space-y-3">
            {[
              { key: 'base_rate', label: 'Tarif de baza', color: 'bg-blue-500' },
              { key: 'word_rate', label: 'Tarif per cuvant', color: 'bg-green-500' },
              { key: 'similarity', label: 'Similaritate KNN', color: 'bg-purple-500' },
            ].map(({ key, label, color }) => (
              <div key={key} className="flex items-center gap-3">
                <span className="text-xs text-slate-400 w-32">{label}</span>
                <input type="range" min={10} max={80} value={weights[key]}
                  onChange={e => handleWeightChange(key, parseInt(e.target.value))}
                  className="flex-1 accent-blue-500 h-1.5" />
                <span className="text-xs font-mono text-slate-300 w-10 text-right">{weights[key]}%</span>
              </div>
            ))}
            <div className="flex items-center justify-between pt-2 border-t border-slate-700">
              <span className="text-xs text-slate-500">Total: {weights.base_rate + weights.word_rate + weights.similarity}%</span>
              <button onClick={saveWeights} disabled={savingWeights}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs disabled:opacity-50">
                {savingWeights ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />} Salveaza ponderi
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Comparison panel (after calibration) */}
      {comparison && (
        <div className="mt-4 border border-slate-700 rounded-lg overflow-hidden">
          <div className="bg-slate-800/80 px-4 py-3 flex items-center gap-2">
            {comparison.applied ? (
              <ShieldCheck size={16} className="text-emerald-400" />
            ) : (
              <ShieldAlert size={16} className="text-red-400" />
            )}
            <span className="text-sm font-semibold text-slate-200">
              {comparison.applied ? 'Calibrare aplicată' : 'Calibrare RESPINSĂ'}
            </span>
          </div>

          <div className="p-4 space-y-3">
            {/* Before → After comparison */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
              <div className="bg-slate-800/40 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">ÎNAINTE ({comparison.before.source})</p>
                <p className="text-sm text-slate-300">
                  MAPE: {comparison.before.mape != null ? `${comparison.before.mape}%` : 'N/A'}
                </p>
                <div className="text-xs text-slate-500 mt-1">
                  {Object.entries(comparison.before.weights).map(([k, v]) => (
                    <span key={k} className="mr-2">{k}: {(v * 100).toFixed(0)}%</span>
                  ))}
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight size={20} className="text-slate-600" />
              </div>

              <div className="bg-slate-800/40 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">DUPĂ (calibrare nouă)</p>
                <p className="text-sm text-slate-300">
                  MAPE: {comparison.after.mape}%
                  {' '}({comparison.after.within_10}/{comparison.after.total_files} sub 10%)
                </p>
                <div className="text-xs text-slate-500 mt-1">
                  {Object.entries(comparison.after.weights).map(([k, v]) => (
                    <span key={k} className="mr-2">{k}: {(v * 100).toFixed(0)}%</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Warnings */}
            {comparison.warnings && comparison.warnings.length > 0 && (
              <div className="space-y-1">
                {comparison.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-amber-400/80">
                    <AlertCircle size={12} className="mt-0.5 shrink-0" />
                    {w}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      {message && (
        <div className={`mt-3 p-3 border rounded-lg ${msgColors[messageType]}`}>
          <p className="text-sm">{message}</p>
        </div>
      )}
    </div>
  );
}
