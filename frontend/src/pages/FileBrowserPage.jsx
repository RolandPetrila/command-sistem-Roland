import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import {
  Folder,
  FileText,
  Image,
  FileSpreadsheet,
  File as FileIcon,
  ChevronRight,
  ArrowLeft,
  Download,
  Trash2,
  Pencil,
  FolderPlus,
  Upload,
  Search,
  Loader2,
  AlertCircle,
  CheckCircle,
  Copy,
  X,
  Eye,
} from 'lucide-react';

const API = `${window.location.origin}/api/fm`;

const PREVIEW_EXT = new Set(['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp']);
const TEXT_EXT = new Set([
  '.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.txt', '.csv',
  '.cfg', '.toml', '.yaml', '.yml', '.html', '.css', '.sh', '.bat', '.sql', '.ini',
]);

function iconFor(entry) {
  if (entry.type === 'directory') return Folder;
  const ext = (entry.extension || '').toLowerCase();
  if (['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'].includes(ext)) return Image;
  if (['.xlsx', '.xls', '.csv'].includes(ext)) return FileSpreadsheet;
  if (TEXT_EXT.has(ext) || ext === '.pdf') return FileText;
  return FileIcon;
}

function iconColor(entry) {
  if (entry.type === 'directory') return 'text-amber-400';
  const ext = (entry.extension || '').toLowerCase();
  if (['.pdf'].includes(ext)) return 'text-red-400';
  if (['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'].includes(ext)) return 'text-emerald-400';
  if (['.docx', '.doc'].includes(ext)) return 'text-blue-400';
  if (['.xlsx', '.xls', '.csv'].includes(ext)) return 'text-green-400';
  if (['.py'].includes(ext)) return 'text-yellow-400';
  if (['.js', '.jsx', '.ts', '.tsx'].includes(ext)) return 'text-cyan-400';
  return 'text-slate-500';
}

function formatSize(b) {
  if (b == null) return '';
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('ro-RO') + ' ' + d.toLocaleTimeString('ro-RO', { hour: '2-digit', minute: '2-digit' });
}

