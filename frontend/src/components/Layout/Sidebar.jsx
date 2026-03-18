import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Command, ChevronDown } from 'lucide-react';
import { NAV_SECTIONS } from '../../modules/manifest';

export default function Sidebar() {
  const location = useLocation();

  // Track collapsed categories (all expanded by default)
  const [collapsed, setCollapsed] = useState({});

  const toggleCategory = (category) => {
    setCollapsed(prev => ({ ...prev, [category]: !prev[category] }));
  };

  // Check if any item in a category is active
  const isCategoryActive = (items) =>
    items.some(item =>
      item.path === '/'
        ? location.pathname === '/'
        : location.pathname.startsWith(item.path)
    );

  return (
    <aside className="w-64 bg-slate-900/95 border-r border-slate-800 flex flex-col shrink-0">
      {/* Logo / Brand */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center shadow-lg glow-primary">
            <Command className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white text-sm leading-tight">Roland</h1>
            <p className="text-xs text-slate-400">Command Center</p>
          </div>
        </div>
      </div>

      {/* Navigation — dynamic from manifest */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_SECTIONS.map((section, sIdx) => {
          const isCollapsed = section.collapsible && collapsed[section.category];
          const hasActiveItem = isCategoryActive(section.items);

          return (
            <div key={sIdx} className={section.category ? 'mt-3' : ''}>
              {/* Category header (if present) */}
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

              {/* Nav items */}
              {!isCollapsed && section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
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

      {/* Bottom section */}
      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/60 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Versiune</p>
          <p className="text-sm font-medium text-slate-200">v0.2.0</p>
        </div>
      </div>
    </aside>
  );
}
