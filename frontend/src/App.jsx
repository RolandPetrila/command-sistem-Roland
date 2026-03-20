import React, { useState, useEffect, lazy, Suspense } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Footer from './components/Layout/Footer';
import DashboardPage from './pages/DashboardPage';
import ErrorBoundary from './components/shared/ErrorBoundary';
import CommandPalette from './components/shared/CommandPalette';
import FloatingOCR from './components/shared/FloatingOCR';
import GlobalToast from './components/shared/GlobalToast';
import { PAGE_TITLES } from './modules/manifest';
import { logPageView } from './api/client';
import { useGlobalHotkeys } from './hooks/useHotkeys';
import { Loader2 } from 'lucide-react';

// Lazy-loaded pages for code splitting
const UploadPage = lazy(() => import('./pages/UploadPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const CalibrationPage = lazy(() => import('./pages/CalibrationPage'));
const FileBrowserPage = lazy(() => import('./pages/FileBrowserPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const QRGeneratorPage = lazy(() => import('./pages/QRGeneratorPage'));
const NotepadPage = lazy(() => import('./pages/NotepadPage'));
const VaultPage = lazy(() => import('./pages/VaultPage'));
const ConverterPage = lazy(() => import('./pages/ConverterPage'));
const AIChatPage = lazy(() => import('./pages/AIChatPage'));
const DocumentAIPage = lazy(() => import('./pages/DocumentAIPage'));
const TranslatorPage = lazy(() => import('./pages/TranslatorPage'));
const InvoicePage = lazy(() => import('./pages/InvoicePage'));
const AISearchPage = lazy(() => import('./pages/AISearchPage'));
const ITPPage = lazy(() => import('./pages/ITPPage'));
const CalculatorPage = lazy(() => import('./pages/CalculatorPage'));
const PasswordGenPage = lazy(() => import('./pages/PasswordGenPage'));
const BarcodePage = lazy(() => import('./pages/BarcodePage'));
const CalculatorAdvancedPage = lazy(() => import('./pages/CalculatorAdvancedPage'));
const AutomationsPage = lazy(() => import('./pages/AutomationsPage'));
const IntegrationsPage = lazy(() => import('./pages/IntegrationsPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const NumberConverterPage = lazy(() => import('./pages/NumberConverterPage'));
const CompanyCheckPage = lazy(() => import('./pages/CompanyCheckPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="animate-spin text-blue-400" size={28} />
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const [showShortcuts, setShowShortcuts] = useState(false);

  useEffect(() => {
    logPageView(location.pathname);
  }, [location.pathname]);

  // Global keyboard shortcuts
  useGlobalHotkeys(
    null, // command palette handled by CommandPalette component itself
    () => setShowShortcuts(prev => !prev)
  );

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          pageTitles={PAGE_TITLES}
          showShortcuts={showShortcuts}
          onToggleShortcuts={() => setShowShortcuts(prev => !prev)}
        />
        <main className="flex-1 overflow-y-auto p-6">
          <ErrorBoundary>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/calibration" element={<CalibrationPage />} />
                <Route path="/files" element={<FileBrowserPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/qr" element={<QRGeneratorPage />} />
                <Route path="/notepad" element={<NotepadPage />} />
                <Route path="/vault" element={<VaultPage />} />
                <Route path="/converter" element={<ConverterPage />} />
                <Route path="/ai-chat" element={<AIChatPage />} />
                <Route path="/ai-docs" element={<DocumentAIPage />} />
                <Route path="/translator" element={<TranslatorPage />} />
                <Route path="/invoices" element={<InvoicePage />} />
                <Route path="/ai-search" element={<AISearchPage />} />
                <Route path="/calc" element={<CalculatorPage />} />
                <Route path="/password" element={<PasswordGenPage />} />
                <Route path="/barcode" element={<BarcodePage />} />
                <Route path="/calculator" element={<CalculatorAdvancedPage />} />
                <Route path="/itp" element={<ITPPage />} />
                <Route path="/automations" element={<AutomationsPage />} />
                <Route path="/integrations" element={<IntegrationsPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/number-converter" element={<NumberConverterPage />} />
                <Route path="/company-check" element={<CompanyCheckPage />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
        <Footer />
      </div>
      <CommandPalette />
      <FloatingOCR />
      <GlobalToast />
    </div>
  );
}
