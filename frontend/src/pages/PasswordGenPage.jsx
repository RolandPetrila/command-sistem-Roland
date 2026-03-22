import React, { useState, useCallback, useEffect } from 'react';
import { KeyRound, Copy, Check, RefreshCw, Eye, EyeOff, Shield, BookOpen, Clock, Trash2 } from 'lucide-react';
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
  // R3-54: Tab mode — password vs passphrase
  const [mode, setMode] = useState('password'); // 'password' | 'passphrase'

  // Generator settings
  const [length, setLength] = useState(20);
  const [uppercase, setUppercase] = useState(true);
  const [lowercase, setLowercase] = useState(true);
  const [digits, setDigits] = useState(true);
  const [symbols, setSymbols] = useState(true);
  const [excludeAmbiguous, setExcludeAmbiguous] = useState(false);

  // R3-54: Passphrase settings
  const [ppWords, setPpWords] = useState(4);
  const [ppSeparator, setPpSeparator] = useState('-');
  const [ppResult, setPpResult] = useState(null);
  const [ppLoading, setPpLoading] = useState(false);

  // R3-56: Password history
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [revealedIdx, setRevealedIdx] = useState(null);
  const [copiedIdx, setCopiedIdx] = useState(null);

  // Check strength for custom password
  const [customPassword, setCustomPassword] = useState('');
  const [customStrength, setCustomStrength] = useState(null);
  const [checkingStrength, setCheckingStrength] = useState(false);

  // R3-56: Load password history (defined early for use in generate callbacks)
  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const { data } = await apiClient.get('/api/tools/password-history');
      setHistory(data.history || []);
    } catch {
      // toast handles it
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

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
      loadHistory();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la generare');
      setPassword('');
      setStrength(null);
    } finally {
      setLoading(false);
    }
  }, [length, uppercase, lowercase, digits, symbols, excludeAmbiguous, loadHistory]);

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

  // R3-54: Generate passphrase
  const generatePassphrase = useCallback(async () => {
    setPpLoading(true);
    setError('');
    setCopied(false);
    try {
      const { data } = await apiClient.get('/api/tools/generate-passphrase', {
        params: { words: ppWords, separator: ppSeparator },
      });
      setPpResult(data);
      setPassword(data.passphrase);
      setStrength(data.strength);
      loadHistory();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la generare fraza');
    } finally {
      setPpLoading(false);
    }
  }, [ppWords, ppSeparator, loadHistory]);

  // R3-56: Copy from history
  const copyHistoryItem = async (pw, idx) => {
    try {
      await navigator.clipboard.writeText(pw);
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    } catch {
      const el = document.createElement('textarea');
      el.value = pw;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    }
  };

  const strengthInfo = strength ? STRENGTH_COLORS[strength.score] || STRENGTH_COLORS[0] : null;
  const customStrengthInfo = customStrength ? STRENGTH_COLORS[customStrength.score] || STRENGTH_COLORS[0] : null;

  const toggleClass = (active) =>
    `relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer ${active ? 'bg-primary-600' : 'bg-slate-600'}`;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* R3-54: Mode tabs */}
      <div className="flex gap-1 bg-slate-800/60 rounded-lg p-1">
        {[
          { id: 'password', label: 'Parola', icon: KeyRound },
          { id: 'passphrase', label: 'Fraza-parola', icon: BookOpen },
        ].map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => { setMode(id); setError(''); }}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${mode === id ? 'bg-primary-600/30 text-primary-300' : 'text-slate-400 hover:text-slate-200'}`}>
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {/* Generator Card */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
          {mode === 'password' ? <KeyRound className="w-5 h-5 text-primary-400" /> : <BookOpen className="w-5 h-5 text-primary-400" />}
          {mode === 'password' ? 'Generator Parole' : 'Generator Fraze-Parola'}
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

        {/* Settings — password mode */}
        {mode === 'password' && (
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
        )}

        {/* R3-54: Settings — passphrase mode */}
        {mode === 'passphrase' && (
          <div className="space-y-4 mb-5">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-slate-300">Numar cuvinte</label>
                <span className="text-sm font-mono text-primary-400 bg-slate-800 px-2 py-0.5 rounded">
                  {ppWords}
                </span>
              </div>
              <input
                type="range" min={3} max={8} value={ppWords}
                onChange={(e) => setPpWords(Number(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-500
                  [&::-webkit-slider-thumb]:hover:bg-primary-400 [&::-webkit-slider-thumb]:transition-colors"
              />
              <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                <span>3</span><span>4</span><span>5</span><span>6</span><span>7</span><span>8</span>
              </div>
            </div>
            <div>
              <label className="text-sm text-slate-300 mb-2 block">Separator</label>
              <div className="flex gap-2">
                {['-', '.', '_', ' ', '+'].map(sep => (
                  <button key={sep} onClick={() => setPpSeparator(sep)}
                    className={`px-4 py-2 rounded-lg text-sm font-mono transition-colors border ${ppSeparator === sep ? 'border-primary-500 bg-primary-600/20 text-white' : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:text-slate-200'}`}>
                    {sep === ' ' ? '␣' : sep}
                  </button>
                ))}
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-xs text-slate-500">
              Fraza-parola = cuvinte romanesti + numar. Usor de memorat, greu de spart.
              Exemplu: <span className="text-primary-400 font-mono">castel-verde-munte-42</span>
            </div>
          </div>
        )}

        {/* Generate button */}
        <button
          onClick={mode === 'password' ? generate : generatePassphrase}
          disabled={loading || ppLoading}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
        >
          <RefreshCw className={`w-4 h-4 ${(loading || ppLoading) ? 'animate-spin' : ''}`} />
          {(loading || ppLoading) ? 'Se genereaza...' : mode === 'password' ? 'Genereaza Parola' : 'Genereaza Fraza-Parola'}
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

      {/* R3-56: Password history */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-md font-semibold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-400" />
            Parole recente (sesiune)
          </h3>
          <button onClick={loadHistory} disabled={historyLoading}
            className="text-xs text-slate-400 hover:text-primary-400 transition-colors">
            <RefreshCw className={`w-3.5 h-3.5 ${historyLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {history.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-4">
            Nicio parola generata in aceasta sesiune
          </p>
        ) : (
          <div className="space-y-2">
            {history.map((item, idx) => (
              <div key={idx} className="flex items-center gap-3 bg-slate-800/50 rounded-lg p-3">
                <div className="flex-1 min-w-0">
                  <p className={`font-mono text-sm truncate ${revealedIdx === idx ? 'text-white' : 'text-slate-500'}`}>
                    {revealedIdx === idx ? item.password : '\u2022'.repeat(Math.min(item.length || 16, 24))}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] text-slate-600">{item.strength_label}</span>
                    <span className="text-[10px] text-slate-600">{item.length} char</span>
                    <span className="text-[10px] text-slate-600">{item.timestamp}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button onClick={() => setRevealedIdx(revealedIdx === idx ? null : idx)}
                    className="p-1.5 text-slate-400 hover:text-primary-400 transition-colors" title="Arata/Ascunde">
                    {revealedIdx === idx ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                  <button onClick={() => copyHistoryItem(item.password, idx)}
                    className="p-1.5 text-slate-400 hover:text-primary-400 transition-colors" title="Copiaza">
                    {copiedIdx === idx ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
