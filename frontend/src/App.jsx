import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Footer from './components/Layout/Footer';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import HistoryPage from './pages/HistoryPage';
import CalibrationPage from './pages/CalibrationPage';
import FileBrowserPage from './pages/FileBrowserPage';
import SettingsPage from './pages/SettingsPage';
import QRGeneratorPage from './pages/QRGeneratorPage';
import NotepadPage from './pages/NotepadPage';
import VaultPage from './pages/VaultPage';
import ConverterPage from './pages/ConverterPage';
import ErrorBoundary from './components/shared/ErrorBoundary';
import CommandPalette from './components/shared/CommandPalette';
import { PAGE_TITLES } from './modules/manifest';

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header pageTitles={PAGE_TITLES} />
        <main className="flex-1 overflow-y-auto p-6">
          <ErrorBoundary>
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
            </Routes>
          </ErrorBoundary>
        </main>
        <Footer />
      </div>
      <CommandPalette />
    </div>
  );
}
