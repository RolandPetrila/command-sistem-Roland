import React, { useState, useRef } from 'react';
import { Camera, X, Copy, Send, Loader2, StickyNote, Bot } from 'lucide-react';
import api from '../../api/client';

export default function FloatingOCR() {
  const [open, setOpen] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    setProcessing(true);
    setResult('');
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/api/ai/ocr-enhance', formData);
      setResult(data.enhanced_text || data.raw_text || data.text || '');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setProcessing(false);
  };

  const handlePaste = async (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) handleFile(file);
        return;
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer?.files?.[0];
    if (file && file.type.startsWith('image/')) handleFile(file);
  };

  const copyText = () => {
    navigator.clipboard.writeText(result);
  };

  // Keyboard shortcut: Ctrl+Shift+O
  React.useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'O') {
        e.preventDefault();
        setOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  if (!open) {
    return (
      <button onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-12 h-12 bg-purple-600 hover:bg-purple-700 rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110"
        title="OCR Rapid (Ctrl+Shift+O)">
        <Camera size={20} className="text-white" />
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
        onPaste={handlePaste} onDrop={handleDrop} onDragOver={e => e.preventDefault()}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Camera size={18} className="text-purple-400" />
            <span className="font-medium text-sm">OCR Rapid</span>
            <span className="text-xs text-gray-500">Ctrl+Shift+O</span>
          </div>
          <button onClick={() => { setOpen(false); setResult(''); setError(''); }}
            className="p-1.5 hover:bg-gray-800 rounded-lg"><X size={16} /></button>
        </div>

        {/* Drop zone */}
        <div className="p-5">
          {!result && !processing && (
            <div className="border-2 border-dashed border-gray-700 rounded-xl p-8 text-center cursor-pointer hover:border-purple-500 transition-colors"
              onClick={() => fileRef.current?.click()}>
              <Camera size={32} className="mx-auto mb-3 text-gray-500" />
              <p className="text-sm text-gray-400">Trage o imagine, lipește (Ctrl+V) sau click pentru a selecta</p>
              <p className="text-xs text-gray-600 mt-1">PNG, JPG, TIFF, BMP, WEBP, PDF</p>
              <input type="file" ref={fileRef} onChange={e => handleFile(e.target.files?.[0])} className="hidden"
                accept="image/*,.pdf" />
            </div>
          )}

          {processing && (
            <div className="flex flex-col items-center py-8">
              <Loader2 size={32} className="animate-spin text-purple-400 mb-3" />
              <p className="text-sm text-gray-400">Extrag text din imagine...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 text-sm text-red-400">
              ⚠️ {error}
            </div>
          )}

          {result && (
            <div className="space-y-3">
              <textarea value={result} onChange={e => setResult(e.target.value)}
                className="w-full h-48 bg-gray-800 border border-gray-700 rounded-xl p-3 text-sm resize-none focus:border-purple-500 focus:outline-none font-mono" />
              <div className="flex gap-2">
                <button onClick={copyText}
                  className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors">
                  <Copy size={14} /> Copiază
                </button>
                <button onClick={() => {
                  // Send to notepad via API
                  api.post('/api/notes', { title: 'OCR ' + new Date().toLocaleDateString('ro'), content: result }).catch(() => {});
                  setOpen(false); setResult('');
                }}
                  className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors">
                  <StickyNote size={14} /> Notepad
                </button>
                <button onClick={() => { setResult(''); setError(''); }}
                  className="ml-auto px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm">Altă imagine</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
