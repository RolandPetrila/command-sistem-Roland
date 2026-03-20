import React, { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Send, Paperclip, Bot, User, Loader2, X, Settings2, Database, ChevronDown, Download } from 'lucide-react';
import api from '../api/client';
import TokenIndicator from '../components/shared/TokenIndicator';

export default function AIChatPage() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const [docContext, setDocContext] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [providers, setProviders] = useState([]);
  const [apiKeys, setApiKeys] = useState({ gemini: '', openai: '', groq: '' });
  const [editingKey, setEditingKey] = useState(null);
  const [backendOk, setBackendOk] = useState(false);
  // New: provider selector + context mode
  const [selectedProvider, setSelectedProvider] = useState('auto');
  const [contextMode, setContextMode] = useState(true);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    loadSessions();
    loadProviders();
    loadPreferredProvider();
    const interval = setInterval(() => {
      if (!backendOk) loadProviders();
    }, 5000);
    return () => clearInterval(interval);
  }, [backendOk]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSessions = async () => {
    try {
      const { data } = await api.get('/api/ai/chat/sessions');
      setSessions(data);
    } catch { /* toast handles it */ }
  };

  const loadProviders = async () => {
    try {
      const { data } = await api.get('/api/ai/providers');
      setProviders(data);
      setBackendOk(true);
    } catch {
      setBackendOk(false);
    }
  };

  const loadPreferredProvider = async () => {
    try {
      const { data } = await api.get('/api/ai/provider-select');
      if (data.provider) setSelectedProvider(data.provider);
    } catch { /* toast handles it */ }
  };

  const handleProviderChange = async (provider) => {
    setSelectedProvider(provider);
    try {
      await api.post('/api/ai/provider-select', { provider });
    } catch { /* toast handles it */ }
  };

  const loadSession = async (id) => {
    try {
      const { data } = await api.get(`/api/ai/chat/sessions/${id}`);
      setMessages(data.messages);
      setActiveSession(id);
    } catch { /* toast handles it */ }
  };

  const newSession = async () => {
    try {
      const { data } = await api.post('/api/ai/chat/sessions');
      setSessions(prev => [data, ...prev]);
      setActiveSession(data.id);
      setMessages([]);
    } catch { /* toast handles it */ }
  };

  const deleteSession = async (id, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/ai/chat/sessions/${id}`);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (activeSession === id) {
        setActiveSession(null);
        setMessages([]);
      }
    } catch { /* toast handles it */ }
  };

  const clearAllSessions = async () => {
    if (!window.confirm('Stergi toate conversatiile?')) return;
    try {
      await api.delete('/api/ai/chat/sessions/all');
    } catch {
      // endpoint may not exist — delete individually
      for (const s of sessions) {
        try { await api.delete(`/api/ai/chat/sessions/${s.id}`); } catch { /* toast handles it */ }
      }
    }
    setSessions([]);
    setActiveSession(null);
    setMessages([]);
  };

  const exportConversation = () => {
    if (messages.length === 0) return;
    const lines = messages.map(msg => {
      const prefix = msg.role === 'user' ? '**User:**' : `**AI${msg.provider ? ` (${msg.provider})` : ''}:**`;
      return `${prefix}\n${msg.content}\n`;
    });
    const content = lines.join('\n---\n\n');
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_export_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleFileAttach = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAttachedFile(file);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('question', '__extract_only__');
    try {
      const { data } = await api.post('/api/ai/summarize', formData);
      setDocContext(data.text ? `[Document: ${file.name}]\n${data.text}` : null);
    } catch {
      setDocContext(`[Document atașat: ${file.name}]`);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setLoading(true);

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }]);

    try {
      const baseUrl = window.location.origin;
      const response = await fetch(`${baseUrl}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          session_id: activeSession,
          document_context: docContext,
          provider: selectedProvider !== 'auto' ? selectedProvider : undefined,
          context_mode: contextMode,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let sessionId = activeSession;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.error) {
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.streaming) {
                  last.content = `⚠️ ${data.error}`;
                  last.streaming = false;
                }
                return [...updated];
              });
              break;
            }

            if (data.chunk) {
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.streaming) {
                  last.content += data.chunk;
                  last.provider = data.provider;
                }
                return [...updated];
              });
            }

            if (data.done) {
              sessionId = data.session_id || sessionId;
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.streaming) {
                  last.streaming = false;
                  last.provider = data.provider;
                  last.model = data.model;
                }
                return [...updated];
              });
            }
          } catch { /* skip malformed SSE */ }
        }
      }

      if (sessionId && !activeSession) {
        setActiveSession(sessionId);
      }
      loadSessions();
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.streaming) {
          last.content = `⚠️ Eroare conexiune: ${err.message}`;
          last.streaming = false;
        }
        return [...updated];
      });
    } finally {
      setLoading(false);
    }
  };

  const saveApiKey = async (provider, value) => {
    if (!value.trim()) return;
    try {
      await api.post('/api/ai/config', { key: `${provider}_api_key`, value: value.trim() });
      loadProviders();
      setApiKeys(prev => ({ ...prev, [provider]: '' }));
      setEditingKey(null);
    } catch { /* toast handles it */ }
  };

  const anyProviderConfigured = providers.some(p => p.configured);
  const configuredProviders = providers.filter(p => p.configured);

  return (
    <div className="flex h-[calc(100vh-8rem)] -m-6">
      {/* Session sidebar */}
      <div className="w-64 bg-gray-900 border-r border-gray-700 flex flex-col">
        <div className="p-3 border-b border-gray-700 flex gap-2">
          <button onClick={newSession}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors">
            <Plus size={16} /> Chat Nou
          </button>
          <button onClick={clearAllSessions} title="Sterge toate conversatiile"
            className="p-2 rounded-lg hover:bg-red-700/50 text-gray-400 hover:text-red-400 transition-colors">
            <Trash2 size={16} />
          </button>
          <button onClick={() => setShowConfig(!showConfig)}
            className={`p-2 rounded-lg transition-colors ${showConfig ? 'bg-gray-600' : 'hover:bg-gray-700'}`}>
            <Settings2 size={16} />
          </button>
        </div>

        {showConfig && (
          <div className="p-3 border-b border-gray-700 space-y-2 text-xs">
            <div className="text-gray-400 font-medium mb-1">Provideri AI</div>
            {['gemini', 'openai', 'groq'].map(p => {
              const configured = providers.find(pr => pr.name === p)?.configured;
              const isEditing = editingKey === p;
              return (
                <div key={p} className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${configured ? 'bg-green-500' : 'bg-gray-600'}`} />
                  <span className="w-14 capitalize flex-shrink-0">{p}</span>
                  {configured && !isEditing ? (
                    <>
                      <span className="flex-1 text-green-400">✓ Configurat</span>
                      <button onClick={() => setEditingKey(p)}
                        className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-400">Modifică</button>
                    </>
                  ) : (
                    <>
                      <input type="password" placeholder="API key..."
                        value={apiKeys[p]} onChange={e => setApiKeys(prev => ({ ...prev, [p]: e.target.value }))}
                        onKeyDown={e => { if (e.key === 'Enter') saveApiKey(p, apiKeys[p]); if (e.key === 'Escape') setEditingKey(null); }}
                        autoFocus={isEditing}
                        className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs" />
                      <button onClick={() => saveApiKey(p, apiKeys[p])}
                        className="px-2 py-1 bg-blue-600 hover:bg-blue-500 rounded text-xs">OK</button>
                      {isEditing && (
                        <button onClick={() => setEditingKey(null)}
                          className="px-1 py-1 hover:text-red-400 text-gray-500"><X size={12} /></button>
                      )}
                    </>
                  )}
                </div>
              );
            })}
            {/* Token usage */}
            <div className="pt-2 border-t border-gray-800">
              <TokenIndicator />
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          {sessions.map(s => (
            <div key={s.id} onClick={() => loadSession(s.id)}
              className={`flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-gray-800 border-b border-gray-800 ${activeSession === s.id ? 'bg-gray-800' : ''}`}>
              <span className="text-sm truncate flex-1">{s.title}</span>
              <button onClick={e => deleteSession(s.id, e)}
                className="p-1 hover:text-red-400 opacity-50 hover:opacity-100">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col bg-gray-950">
        {/* Provider selector bar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-gray-800 bg-gray-900/50">
          <select value={selectedProvider} onChange={e => handleProviderChange(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs">
            <option value="auto">Auto (Chain)</option>
            {configuredProviders.map(p => (
              <option key={p.name} value={p.name}>{p.name.charAt(0).toUpperCase() + p.name.slice(1)} — {p.model}</option>
            ))}
          </select>
          <label className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer">
            <input type="checkbox" checked={contextMode} onChange={e => setContextMode(e.target.checked)}
              className="accent-purple-500" />
            <Database size={12} /> Context DB
          </label>
          <TokenIndicator compact />
          <button onClick={exportConversation} disabled={messages.length === 0}
            title="Exporta conversatia (.md)"
            className="ml-auto p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-blue-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            <Download size={16} />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <Bot size={48} className="mb-4 opacity-30" />
              <p className="text-lg">Începe o conversație</p>
              <p className="text-sm mt-1">
                {!backendOk
                  ? 'Backend deconectat — pornește serverul'
                  : anyProviderConfigured
                    ? 'Scrie un mesaj sau atașează un document'
                    : 'Configurează o cheie API din ⚙️ (stânga sus)'}
              </p>
              {anyProviderConfigured && (
                <p className="text-xs text-gray-600 mt-3">
                  Selectează un provider specific din bara de sus sau folosește Auto Chain.
                  {contextMode && ' Context DB activ — AI-ul cunoaște datele tale.'}
                </p>
              )}
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                  <Bot size={16} />
                </div>
              )}
              <div className={`max-w-[75%] rounded-xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}>
                <div className="whitespace-pre-wrap text-sm">{msg.content}
                  {msg.streaming && <span className="inline-block w-2 h-4 bg-blue-400 ml-1 animate-pulse" />}
                </div>
                {msg.provider && !msg.streaming && (
                  <div className="text-xs text-gray-400 mt-1 text-right">
                    {msg.provider}{msg.model ? ` (${msg.model})` : ''}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
                  <User size={16} />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Attached file indicator */}
        {attachedFile && (
          <div className="px-4 pb-1">
            <span className="inline-flex items-center gap-1 bg-gray-800 rounded-full px-3 py-1 text-xs text-gray-300">
              <Paperclip size={12} /> {attachedFile.name}
              <button onClick={() => { setAttachedFile(null); setDocContext(null); }}
                className="ml-1 hover:text-red-400"><X size={12} /></button>
            </span>
          </div>
        )}

        {/* Input area */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex gap-2">
            <button onClick={() => fileInputRef.current?.click()}
              className="p-3 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors" title="Atașează document">
              <Paperclip size={18} />
            </button>
            <input type="file" ref={fileInputRef} onChange={handleFileAttach} className="hidden"
              accept=".pdf,.docx,.txt,.md,.csv,.json" />
            <input ref={inputRef} type="text" value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder={!backendOk ? "Backend deconectat..." : anyProviderConfigured ? "Scrie un mesaj..." : "Configurează un provider AI mai întâi..."}
              disabled={!anyProviderConfigured || !backendOk}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50" />
            <button onClick={sendMessage} disabled={!input.trim() || loading || !anyProviderConfigured || !backendOk}
              className="p-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-colors">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
