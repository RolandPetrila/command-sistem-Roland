import React from 'react';

export default function Footer() {
  return (
    <footer className="h-10 bg-slate-900/60 border-t border-slate-800 flex items-center justify-center px-6 shrink-0">
      <p className="text-xs text-slate-500">
        Calculator Preț Traduceri v1.0.0 &mdash; &copy; {new Date().getFullYear()}
      </p>
    </footer>
  );
}
