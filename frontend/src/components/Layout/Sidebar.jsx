import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Calculator,
  History,
  Settings2,
  FolderOpen,
  Settings,
  FileText,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Panou Principal' },
  { to: '/upload', icon: Calculator, label: 'Calcul Preț' },
  { to: '/history', icon: History, label: 'Istoric' },
  { to: '/calibration', icon: Settings2, label: 'Calibrare' },
  { to: '/files', icon: FolderOpen, label: 'Fișiere' },
  { to: '/settings', icon: Settings, label: 'Setări' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-slate-900/95 border-r border-slate-800 flex flex-col shrink-0">
      {/* Logo / Brand */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center shadow-lg glow-primary">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white text-sm leading-tight">Calculator Preț</h1>
            <p className="text-xs text-slate-400">Traduceri</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold px-3 mb-2">
          Navigare
        </p>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <item.icon className="w-4.5 h-4.5 shrink-0" size={18} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/60 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Versiune</p>
          <p className="text-sm font-medium text-slate-200">v1.0.0</p>
        </div>
      </div>
    </aside>
  );
}
