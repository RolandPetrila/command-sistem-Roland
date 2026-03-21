import React, { useState, useEffect, useRef } from 'react';
import { Languages, Upload, FileText, BookOpen, Repeat, Download, Loader2, Search, Plus, Trash2, X, ChevronDown, ArrowRightLeft } from 'lucide-react';
import api from '../api/client';

const LANGS = [
  { code: 'en', label: 'Engleză' },
  { code: 'ro', label: 'Română' },
  { code: 'sk', label: 'Slovacă' },
  { code: 'de', label: 'Germană' },
  { code: 'fr', label: 'Franceză' },
  { code: 'it', label: 'Italiană' },
  { code: 'es', label: 'Spaniolă' },
];

export default function TranslatorPage() {
  const [tab, setTab] = useState('text'); // text | file | tm | glossary
  // Text translation
  const [sourceText, setSourceText] = useState('');
  const [targetText, setTargetText] = useState('');
  const [sourceLang, setSourceLang] = useState('en');
  const [targetLang, setTargetLang] = useState('ro');
  const [provider, setProvider] = useState('');
  const [translating, setTranslating] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const [tmHits, setTmHits] = useState(0);
  const [useTm, setUseTm] = useState(true);
  const [useGlossary, setUseGlossary] = useState(true);
  // File translation
  const [file, setFile] = useState(null);
  const [fileTranslating, setFileTranslating] = useState(false);
  const [fileResult, setFileResult] = useState(null);
  const fileRef = useRef(null);
  // TM
  const [tmEntries, setTmEntries] = useState([]);
  const [tmSearch, setTmSearch] = useState('');
  const [tmStats, setTmStats] = useState(null);
  // Glossary
  const [glossaryTerms, setGlossaryTerms] = useState([]);
  const [glossarySearch, setGlossarySearch] = useState('');
  const [newTerm, setNewTerm] = useState({ term_source: '', term_target: '', domain: 'general' });
  const [showAddTerm, setShowAddTerm] = useState(false);
  // F10: Per-client glossary
  const [glossaryClients, setGlossaryClients] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState('');
  // Usage
  const [usage, setUsage] = useState(null);
  // Detect
  const [detectedLang, setDetectedLang] = useState(null);

  useEffect(() => { loadUsage(); }, []);
  useEffect(() => { if (tab === 'tm') { loadTmStats(); loadTm(); } }, [tab]);
  useEffect(() => {
    if (tab === 'glossary') {
      loadGlossary();
      loadGlossaryClients();
    }
  }, [tab]);

  const loadUsage = async () => {
    try {
      const { data } = await api.get('/api/translator/usage');
      setUsage(data);
    } catch { /* toast handles it */ }
  };

  const loadTm = async () => {
    try {
      const url = tmSearch ? `/api/translator/tm/search?q=${encodeURIComponent(tmSearch)}&source_lang=${sourceLang}&target_lang=${targetLang}` : '/api/translator/tm?limit=50';
      const { data } = await api.get(url);
      setTmEntries(Array.isArray(data) ? data : data.entries || []);
    } catch { /* toast handles it */ }
  };

  const loadTmStats = async () => {
    try {
      const { data } = await api.get('/api/translator/tm/stats');
      setTmStats(data);
    } catch { /* toast handles it */ }
  };

  const loadGlossaryClients = async () => {
    try {
      const { data } = await api.get('/api/invoice/clients');
      setGlossaryClients(data || []);
    } catch { /* toast handles it */ }
  };

  const loadGlossary = async () => {
    try {
      let url = glossarySearch ? `/api/translator/glossary?search=${encodeURIComponent(glossarySearch)}` : '/api/translator/glossary';
      if (selectedClientId) url += (url.includes('?') ? '&' : '?') + `client_id=${selectedClientId}`;
      const { data } = await api.get(url);
      setGlossaryTerms(Array.isArray(data) ? data : []);
    } catch { /* toast handles it */ }
  };

  const handleTranslate = async () => {
    if (!sourceText.trim() || translating) return;
    setTranslating(true);
    setTargetText('');
    setDetectedLang(null);
    try {
      const { data } = await api.post('/api/translator/text', {
        text: sourceText, source_lang: sourceLang, target_lang: targetLang,
        use_tm: useTm, use_glossary: useGlossary,
      });
      setTargetText(data.translated_text || '');
      setProvider(data.provider || '');
      setCharCount(data.chars_count || 0);
      setTmHits(data.tm_hits || 0);
      if (data.detected_lang) setDetectedLang(data.detected_lang);
    } catch (err) {
      setTargetText(`⚠️ Eroare: ${err.response?.data?.detail || err.message}`);
    } finally {
      setTranslating(false);
    }
  };

  const handleDetect = async () => {
    if (!sourceText.trim()) return;
    try {
      const { data } = await api.post('/api/translator/detect', { text: sourceText });
      setDetectedLang(data.language);
      const found = LANGS.find(l => l.code === data.language);
      if (found) setSourceLang(data.language);
    } catch { /* toast handles it */ }
  };

  const swapLangs = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setSourceText(targetText);
    setTargetText(sourceText);
  };

  const handleFileTranslate = async () => {
    if (!file || fileTranslating) return;
    setFileTranslating(true);
    setFileResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('source_lang', sourceLang);
      formData.append('target_lang', targetLang);
      const { data } = await api.post('/api/translator/file', formData, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
      });
      // Verify we got a real file back (not a JSON error returned as blob)
      if (data.type && data.type.includes('json')) {
        const text = await data.text();
        const parsed = JSON.parse(text);
        setFileResult({ error: parsed.detail || 'Eroare necunoscuta la traducere' });
        return;
      }
      const url = URL.createObjectURL(data);
      setFileResult({ url, name: `tradus_${file.name.replace(/\.[^.]+$/, '')}.docx` });
    } catch (err) {
      // Read error from blob response
      let errorMsg = err.message;
      if (err.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text();
          const parsed = JSON.parse(text);
          errorMsg = parsed.detail || text;
          if (Array.isArray(errorMsg)) errorMsg = errorMsg.map(e => e.msg || e).join('; ');
        } catch { /* use default err.message */ }
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      setFileResult({ error: errorMsg });
    } finally {
      setFileTranslating(false);
    }
  };

  const handleAddTerm = async () => {
    if (!newTerm.term_source.trim() || !newTerm.term_target.trim()) return;
    try {
      await api.post('/api/translator/glossary', { ...newTerm, source_lang: sourceLang, target_lang: targetLang });
      setNewTerm({ term_source: '', term_target: '', domain: 'general' });
      setShowAddTerm(false);
      loadGlossary();
    } catch { /* toast handles it */ }
  };

  const handleDeleteTerm = async (id) => {
    try {
      await api.delete(`/api/translator/glossary/${id}`);
      loadGlossary();
    } catch { /* toast handles it */ }
  };

  const tabs = [
    { id: 'text', label: 'Text', icon: Languages },
    { id: 'file', label: 'Fișier', icon: FileText },
    { id: 'tm', label: 'Translation Memory', icon: BookOpen },
    { id: 'glossary', label: 'Glosar', icon: BookOpen },
  ];

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-xl p-1">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === t.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
        {/* Usage indicator */}
        {usage?.deepl && (
          <div className="ml-auto flex items-center gap-2 text-xs text-gray-500 px-3">
            <span>DeepL: {((usage.deepl.character_count || 0) / 1000).toFixed(0)}K / {((usage.deepl.character_limit || 500000) / 1000).toFixed(0)}K</span>
            <div className="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(100, ((usage.deepl.character_count || 0) / (usage.deepl.character_limit || 500000)) * 100)}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Language selector bar */}
      <div className="flex items-center gap-3 bg-gray-900 rounded-xl p-3">
        <select value={sourceLang} onChange={e => setSourceLang(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
        </select>
        <button onClick={swapLangs} className="p-2 hover:bg-gray-800 rounded-lg transition-colors" title="Inversează limbile">
          <ArrowRightLeft size={18} className="text-blue-400" />
        </button>
        <select value={targetLang} onChange={e => setTargetLang(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
        </select>
        <button onClick={handleDetect} className="ml-2 text-xs text-gray-400 hover:text-blue-400 transition-colors">
          Detectează limbă
        </button>
        {detectedLang && <span className="text-xs text-green-400">Detectat: {LANGS.find(l => l.code === detectedLang)?.label || detectedLang}</span>}
        <div className="ml-auto flex items-center gap-3 text-xs text-gray-500">
          <label className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={useTm} onChange={e => setUseTm(e.target.checked)} className="accent-blue-500" />
            TM
          </label>
          <label className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={useGlossary} onChange={e => setUseGlossary(e.target.checked)} className="accent-blue-500" />
            Glosar
          </label>
        </div>
      </div>

      {/* TEXT TAB */}
      {tab === 'text' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <textarea value={sourceText} onChange={e => setSourceText(e.target.value)}
              placeholder="Scrie sau lipește textul de tradus..."
              className="w-full h-64 bg-gray-900 border border-gray-700 rounded-xl p-4 text-sm resize-none focus:border-blue-500 focus:outline-none" />
            {/* Character counter with color coding */}
            {(() => {
              const chars = sourceText.length;
              const limit = 500000;
              const tokens = Math.ceil(chars / 4);
              const pct = (chars / limit) * 100;
              const colorClass = pct > 90 ? 'text-red-400' : pct > 70 ? 'text-yellow-400' : 'text-green-400';
              return chars > 0 ? (
                <div className={`text-xs ${colorClass} px-1 py-1`}>
                  {chars.toLocaleString('ro-RO')} caractere | ~{tokens.toLocaleString('ro-RO')} tokeni
                  <span className="text-gray-600 ml-2">({pct.toFixed(1)}% din limita DeepL 500K/luna)</span>
                </div>
              ) : null;
            })()}
            <div className="flex justify-between text-xs text-gray-500">
              <span>{sourceText.length} caractere</span>
              <button onClick={handleTranslate} disabled={translating || !sourceText.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white text-sm font-medium transition-colors">
                {translating ? <Loader2 size={14} className="animate-spin" /> : <Languages size={14} />}
                Traduce
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <textarea value={targetText} readOnly
              placeholder="Traducerea va apărea aici..."
              className="w-full h-64 bg-gray-900 border border-gray-700 rounded-xl p-4 text-sm resize-none text-green-200" />
            <div className="flex justify-between text-xs text-gray-500">
              <span>
                {provider && <span className="text-blue-400">{provider}</span>}
                {charCount > 0 && <span className="ml-2">{charCount} chars</span>}
                {tmHits > 0 && <span className="ml-2 text-yellow-400">TM: {tmHits} potriviri</span>}
              </span>
              {targetText && (
                <button onClick={() => navigator.clipboard.writeText(targetText)}
                  className="text-gray-400 hover:text-white transition-colors">Copiază</button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* FILE TAB */}
      {tab === 'file' && (
        <div className="bg-gray-900 rounded-xl p-6 space-y-4">
          <div className="border-2 border-dashed border-gray-700 rounded-xl p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
            onClick={() => fileRef.current?.click()}>
            <Upload size={32} className="mx-auto mb-3 text-gray-500" />
            <p className="text-sm text-gray-400">{file ? file.name : 'Click sau trage un fișier (PDF, DOCX, TXT)'}</p>
            <input type="file" ref={fileRef} onChange={e => setFile(e.target.files?.[0])} className="hidden"
              accept=".pdf,.docx,.txt,.md" />
          </div>
          {file && (
            <div className="flex items-center gap-3">
              <FileText size={16} className="text-blue-400" />
              <span className="text-sm">{file.name}</span>
              <button onClick={() => { setFile(null); setFileResult(null); }}
                className="text-gray-500 hover:text-red-400"><X size={14} /></button>
              <button onClick={handleFileTranslate} disabled={fileTranslating}
                className="ml-auto flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors">
                {fileTranslating ? <Loader2 size={14} className="animate-spin" /> : <Languages size={14} />}
                Traduce fișier
              </button>
            </div>
          )}
          {fileResult && !fileResult.error && (
            <a href={fileResult.url} download={fileResult.name}
              className="flex items-center gap-2 px-4 py-3 bg-green-600/20 border border-green-600/40 rounded-xl text-green-400 hover:bg-green-600/30 transition-colors">
              <Download size={16} /> Descarcă: {fileResult.name}
            </a>
          )}
          {fileResult?.error && (
            <p className="text-red-400 text-sm">⚠️ {fileResult.error}</p>
          )}
        </div>
      )}

      {/* TM TAB */}
      {tab === 'tm' && (
        <div className="space-y-4">
          {tmStats && (
            <div className="flex gap-4">
              <div className="bg-gray-900 rounded-xl px-4 py-3">
                <div className="text-xs text-gray-500">Segmente</div>
                <div className="text-lg font-bold text-blue-400">{tmStats.total_segments || 0}</div>
              </div>
              <div className="bg-gray-900 rounded-xl px-4 py-3">
                <div className="text-xs text-gray-500">Domenii</div>
                <div className="text-lg font-bold text-blue-400">{tmStats.domains?.length || 0}</div>
              </div>
            </div>
          )}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input value={tmSearch} onChange={e => setTmSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && loadTm()}
                placeholder="Caută în Translation Memory..."
                className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
            <button onClick={loadTm} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm">Caută</button>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {tmEntries.map((entry, i) => (
              <div key={entry.id || i} className="bg-gray-900 rounded-lg p-3 grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-xs text-gray-500 block mb-1">{entry.source_lang?.toUpperCase()}</span>{entry.source_segment}</div>
                <div><span className="text-xs text-gray-500 block mb-1">{entry.target_lang?.toUpperCase()}</span>{entry.target_segment}</div>
              </div>
            ))}
            {tmEntries.length === 0 && <p className="text-sm text-gray-500 text-center py-4">Nicio intrare în TM. Traduce texte pentru a popula automat.</p>}
          </div>
        </div>
      )}

      {/* GLOSSARY TAB */}
      {tab === 'glossary' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input value={glossarySearch} onChange={e => setGlossarySearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && loadGlossary()}
                placeholder="Cauta termen..."
                className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
            <select value={selectedClientId}
              onChange={e => { setSelectedClientId(e.target.value); setTimeout(loadGlossary, 50); }}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm">
              <option value="">Toti clientii</option>
              {glossaryClients.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button onClick={() => setShowAddTerm(!showAddTerm)}
              className="flex items-center gap-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
              <Plus size={14} /> Adauga termen
            </button>
          </div>
          {showAddTerm && (
            <div className="bg-gray-900 rounded-xl p-4 flex gap-3 items-end">
              <div className="flex-1">
                <label className="text-xs text-gray-500 mb-1 block">Termen sursă ({sourceLang.toUpperCase()})</label>
                <input value={newTerm.term_source} onChange={e => setNewTerm(p => ({ ...p, term_source: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div className="flex-1">
                <label className="text-xs text-gray-500 mb-1 block">Termen tradus ({targetLang.toUpperCase()})</label>
                <input value={newTerm.term_target} onChange={e => setNewTerm(p => ({ ...p, term_target: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Domeniu</label>
                <select value={newTerm.domain} onChange={e => setNewTerm(p => ({ ...p, domain: e.target.value }))}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                  <option value="general">General</option>
                  <option value="automotive">Automotive</option>
                  <option value="legal">Juridic</option>
                  <option value="technical">Tehnic</option>
                  <option value="medical">Medical</option>
                </select>
              </div>
              <button onClick={handleAddTerm} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm">Salvează</button>
            </div>
          )}
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {glossaryTerms.map(term => (
              <div key={term.id} className="bg-gray-900 rounded-lg p-3 flex items-center gap-3 text-sm group">
                <span className="flex-1 font-medium">{term.term_source}</span>
                <span className="text-gray-500">→</span>
                <span className="flex-1 text-green-300">{term.term_target}</span>
                <span className="text-xs text-gray-600 px-2 py-0.5 bg-gray-800 rounded">{term.domain}</span>
                <button onClick={() => handleDeleteTerm(term.id)}
                  className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
            {glossaryTerms.length === 0 && <p className="text-sm text-gray-500 text-center py-4">Glosarul e gol. Adaugă termeni frecvenți pentru traduceri mai precise.</p>}
          </div>
        </div>
      )}
    </div>
  );
}
