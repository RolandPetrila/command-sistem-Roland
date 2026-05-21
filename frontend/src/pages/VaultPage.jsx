import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { KeyRound, Plus, Trash2, Eye, EyeOff, Lock, Unlock, ShieldCheck, CheckCircle, XCircle, Loader2, Download, Upload, AlertTriangle, Calendar, Copy, Check } from 'lucide-react';
import apiClient from '../api/client';

const PROVIDERS = ['generic', 'deepl', 'google', 'github', 'openai', 'azure', 'groq', 'gemini', 'cerebras', 'mistral'];

function getPasswordStrength(pw) {
  const checks = {
    min_length: pw.length >= 12,
    has_upper: /[A-Z]/.test(pw),
    has_lower: /[a-z]/.test(pw),
    has_digit: /\d/.test(pw),
  };
  const passed = Object.values(checks).filter(Boolean).length;
  let score = 'weak';
  if (passed === 4) score = 'strong';
  else if (passed >= 2 && pw.length >= 8) score = 'moderate';
  return { score, checks };
}

const STRENGTH_COLORS = { weak: 'bg-red-500', moderate: 'bg-yellow-500', strong: 'bg-emerald-500' };
const STRENGTH_LABELS = { weak: 'Slaba', moderate: 'Moderata', strong: 'Puternica' };
const STRENGTH_TEXT_COLORS = { weak: 'text-red-400', moderate: 'text-yellow-400', strong: 'text-emerald-400' };

