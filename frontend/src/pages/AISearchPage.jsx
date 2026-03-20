import React, { useState } from 'react';
import { Search, FileText, Bot, Loader2, Upload } from 'lucide-react';
import api from '../api/client';

export default function AISearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [ragAnswer, setRagAnswer] = useState('');
  const [ragLoading, setRagLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setResults([]);
    setRagAnswer('');
    setSearchError('');
    try {
      const { data } = await api.get(`/api/ai/search-documents?q=${encodeURIComponent(query)}`);
      setResults(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setSearchError(err.response?.data?.detail || 'Eroare la cautare');
    }
    setSearching(false);
  };

  const handleRagQuery = async () => {
    if (!query.trim()) return;
    setRagLoading(true);
    setRagAnswer('');
    try {
      const { data } = await api.post('/api/ai/rag-query', { question: query });
      setRagAnswer(data.answer || data.response || '');
    } catch {
      setRagAnswer('Nu s-a putut genera raspunsul.');
    }
    setRagLoading(false);
  };

  const handleIndexAll = async () => {
    setIndexing(true);
    try {
      await api.post('/api/ai/index-all-documents');
    } catch { /* toast handles it */ }
    setIndexing(false);
  };

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
          <input value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Caută în documente... (ex: 'contract BMW', 'penalizări', 'factură')"
            className="w-full bg-gray-900 border border-gray-700 rounded-xl pl-12 pr-4 py-3 text-sm focus:border-blue-500 focus:outline-none" />
        </div>
        <button onClick={handleSearch} disabled={searching || !query.trim()}
          className="flex items-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl text-sm font-medium transition-colors">
          {searching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          Caută
        </button>
        <button onClick={handleRagQuery} disabled={ragLoading || !query.trim()}
          className="flex items-center gap-2 px-5 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-xl text-sm font-medium transition-colors"
          title="Întreabă AI-ul despre documentele tale">
          {ragLoading ? <Loader2 size={16} className="animate-spin" /> : <Bot size={16} />}
          Întreabă AI
        </button>
      </div>

      {/* Index button */}
      <div className="flex items-center gap-3 text-xs text-gray-500">
        <button onClick={handleIndexAll} disabled={indexing}
          className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
          {indexing ? <Loader2 size={12} className="animate-spin" /> : <Upload size={12} />}
          Re-indexează toate documentele
        </button>
        <span>Documentele sunt indexate automat la upload.</span>
      </div>

      {/* RAG Answer */}
      {ragAnswer && (
        <div className="bg-purple-900/10 border border-purple-800/30 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-sm text-purple-400">
            <Bot size={16} /> Răspuns AI
          </div>
          <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{ragAnswer}</div>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm text-gray-400">{results.length} documente găsite</h3>
          {results.map((doc, i) => (
            <div key={i} className="bg-gray-900 rounded-xl p-4 space-y-1">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-blue-400" />
                <span className="font-medium text-sm">{doc.file_name}</span>
                {doc.classification && (
                  <span className="text-xs px-2 py-0.5 bg-gray-800 rounded-full text-gray-400">{doc.classification}</span>
                )}
                {doc.language && (
                  <span className="text-xs text-gray-600">{doc.language.toUpperCase()}</span>
                )}
              </div>
              {doc.snippet && (
                <p className="text-xs text-gray-400 line-clamp-2">{doc.snippet}</p>
              )}
              <div className="text-xs text-gray-600">{doc.file_path}</div>
            </div>
          ))}
        </div>
      )}

      {searchError && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-4 text-sm text-red-400">{searchError}</div>
      )}

      {!searching && results.length === 0 && query && !searchError && (
        <div className="text-center py-8 text-gray-500">
          <Search size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Niciun rezultat. Încearcă termeni diferiți sau indexează documentele.</p>
        </div>
      )}

      {!query && (
        <div className="text-center py-12 text-gray-500">
          <Search size={48} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg">Caută în documentele tale</p>
          <p className="text-sm mt-1">Caută text, clasificări, sau întreabă AI-ul despre conținutul documentelor.</p>
        </div>
      )}
    </div>
  );
}
