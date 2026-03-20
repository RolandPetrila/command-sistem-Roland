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
  KeyRound,
  ArrowRightLeft,
  Bot,
  FileSearch,
  Languages,
  Receipt,
  Search,
  Sigma,
  Lock,
  Barcode,
  Hash,
  Car,
  Zap,
  Plug,
  BarChart3,
  Building2,
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
      { path: '/translator', label: 'Traducător', icon: Languages },
      { path: '/upload', label: 'Calcul Preț', icon: Calculator },
      { path: '/history', label: 'Istoric', icon: History },
      { path: '/calibration', label: 'Calibrare', icon: Settings2 },
    ],
  },
  {
    category: 'AI',
    collapsible: true,
    items: [
      { path: '/ai-chat', label: 'Chat AI', icon: Bot },
      { path: '/ai-docs', label: 'Analiză Documente', icon: FileSearch },
      { path: '/ai-search', label: 'Căutare Documente', icon: Search },
    ],
  },
  {
    category: 'Productivitate',
    collapsible: true,
    items: [
      { path: '/invoices', label: 'Facturare', icon: Receipt },
      { path: '/converter', label: 'Convertor Fișiere', icon: ArrowRightLeft },
      { path: '/qr', label: 'QR Generator', icon: QrCode },
      { path: '/barcode', label: 'Cod de Bare', icon: Barcode },
      { path: '/notepad', label: 'Notepad', icon: StickyNote },
      { path: '/calc', label: 'Calculator', icon: Sigma },
      { path: '/calculator', label: 'Calculator Avansat', icon: Calculator },
      { path: '/password', label: 'Generator Parole', icon: Lock },
      { path: '/number-converter', label: 'Convertor Numere', icon: Hash },
      { path: '/company-check', label: 'Verificare Firma', icon: Building2 },
    ],
  },
  {
    category: 'ITP',
    collapsible: true,
    items: [
      { path: '/itp', label: 'Inspecții ITP', icon: Car },
    ],
  },
  {
    category: 'Sistem',
    collapsible: true,
    items: [
      { path: '/automations', label: 'Automatizări', icon: Zap },
      { path: '/integrations', label: 'Integrări', icon: Plug },
      { path: '/reports', label: 'Rapoarte', icon: BarChart3 },
      { path: '/vault', label: 'API Key Vault', icon: KeyRound },
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