function StrengthBar({ password }) {
  if (!password) return null;
  const { score, checks } = getPasswordStrength(password);
  const widths = { weak: 'w-1/3', moderate: 'w-2/3', strong: 'w-full' };
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-400">Putere parola</span>
        <span className={`text-xs font-medium ${STRENGTH_TEXT_COLORS[score]}`}>{STRENGTH_LABELS[score]}</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-300 ${STRENGTH_COLORS[score]} ${widths[score]}`} />
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1 text-xs">
        <span className={checks.min_length ? 'text-emerald-400' : 'text-slate-500'}>{checks.min_length ? '\u2713' : '\u2717'} Min. 12 caractere</span>
        <span className={checks.has_upper ? 'text-emerald-400' : 'text-slate-500'}>{checks.has_upper ? '\u2713' : '\u2717'} Litera mare (A-Z)</span>
        <span className={checks.has_lower ? 'text-emerald-400' : 'text-slate-500'}>{checks.has_lower ? '\u2713' : '\u2717'} Litera mica (a-z)</span>
        <span className={checks.has_digit ? 'text-emerald-400' : 'text-slate-500'}>{checks.has_digit ? '\u2713' : '\u2717'} Cifra (0-9)</span>
      </div>
    </div>
  );
}

function isExpiringSoon(expiresAt) {
  if (!expiresAt) return false;
  const diff = new Date(expiresAt) - new Date();
  return diff > 0 && diff < 7 * 24 * 60 * 60 * 1000;
}

function isExpired(expiresAt) {
  if (!expiresAt) return false;
  return new Date(expiresAt) < new Date();
}

function VaultUsageOverview() {
  const [usage, setUsage] = useState([]);
  useEffect(() => {
    apiClient.get('/api/vault/usage-overview').then(r => setUsage(r.data.providers || []))
      .catch(() => setUsage([]));
  }, []);
  if (usage.length === 0) return null;
  return (
    <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5 mb-4">
      <h3 className="text-sm font-medium text-gray-300 mb-3">Utilizare Free Tier</h3>
      {usage.map(u => {
        const pct = Math.min(100, Math.round((u.used / Math.max(u.limit, 1)) * 100));
        const color = pct < 50 ? 'bg-green-500' : pct < 80 ? 'bg-yellow-500' : 'bg-red-500';
        return (
          <div key={u.provider} className="mb-2">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{u.provider}</span>
              <span>{u.used?.toLocaleString()} / {u.limit?.toLocaleString()} {u.unit} ({pct}%)</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-1.5">
              <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function VaultPage() {
  const [configured, setConfigured] = useState(null); // null=loading, true/false
  const [unlocked, setUnlocked] = useState(false);
  const [masterPw, setMasterPw] = useState('');
  const [sessionToken, setSessionToken] = useState(''); // SEC-11: session token from unlock
  const [keys, setKeys] = useState([]);
  const [error, setError] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newKey, setNewKey] = useState({ name: '', value: '', provider: 'generic', expires_at: '' });
  const [revealedKey, setRevealedKey] = useState(null);
  const [revealedValue, setRevealedValue] = useState('');
  // R3-43: Test key
  const [testingKey, setTestingKey] = useState(null);
  const [testResult, setTestResult] = useState({});
  // R4-02: Backup/Restore
  const [restoring, setRestoring] = useState(false);
  // R4-03: Expiring keys
  const [expiringKeys, setExpiringKeys] = useState([]);
  // QUAL-31: Copy feedback
  const [copiedKey, setCopiedKey] = useState(null);

  // SEC-11: Build auth header — prefer session token over master password
  const authHeader = useCallback(() => {
    if (sessionToken) return { 'x-vault-session': sessionToken };
    return { 'x-master-password': masterPw };
  }, [sessionToken, masterPw]);

  // Check vault status
  useEffect(() => {
    apiClient.get('/api/vault/status')
      .then(({ data }) => setConfigured(data.configured))
      .catch(() => setConfigured(false));
  }, []);

  const loadKeys = useCallback(async () => {
    try {
      const { data } = await apiClient.get('/api/vault/keys');
      setKeys(data);
    } catch (err) {
      console.error('Failed to load keys:', err);
    }
    try {
      const { data } = await apiClient.get('/api/vault/keys/expiring');
      setExpiringKeys(data);
    } catch {
      /* toast handles it */
    }
  }, []);

  // Setup master password
  const handleSetup = async () => {
    setError('');
    const strength = getPasswordStrength(masterPw);
    if (strength.score === 'weak') {
      setError('Parola prea slaba. Trebuie: min. 12 caractere, litera mare, litera mica, cifra.');
      return;
    }
    try {
      await apiClient.post('/api/vault/setup', { master_password: masterPw });
      setConfigured(true);
      // SEC-11: get session token immediately after setup
      const { data: unlockData } = await apiClient.post('/api/vault/unlock', { master_password: masterPw });
      setSessionToken(unlockData.session_token || '');
      setUnlocked(true);
      await loadKeys();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la configurare');
    }
  };

  // Unlock vault
  const handleUnlock = async () => {
    setError('');
    try {
      // SEC-11: store session token so subsequent requests use it instead of master password
      const { data } = await apiClient.post('/api/vault/unlock', { master_password: masterPw });
      setSessionToken(data.session_token || '');
      setUnlocked(true);
      await loadKeys();
    } catch (err) {
      setError(err.response?.data?.detail || 'Parolă incorectă');
    }
  };

  // Add key
  const handleAddKey = async () => {
    setError('');
    if (!newKey.name || !newKey.value) {
      setError('Nume și valoare sunt obligatorii');
      return;
    }
    try {
      const payload = { ...newKey };
      if (!payload.expires_at) delete payload.expires_at;
      await apiClient.post('/api/vault/keys', payload, {
        headers: authHeader(),
      });
      setNewKey({ name: '', value: '', provider: 'generic', expires_at: '' });
      setShowAdd(false);
      await loadKeys();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la salvare');
    }
  };

  // Reveal key value
  const handleReveal = async (name) => {
    if (revealedKey === name) {
      setRevealedKey(null);
      setRevealedValue('');
      return;
    }
    try {
      const { data } = await apiClient.get(`/api/vault/keys/${name}`, {
        headers: authHeader(),
      });
      setRevealedKey(name);
      setRevealedValue(data.value);
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la decriptare');
    }
  };

  // QUAL-31: Copy key value to clipboard with visual feedback
  const handleCopy = async (name, value) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(name);
      setTimeout(() => setCopiedKey(null), 2000);
    } catch {
      /* silent — clipboard not available */
    }
  };

  // R3-43: Test key
  const handleTestKey = async (name) => {
    setTestingKey(name);
    setTestResult(prev => ({ ...prev, [name]: null }));
    try {
      const { data } = await apiClient.post(`/api/vault/keys/${name}/test`, {}, {
        headers: authHeader(),
      });
      setTestResult(prev => ({ ...prev, [name]: data.success !== false ? 'ok' : 'fail' }));
    } catch {
      setTestResult(prev => ({ ...prev, [name]: 'fail' }));
    }
    setTestingKey(null);
  };

  // Delete key (R3-57: with confirmation + confirm=true param)
  const handleDelete = async (name) => {
    if (!window.confirm(`Sigur stergi cheia "${name}"?`)) return;
    try {
      await apiClient.delete(`/api/vault/keys/${name}`, {
        params: { confirm: true },
        headers: authHeader(),
      });
      if (revealedKey === name) {
        setRevealedKey(null);
        setRevealedValue('');
      }
      await loadKeys();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la ștergere');
    }
  };

  // R4-02: Backup vault
  const handleBackup = async () => {
    try {
      const { data } = await apiClient.get('/api/vault/backup', {
        headers: authHeader(),
      });
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vault_backup_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la backup');
    }
  };

  // R4-02: Restore vault
  const handleRestore = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      setRestoring(true);
      setError('');
      try {
        const text = await file.text();
        const backup = JSON.parse(text);
        const { data } = await apiClient.post('/api/vault/restore', { backup }, {
          headers: authHeader(),
        });
        setError('');
        await loadKeys();
        alert(`Restaurare completa: ${data.imported} importate, ${data.skipped} sarite (duplicate).`);
      } catch (err) {
        setError(err.response?.data?.detail || 'Eroare la restaurare — format invalid?');
      }
      setRestoring(false);
    };
    input.click();
  };

  // Loading state
  if (configured === null) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  // Setup or Unlock screen
  if (!configured || !unlocked) {
    return (
      <div className="max-w-md mx-auto mt-16">
        <div className="card p-8 text-center">
          <div className="w-16 h-16 bg-primary-600/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <KeyRound className="w-8 h-8 text-primary-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">
            {configured ? 'Deblochează Vault' : 'Configurare Vault'}
          </h2>
          <p className="text-slate-400 text-sm mb-6">
            {configured
              ? 'Introdu master password pentru a accesa cheile API.'
              : 'Setează un master password pentru a proteja cheile API.'}
          </p>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4 text-red-400 text-sm">
              {error}
            </div>
          )}

          <input
            type="password"
            value={masterPw}
            onChange={(e) => setMasterPw(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (configured ? handleUnlock() : handleSetup())}
            placeholder="Master password..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white text-center focus:border-primary-500 focus:outline-none mb-4"
            autoFocus
          />

          {!configured && <StrengthBar password={masterPw} />}

          <button
            onClick={configured ? handleUnlock : handleSetup}
            className="btn-primary w-full py-3 flex items-center justify-center gap-2"
          >
            {configured ? <Unlock className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
            {configured ? 'Deblochează' : 'Configurează Vault'}
          </button>
        </div>
      </div>
    );
  }

  // Main vault view
  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <VaultUsageOverview />
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 text-emerald-400 text-sm">
          <Lock className="w-4 h-4" />
          <span>Vault deblocat</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleBackup}
            className="flex items-center gap-1.5 text-sm py-2 px-3 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            title="Backup vault"
          >
            <Download className="w-4 h-4" />
            Backup
          </button>
          <button
            onClick={handleRestore}
            disabled={restoring}
            className="flex items-center gap-1.5 text-sm py-2 px-3 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            title="Restaureaza din backup"
          >
            {restoring ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            Restore
          </button>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="btn-primary flex items-center gap-2 text-sm py-2 px-4"
          >
            <Plus className="w-4 h-4" />
            Cheie noua
          </button>
        </div>
      </div>

      {/* R4-03: Expiring keys warning banner */}
      {expiringKeys.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-yellow-300 text-sm font-medium">Chei care expira curand</p>
            <ul className="mt-1 space-y-0.5">
              {expiringKeys.map((ek) => (
                <li key={ek.name} className="text-yellow-400/80 text-xs">
                  {ek.name} ({ek.provider}) — expira {ek.expires_at}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Add key form */}
      {showAdd && (
        <div className="card p-4 space-y-3 border border-primary-500/30">
          <div className="grid grid-cols-2 gap-3">
            <input
              value={newKey.name}
              onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
              placeholder="Nume cheie (ex: deepl_api_key)"
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none"
            />
            <select
              value={newKey.provider}
              onChange={(e) => setNewKey({ ...newKey, provider: e.target.value })}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none"
            >
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
              ))}
            </select>
          </div>
          <input
            type="password"
            value={newKey.value}
            onChange={(e) => setNewKey({ ...newKey, value: e.target.value })}
            placeholder="Valoare cheie API..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none font-mono"
          />
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-500" />
            <input
              type="date"
              value={newKey.expires_at}
              onChange={(e) => setNewKey({ ...newKey, expires_at: e.target.value })}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none flex-1"
            />
            <span className="text-xs text-slate-500">Data expirare (optional)</span>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowAdd(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">
              Anulează
            </button>
            <button onClick={handleAddKey} className="btn-primary px-4 py-2 text-sm">
              Salvează
            </button>
          </div>
        </div>
      )}

      {/* Keys list */}
      {keys.length === 0 ? (
        <div className="card p-12 text-center">
          <KeyRound className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Nicio cheie API stocată</p>
          <p className="text-slate-500 text-sm mt-1">Apasă "Cheie nouă" pentru a adăuga prima cheie</p>
        </div>
      ) : (
        <div className="space-y-2">
          {keys.map((k) => (
            <div key={k.name} className="card p-4 flex items-center gap-4">
              <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center shrink-0">
                <KeyRound className="w-5 h-5 text-primary-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-white font-medium text-sm truncate">{k.name}</span>
                  <span className="text-xs px-2 py-0.5 bg-slate-800 rounded-full text-slate-400">
                    {k.provider}
                  </span>
                  {k.expires_at && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${isExpired(k.expires_at) ? 'bg-red-500/20 text-red-400' : isExpiringSoon(k.expires_at) ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-800 text-slate-400'}`}>
                      {isExpired(k.expires_at) ? 'Expirata' : `Exp: ${k.expires_at}`}
                    </span>
                  )}
                </div>
                {revealedKey === k.name ? (
                  <div className="flex items-center gap-2 mt-1">
                    <code className="text-emerald-400 text-xs font-mono truncate flex-1">
                      {revealedValue}
                    </code>
                    {copiedKey === k.name && (
                      <span className="text-emerald-400 text-xs shrink-0">Copiat!</span>
                    )}
                  </div>
                ) : (
                  <span className="text-slate-500 text-xs mt-1 block">••••••••••••••••</span>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => handleTestKey(k.name)}
                  disabled={testingKey === k.name}
                  className={`p-2 transition-colors ${testResult[k.name] === 'ok' ? 'text-green-400' : testResult[k.name] === 'fail' ? 'text-red-400' : 'text-slate-400 hover:text-emerald-400'}`}
                  title="Verifica cheia"
                >
                  {testingKey === k.name ? <Loader2 className="w-4 h-4 animate-spin" /> : testResult[k.name] === 'ok' ? <CheckCircle className="w-4 h-4" /> : testResult[k.name] === 'fail' ? <XCircle className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => handleReveal(k.name)}
                  className="p-2 text-slate-400 hover:text-primary-400 transition-colors"
                  title={revealedKey === k.name ? 'Ascunde' : 'Arată valoarea'}
                >
                  {revealedKey === k.name ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                {revealedKey === k.name && (
                  <button
                    onClick={() => handleCopy(k.name, revealedValue)}
                    className={`p-2 transition-colors ${copiedKey === k.name ? 'text-emerald-400' : 'text-slate-400 hover:text-emerald-400'}`}
                    title="Copiaza valoarea"
                  >
                    {copiedKey === k.name ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                )}
                <button
                  onClick={() => handleDelete(k.name)}
                  className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                  title="Șterge"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
