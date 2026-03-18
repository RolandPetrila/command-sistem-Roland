import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Command, ChevronDown, Menu, X } from 'lucide-react';
import { NAV_SECTIONS } from '../../modules/manifest';

export default function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState({});
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleCategory = (category) => {
    setCollapsed(prev => ({ ...prev, [category]: !prev[category] }));
  };

  const isCategoryActive = (items) =>
    items.some(item =>
      item.path === '/'
        ? location.pathname === '/'
        : location.pathname.startsWith(item.path)
    );

  const sidebarContent = (
    <>
      {/* Logo / Brand */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center shadow-lg glow-primary">
            <Command className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white text-sm leading-tight">Roland</h1>
            <p className="text-xs text-slate-400">Command Center</p>
          </div>
        </div>
        {/* Close button — mobile only */}
        <button
          onClick={() => setMobileOpen(false)}
          className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_SECTIONS.map((section, sIdx) => {
          const isCollapsed = section.collapsible && collapsed[section.category];
          const hasActiveItem = isCategoryActive(section.items);

          return (
            <div key={sIdx} className={section.category ? 'mt-3' : ''}>
              {section.category && (
                <button
                  onClick={() => section.collapsible && toggleCategory(section.category)}
                  className={`w-full flex items-center justify-between px-3 mb-1 ${
                    section.collapsible ? 'cursor-pointer hover:text-slate-300' : 'cursor-default'
                  }`}
                >
                  <span className={`text-[10px] uppercase tracking-wider font-semibold ${
                    hasActiveItem ? 'text-primary-400' : 'text-slate-500'
                  }`}>
                    {section.category}
                  </span>
                  {section.collapsible && (
                    <ChevronDown
                      className={`w-3 h-3 text-slate-500 transition-transform duration-200 ${
                        isCollapsed ? '-rotate-90' : ''
                      }`}
                    />
                  )}
                </button>
              )}

              {!isCollapsed && section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  onClick={() => setMobileOpen(false)}
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
            </div>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/60 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Versiune</p>
          <p className="text-sm font-medium text-slate-200">v0.3.0</p>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Hamburger button — mobile only */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-3 left-3 z-50 p-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-colors shadow-lg"
        aria-label="Deschide meniu"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Desktop sidebar — always visible on lg+ */}
      <aside className="hidden lg:flex w-64 bg-slate-900/95 border-r border-slate-800 flex-col shrink-0">
        {sidebarContent}
      </aside>

      {/* Mobile overlay + sidebar */}
      {mobileOpen && (
        <>
          {/* Backdrop */}
          <div
            className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          {/* Sidebar drawer */}
          <aside className="lg:hidden fixed inset-y-0 left-0 z-50 w-72 bg-slate-900 border-r border-slate-800 flex flex-col shadow-2xl animate-slide-in">
            {sidebarContent}
          </aside>
        </>
      )}
    </>
  );
}
