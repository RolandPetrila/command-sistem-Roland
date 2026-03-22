import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Plus, Trash2, FileText, StickyNote, Wand2, ListChecks, Languages, Loader2, Tag, Search, Download, CheckSquare, Square, FolderEdit } from 'lucide-react';
import apiClient from '../api/client';

export default function NotepadPage() {
  // AI action state
  const [aiResult, setAiResult] = useState('');
  const [aiAction, setAiAction] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  const handleAiAction = async (action) => {
    if (!content.trim() || aiLoading) return;
    setAiLoading(true);
    setAiAction(action);
    setAiResult('');
    try {
      const { data } = await apiClient.post(`/api/ai/notepad/${action}`, { text: content });
      setAiResult(data.result || '');
    } catch {
      setAiResult('Eroare la procesarea AI.');
    }
    setAiLoading(false);
  };

  const applyAiResult = () => {
    if (aiResult) {
      handleContentChange(aiResult);
      setAiResult('');
      setAiAction('');
    }
  };

  const [notes, setNotes] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  // R3-44: Categories
  const [category, setCategory] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  // R3-48: Search
  const [noteSearch, setNoteSearch] = useState('');
  const [saving, setSaving] = useState(false);
  const saveTimerRef = useRef(null);
  // R4-19: Bulk selection state
  const [bulkSelected, setBulkSelected] = useState(new Set());
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [showBulkCatDialog, setShowBulkCatDialog] = useState(false);
  const [bulkCat, setBulkCat] = useState('general');

  // Load notes list
  const loadNotes = useCallback(async () => {
    try {
      const { data } = await apiClient.get('/api/notes');
      setNotes(data);
    } catch (err) {
      console.error('Failed to load notes:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  // Auto-select first note on initial load
  useEffect(() => {
    if (notes.length > 0 && activeId === null) {
      loadNote(notes[0].id);
    }
  }, [notes]);

  // Load single note
  const loadNote = async (id) => {
    try {
      const { data } = await apiClient.get(`/api/notes/${id}`);
      setActiveId(id);
      setTitle(data.title);
      setContent(data.content);
      setCategory(data.category || '');
    } catch (err) {
      console.error('Failed to load note:', err);
    }
  };

  // Auto-save (debounced 800ms)
  const autoSave = useCallback(async (id, newTitle, newContent, newCategory) => {
    if (!id) return;
    setSaving(true);
    try {
      await apiClient.put(`/api/notes/${id}`, {
        title: newTitle,
        content: newContent,
        ...(newCategory !== undefined && { category: newCategory }),
      });
      setNotes(prev =>
        prev.map(n =>
          n.id === id
            ? { ...n, title: newTitle, updated_at: new Date().toISOString() }
            : n
        )
      );
    } catch (err) {
      console.error('Auto-save failed:', err);
    } finally {
      setSaving(false);
    }
  }, []);

  const handleTitleChange = (newTitle) => {
    setTitle(newTitle);
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(
      () => autoSave(activeId, newTitle, content, category),
      800
    );
  };

  const handleContentChange = (newContent) => {
    setContent(newContent);
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(
      () => autoSave(activeId, title, newContent, category),
      800
    );
  };

  // R3-49: Export note
  const handleExport = (format = 'md') => {
    if (!activeId || !content) return;
    const ext = format === 'txt' ? 'txt' : 'md';
    const blob = new Blob([format === 'md' ? `# ${title}\n\n${content}` : content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(title || 'nota').replace(/\s+/g, '_')}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCategoryChange = (newCat) => {
    setCategory(newCat);
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(
      () => autoSave(activeId, title, content, newCat),
      800
    );
  };

  // Create new note
  const handleCreate = async () => {
    try {
      const { data } = await apiClient.post('/api/notes', {
        title: 'Notă nouă',
        content: '',
      });
      await loadNotes();
      loadNote(data.id);
    } catch (err) {
      console.error('Failed to create note:', err);
    }
  };

  // Delete note
  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/api/notes/${id}`);
      if (activeId === id) {
        setActiveId(null);
        setTitle('');
        setContent('');
      }
      const { data } = await apiClient.get('/api/notes');
      setNotes(data);
      // Select next note if available
      if (activeId === id && data.length > 0) {
        loadNote(data[0].id);
      }
    } catch (err) {
      console.error('Failed to delete note:', err);
    }
  };

  // R4-19: Bulk operation handlers
  const filteredNotes = notes.filter(n =>
    (!categoryFilter || (n.category || '') === categoryFilter) &&
    (!noteSearch || n.title?.toLowerCase().includes(noteSearch.toLowerCase()))
  );

  const toggleBulkSelect = (id) => {
    setBulkSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (bulkSelected.size === filteredNotes.length) {
      setBulkSelected(new Set());
    } else {
      setBulkSelected(new Set(filteredNotes.map(n => n.id)));
    }
  };

  const handleBulkDelete = async () => {
    if (bulkSelected.size === 0) return;
    if (!confirm(`Stergi ${bulkSelected.size} note? Aceasta actiune este ireversibila.`)) return;
    setBulkLoading(true);
    try {
      await apiClient.post('/api/notes/bulk-delete', { ids: [...bulkSelected] });
      setBulkSelected(new Set());
      setBulkMode(false);
      await loadNotes();
      if (bulkSelected.has(activeId)) {
        setActiveId(null);
        setTitle('');
        setContent('');
      }
    } catch {
      // toast handles error
    } finally {
      setBulkLoading(false);
    }
  };

  const handleBulkExport = async () => {
    if (bulkSelected.size === 0) return;
    setBulkLoading(true);
    try {
      const { data } = await apiClient.post('/api/notes/bulk-export', { ids: [...bulkSelected] });
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `note_export_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // toast handles error
    } finally {
      setBulkLoading(false);
    }
  };

  const handleBulkCategory = async () => {
    if (bulkSelected.size === 0) return;
    setBulkLoading(true);
    try {
      await apiClient.post('/api/notes/bulk-update-category', { ids: [...bulkSelected], category: bulkCat });
      setShowBulkCatDialog(false);
      setBulkSelected(new Set());
      setBulkMode(false);
      await loadNotes();
    } catch {
      // toast handles error
    } finally {
      setBulkLoading(false);
    }
  };

  return (
    <div className="flex gap-4 h-[calc(100vh-12rem)]">
      {/* Notes list */}
      <div className="w-64 shrink-0 card p-3 flex flex-col">
        <div className="flex gap-1 mb-2">
          <button
            onClick={handleCreate}
            className="btn-primary flex-1 flex items-center justify-center gap-2 py-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Notă nouă
          </button>
          <button
            onClick={() => { setBulkMode(!bulkMode); setBulkSelected(new Set()); }}
            className={`px-2.5 py-2 rounded-lg text-xs transition-colors ${bulkMode ? 'bg-primary-600/30 text-primary-300' : 'bg-slate-800/60 text-slate-500 hover:text-slate-300'}`}
            title="Selectie multipla"
          >
            <CheckSquare className="w-4 h-4" />
          </button>
        </div>
        {/* R4-19: Bulk toolbar */}
        {bulkMode && (
          <div className="mb-2 space-y-1">
            <div className="flex items-center gap-2">
              <button onClick={toggleSelectAll}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200">
                {bulkSelected.size === filteredNotes.length && filteredNotes.length > 0
                  ? <CheckSquare className="w-3.5 h-3.5 text-primary-400" />
                  : <Square className="w-3.5 h-3.5" />}
                {bulkSelected.size === filteredNotes.length && filteredNotes.length > 0 ? 'Deselecteaza' : 'Selecteaza tot'}
              </button>
              {bulkSelected.size > 0 && (
                <span className="text-xs text-primary-400">{bulkSelected.size} selectate</span>
              )}
            </div>
            {bulkSelected.size > 0 && (
              <div className="flex gap-1">
                <button onClick={handleBulkDelete} disabled={bulkLoading}
                  className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-xs disabled:opacity-50">
                  <Trash2 className="w-3 h-3" /> Sterge ({bulkSelected.size})
                </button>
                <button onClick={handleBulkExport} disabled={bulkLoading}
                  className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded-lg text-xs disabled:opacity-50">
                  <Download className="w-3 h-3" /> Export
                </button>
                <button onClick={() => setShowBulkCatDialog(true)} disabled={bulkLoading}
                  className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded-lg text-xs disabled:opacity-50">
                  <FolderEdit className="w-3 h-3" /> Cat.
                </button>
              </div>
            )}
          </div>
        )}
        {/* R3-48: Search */}
        <div className="relative mb-2">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
          <input value={noteSearch} onChange={e => setNoteSearch(e.target.value)}
            placeholder="Cauta note..."
            className="w-full bg-slate-800/60 border border-slate-700 rounded-lg pl-8 pr-2 py-1.5 text-xs focus:border-primary-500 focus:outline-none" />
        </div>
        {/* R3-44: Category filter */}
        <div className="flex flex-wrap gap-1 mb-2">
          {['', 'general', 'work', 'personal', 'ideas'].map(cat => (
            <button key={cat} onClick={() => setCategoryFilter(cat)}
              className={`px-2 py-0.5 rounded text-xs transition-colors ${categoryFilter === cat ? 'bg-primary-600/30 text-primary-300' : 'bg-slate-800/60 text-slate-500 hover:text-slate-300'}`}>
              {cat || 'Toate'}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto space-y-1">
          {filteredNotes.map((note) => (
            <div
              key={note.id}
              onClick={() => bulkMode ? toggleBulkSelect(note.id) : loadNote(note.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm group transition-colors ${
                bulkMode && bulkSelected.has(note.id)
                  ? 'bg-primary-600/20 text-primary-300'
                  : note.id === activeId && !bulkMode
                  ? 'bg-primary-600/20 text-primary-300'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              {bulkMode ? (
                bulkSelected.has(note.id)
                  ? <CheckSquare className="w-3.5 h-3.5 shrink-0 text-primary-400" />
                  : <Square className="w-3.5 h-3.5 shrink-0" />
              ) : (
                <FileText className="w-3.5 h-3.5 shrink-0" />
              )}
              <span className="flex-1 truncate">{note.title}</span>
              {!bulkMode && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(note.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
          {notes.length === 0 && (
            <div className="flex flex-col items-center py-8 text-slate-500">
              <StickyNote className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm">Nicio notă</p>
              <p className="text-xs mt-1">Apasă "Notă nouă" pentru a începe</p>
            </div>
          )}
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 card p-4 flex flex-col">
        {activeId ? (
          <>
            <div className="flex items-center gap-3 mb-3">
              <input
                value={title}
                onChange={(e) => handleTitleChange(e.target.value)}
                className="flex-1 bg-transparent text-white text-lg font-semibold outline-none border-b border-transparent focus:border-primary-500 pb-1 transition-colors"
                placeholder="Titlu notă..."
              />
              {/* R3-44: Category selector */}
              <select value={category} onChange={e => handleCategoryChange(e.target.value)}
                className="bg-slate-800/60 border border-slate-700 rounded-lg px-2 py-1 text-xs text-slate-400 focus:outline-none focus:border-primary-500">
                <option value="">Fara categorie</option>
                <option value="general">General</option>
                <option value="work">Work</option>
                <option value="personal">Personal</option>
                <option value="ideas">Ideas</option>
              </select>
              {saving && (
                <span className="text-xs text-emerald-400 animate-pulse">
                  Salvare...
                </span>
              )}
            </div>
            <textarea
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              className="flex-1 bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-slate-200 text-sm resize-none focus:border-primary-500 focus:outline-none font-mono leading-relaxed transition-colors"
              placeholder="Scrie aici..."
            />
            {/* R3-49: Export + AI Actions */}
            <div className="flex items-center gap-2 mt-2">
              <button onClick={() => handleExport('md')} disabled={!content}
                className="flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-xs transition-colors">
                <Download size={12} /> .md
              </button>
              <button onClick={() => handleExport('txt')} disabled={!content}
                className="flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-xs transition-colors">
                <Download size={12} /> .txt
              </button>
              <span className="text-xs text-slate-600 mx-1">|</span>
              <span className="text-xs text-slate-500">AI:</span>
              <button onClick={() => handleAiAction('improve')} disabled={aiLoading || !content.trim()}
                className="flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-xs transition-colors">
                {aiLoading && aiAction === 'improve' ? <Loader2 size={12} className="animate-spin" /> : <Wand2 size={12} />}
                Îmbunătățește
              </button>
              <button onClick={() => handleAiAction('summarize')} disabled={aiLoading || !content.trim()}
                className="flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-xs transition-colors">
                {aiLoading && aiAction === 'summarize' ? <Loader2 size={12} className="animate-spin" /> : <ListChecks size={12} />}
                Rezumă
              </button>
              <button onClick={() => handleAiAction('translate')} disabled={aiLoading || !content.trim()}
                className="flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-xs transition-colors">
                {aiLoading && aiAction === 'translate' ? <Loader2 size={12} className="animate-spin" /> : <Languages size={12} />}
                Traduce RO↔EN
              </button>
            </div>
            {/* AI Result */}
            {aiResult && (
              <div className="mt-2 bg-purple-900/10 border border-purple-800/30 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-purple-400">Rezultat AI ({aiAction})</span>
                  <div className="flex gap-1">
                    <button onClick={applyAiResult}
                      className="px-2 py-0.5 bg-purple-600 hover:bg-purple-700 rounded text-xs">Aplică</button>
                    <button onClick={() => navigator.clipboard.writeText(aiResult)}
                      className="px-2 py-0.5 bg-slate-700 hover:bg-slate-600 rounded text-xs">Copiază</button>
                    <button onClick={() => { setAiResult(''); setAiAction(''); }}
                      className="px-2 py-0.5 bg-slate-700 hover:bg-slate-600 rounded text-xs">Închide</button>
                  </div>
                </div>
                <div className="text-sm text-slate-300 whitespace-pre-wrap max-h-32 overflow-y-auto">{aiResult}</div>
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
            <StickyNote className="w-12 h-12 mb-3 opacity-30" />
            <p>Selectează sau creează o notă</p>
          </div>
        )}
      </div>

      {/* R4-19: Bulk category change dialog */}
      {showBulkCatDialog && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowBulkCatDialog(false)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 w-80 space-y-3" onClick={e => e.stopPropagation()}>
            <h3 className="text-sm font-semibold text-slate-200">Schimba categoria ({bulkSelected.size} note)</h3>
            <select value={bulkCat} onChange={e => setBulkCat(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500">
              <option value="general">General</option>
              <option value="work">Work</option>
              <option value="personal">Personal</option>
              <option value="ideas">Ideas</option>
            </select>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowBulkCatDialog(false)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs">Anuleaza</button>
              <button onClick={handleBulkCategory} disabled={bulkLoading}
                className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 rounded-lg text-xs disabled:opacity-50">Aplica</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
