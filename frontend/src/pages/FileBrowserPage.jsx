import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import apiClient from '../api/client';
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
  Maximize2,
  Star,
  Tag,
  Clipboard,
  RotateCcw,
  Replace,
} from 'lucide-react';

const FM_BASE = `${window.location.origin}/api/fm`; // for direct URLs (img src, download href)

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
  // F7: Fullscreen preview
  const [fullPreview, setFullPreview] = useState(false);
  // R3-26: Tags
  const [allTags, setAllTags] = useState([]);
  const [tagFilter, setTagFilter] = useState(null);
  const [tagInput, setTagInput] = useState('');
  // R3-27: Favorites
  const [favorites, setFavorites] = useState(new Set());
  const [showFavOnly, setShowFavOnly] = useState(false);
  // R3-39: Fulltext search
  const [fulltextQuery, setFulltextQuery] = useState('');
  const [fulltextResults, setFulltextResults] = useState(null);
  const [fulltextLoading, setFulltextLoading] = useState(false);
  // R3-40: Auto-organize
  const [organizePreview, setOrganizePreview] = useState(null);
  const [organizeLoading, setOrganizeLoading] = useState(false);
  // R4-21: Batch select + rename
  const [batchSelected, setBatchSelected] = useState(new Set());
  const [batchRenameModal, setBatchRenameModal] = useState(false);
  const [renameOp, setRenameOp] = useState('prefix');
  const [renameValue, setRenameValue] = useState('');
  const [renameFrom, setRenameFrom] = useState('');
  const [renameTo, setRenameTo] = useState('');
  // R4-22: Trash
  const [trashModal, setTrashModal] = useState(false);
  const [trashItems, setTrashItems] = useState([]);
  const [trashSize, setTrashSize] = useState(0);
  const [trashLoading, setTrashLoading] = useState(false);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const browse = useCallback(async (path = '') => {
    setLoading(true);
    setSelected(null);
    setPreview(null);
    setBatchSelected(new Set());
    try {
      const { data } = await apiClient.get('/api/fm/browse', { params: { path } });
      setCurrentPath(path);
      setEntries(data.entries || []);
      setParentPath(data.parent);
    } catch {
      showToast('Eroare la incarcarea fisierelor', 'error');
    }
    setLoading(false);
  }, []);

  useEffect(() => { browse(''); loadTagsAndFavs(); }, [browse]);

  const loadTagsAndFavs = async () => {
    try {
      const [t, f] = await Promise.allSettled([
        apiClient.get('/api/fm/tags'),
        apiClient.get('/api/fm/favorites'),
      ]);
      if (t.status === 'fulfilled') setAllTags(t.value.data?.tags || t.value.data || []);
      if (f.status === 'fulfilled') {
        const favs = f.value.data?.favorites || f.value.data || [];
        setFavorites(new Set(favs.map(fv => fv.path || fv)));
      }
    } catch { /* ok */ }
  };

  const toggleFavorite = async (entry) => {
    try {
      await apiClient.post('/api/fm/favorites', { path: entry.path });
      setFavorites(prev => {
        const next = new Set(prev);
        if (next.has(entry.path)) next.delete(entry.path); else next.add(entry.path);
        return next;
      });
    } catch { /* toast handles it */ }
  };

  const addTag = async (entry) => {
    if (!tagInput.trim()) return;
    try {
      await apiClient.post('/api/fm/tags', { path: entry.path, tag: tagInput.trim() });
      setTagInput('');
      loadTagsAndFavs();
      showToast(`Tag "${tagInput.trim()}" adaugat`);
    } catch { /* toast handles it */ }
  };

  // R3-39: Fulltext search
  const handleFulltextSearch = async () => {
    if (!fulltextQuery.trim()) return;
    setFulltextLoading(true);
    try {
      const { data } = await apiClient.get('/api/fm/search/fulltext', { params: { q: fulltextQuery, path: currentPath } });
      setFulltextResults(data?.results || data || []);
    } catch { setFulltextResults([]); }
    setFulltextLoading(false);
  };

  // R3-40: Auto-organize
  const handleAutoOrganize = async (confirm = false) => {
    setOrganizeLoading(true);
    try {
      const { data } = await apiClient.post('/api/fm/auto-organize', { path: currentPath, confirm });
      if (confirm) {
        showToast(`Organizat: ${data.moved || 0} fisiere mutate`);
        setOrganizePreview(null);
        browse(currentPath);
      } else {
        setOrganizePreview(data?.preview || data?.moves || data || []);
      }
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la organizare', 'error');
    }
    setOrganizeLoading(false);
  };

  // R4-21: Batch select toggle
  const toggleBatchSelect = (entry) => {
    setBatchSelected(prev => {
      const next = new Set(prev);
      if (next.has(entry.name)) next.delete(entry.name); else next.add(entry.name);
      return next;
    });
  };

  // R4-21: Batch rename
  const handleBatchRename = async () => {
    const payload = {
      files: Array.from(batchSelected),
      operation: renameOp,
      value: renameValue,
      replace_from: renameFrom,
      replace_to: renameTo,
      path: currentPath,
    };
    try {
      const { data } = await apiClient.post('/api/fm/batch-rename', payload);
      const count = data.renamed?.length || 0;
      const errCount = data.errors?.length || 0;
      showToast(`Redenumit: ${count} fisiere${errCount > 0 ? `, ${errCount} erori` : ''}`);
      setBatchRenameModal(false);
      setBatchSelected(new Set());
      setRenameValue('');
      setRenameFrom('');
      setRenameTo('');
      browse(currentPath);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la redenumire batch', 'error');
    }
  };

  // R4-21: Preview new names
  const batchRenamePreview = () => {
    return Array.from(batchSelected).map(fname => {
      const stem = fname.includes('.') ? fname.substring(0, fname.lastIndexOf('.')) : fname;
      const ext = fname.includes('.') ? fname.substring(fname.lastIndexOf('.')) : '';
      let newName = fname;
      if (renameOp === 'prefix' && renameValue) newName = `${renameValue}${fname}`;
      else if (renameOp === 'suffix' && renameValue) newName = `${stem}${renameValue}${ext}`;
      else if (renameOp === 'replace' && renameFrom) newName = fname.replace(renameFrom, renameTo);
      return { old: fname, new: newName };
    });
  };

  // R4-22: Load trash
  const loadTrash = async () => {
    setTrashLoading(true);
    try {
      const { data } = await apiClient.get('/api/fm/trash');
      setTrashItems(data.items || []);
      setTrashSize(data.total_size || 0);
    } catch { /* toast handles it */ }
    setTrashLoading(false);
  };

  // R4-22: Restore from trash
  const restoreFromTrash = async (trashName) => {
    try {
      const { data } = await apiClient.post('/api/fm/trash/restore', { trash_name: trashName });
      showToast(`Restaurat: ${data.restored}`);
      loadTrash();
      browse(currentPath);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la restaurare', 'error');
    }
  };

  // R4-22: Empty trash
  const emptyTrash = async () => {
    try {
      const { data } = await apiClient.post('/api/fm/trash/empty');
      showToast(`Cos golit: ${data.deleted_count} fisiere sterse permanent`);
      loadTrash();
    } catch (e) {
      showToast(e.response?.data?.detail || 'Eroare la golire cos', 'error');
    }
  };

  // R4-23: Copy path to clipboard
  const copyPath = async (entry) => {
    try {
      await navigator.clipboard.writeText(entry.path);
      showToast(`Copiat: ${entry.path}`);
    } catch {
      showToast('Nu s-a putut copia calea', 'error');
    }
  };

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
      setPreview({ type: ext === '.pdf' ? 'pdf' : 'image', url: `${FM_BASE}/serve?path=${encodeURIComponent(entry.path)}` });
    } else if (TEXT_EXT.has(ext)) {
      setPreviewLoading(true);
      try {
        const { data } = await apiClient.get(`/api/fm/serve?path=${encodeURIComponent(entry.path)}`, { responseType: 'text' });
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
    a.href = `${FM_BASE}/download?path=${encodeURIComponent(entry.path)}`;
    a.download = entry.name;
    a.click();
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await apiClient.delete('/api/fm/delete', { params: { path: deleteConfirm.path } });
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
      await apiClient.post('/api/fm/rename', { path: renameModal.path, new_name: newName.trim() });
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
      await apiClient.post('/api/fm/mkdir', { path: currentPath, name: name.trim() });
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
      const { data } = await apiClient.post('/api/fm/upload', formData, {
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
      const { data } = await apiClient.post('/api/fm/duplicates', { path: currentPath });
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
        <button onClick={() => setShowFavOnly(p => !p)}
          className={`flex items-center gap-1 text-sm py-1.5 px-3 rounded-lg border transition-colors ${showFavOnly ? 'bg-amber-600/20 border-amber-500/40 text-amber-400' : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'}`}>
          <Star size={14} /> Favorite
        </button>
        {/* R3-40: Auto-organize */}
        <button onClick={() => handleAutoOrganize(false)} disabled={organizeLoading}
          className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3">
          {organizeLoading ? <Loader2 size={14} className="animate-spin" /> : <FolderPlus size={14} />}
          Organizeaza
        </button>
        {/* R4-21: Batch Rename (visible when files selected) */}
        {batchSelected.size > 0 && (
          <button onClick={() => setBatchRenameModal(true)}
            className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3 border-amber-500/40 text-amber-400">
            <Replace size={14} /> Rename ({batchSelected.size})
          </button>
        )}
        {/* R4-22: Trash */}
        <button onClick={() => { setTrashModal(true); loadTrash(); }}
          className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3">
          <Trash2 size={14} /> Cos
        </button>
        {/* R3-39: Fulltext search */}
        <div className="relative flex items-center gap-1">
          <input value={fulltextQuery} onChange={e => setFulltextQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleFulltextSearch()}
            placeholder="Cauta in continut..."
            className="bg-slate-800 border border-slate-700 rounded-lg pl-8 pr-2 py-1.5 text-xs w-40 focus:w-56 transition-all focus:border-primary-500 focus:outline-none" />
          <Search size={12} className="absolute left-2.5 text-slate-500" />
          {fulltextLoading && <Loader2 size={12} className="animate-spin text-slate-400" />}
        </div>

        {/* Breadcrumbs */}
        <div className="flex items-center gap-1 text-xs text-slate-400 ml-auto overflow-hidden">
          <button onClick={() => browse('')} className="hover:text-white hover:underline transition-colors shrink-0">Proiect</button>
          {breadcrumbs.map((part, i) => {
            const isLast = i === breadcrumbs.length - 1;
            return (
              <React.Fragment key={i}>
                <ChevronRight size={12} className="shrink-0" />
                {isLast ? (
                  <span className="text-white truncate">{part}</span>
                ) : (
                  <button
                    onClick={() => browse(breadcrumbs.slice(0, i + 1).join('/'))}
                    className="hover:text-white hover:underline transition-colors truncate"
                  >{part}</button>
                )}
              </React.Fragment>
            );
          })}
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
              {entries.filter(e => !showFavOnly || favorites.has(e.path)).map((entry) => {
                const Icon = iconFor(entry);
                const isSelected = selected?.path === entry.path;
                const isFav = favorites.has(entry.path);
                return (
                  <div
                    key={entry.path}
                    className={`flex items-center gap-3 px-3 py-2 cursor-pointer transition-colors group ${
                      isSelected ? 'bg-primary-600/15' : 'hover:bg-slate-800/40'
                    }`}
                    onClick={() => handleClick(entry)}
                  >
                    {/* R4-21: Batch select checkbox */}
                    {entry.type === 'file' && (
                      <input type="checkbox" checked={batchSelected.has(entry.name)}
                        onClick={(e) => e.stopPropagation()}
                        onChange={() => toggleBatchSelect(entry)}
                        className="shrink-0 w-3.5 h-3.5 accent-primary-500 cursor-pointer" />
                    )}
                    <button onClick={(e) => { e.stopPropagation(); toggleFavorite(entry); }}
                      className={`shrink-0 p-0.5 ${isFav ? 'text-amber-400' : 'text-slate-700 hover:text-amber-400'}`}>
                      <Star size={12} fill={isFav ? 'currentColor' : 'none'} />
                    </button>
                    <Icon size={16} className={`shrink-0 ${iconColor(entry)}`} />
                    <span className="flex-1 text-sm text-slate-200 truncate">{entry.name}</span>
                    <span className="text-xs text-slate-500 hidden sm:block w-20 text-right">{formatSize(entry.size)}</span>
                    <span className="text-xs text-slate-600 hidden md:block w-32 text-right">{formatDate(entry.modified)}</span>

                    {/* Actions */}
                    {entry.type === 'file' && (
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {/* R4-23: Copy path */}
                        <button onClick={(e) => { e.stopPropagation(); copyPath(entry); }}
                          className="p-1 text-slate-500 hover:text-emerald-400" title="Copiaza calea">
                          <Clipboard size={14} />
                        </button>
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
                        {/* R4-23: Copy path for dirs too */}
                        <button onClick={(e) => { e.stopPropagation(); copyPath(entry); }}
                          className="p-1 text-slate-500 hover:text-emerald-400" title="Copiaza calea">
                          <Clipboard size={14} />
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
              <div className="flex items-center gap-1">
                {preview && preview.type !== 'unsupported' && (
                  <button onClick={() => setFullPreview(true)}
                    className="p-1 text-slate-500 hover:text-white" title="Vizualizare completa">
                    <Maximize2 size={14} />
                  </button>
                )}
                <button onClick={() => { setSelected(null); setPreview(null); }}
                  className="p-1 text-slate-500 hover:text-white">
                  <X size={14} />
                </button>
              </div>
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

      {/* F7: Fullscreen Preview Modal */}
      {fullPreview && selected && preview && (
        <div className="fixed inset-0 z-50 flex flex-col bg-black/90 backdrop-blur-sm" onClick={() => setFullPreview(false)}>
          <div className="flex items-center justify-between px-6 py-3 bg-slate-900/90 border-b border-slate-700 shrink-0" onClick={e => e.stopPropagation()}>
            <span className="text-sm font-medium text-slate-200 truncate">{selected.name}</span>
            <div className="flex items-center gap-2">
              <button onClick={() => handleDownload(selected)}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs">
                <Download size={13} /> Descarca
              </button>
              <button onClick={() => setFullPreview(false)}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg">
                <X size={16} />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-auto flex items-center justify-center p-4" onClick={e => e.stopPropagation()}>
            {preview.type === 'image' ? (
              <img src={preview.url} alt={selected.name} className="max-w-full max-h-full object-contain rounded-lg" />
            ) : preview.type === 'pdf' ? (
              <iframe src={preview.url} className="w-full h-full rounded-lg border border-slate-700 bg-white" title={selected.name} />
            ) : preview.type === 'text' ? (
              <pre className="text-sm text-slate-300 font-mono bg-slate-800/80 rounded-lg p-6 overflow-auto whitespace-pre-wrap break-words w-full max-w-4xl max-h-full">
                {preview.content}
              </pre>
            ) : null}
          </div>
        </div>
      )}

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

      {/* R3-39: Fulltext search results */}
      {fulltextResults && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 rounded-xl p-6 w-full max-w-lg max-h-[70vh] overflow-y-auto space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Rezultate cautare: "{fulltextQuery}"</h3>
              <button onClick={() => setFulltextResults(null)} className="p-1.5 hover:bg-slate-800 rounded"><X size={16} /></button>
            </div>
            {fulltextResults.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">Niciun rezultat gasit</p>
            ) : (
              <div className="space-y-2">
                {fulltextResults.map((r, i) => (
                  <div key={i} className="bg-slate-800 rounded-lg p-3 cursor-pointer hover:bg-slate-700" onClick={() => { setFulltextResults(null); browse(r.directory || ''); }}>
                    <div className="text-sm font-medium text-primary-400">{r.filename || r.name || r.path}</div>
                    {r.snippet && <div className="text-xs text-slate-400 mt-1 line-clamp-2">{r.snippet}</div>}
                    {r.score && <div className="text-xs text-slate-600">Relevanta: {(r.score * 100).toFixed(0)}%</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* R3-40: Auto-organize preview */}
      {organizePreview && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 rounded-xl p-6 w-full max-w-lg max-h-[70vh] overflow-y-auto space-y-3">
            <h3 className="text-sm font-medium">Previzualizare organizare automata</h3>
            {Array.isArray(organizePreview) && organizePreview.length > 0 ? (
              <>
                <div className="space-y-1">
                  {organizePreview.map((m, i) => (
                    <div key={i} className="text-xs flex gap-2">
                      <span className="text-slate-400 truncate flex-1">{m.from || m.source}</span>
                      <span className="text-slate-600">→</span>
                      <span className="text-emerald-400 truncate flex-1">{m.to || m.destination}</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 justify-end">
                  <button onClick={() => setOrganizePreview(null)} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm">Anuleaza</button>
                  <button onClick={() => handleAutoOrganize(true)} disabled={organizeLoading}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg text-sm flex items-center gap-2">
                    {organizeLoading ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />} Aplica
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="text-sm text-slate-500 text-center py-4">Toate fisierele sunt deja organizate.</p>
                <button onClick={() => setOrganizePreview(null)} className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm">Inchide</button>
              </>
            )}
          </div>
        </div>
      )}

      {/* R4-21: Batch Rename Modal */}
      {batchRenameModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setBatchRenameModal(false)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold">Redenumire Batch ({batchSelected.size} fisiere)</h3>
              <button onClick={() => setBatchRenameModal(false)} className="p-1 text-slate-500 hover:text-white"><X size={16} /></button>
            </div>

            {/* Operation type */}
            <div className="mb-3">
              <label className="text-xs text-slate-400 mb-1 block">Operatie</label>
              <select value={renameOp} onChange={e => setRenameOp(e.target.value)}
                className="input-field w-full text-sm">
                <option value="prefix">Adauga prefix</option>
                <option value="suffix">Adauga sufix</option>
                <option value="replace">Gaseste si inlocuieste</option>
              </select>
            </div>

            {/* Value inputs */}
            {renameOp !== 'replace' ? (
              <div className="mb-3">
                <label className="text-xs text-slate-400 mb-1 block">{renameOp === 'prefix' ? 'Prefix' : 'Sufix'}</label>
                <input type="text" value={renameValue} onChange={e => setRenameValue(e.target.value)}
                  placeholder={renameOp === 'prefix' ? 'ex: 2026-03_' : 'ex: _final'}
                  className="input-field w-full text-sm" autoFocus />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Gaseste</label>
                  <input type="text" value={renameFrom} onChange={e => setRenameFrom(e.target.value)}
                    placeholder="text vechi" className="input-field w-full text-sm" autoFocus />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Inlocuieste cu</label>
                  <input type="text" value={renameTo} onChange={e => setRenameTo(e.target.value)}
                    placeholder="text nou" className="input-field w-full text-sm" />
                </div>
              </div>
            )}

            {/* Preview table */}
            <div className="mb-4 max-h-48 overflow-y-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-800">
                    <th className="text-left py-1 pr-2">Nume vechi</th>
                    <th className="text-center py-1 px-1">→</th>
                    <th className="text-left py-1 pl-2">Nume nou</th>
                  </tr>
                </thead>
                <tbody>
                  {batchRenamePreview().map((p, i) => (
                    <tr key={i} className="border-b border-slate-800/50">
                      <td className="py-1 pr-2 text-slate-400 truncate max-w-[180px]">{p.old}</td>
                      <td className="py-1 px-1 text-slate-600 text-center">→</td>
                      <td className={`py-1 pl-2 truncate max-w-[180px] ${p.old !== p.new ? 'text-emerald-400' : 'text-slate-600'}`}>{p.new}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex gap-2 justify-end">
              <button onClick={() => setBatchRenameModal(false)} className="btn-secondary text-sm py-1.5 px-4">Anuleaza</button>
              <button onClick={handleBatchRename} className="btn-primary text-sm py-1.5 px-4 flex items-center gap-1">
                <Replace size={13} /> Aplica
              </button>
            </div>
          </div>
        </div>
      )}

      {/* R4-22: Trash Modal */}
      {trashModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setTrashModal(false)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold flex items-center gap-2">
                  <Trash2 size={16} /> Cos de gunoi
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {trashItems.length} fisiere, {formatSize(trashSize)} — auto-stergere dupa 7 zile
                </p>
              </div>
              <button onClick={() => setTrashModal(false)} className="p-1 text-slate-500 hover:text-white"><X size={16} /></button>
            </div>

            {trashLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="animate-spin text-primary-400" size={20} />
              </div>
            ) : trashItems.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">Cosul de gunoi este gol.</p>
            ) : (
              <div className="space-y-2 mb-4">
                {trashItems.map((item, i) => (
                  <div key={i} className="flex items-center gap-3 bg-slate-800/60 rounded-lg p-2.5">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-slate-200 truncate">{item.filename}</div>
                      <div className="text-xs text-slate-500 flex gap-3">
                        <span>{formatSize(item.size)}</span>
                        <span>Sters: {formatDate(item.deleted_at)}</span>
                      </div>
                    </div>
                    <button onClick={() => restoreFromTrash(item.trash_name)}
                      className="p-1.5 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-900/30 rounded" title="Restaureaza">
                      <RotateCcw size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {trashItems.length > 0 && (
              <button onClick={emptyTrash}
                className="w-full btn-danger text-sm py-2 flex items-center justify-center gap-1">
                <Trash2 size={13} /> Goleste cosul ({trashItems.length} fisiere)
              </button>
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
