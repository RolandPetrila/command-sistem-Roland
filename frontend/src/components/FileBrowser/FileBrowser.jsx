import React, { useState, useEffect } from 'react';
import { Folder, FolderOpen, FileText, ChevronRight, ChevronDown, Loader2 } from 'lucide-react';
import { listFiles } from '../../api/client';

function FileTreeNode({ item, level = 0, onSelectFile, selectedPath }) {
  const [expanded, setExpanded] = useState(false);
  const [children, setChildren] = useState(null);
  const [loading, setLoading] = useState(false);

  const isDir = item.type === 'directory';
  const isSelected = selectedPath === item.path;

  const handleClick = async () => {
    if (isDir) {
      if (!expanded && children === null) {
        setLoading(true);
        try {
          const data = await listFiles(item.path);
          setChildren(data.tree || data.entries || []);
        } catch {
          setChildren([]);
        }
        setLoading(false);
      }
      setExpanded(!expanded);
    } else {
      onSelectFile(item.path);
    }
  };

  return (
    <div>
      <button
        onClick={handleClick}
        className={`flex items-center gap-1.5 w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors ${
          isSelected
            ? 'bg-primary-600/20 text-primary-400'
            : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-200'
        }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {isDir ? (
          <>
            {loading ? (
              <Loader2 size={14} className="animate-spin text-slate-500 shrink-0" />
            ) : expanded ? (
              <ChevronDown size={14} className="text-slate-500 shrink-0" />
            ) : (
              <ChevronRight size={14} className="text-slate-500 shrink-0" />
            )}
            {expanded ? (
              <FolderOpen size={15} className="text-amber-400 shrink-0" />
            ) : (
              <Folder size={15} className="text-amber-400/70 shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5 shrink-0" />
            <FileText size={15} className="text-slate-500 shrink-0" />
          </>
        )}
        <span className="truncate">{item.name}</span>
      </button>

      {expanded && children && (
        <div>
          {children.map((child, idx) => (
            <FileTreeNode
              key={`${child.path}-${idx}`}
              item={child}
              level={level + 1}
              onSelectFile={onSelectFile}
              selectedPath={selectedPath}
            />
          ))}
          {children.length === 0 && (
            <p
              className="text-xs text-slate-500 italic py-1"
              style={{ paddingLeft: `${(level + 1) * 16 + 8}px` }}
            >
              Folder gol
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function FileBrowser({ onSelectFile, selectedPath }) {
  const [rootEntries, setRootEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listFiles('')
      .then((data) => setRootEntries(data.tree || data.entries || []))
      .catch(() => setRootEntries([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="card h-full overflow-y-auto">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">Fișiere Proiect</h3>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="animate-spin text-primary-400" size={20} />
        </div>
      ) : rootEntries.length === 0 ? (
        <p className="text-sm text-slate-400 text-center py-8">
          Nu s-au găsit fișiere. Verificați conexiunea la backend.
        </p>
      ) : (
        <div className="space-y-0.5">
          {rootEntries.map((item, idx) => (
            <FileTreeNode
              key={`${item.path}-${idx}`}
              item={item}
              onSelectFile={onSelectFile}
              selectedPath={selectedPath}
            />
          ))}
        </div>
      )}
    </div>
  );
}
