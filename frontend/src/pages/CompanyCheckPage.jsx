import React, { useState } from 'react';
import { Search, Building2, MapPin, Phone, FileCheck, Loader2, AlertCircle } from 'lucide-react';
import api from '../api/client';

export default function CompanyCheckPage() {
  const [cui, setCui] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleCheck = async () => {
    const cleaned = cui.trim().replace(/\D/g, '');
    if (!cleaned) {
      setError('Introdu un CUI valid (doar cifre).');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const { data } = await api.get(`/api/quick-tools/company-check/${cleaned}`);
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 404) {
        setError('CUI negasit. Verifica daca numarul este corect.');
      } else if (detail) {
        setError(typeof detail === 'string' ? detail : 'Eroare la verificare. Incearca din nou.');
      } else {
        setError('Eroare de conexiune. Verifica daca backend-ul este pornit.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Building2 size={28} className="text-blue-400" />
          Verificare Firma (ANAF)
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Verifica date publice despre o firma din Romania dupa CUI
        </p>
      </div>

      {/* Search */}
      <div className="bg-gray-900 rounded-xl p-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              value={cui}
              onChange={e => setCui(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCheck()}
              placeholder="Introdu CUI (ex: 43978110)"
              className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleCheck}
            disabled={loading || !cui.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-medium transition-colors"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Verifica
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 bg-red-900/30 border border-red-700/50 rounded-xl p-4 text-red-300 text-sm">
          <AlertCircle size={18} className="flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-gray-900 rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2 text-blue-400">
            <FileCheck size={20} />
            Rezultat verificare
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow icon={Building2} label="Denumire" value={result.denumire || result.name || '-'} />
            <InfoRow icon={MapPin} label="Adresa" value={result.adresa || result.address || '-'} />
            <InfoRow icon={Phone} label="Telefon" value={result.telefon || result.phone || '-'} />
            <InfoRow icon={MapPin} label="Cod Postal" value={result.cod_postal || result.postal_code || '-'} />
            <InfoRow icon={FileCheck} label="Stare" value={result.stare || result.status || '-'} highlight />
            <InfoRow
              icon={FileCheck}
              label="TVA"
              value={result.tva !== undefined ? (result.tva ? 'Da' : 'Nu') : (result.vat ? 'Da' : 'Nu')}
              highlight
            />
          </div>

          {(result.data_verificare || result.verification_date) && (
            <div className="text-xs text-gray-500 pt-2 border-t border-gray-800">
              Data verificare: {result.data_verificare || result.verification_date}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function InfoRow({ icon: Icon, label, value, highlight }) {
  return (
    <div className="flex items-start gap-3 bg-gray-800/50 rounded-lg p-3">
      <Icon size={16} className="text-gray-500 mt-0.5 flex-shrink-0" />
      <div>
        <div className="text-xs text-gray-500">{label}</div>
        <div className={`text-sm mt-0.5 ${highlight ? 'text-blue-300 font-medium' : 'text-gray-200'}`}>
          {value}
        </div>
      </div>
    </div>
  );
}
