import React, { useState, useCallback, useEffect } from 'react';
import { Barcode, Download, RefreshCw, Copy, Check } from 'lucide-react';
import apiClient from '../api/client';

const BARCODE_TYPES = [
  { id: 'code128', name: 'Code 128', desc: 'Alfanumeric universal', placeholder: 'Orice text (ex: ABC-123-xyz)' },
  { id: 'ean13', name: 'EAN-13', desc: 'Cod produs (magazin)', placeholder: 'Exact 12 sau 13 cifre (ex: 590123456789)' },
  { id: 'code39', name: 'Code 39', desc: 'Industrial alfanumeric', placeholder: 'Litere mari, cifre (ex: PROD-001)' },
  { id: 'qr', name: 'QR Code', desc: 'Cod matrice 2D', placeholder: 'Orice text sau URL (ex: https://google.com)' },
];

export default function BarcodePage() {
  const [data, setData] = useState('');
  const [barcodeType, setBarcodeType] = useState('code128');
  const [showText, setShowText] = useState(true);
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generated, setGenerated] = useState(false);
  const [copied, setCopied] = useState(false);

  // Cleanup blob URL on unmount or change
  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  const generate = useCallback(async () => {
    if (!data.trim()) {
      setError('Introdu textul de encodat');
      return;
    }

    setLoading(true);
    setError('');
    setGenerated(false);
    setCopied(false);

    // Cleanup previous blob
    if (imageUrl) {
      URL.revokeObjectURL(imageUrl);
      setImageUrl(null);
    }

    try {
      const res = await apiClient.post(
        '/api/tools/generate-barcode',
        {
          data: data.trim(),
          barcode_type: barcodeType,
          show_text: showText,
        },
        { responseType: 'blob' }
      );

      const blob = new Blob([res.data], { type: 'image/png' });
      const url = URL.createObjectURL(blob);
      setImageUrl(url);
      setGenerated(true);
    } catch (err) {
      if (err.response?.data) {
        try {
          const text = await err.response.data.text();
          const json = JSON.parse(text);
          setError(json.detail || 'Eroare la generare');
        } catch {
          setError('Eroare la generarea codului de bare');
        }
      } else {
        setError('Eroare de conexiune cu serverul');
      }
      setImageUrl(null);
    } finally {
      setLoading(false);
    }
  }, [data, barcodeType, showText, imageUrl]);

  const download = useCallback(() => {
    if (!imageUrl) return;
    const safe = data.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 20);
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `barcode_${barcodeType}_${safe}.png`;
    link.click();
  }, [imageUrl, barcodeType, data]);

  const copyImage = useCallback(async () => {
    if (!imageUrl) return;
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob }),
      ]);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: copy the data URL text
      try {
        await navigator.clipboard.writeText(data);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch {
        // toast handles it
      }
    }
  }, [imageUrl, data]);

  const selectedType = BARCODE_TYPES.find(t => t.id === barcodeType) || BARCODE_TYPES[0];

  return (
    <div className="max-w-xl mx-auto space-y-6">
      {/* Settings */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
          <Barcode className="w-5 h-5 text-primary-400" />
          Generator Coduri de Bare
        </h2>

        {/* Barcode type selector */}
        <div className="mb-4">
          <label className="text-sm text-slate-400 mb-2 block">Tip cod de bare</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {BARCODE_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => {
                  setBarcodeType(type.id);
                  setError('');
                  setGenerated(false);
                  setCopied(false);
                  if (imageUrl) {
                    URL.revokeObjectURL(imageUrl);
                    setImageUrl(null);
                  }
                }}
                className={`p-3 rounded-lg text-center transition-all border ${
                  barcodeType === type.id
                    ? 'border-primary-500 bg-primary-600/20 text-white'
                    : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:bg-slate-700/50 hover:text-slate-300'
                }`}
              >
                <p className="text-sm font-semibold">{type.name}</p>
                <p className="text-[10px] mt-0.5 opacity-70">{type.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Data input */}
        <div className="mb-4">
          <label className="text-sm text-slate-400 mb-2 block">
            Continut cod de bare
          </label>
          <input
            type="text"
            value={data}
            onChange={(e) => {
              setData(e.target.value);
              setError('');
            }}
            onKeyDown={(e) => e.key === 'Enter' && generate()}
            placeholder={selectedType.placeholder}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white text-sm font-mono focus:border-primary-500 focus:outline-none transition-colors"
            maxLength={500}
          />
          <p className="text-[10px] text-slate-600 mt-1">
            {barcodeType === 'ean13'
              ? 'EAN-13 accepta exact 12 cifre (checksum automat) sau 13 cifre'
              : barcodeType === 'code39'
              ? 'Code 39 accepta litere mari, cifre, spatii si simbolurile: - . $ / + %'
              : barcodeType === 'qr'
              ? 'QR Code accepta orice text, URL-uri, numere, etc.'
              : 'Code 128 accepta orice text alfanumeric'}
          </p>
        </div>

        {/* Show text toggle */}
        <label className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 mb-5 cursor-pointer">
          <span className="text-sm text-slate-300">Afiseaza textul sub cod</span>
          <div
            className={`relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer ${
              showText ? 'bg-primary-600' : 'bg-slate-600'
            }`}
            onClick={() => setShowText(!showText)}
          >
            <div
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${
                showText ? 'translate-x-5' : ''
              }`}
            />
          </div>
        </label>

        {error && (
          <p className="text-red-400 text-sm mb-4">{error}</p>
        )}

        {/* Generate button */}
        <button
          onClick={generate}
          disabled={loading || !data.trim()}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Se genereaza...' : 'Genereaza Cod de Bare'}
        </button>
      </div>

      {/* Preview */}
      {generated && imageUrl && (
        <div className="card p-6 flex flex-col items-center gap-4">
          <h3 className="text-sm font-medium text-slate-400">Previzualizare</h3>
          <div className="bg-white p-6 rounded-lg shadow-inner">
            <img
              src={imageUrl}
              alt={`Cod de bare ${barcodeType}: ${data}`}
              className="max-w-full h-auto"
              style={{ minHeight: 60, imageRendering: 'pixelated' }}
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={download}
              className="btn-primary flex items-center gap-2 px-4 py-2 text-sm"
            >
              <Download className="w-4 h-4" />
              Descarca PNG
            </button>
            <button
              onClick={copyImage}
              className="btn-secondary flex items-center gap-2 px-4 py-2 text-sm"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copiat!' : 'Copiaza Imaginea'}
            </button>
            <button
              onClick={generate}
              className="btn-secondary flex items-center gap-2 px-4 py-2 text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Regenereaza
            </button>
          </div>
          <p className="text-xs text-slate-500 text-center">
            {selectedType.name} &mdash; {data}
          </p>
        </div>
      )}

      {/* Info */}
      <div className="card p-4">
        <h3 className="text-sm font-medium text-slate-400 mb-2">Informatii tipuri</h3>
        <div className="space-y-2 text-xs text-slate-500">
          <p>
            <span className="text-slate-300 font-medium">Code 128</span> &mdash; Cel mai versatil. Accepta litere, cifre, simboluri. Ideal pentru etichete, inventar, logistica.
          </p>
          <p>
            <span className="text-slate-300 font-medium">EAN-13</span> &mdash; Standard international pentru produse de magazin. Necesita exact 12 sau 13 cifre.
          </p>
          <p>
            <span className="text-slate-300 font-medium">Code 39</span> &mdash; Standard industrial. Litere mari, cifre si cateva simboluri. Folosit in armata, sanatate, industrie.
          </p>
          <p>
            <span className="text-slate-300 font-medium">QR Code</span> &mdash; Cod matrice 2D. Accepta orice text sau URL. Ideal pentru link-uri, informatii de contact.
          </p>
        </div>
      </div>
    </div>
  );
}