export default function FileBrowserPage() {
  const [currentPath, setCurrentPath] = useState('');
  const [entries, setEntries] = useState([]);
  const [parentPath, setParentPath] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // Modals
  const [renameModal, setRenameModal] = useState(null);
  const [mkdirModal, setMkdirModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [dupeResults, setDupeResults] = useState(null);
  const [dupeLoading, setDupeLoading] = useState(false);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const browse = useCallback(async (path = '') => {
    setLoading(true);
    setSelected(null);
    setPreview(null);
    try {
      const { data } = await axios.get(`${API}/browse`, { params: { path } });
      setCurrentPath(path);
      setEntries(data.entries || []);
      setParentPath(data.parent);
    } catch {
      showToast('Eroare la incarcarea fisierelor', 'error');
    }
    setLoading(false);
  }, []);

  useEffect(() => { browse(''); }, [browse]);

  const handleClick = (entry) => {
    if (entry.type === 'directory') {
      browse(entry.path);
    } else {
      setSelected(entry);
      loadPreview(entry);
    }
  };

  const loadPreview = async (entry) => {
    const ext = (entry.extension || '').toLowerCase();
    if (PREVIEW_EXT.has(ext)) {
      setPreview({ type: ext === '.pdf' ? 'pdf' : 'image', url: `${API}/serve?path=${encodeURIComponent(entry.path)}` });
    } else if (TEXT_EXT.has(ext)) {
      setPreviewLoading(true);
      try {
        const { data } = await axios.get(`${API}/serve?path=${encodeURIComponent(entry.path)}`, { responseType: 'text' });
        setPreview({ type: 'text', content: typeof data === 'string' ? data : JSON.stringify(data, null, 2) });
      } catch {
        setPreview({ type: 'unsupported' });
      }
      setPreviewLoading(false);
    } else {
      setPreview({ type: 'unsupported' });
    }
  };

  const handleDownload = (entry) => {
    const a = document.createElement('a');
    a.href = `${API}/download?path=${encodeURIComponent(entry.path)}`;
    a.download = entry.name;
    a.click();
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await axios.delete(`${API}/delete`, { params: { path: deleteConfirm.path } });
      showToast(`Sters: ${deleteConfirm.name}`);
      setDeleteConfirm(null);
      if (selected?.path === deleteConfirm.path) { setSelected(null); setPreview(null); }
      browse(currentPath);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la stergere', 'error');
    }
  };

  const handleRename = async (newName) => {
    if (!renameModal || !newName.trim()) return;
    try {
      await axios.post(`${API}/rename`, { path: renameModal.path, new_name: newName.trim() });
      showToast(`Redenumit: ${renameModal.name} -> ${newName}`);
      setRenameModal(null);
      browse(currentPath);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la redenumire', 'error');
    }
  };

  const handleMkdir = async (name) => {
    if (!name.trim()) return;
    try {
      await axios.post(`${API}/mkdir`, { path: currentPath, name: name.trim() });
      showToast(`Folder creat: ${name}`);
      setMkdirModal(false);
      browse(currentPath);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la creare folder', 'error');
    }
  };

  const onDrop = useCallback(async (files) => {
    if (!files.length) return;
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('directory', currentPath);
    try {
      const { data } = await axios.post(`${API}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      showToast(`Uploadat: ${data.uploaded.length} fisiere`);
      browse(currentPath);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la upload', 'error');
    }
  }, [currentPath, browse]);

  const { getRootProps, getInputProps, isDragActive, open: openUpload } = useDropzone({
    onDrop,
    noClick: true,
    noKeyboard: true,
  });

  const handleDuplicates = async () => {
    setDupeLoading(true);
    try {
      const { data } = await axios.post(`${API}/duplicates`, { path: currentPath });
      setDupeResults(data);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare scanare duplicate', 'error');
    }
    setDupeLoading(false);
  };

  const breadcrumbs = currentPath ? currentPath.split('/') : [];

  return (
    <div className="h-[calc(100vh-160px)] flex flex-col gap-3" {...getRootProps()}>
      <input {...getInputProps()} />

      {/* Drag overlay */}
      {isDragActive && (
        <div className="fixed inset-0 z-50 bg-primary-500/10 border-2 border-dashed border-primary-500 flex items-center justify-center">
          <p className="text-lg text-primary-400 font-medium">Elibereaza pentru upload</p>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex items-center gap-2 flex-wrap">
        {parentPath !== null && (
          <button onClick={() => browse(parentPath || '')} className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3">
            <ArrowLeft size={14} /> Inapoi
          </button>
        )}
        <button onClick={openUpload} className="btn-primary flex items-center gap-1 text-sm py-1.5 px-3">
          <Upload size={14} /> Upload
        </button>
        <button onClick={() => setMkdirModal(true)} className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3">
          <FolderPlus size={14} /> Folder Nou
        </button>
        <button onClick={handleDuplicates} disabled={dupeLoading} className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3">
          {dupeLoading ? <Loader2 size={14} className="animate-spin" /> : <Copy size={14} />}
          Duplicate
        </button>

        {/* Breadcrumbs */}
        <div className="flex items-center gap-1 text-xs text-slate-400 ml-auto overflow-hidden">
          <button onClick={() => browse('')} className="hover:text-white transition-colors shrink-0">Proiect</button>
          {breadcrumbs.map((part, i) => (
            <React.Fragment key={i}>
              <ChevronRight size={12} className="shrink-0" />
              <button
                onClick={() => browse(breadcrumbs.slice(0, i + 1).join('/'))}
                className="hover:text-white transition-colors truncate"
              >{part}</button>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex gap-3 min-h-0">
        {/* File list */}
        <div className="flex-1 card overflow-y-auto min-w-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-primary-400" size={24} />
            </div>
          ) : entries.length === 0 ? (
            <p className="text-center text-slate-500 py-12 text-sm">Folder gol. Trage fisiere aici pentru upload.</p>
          ) : (
            <div className="divide-y divide-slate-800/50">
              {entries.map((entry) => {
                const Icon = iconFor(entry);
                const isSelected = selected?.path === entry.path;
                return (
                  <div
                    key={entry.path}
                    className={`flex items-center gap-3 px-3 py-2 cursor-pointer transition-colors group ${
                      isSelected ? 'bg-primary-600/15' : 'hover:bg-slate-800/40'
                    }`}
                    onClick={() => handleClick(entry)}
                  >
                    <Icon size={16} className={`shrink-0 ${iconColor(entry)}`} />
                    <span className="flex-1 text-sm text-slate-200 truncate">{entry.name}</span>
                    <span className="text-xs text-slate-500 hidden sm:block w-20 text-right">{formatSize(entry.size)}</span>
                    <span className="text-xs text-slate-600 hidden md:block w-32 text-right">{formatDate(entry.modified)}</span>

                    {/* Actions */}
                    {entry.type === 'file' && (
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={(e) => { e.stopPropagation(); handleDownload(entry); }}
                          className="p-1 text-slate-500 hover:text-primary-400" title="Descarca">
                          <Download size={14} />
                        </button>
                        <button onClick={(e) => { e.stopPropagation(); setRenameModal(entry); }}
                          className="p-1 text-slate-500 hover:text-amber-400" title="Redenumeste">
                          <Pencil size={14} />
                        </button>
                        <button onClick={(e) => { e.stopPropagation(); setDeleteConfirm(entry); }}
                          className="p-1 text-slate-500 hover:text-red-400" title="Sterge">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    )}
                    {entry.type === 'directory' && (
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={(e) => { e.stopPropagation(); setRenameModal(entry); }}
                          className="p-1 text-slate-500 hover:text-amber-400" title="Redenumeste">
                          <Pencil size={14} />
                        </button>
                        <button onClick={(e) => { e.stopPropagation(); setDeleteConfirm(entry); }}
                          className="p-1 text-slate-500 hover:text-red-400" title="Sterge">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Preview panel */}
        {selected && (
          <div className="w-full lg:w-96 card flex flex-col overflow-hidden shrink-0">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
              <span className="text-sm font-medium text-slate-200 truncate">{selected.name}</span>
              <button onClick={() => { setSelected(null); setPreview(null); }}
                className="p-1 text-slate-500 hover:text-white">
                <X size={14} />
              </button>
            </div>

            {/* Preview content */}
            <div className="flex-1 overflow-auto min-h-0">
              {previewLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="animate-spin text-primary-400" size={20} />
                </div>
              ) : preview?.type === 'image' ? (
                <img src={preview.url} alt={selected.name} className="max-w-full rounded-lg" />
              ) : preview?.type === 'pdf' ? (
                <iframe src={preview.url} className="w-full h-full min-h-[400px] rounded-lg border border-slate-700" />
              ) : preview?.type === 'text' ? (
                <pre className="text-xs text-slate-300 font-mono bg-slate-800/60 rounded-lg p-3 overflow-auto whitespace-pre-wrap break-words max-h-[500px]">
                  {preview.content}
                </pre>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Eye size={24} className="mx-auto mb-2" />
                  <p className="text-sm">Preview indisponibil pentru acest format</p>
                </div>
              )}
            </div>

            {/* File info + actions */}
            <div className="mt-3 pt-2 border-t border-slate-800 space-y-2">
              <div className="flex justify-between text-xs text-slate-500">
                <span>Dimensiune:</span>
                <span className="text-slate-300">{formatSize(selected.size)}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>Modificat:</span>
                <span className="text-slate-300">{formatDate(selected.modified)}</span>
              </div>
              <div className="flex gap-2 pt-1">
                <button onClick={() => handleDownload(selected)} className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1 flex-1">
                  <Download size={13} /> Descarca
                </button>
                <button onClick={() => setRenameModal(selected)} className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1">
                  <Pencil size={13} />
                </button>
                <button onClick={() => setDeleteConfirm(selected)} className="btn-danger text-xs py-1.5 px-3 flex items-center gap-1">
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium shadow-lg ${
          toast.type === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
        }`}>
          {toast.type === 'error' ? <AlertCircle size={14} /> : <CheckCircle size={14} />}
          {toast.msg}
        </div>
      )}

      {/* Rename Modal */}
      {renameModal && <InputModal title={`Redenumeste: ${renameModal.name}`} initial={renameModal.name}
        onConfirm={handleRename} onClose={() => setRenameModal(null)} />}

      {/* Mkdir Modal */}
      {mkdirModal && <InputModal title="Folder nou" initial="" placeholder="Nume folder"
        onConfirm={handleMkdir} onClose={() => setMkdirModal(false)} />}

      {/* Delete Confirm */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setDeleteConfirm(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 max-w-sm w-full mx-4 shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-semibold mb-2">Confirma stergerea</h3>
            <p className="text-sm text-slate-400 mb-4">
              Stergi <strong className="text-slate-200">{deleteConfirm.name}</strong>?
              {deleteConfirm.type === 'directory' && <span className="text-red-400"> Toate fisierele din folder vor fi sterse!</span>}
            </p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setDeleteConfirm(null)} className="btn-secondary text-sm py-1.5 px-4">Anuleaza</button>
              <button onClick={handleDelete} className="btn-danger text-sm py-1.5 px-4">Sterge</button>
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Results */}
      {dupeResults && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setDupeResults(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 max-w-2xl w-full mx-4 shadow-2xl max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold">Fisiere Duplicate</h3>
              <button onClick={() => setDupeResults(null)} className="p-1 text-slate-500 hover:text-white"><X size={16} /></button>
            </div>
            {dupeResults.groups.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-6">Nu s-au gasit duplicate.</p>
            ) : (
              <>
                <p className="text-xs text-slate-500 mb-3">
                  {dupeResults.groups.length} grupuri, {formatSize(dupeResults.total_wasted)} spatiu irosit
                </p>
                <div className="space-y-3">
                  {dupeResults.groups.map((g, i) => (
                    <div key={i} className="bg-slate-800/60 rounded-lg p-3">
                      <p className="text-xs text-slate-500 mb-1">{formatSize(g.size)} x {g.count} copii</p>
                      {g.files.map((f, j) => (
                        <div key={j} className="flex items-center justify-between text-sm py-0.5">
                          <span className="text-slate-300 truncate flex-1">{f.path}</span>
                          <button onClick={() => { setDeleteConfirm(f); setDupeResults(null); }}
                            className="text-red-400 hover:text-red-300 text-xs ml-2 shrink-0">Sterge</button>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function InputModal({ title, initial = '', placeholder = '', onConfirm, onClose }) {
  const [value, setValue] = useState(initial);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 max-w-sm w-full mx-4 shadow-2xl" onClick={e => e.stopPropagation()}>
        <h3 className="text-base font-semibold mb-3">{title}</h3>
        <input type="text" value={value} onChange={e => setValue(e.target.value)}
          placeholder={placeholder} autoFocus
          className="input-field w-full mb-4"
          onKeyDown={e => e.key === 'Enter' && onConfirm(value)} />
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="btn-secondary text-sm py-1.5 px-4">Anuleaza</button>
          <button onClick={() => onConfirm(value)} className="btn-primary text-sm py-1.5 px-4">Confirma</button>
        </div>
      </div>
    </div>
  );
}
