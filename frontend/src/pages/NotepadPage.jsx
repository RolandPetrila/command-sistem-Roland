import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Plus, Trash2, FileText, StickyNote } from 'lucide-react';
import apiClient from '../api/client';

export default function NotepadPage() {
  const [notes, setNotes] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const saveTimerRef = useRef(null);

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
    } catch (err) {
      console.error('Failed to load note:', err);
    }
  };

  // Auto-save (debounced 800ms)
  const autoSave = useCallback(async (id, newTitle, newContent) => {
    if (!id) return;
    setSaving(true);
    try {
      await apiClient.put(`/api/notes/${id}`, {
        title: newTitle,
        content: newContent,
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
      () => autoSave(activeId, newTitle, content),
      800
    );
  };

  const handleContentChange = (newContent) => {
    setContent(newContent);
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(
      () => autoSave(activeId, title, newContent),
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

  return (
    <div className="flex gap-4 h-[calc(100vh-12rem)]">
      {/* Notes list */}
      <div className="w-64 shrink-0 card p-3 flex flex-col">
        <button
          onClick={handleCreate}
          className="btn-primary flex items-center justify-center gap-2 py-2 mb-3 text-sm w-full"
        >
          <Plus className="w-4 h-4" />
          Notă nouă
        </button>
        <div className="flex-1 overflow-y-auto space-y-1">
          {notes.map((note) => (
            <div
              key={note.id}
              onClick={() => loadNote(note.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm group transition-colors ${
                note.id === activeId
                  ? 'bg-primary-600/20 text-primary-300'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5 shrink-0" />
              <span className="flex-1 truncate">{note.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(note.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
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
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
            <StickyNote className="w-12 h-12 mb-3 opacity-30" />
            <p>Selectează sau creează o notă</p>
          </div>
        )}
      </div>
    </div>
  );
}
