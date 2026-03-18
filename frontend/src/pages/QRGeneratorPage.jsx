import React, { useState, useRef } from 'react';
import QRCode from 'react-qr-code';
import { Download, QrCode, Copy, Check } from 'lucide-react';

export default function QRGeneratorPage() {
  const [text, setText] = useState('');
  const [size, setSize] = useState(256);
  const [copied, setCopied] = useState(false);
  const qrRef = useRef(null);

  const handleDownload = () => {
    if (!text || !qrRef.current) return;
    const svg = qrRef.current.querySelector('svg');
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, size, size);
      ctx.drawImage(img, 0, 0, size, size);
      const link = document.createElement('a');
      link.download = 'qrcode.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  };

  const handleCopyDataUrl = () => {
    if (!text || !qrRef.current) return;
    const svg = qrRef.current.querySelector('svg');
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, size, size);
      ctx.drawImage(img, 0, 0, size, size);
      canvas.toBlob(blob => {
        navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      {/* Input */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <QrCode className="w-5 h-5 text-primary-400" />
          Generator QR Code
        </h2>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Introdu text sau URL... (ex: https://google.com)"
          className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white text-sm resize-none h-24 focus:border-primary-500 focus:outline-none transition-colors"
        />
        <div className="flex items-center gap-4 mt-3">
          <label className="text-sm text-slate-400">Dimensiune:</label>
          <select
            value={size}
            onChange={(e) => setSize(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:border-primary-500 focus:outline-none"
          >
            <option value={128}>128px</option>
            <option value={256}>256px (recomandat)</option>
            <option value={512}>512px</option>
          </select>
        </div>
      </div>

      {/* QR Preview */}
      {text && (
        <div className="card p-6 flex flex-col items-center gap-4">
          <div ref={qrRef} className="bg-white p-4 rounded-lg">
            <QRCode value={text} size={size} />
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleDownload}
              className="btn-primary flex items-center gap-2 px-4 py-2 text-sm"
            >
              <Download className="w-4 h-4" />
              Descarcă PNG
            </button>
            <button
              onClick={handleCopyDataUrl}
              className="btn-secondary flex items-center gap-2 px-4 py-2 text-sm"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copiat!' : 'Copiază'}
            </button>
          </div>
          <p className="text-xs text-slate-500 text-center max-w-sm">
            {text.length} caractere encoded
          </p>
        </div>
      )}
    </div>
  );
}
