import React, { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Send, Paperclip, Bot, User, Loader2, X, Settings2 } from 'lucide-react';
import api from '../api/client';

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
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    loadSessions();
    loadProviders();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSessions = async () => {
    try {
      const { data } = await api.get('/api/ai/chat/sessions');
      setSessions(data);
    } catch { /* sessions table might not exist yet */ }
  };

  const loadProviders = async () => {
    try {
      const { data } = await api.get('/api/ai/providers');
      setProviders(data);
    } catch { /* ignore */ }
  };

  const loadSession = async (id) => {
    try {
      const { data } = await api.get(`/api/ai/chat/sessions/${id}`);
      setMessages(data.messages);
      setActiveSession(id);
    } catch { /* ignore */ }
  };

  const newSession = async () => {
    try {
      const { data } = await api.post('/api/ai/chat/sessions');
      setSessions(prev => [data, ...prev]);
      setActiveSession(data.id);
      setMessages([]);
    } catch { /* ignore */ }
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
    } catch { /* ignore */ }
  };

  const handleFileAttach = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAttachedFile(file);

    // Extract text for context
    const formData = new FormData();
    formData.append('file', file);
    formData.append('question', '__extract_only__');
    try {
      // Use summarize endpoint just to extract text
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

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    // Add empty assistant message for streaming
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

      // Update session
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
    } catch { /* ignore */ }
  };

  const anyProviderConfigured = providers.some(p => p.configured);

  return (
    <div className="flex h-[calc(100vh-8rem)] -m-6">
      {/* Session sidebar */}
      <div className="w-64 bg-gray-900 border-r border-gray-700 flex flex-col">
        <div className="p-3 border-b border-gray-700 flex gap-2">
          <button onClick={newSession}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors">
            <Plus size={16} /> Chat Nou
          </button>
          <button onClick={() => setShowConfig(!showConfig)}
            className={`p-2 rounded-lg transition-colors ${showConfig ? 'bg-gray-600' : 'hover:bg-gray-700'}`}>
            <Settings2 size={16} />
          </button>
        </div>

        {showConfig && (
          <div className="p-3 border-b border-gray-700 space-y-2 text-xs">
            <div className="text-gray-400 font-medium mb-1">Chei API</div>
            {['gemini', 'openai', 'groq'].map(p => (
              <div key={p} className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${providers.find(pr => pr.name === p)?.configured ? 'bg-green-500' : 'bg-gray-600'}`} />
                <span className="w-14 capitalize">{p}</span>
                <input type="password" placeholder="API key..."
                  value={apiKeys[p]} onChange={e => setApiKeys(prev => ({ ...prev, [p]: e.target.value }))}
                  onKeyDown={e => e.key === 'Enter' && saveApiKey(p, apiKeys[p])}
                  className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs" />
                <button onClick={() => saveApiKey(p, apiKeys[p])}
                  className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs">OK</button>
              </div>
            ))}
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
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <Bot size={48} className="mb-4 opacity-30" />
              <p className="text-lg">Începe o conversație</p>
              <p className="text-sm mt-1">
                {anyProviderConfigured
                  ? 'Scrie un mesaj sau atașează un document'
                  : 'Configurează o cheie API din ⚙️ (stânga sus)'}
              </p>
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
                  <div className="text-xs text-gray-400 mt-1 text-right">{msg.provider}</div>
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
              placeholder={anyProviderConfigured ? "Scrie un mesaj..." : "Configurează un provider AI mai întâi..."}
              disabled={!anyProviderConfigured}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50" />
            <button onClick={sendMessage} disabled={!input.trim() || loading || !anyProviderConfigured}
              className="p-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-colors">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
