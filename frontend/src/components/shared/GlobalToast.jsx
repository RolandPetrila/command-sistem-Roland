import React, { useState, useEffect, useCallback } from 'react';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';

const ICONS = {
  error: AlertCircle,
  success: CheckCircle,
  info: Info,
};

const COLORS = {
  error: 'bg-red-500/15 border-red-500/40 text-red-300',
  success: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300',
  info: 'bg-blue-500/15 border-blue-500/40 text-blue-300',
};

const ICON_COLORS = {
  error: 'text-red-400',
  success: 'text-emerald-400',
  info: 'text-blue-400',
};

export function showToast(message, type = 'error', duration = 5000) {
  window.dispatchEvent(new CustomEvent('global-toast', {
    detail: { message, type, duration, id: Date.now() },
  }));
}

export default function GlobalToast() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((e) => {
    const toast = e.detail;
    setToasts(prev => [...prev.slice(-4), toast]); // max 5
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== toast.id));
    }, toast.duration || 5000);
  }, []);

  useEffect(() => {
    window.addEventListener('global-toast', addToast);
    return () => window.removeEventListener('global-toast', addToast);
  }, [addToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-16 right-4 z-[60] flex flex-col gap-2 max-w-sm">
      {toasts.map(toast => {
        const Icon = ICONS[toast.type] || Info;
        return (
          <div key={toast.id}
            className={`flex items-start gap-2 px-4 py-3 rounded-lg border backdrop-blur-sm shadow-lg animate-slide-in-right ${COLORS[toast.type] || COLORS.info}`}>
            <Icon size={16} className={`mt-0.5 shrink-0 ${ICON_COLORS[toast.type] || ICON_COLORS.info}`} />
            <span className="text-sm flex-1 break-words">{toast.message}</span>
            <button onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
              className="shrink-0 mt-0.5 opacity-60 hover:opacity-100">
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
