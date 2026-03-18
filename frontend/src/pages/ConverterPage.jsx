import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import {
  FileText,
  Scissors,
  Layers,
  Image,
  Maximize2,
  Table,
  Archive,
  Type,
  Upload,
  Download,
  Loader2,
  X,
  CheckCircle,
  AlertCircle,
  Trash2,
  ArrowRight,
} from 'lucide-react';

const API = `${window.location.origin}/api/converter`;

const CONVERSIONS = [
  {
    id: 'pdf-to-docx',
    title: 'PDF \u2192 DOCX',
    desc: 'Document Word editabil din PDF',
    icon: FileText,
    accept: { 'application/pdf': ['.pdf'] },
    group: 'Documente',
    multi: false,
    color: 'blue',
  },
  {
    id: 'docx-to-pdf',
    title: 'DOCX \u2192 PDF',
    desc: 'Converteste Word in PDF',
    icon: FileText,
    accept: {
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    group: 'Documente',
    multi: false,
    color: 'red',
  },
  {
    id: 'merge-pdfs',
    title: 'Merge PDFs',
    desc: 'Combina mai multe PDF-uri intr-unul singur',
    icon: Layers,
    accept: { 'application/pdf': ['.pdf'] },
    group: 'Documente',
    multi: true,
    color: 'purple',
  },
  {
    id: 'split-pdf',
    title: 'Split PDF',
    desc: 'Extrage pagini individuale din PDF',
    icon: Scissors,
    accept: { 'application/pdf': ['.pdf'] },
    group: 'Documente',
    multi: false,
    color: 'amber',
    options: ['pages'],
  },
  {
    id: 'compress-images',
    title: 'Compresie Imagini',
    desc: 'Reduce dimensiunea fisierelor imagine',
    icon: Image,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.bmp'] },
    group: 'Imagini',
    multi: true,
    color: 'emerald',
    options: ['quality'],
  },
  {
    id: 'resize-images',
    title: 'Resize Imagini',
    desc: 'Redimensioneaza imagini la dimensiuni specifice',
    icon: Maximize2,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.bmp'] },
    group: 'Imagini',
    multi: true,
    color: 'cyan',
    options: ['dimensions'],
  },
  {
    id: 'csv-to-json',
    title: 'CSV \u2192 JSON',
    desc: 'Converteste CSV in format JSON',
    icon: Table,
    accept: { 'text/csv': ['.csv'] },
    group: 'Date',
    multi: false,
    color: 'orange',
  },
  {
    id: 'excel-to-json',
    title: 'Excel \u2192 JSON',
    desc: 'Extrage date din Excel in JSON',
    icon: Table,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    group: 'Date',
    multi: false,
    color: 'green',
  },
  {
    id: 'create-zip',
    title: 'Creare ZIP',
    desc: 'Comprima fisiere intr-o arhiva ZIP',
    icon: Archive,
    accept: {},
    group: 'Utilitati',
    multi: true,
    color: 'slate',
  },
  {
    id: 'extract-text',
    title: 'Extragere Text',
    desc: 'OCR — extrage text din PDF sau imagini',
    icon: Type,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'],
    },
    group: 'Utilitati',
    multi: false,
    color: 'indigo',
  },
];

const GROUPS = [...new Set(CONVERSIONS.map((c) => c.group))];

const COLOR_MAP = {
  blue: 'bg-blue-500/15 text-blue-400 border-blue-500/30 hover:bg-blue-500/25',
  red: 'bg-red-500/15 text-red-400 border-red-500/30 hover:bg-red-500/25',
  purple: 'bg-purple-500/15 text-purple-400 border-purple-500/30 hover:bg-purple-500/25',
  amber: 'bg-amber-500/15 text-amber-400 border-amber-500/30 hover:bg-amber-500/25',
  emerald: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/25',
  cyan: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30 hover:bg-cyan-500/25',
  orange: 'bg-orange-500/15 text-orange-400 border-orange-500/30 hover:bg-orange-500/25',
  green: 'bg-green-500/15 text-green-400 border-green-500/30 hover:bg-green-500/25',
  slate: 'bg-slate-500/15 text-slate-400 border-slate-500/30 hover:bg-slate-500/25',
  indigo: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30 hover:bg-indigo-500/25',
};

