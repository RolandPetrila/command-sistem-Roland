import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const SHORTCUTS = [
  { key: 'k', ctrl: true, shift: false, path: null, action: 'command-palette', label: 'Command Palette' },
  { key: 'n', ctrl: true, shift: false, path: '/notepad', label: 'Notepad Nou' },
  { key: 't', ctrl: true, shift: true, path: '/translator', label: 'Traducator' },
  { key: 'c', ctrl: true, shift: true, path: '/upload', label: 'Calculator Pret' },
  { key: 'f', ctrl: true, shift: true, path: '/files', label: 'File Manager' },
  { key: '/', ctrl: true, shift: false, path: null, action: 'show-shortcuts', label: 'Afiseaza Shortcuts' },
];

export function useGlobalHotkeys(onCommandPalette, onShowShortcuts) {
  const navigate = useNavigate();

  useEffect(() => {
    function handleKeyDown(e) {
      // Don't trigger if typing in input/textarea
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
        // Only allow Ctrl+K (command palette) from inputs
        if (!(e.ctrlKey && e.key === 'k')) return;
      }

      for (const shortcut of SHORTCUTS) {
        const ctrlMatch = shortcut.ctrl ? (e.ctrlKey || e.metaKey) : true;
        const shiftMatch = shortcut.shift ? e.shiftKey : !e.shiftKey;
        const keyMatch = e.key.toLowerCase() === shortcut.key;

        if (ctrlMatch && shiftMatch && keyMatch) {
          e.preventDefault();
          if (shortcut.action === 'command-palette' && onCommandPalette) {
            onCommandPalette();
          } else if (shortcut.action === 'show-shortcuts' && onShowShortcuts) {
            onShowShortcuts();
          } else if (shortcut.path) {
            navigate(shortcut.path);
          }
          return;
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate, onCommandPalette, onShowShortcuts]);
}

export { SHORTCUTS };
