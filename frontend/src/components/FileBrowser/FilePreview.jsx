import React, { useState, useEffect } from 'react';
import { FileText, Loader2, AlertCircle } from 'lucide-react';
import { getFileContent } from '../../api/client';

export default function FilePreview({ filePath }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!filePath) return;

    let mounted = true;
    setLoading(true);
    setError('');

    getFileContent(filePath)
      .then((data) => {
        if (mounted) setContent(typeof data === 'string' ? data : data.content || JSON.stringify(data, null, 2));
      })
      .catch((err) => {
        if (mounted) setError('Nu s-a putut încărca conținutul fișierului.');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [filePath]);

  if (!filePath) {
    return (
      <div className="card h-full flex items-center justify-center">
        <div className="text-center">
          <FileText size={40} className="text-slate-700 mx-auto mb-3" />
          <p className="text-sm text-slate-400">Selectează un fișier pentru previzualizare</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card h-full flex flex-col">
      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-slate-800">
        <FileText size={16} className="text-slate-400" />
        <span className="text-sm text-slate-300 font-medium truncate">{filePath}</span>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="animate-spin text-primary-400" size={24} />
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle size={16} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      ) : (
        <pre className="flex-1 overflow-auto bg-slate-800/60 rounded-lg p-4 text-sm text-slate-300 font-mono leading-relaxed whitespace-pre-wrap break-words">
          {content}
        </pre>
      )}
    </div>
  );
}
