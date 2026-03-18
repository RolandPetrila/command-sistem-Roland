/**
 * Module manifest — sursa unică pentru navigare sidebar + routes.
 *
 * Când adaugi un modul nou:
 * 1. Adaugă o secțiune în NAV_SECTIONS (cu category + items)
 * 2. Adaugă Route-ul corespunzător în App.jsx
 * 3. Backend: adaugă modulul în backend/modules/[name]/
 */

import {
  LayoutDashboard,
  Calculator,
  History,
  Settings2,
  FolderOpen,
  Settings,
  QrCode,
  StickyNote,
} from 'lucide-react';

export const NAV_SECTIONS = [
  {
    category: null, // fără header — top-level
    items: [
      { path: '/', label: 'Panou Principal', icon: LayoutDashboard },
    ],
  },
  {
    category: 'Traduceri',
    collapsible: true,
    items: [
      { path: '/upload', label: 'Calcul Preț', icon: Calculator },
      { path: '/history', label: 'Istoric', icon: History },
      { path: '/calibration', label: 'Calibrare', icon: Settings2 },
    ],
  },
  {
    category: 'Quick Tools',
    collapsible: true,
    items: [
      { path: '/qr', label: 'QR Generator', icon: QrCode },
      { path: '/notepad', label: 'Notepad', icon: StickyNote },
    ],
  },
  {
    category: 'Sistem',
    collapsible: true,
    items: [
      { path: '/files', label: 'Browser Fișiere', icon: FolderOpen },
      { path: '/settings', label: 'Setări', icon: Settings },
    ],
  },
];

// Flat list of all routes (pentru pageTitles în Header)
export const ALL_ROUTES = NAV_SECTIONS.flatMap(section =>
  section.items.map(item => ({
    path: item.path,
    label: item.label,
  }))
);

// pageTitles object (pentru Header component)
export const PAGE_TITLES = Object.fromEntries(
  ALL_ROUTES.map(r => [r.path, r.label])
);
