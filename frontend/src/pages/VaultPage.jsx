import React, { useState, useEffect, useCallback } from 'react';
import { KeyRound, Plus, Trash2, Eye, EyeOff, Lock, Unlock, ShieldCheck } from 'lucide-react';
import apiClient from '../api/client';

const PROVIDERS = ['generic', 'deepl', 'google', 'github', 'openai', 'azure', 'groq'];

export default function VaultPage() {
  const [configured, setConfigured] = useState(null); // null=loading, true/false
  const [unlocked, setUnlocked] = useState(false);
  const [masterPw, setMasterPw] = useState('');
  const [keys, setKeys] = useState([]);
  const [error, setError] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newKey, setNewKey] = useState({ name: '', value: '', provider: 'generic' });
  const [revealedKey, setRevealedKey] = useState(null);
  const [revealedValue, setRevealedValue] = useState('');

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
  }, []);

  // Setup master password
  const handleSetup = async () => {
    setError('');
    if (masterPw.length < 4) {
      setError('Parola trebuie să aibă minim 4 caractere');
      return;
    }
    try {
      await apiClient.post('/api/vault/setup', { master_password: masterPw });
      setConfigured(true);
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
      await apiClient.post('/api/vault/unlock', { master_password: masterPw });
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
      await apiClient.post('/api/vault/keys', newKey, {
        headers: { 'x-master-password': masterPw },
      });
      setNewKey({ name: '', value: '', provider: 'generic' });
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
        headers: { 'x-master-password': masterPw },
      });
      setRevealedKey(name);
      setRevealedValue(data.value);
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la decriptare');
    }
  };

  // Delete key
  const handleDelete = async (name) => {
    try {
      await apiClient.delete(`/api/vault/keys/${name}`, {
        headers: { 'x-master-password': masterPw },
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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-emerald-400 text-sm">
          <Lock className="w-4 h-4" />
          <span>Vault deblocat</span>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="btn-primary flex items-center gap-2 text-sm py-2 px-4"
        >
          <Plus className="w-4 h-4" />
          Cheie nouă
        </button>
      </div>

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
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium text-sm truncate">{k.name}</span>
                  <span className="text-xs px-2 py-0.5 bg-slate-800 rounded-full text-slate-400">
                    {k.provider}
                  </span>
                </div>
                {revealedKey === k.name ? (
                  <code className="text-emerald-400 text-xs font-mono mt-1 block truncate">
                    {revealedValue}
                  </code>
                ) : (
                  <span className="text-slate-500 text-xs mt-1 block">••••••••••••••••</span>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => handleReveal(k.name)}
                  className="p-2 text-slate-400 hover:text-primary-400 transition-colors"
                  title={revealedKey === k.name ? 'Ascunde' : 'Arată valoarea'}
                >
                  {revealedKey === k.name ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
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
