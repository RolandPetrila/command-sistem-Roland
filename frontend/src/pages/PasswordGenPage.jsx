import React, { useState, useCallback } from 'react';
import { KeyRound, Copy, Check, RefreshCw, Eye, EyeOff, Shield } from 'lucide-react';
import apiClient from '../api/client';

const STRENGTH_COLORS = {
  0: { bar: 'bg-red-500', text: 'text-red-400', label: 'Foarte slaba', width: 'w-1/5' },
  1: { bar: 'bg-orange-500', text: 'text-orange-400', label: 'Slaba', width: 'w-2/5' },
  2: { bar: 'bg-yellow-500', text: 'text-yellow-400', label: 'Medie', width: 'w-3/5' },
  3: { bar: 'bg-green-500', text: 'text-green-400', label: 'Puternica', width: 'w-4/5' },
  4: { bar: 'bg-emerald-400', text: 'text-emerald-400', label: 'Foarte puternica', width: 'w-full' },
};

export default function PasswordGenPage() {
  const [password, setPassword] = useState('');
  const [strength, setStrength] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showPassword, setShowPassword] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Generator settings
  const [length, setLength] = useState(20);
  const [uppercase, setUppercase] = useState(true);
  const [lowercase, setLowercase] = useState(true);
  const [digits, setDigits] = useState(true);
  const [symbols, setSymbols] = useState(true);
  const [excludeAmbiguous, setExcludeAmbiguous] = useState(false);

  // Check strength for custom password
  const [customPassword, setCustomPassword] = useState('');
  const [customStrength, setCustomStrength] = useState(null);
  const [checkingStrength, setCheckingStrength] = useState(false);

  const generate = useCallback(async () => {
    setLoading(true);
    setError('');
    setCopied(false);
    try {
      const res = await apiClient.post('/api/tools/generate-password', {
        length,
        uppercase,
        lowercase,
        digits,
        symbols,
        exclude_ambiguous: excludeAmbiguous,
      });
      setPassword(res.data.password);
      setStrength(res.data.strength);
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la generare');
      setPassword('');
      setStrength(null);
    } finally {
      setLoading(false);
    }
  }, [length, uppercase, lowercase, digits, symbols, excludeAmbiguous]);

  const copyToClipboard = useCallback(async () => {
    if (!password) return;
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for non-HTTPS
      const el = document.createElement('textarea');
      el.value = password;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [password]);

  const checkStrength = useCallback(async () => {
    if (!customPassword.trim()) return;
    setCheckingStrength(true);
    try {
      const res = await apiClient.post('/api/tools/check-password-strength', {
        password: customPassword,
      });
      setCustomStrength(res.data);
    } catch {
      setCustomStrength(null);
    } finally {
      setCheckingStrength(false);
    }
  }, [customPassword]);

  const strengthInfo = strength ? STRENGTH_COLORS[strength.score] || STRENGTH_COLORS[0] : null;
  const customStrengthInfo = customStrength ? STRENGTH_COLORS[customStrength.score] || STRENGTH_COLORS[0] : null;

  const toggleClass = (active) =>
    `relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer ${active ? 'bg-primary-600' : 'bg-slate-600'}`;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Generator Card */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
          <KeyRound className="w-5 h-5 text-primary-400" />
          Generator Parole
        </h2>

        {/* Password display */}
        <div className="bg-slate-900 rounded-lg p-4 mb-4 flex items-center gap-3">
          <p
            className={`flex-1 font-mono text-lg break-all ${
              password ? 'text-white' : 'text-slate-600'
            } ${!showPassword && password ? 'tracking-widest' : ''}`}
          >
            {!password
              ? 'Apasa "Genereaza" pentru o parola noua...'
              : showPassword
              ? password
              : '\u2022'.repeat(Math.min(password.length, 30))}
          </p>
          {password && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setShowPassword(!showPassword)}
                className="p-2 text-slate-400 hover:text-white transition-colors rounded"
                title={showPassword ? 'Ascunde' : 'Arata'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
              <button
                onClick={copyToClipboard}
                className="p-2 text-slate-400 hover:text-primary-400 transition-colors rounded"
                title="Copiaza"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          )}
        </div>

        {/* Strength bar */}
        {strengthInfo && (
          <div className="mb-5">
            <div className="flex items-center justify-between mb-1.5">
              <span className={`text-sm font-medium ${strengthInfo.text}`}>
                {strengthInfo.label}
              </span>
              <span className="text-xs text-slate-500">
                {strength.entropy_bits} bits entropie
              </span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${strengthInfo.bar} ${strengthInfo.width} rounded-full transition-all duration-500`}
              />
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs text-slate-500">
                Timp estimat spargere: {strength.crack_time_display}
              </span>
            </div>
          </div>
        )}

        {error && (
          <p className="text-red-400 text-sm mb-4">{error}</p>
        )}

        {/* Settings */}
        <div className="space-y-4 mb-5">
          {/* Length slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-slate-300">Lungime</label>
              <span className="text-sm font-mono text-primary-400 bg-slate-800 px-2 py-0.5 rounded">
                {length}
              </span>
            </div>
            <input
              type="range"
              min={8}
              max={128}
              value={length}
              onChange={(e) => setLength(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-500
                [&::-webkit-slider-thumb]:hover:bg-primary-400 [&::-webkit-slider-thumb]:transition-colors"
            />
            <div className="flex justify-between text-[10px] text-slate-600 mt-1">
              <span>8</span>
              <span>32</span>
              <span>64</span>
              <span>128</span>
            </div>
          </div>

          {/* Toggles */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Litere mari (A-Z)', value: uppercase, setter: setUppercase },
              { label: 'Litere mici (a-z)', value: lowercase, setter: setLowercase },
              { label: 'Cifre (0-9)', value: digits, setter: setDigits },
              { label: 'Simboluri (!@#$)', value: symbols, setter: setSymbols },
            ].map(({ label, value, setter }) => (
              <label key={label} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 cursor-pointer">
                <span className="text-sm text-slate-300">{label}</span>
                <div
                  className={toggleClass(value)}
                  onClick={() => setter(!value)}
                >
                  <div
                    className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${
                      value ? 'translate-x-5' : ''
                    }`}
                  />
                </div>
              </label>
            ))}
          </div>

          {/* Exclude ambiguous */}
          <label className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 cursor-pointer">
            <div>
              <span className="text-sm text-slate-300">Exclude ambigue</span>
              <p className="text-[10px] text-slate-500 mt-0.5">Elimina: 0, O, 1, l, I, |</p>
            </div>
            <div
              className={toggleClass(excludeAmbiguous)}
              onClick={() => setExcludeAmbiguous(!excludeAmbiguous)}
            >
              <div
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${
                  excludeAmbiguous ? 'translate-x-5' : ''
                }`}
              />
            </div>
          </label>
        </div>

        {/* Generate button */}
        <button
          onClick={generate}
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Se genereaza...' : 'Genereaza Parola'}
        </button>
      </div>

      {/* Check existing password */}
      <div className="card p-6">
        <h3 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 text-cyan-400" />
          Verifica forta unei parole existente
        </h3>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={customPassword}
            onChange={(e) => {
              setCustomPassword(e.target.value);
              setCustomStrength(null);
            }}
            onKeyDown={(e) => e.key === 'Enter' && checkStrength()}
            placeholder="Introdu parola de verificat..."
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-primary-500 focus:outline-none transition-colors"
          />
          <button
            onClick={checkStrength}
            disabled={checkingStrength || !customPassword.trim()}
            className="btn-secondary px-4 py-2 text-sm whitespace-nowrap"
          >
            {checkingStrength ? 'Se verifica...' : 'Verifica'}
          </button>
        </div>

        {customStrengthInfo && customStrength && (
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-medium ${customStrengthInfo.text}`}>
                {customStrengthInfo.label}
              </span>
              <span className="text-xs text-slate-500">
                Scor: {customStrength.score}/4
              </span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden mb-3">
              <div
                className={`h-full ${customStrengthInfo.bar} ${customStrengthInfo.width} rounded-full transition-all duration-500`}
              />
            </div>
            <div className="space-y-1.5">
              <p className="text-xs text-slate-400">
                Entropie: {customStrength.entropy_bits} bits
              </p>
              <p className="text-xs text-slate-400">
                Timp spargere: {customStrength.crack_time_display}
              </p>
              {customStrength.feedback.length > 0 && (
                <div className="mt-2 space-y-1">
                  {customStrength.feedback.map((fb, i) => (
                    <p key={i} className="text-xs text-slate-400 flex items-start gap-1.5">
                      <span className="text-yellow-500 mt-0.5">&#8226;</span>
                      {fb}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
