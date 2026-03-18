import React from 'react';
import { FileText, X, CheckSquare, Square } from 'lucide-react';

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileType(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  return ext === 'pdf' ? 'PDF' : ext === 'docx' ? 'DOCX' : ext.toUpperCase();
}

export default function FileList({ files, selectedIds, onToggleSelect, onSelectAll, onRemove }) {
  if (!files || files.length === 0) return null;

  const allSelected = selectedIds.length === files.length;

  return (
    <div className="card mt-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-300">
          Fișiere selectate ({files.length})
        </h3>
        <button
          onClick={onSelectAll}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-primary-400 transition-colors"
        >
          {allSelected ? <CheckSquare size={14} /> : <Square size={14} />}
          {allSelected ? 'Deselectează tot' : 'Selectează tot'}
        </button>
      </div>

      <div className="space-y-2 max-h-60 overflow-y-auto">
        {files.map((file, idx) => {
          const fileType = getFileType(file);
          const isSelected = selectedIds.includes(idx);

          return (
            <div
              key={`${file.name}-${idx}`}
              className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-150 ${
                isSelected
                  ? 'bg-primary-600/10 border border-primary-500/20'
                  : 'bg-slate-800/50 border border-transparent'
              }`}
            >
              <button onClick={() => onToggleSelect(idx)} className="shrink-0">
                {isSelected ? (
                  <CheckSquare size={16} className="text-primary-400" />
                ) : (
                  <Square size={16} className="text-slate-500" />
                )}
              </button>

              <FileText size={18} className="text-slate-400 shrink-0" />

              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 truncate">{file.name}</p>
                <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
              </div>

              <span className={fileType === 'PDF' ? 'badge-pdf' : 'badge-docx'}>{fileType}</span>

              <button
                onClick={() => onRemove(idx)}
                className="p-1 text-slate-500 hover:text-red-400 transition-colors rounded"
              >
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