const ACTIVE_MAP = {
  blue: 'ring-2 ring-blue-500/50 bg-blue-500/25',
  red: 'ring-2 ring-red-500/50 bg-red-500/25',
  purple: 'ring-2 ring-purple-500/50 bg-purple-500/25',
  amber: 'ring-2 ring-amber-500/50 bg-amber-500/25',
  emerald: 'ring-2 ring-emerald-500/50 bg-emerald-500/25',
  cyan: 'ring-2 ring-cyan-500/50 bg-cyan-500/25',
  orange: 'ring-2 ring-orange-500/50 bg-orange-500/25',
  green: 'ring-2 ring-green-500/50 bg-green-500/25',
  slate: 'ring-2 ring-slate-500/50 bg-slate-500/25',
  indigo: 'ring-2 ring-indigo-500/50 bg-indigo-500/25',
};

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ConverterPage() {
  const [selected, setSelected] = useState(null);
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [options, setOptions] = useState({ quality: 80, width: 800, height: 0, pages: 'all' });

  const handleSelect = (conv) => {
    if (selected?.id === conv.id) {
      setSelected(null);
    } else {
      setSelected(conv);
      setFiles([]);
      setStatus('idle');
      setResult(null);
      setError('');
    }
  };

  const onDrop = useCallback(
    (accepted) => {
      if (!selected) return;
      if (selected.multi) {
        setFiles((prev) => [...prev, ...accepted]);
      } else {
        setFiles(accepted.slice(0, 1));
      }
      setStatus('idle');
      setResult(null);
      setError('');
    },
    [selected]
  );

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleConvert = async () => {
    if (!files.length || !selected) return;
    setStatus('converting');
    setError('');
    setResult(null);

    const formData = new FormData();
    if (selected.multi) {
      files.forEach((f) => formData.append('files', f));
    } else {
      formData.append('file', files[0]);
    }

    if (selected.options?.includes('quality')) {
      formData.append('quality', options.quality);
    }
    if (selected.options?.includes('dimensions')) {
      formData.append('width', options.width);
      formData.append('height', options.height);
      formData.append('keep_ratio', 'true');
    }
    if (selected.options?.includes('pages')) {
      formData.append('pages', options.pages);
    }

    try {
      const resp = await axios.post(`${API}/${selected.id}`, formData, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });

      const disposition = resp.headers['content-disposition'] || '';
      const match = disposition.match(/filename="(.+?)"/);
      const filename = match ? match[1] : `converted_${Date.now()}`;

      setResult({ blob: resp.data, filename, size: resp.data.size });
      setStatus('done');
    } catch (err) {
      let msg = 'Eroare la conversie';
      if (err.response?.data) {
        try {
          const text = await err.response.data.text();
          const parsed = JSON.parse(text);
          msg = parsed.detail || msg;
        } catch {
          // ignore parse errors
        }
      }
      setError(msg);
      setStatus('error');
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const url = URL.createObjectURL(result.blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.filename;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    a.remove();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: selected?.accept || {},
    multiple: selected?.multi || false,
    noClick: false,
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Conversion cards by group */}
      {GROUPS.map((group) => (
        <div key={group}>
          <h3 className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-2 px-1">
            {group}
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {CONVERSIONS.filter((c) => c.group === group).map((conv) => {
              const Icon = conv.icon;
              const isActive = selected?.id === conv.id;
              return (
                <button
                  key={conv.id}
                  onClick={() => handleSelect(conv)}
                  className={`flex flex-col items-start gap-1.5 p-3 rounded-xl border transition-all duration-200 text-left ${
                    COLOR_MAP[conv.color]
                  } ${isActive ? ACTIVE_MAP[conv.color] : 'border'}`}
                >
                  <div className="flex items-center gap-2">
                    <Icon size={16} />
                    <span className="font-medium text-sm">{conv.title}</span>
                  </div>
                  <p className="text-[11px] opacity-70 leading-tight">{conv.desc}</p>
                </button>
              );
            })}
          </div>
        </div>
      ))}

      {/* Active conversion panel */}
      {selected && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <selected.icon size={20} className="text-primary-400" />
              <h3 className="font-semibold text-lg">{selected.title}</h3>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          {/* Drop zone */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
              isDragActive
                ? 'border-primary-500 bg-primary-500/10'
                : 'border-slate-700 hover:border-slate-500 hover:bg-slate-800/30'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto mb-3 text-slate-500" size={32} />
            <p className="text-sm text-slate-300">
              {isDragActive
                ? 'Elibereaza pentru a incarca'
                : selected.multi
                ? 'Trage fisierele aici sau click pentru selectare'
                : 'Trage fisierul aici sau click pentru selectare'}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {Object.values(selected.accept)
                .flat()
                .join(', ')
                .toUpperCase() || 'Orice format'}
            </p>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="space-y-1.5">
              {files.map((f, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between bg-slate-800/50 rounded-lg px-3 py-2"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText size={14} className="text-slate-400 shrink-0" />
                    <span className="text-sm text-slate-200 truncate">{f.name}</span>
                    <span className="text-xs text-slate-500 shrink-0">{formatSize(f.size)}</span>
                  </div>
                  <button
                    onClick={() => removeFile(i)}
                    className="p-1 text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Options */}
          {selected.options?.includes('quality') && (
            <div className="flex items-center gap-4">
              <label className="text-sm text-slate-400 whitespace-nowrap">Calitate:</label>
              <input
                type="range"
                min={10}
                max={100}
                value={options.quality}
                onChange={(e) => setOptions((o) => ({ ...o, quality: +e.target.value }))}
                className="flex-1 accent-primary-500"
              />
              <span className="text-sm font-medium text-slate-200 w-10 text-right">
                {options.quality}%
              </span>
            </div>
          )}

          {selected.options?.includes('dimensions') && (
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-sm text-slate-400">Latime:</label>
              <input
                type="number"
                value={options.width}
                onChange={(e) => setOptions((o) => ({ ...o, width: +e.target.value }))}
                className="input-field w-24 text-center"
                min={0}
              />
              <span className="text-slate-500">px</span>
              <label className="text-sm text-slate-400 ml-2">Inaltime:</label>
              <input
                type="number"
                value={options.height}
                onChange={(e) => setOptions((o) => ({ ...o, height: +e.target.value }))}
                className="input-field w-24 text-center"
                min={0}
              />
              <span className="text-slate-500">px</span>
              <p className="text-xs text-slate-500 w-full">0 = proportional automat</p>
            </div>
          )}

          {selected.options?.includes('pages') && (
            <div className="flex items-center gap-3">
              <label className="text-sm text-slate-400 whitespace-nowrap">Pagini:</label>
              <input
                type="text"
                value={options.pages}
                onChange={(e) => setOptions((o) => ({ ...o, pages: e.target.value }))}
                className="input-field flex-1"
                placeholder="all, sau 1,3,5-7"
              />
            </div>
          )}

          {/* Convert button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleConvert}
              disabled={files.length === 0 || status === 'converting'}
              className="btn-primary flex items-center gap-2"
            >
              {status === 'converting' ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Se converteste...
                </>
              ) : (
                <>
                  <ArrowRight size={16} />
                  Converteste
                </>
              )}
            </button>

            {status === 'done' && result && (
              <button onClick={handleDownload} className="btn-secondary flex items-center gap-2">
                <Download size={16} />
                Descarca ({result.filename} — {formatSize(result.size)})
              </button>
            )}
          </div>

          {/* Status */}
          {status === 'done' && (
            <div className="flex items-center gap-2 text-emerald-400 text-sm">
              <CheckCircle size={16} />
              Conversie finalizata cu succes!
            </div>
          )}

          {status === 'error' && (
            <div className="flex items-start gap-2 text-red-400 text-sm bg-red-500/10 rounded-lg p-3 border border-red-500/20">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!selected && (
        <div className="text-center py-8 text-slate-500">
          <ArrowRight className="mx-auto mb-2" size={24} />
          <p className="text-sm">Selecteaza un tip de conversie din lista de mai sus</p>
        </div>
      )}
    </div>
  );
}
