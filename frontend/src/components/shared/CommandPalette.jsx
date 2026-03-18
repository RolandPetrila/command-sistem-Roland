import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Fuse from 'fuse.js';
import { Search } from 'lucide-react';
import { NAV_SECTIONS } from '../../modules/manifest';

// Flatten all nav items with their category
const allItems = NAV_SECTIONS.flatMap(section =>
  section.items.map(item => ({
    ...item,
    category: section.category || 'General',
  }))
);

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const fuse = useMemo(
    () => new Fuse(allItems, { keys: ['label', 'category'], threshold: 0.4 }),
    []
  );

  const results = query
    ? fuse.search(query).map(r => r.item)
    : allItems;

  // Global Ctrl+K listener
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(prev => !prev);
        setQuery('');
        setSelectedIndex(0);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen]);

  // Auto-focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      navigate(results[selectedIndex].path);
      setIsOpen(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
      onClick={() => setIsOpen(false)}
    >
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Dialog */}
      <div
        className="relative bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-700">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Caută pagini..."
            className="flex-1 bg-transparent text-white text-sm outline-none placeholder-slate-500"
          />
          <kbd className="text-[10px] text-slate-500 bg-slate-700/80 px-1.5 py-0.5 rounded font-mono">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-72 overflow-y-auto p-2">
          {results.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => { navigate(item.path); setIsOpen(false); }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-colors ${
                  idx === selectedIndex
                    ? 'bg-primary-600/30 text-primary-300'
                    : 'text-slate-300 hover:bg-slate-700/50'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" size={16} />
                <span className="flex-1">{item.label}</span>
                <span className="text-[11px] text-slate-500">{item.category}</span>
              </button>
            );
          })}
          {results.length === 0 && (
            <p className="text-center text-slate-500 text-sm py-6">Niciun rezultat</p>
          )}
        </div>

        {/* Footer hint */}
        <div className="px-4 py-2 border-t border-slate-700/50 flex items-center gap-4 text-[11px] text-slate-500">
          <span>↑↓ navigare</span>
          <span>↵ selectare</span>
          <span>esc închide</span>
        </div>
      </div>
    </div>
  );
}
