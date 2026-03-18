import React, { useState, useRef } from 'react';
import { Upload, FileText, Tag, Database, PenTool, ScanLine, GitCompare, Loader2, X, Copy, Check } from 'lucide-react';
import api from '../api/client';

const TABS = [
  { id: 'analyze', label: 'Analiză', icon: FileText },
  { id: 'ocr', label: 'OCR Inteligent', icon: ScanLine },
  { id: 'diff', label: 'Comparare', icon: GitCompare },
];

export default function DocumentAIPage() {
  const [activeTab, setActiveTab] = useState('analyze');
  const [file, setFile] = useState(null);
  const [file2, setFile2] = useState(null);
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState('');
  const [copied, setCopied] = useState(false);
  const fileRef = useRef(null);
  const file2Ref = useRef(null);

  const handleFile = (e, setter) => {
    const f = e.target.files?.[0];
    if (f) { setter(f); setResult(null); }
  };

  const callEndpoint = async (endpoint, formData, actionLabel) => {
    setLoading(actionLabel);
    setResult(null);
    try {
      const { data } = await api.post(`/api/ai/${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult({ type: endpoint, data, error: null });
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setResult({ type: endpoint, data: null, error: msg });
    } finally {
      setLoading('');
    }
  };

  const runAction = (endpoint, actionLabel) => {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    if (endpoint === 'qa' && question.trim()) {
      fd.append('question', question.trim());
    }
    callEndpoint(endpoint, fd, actionLabel);
  };

  const runDiff = () => {
    if (!file || !file2) return;
    const fd = new FormData();
    fd.append('file1', file);
    fd.append('file2', file2);
    callEndpoint('diff', fd, 'Comparare');
  };

  const runOCR = () => {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    callEndpoint('ocr-enhance', fd, 'OCR');
  };

  const copyResult = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const DropZone = ({ fileState, setter, inputRef, label, accept }) => (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={e => e.preventDefault()}
      onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) { setter(f); setResult(null); } }}
      className="border-2 border-dashed border-gray-600 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition-colors"
    >
      <input type="file" ref={inputRef} onChange={e => handleFile(e, setter)} className="hidden"
        accept={accept || ".pdf,.docx,.txt,.md,.csv,.json,.png,.jpg,.jpeg,.tiff,.bmp,.webp"} />
      {fileState ? (
        <div className="flex items-center justify-center gap-2">
          <FileText size={20} className="text-blue-400" />
          <span className="text-sm">{fileState.name}</span>
          <button onClick={e => { e.stopPropagation(); setter(null); setResult(null); }}
            className="p-1 hover:text-red-400"><X size={14} /></button>
        </div>
      ) : (
        <div className="text-gray-400">
          <Upload size={24} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">{label || 'Trage fișierul aici sau click pentru a selecta'}</p>
        </div>
      )}
    </div>
  );

  const renderResult = () => {
    if (!result) return null;

    if (result.error) {
      return (
        <div className="mt-4 p-4 bg-red-900/30 border border-red-700 rounded-xl">
          <p className="text-red-400 text-sm">⚠️ {result.error}</p>
        </div>
      );
    }

    const d = result.data;

    // Diff result
    if (result.type === 'diff' && d?.ops) {
      return (
        <div className="mt-4 space-y-3">
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400">Similaritate: <strong className="text-white">{d.similarity}%</strong></span>
            <span className="text-green-400">+{d.stats.added} adăugate</span>
            <span className="text-red-400">-{d.stats.deleted} șterse</span>
            <span className="text-yellow-400">~{d.stats.changed} modificate</span>
          </div>
          <div className="bg-gray-900 rounded-xl overflow-hidden max-h-[500px] overflow-y-auto">
            {d.ops.map((op, i) => (
              <div key={i} className={`px-4 py-1 text-sm font-mono ${
                op.tag === 'equal' ? 'text-gray-400' :
                op.tag === 'insert' ? 'bg-green-900/30 text-green-300' :
                op.tag === 'delete' ? 'bg-red-900/30 text-red-300' :
                'bg-yellow-900/20 text-yellow-200'
              }`}>
                {op.tag === 'equal' && op.left_lines.slice(0, 3).map((line, j) => (
                  <div key={j}>{line || '\u00A0'}</div>
                ))}
                {op.tag === 'equal' && op.left_lines.length > 3 && (
                  <div className="text-gray-600 italic">... {op.left_lines.length - 3} linii identice ...</div>
                )}
                {op.tag === 'delete' && op.left_lines.map((line, j) => (
                  <div key={j}>- {line || '\u00A0'}</div>
                ))}
                {op.tag === 'insert' && op.right_lines.map((line, j) => (
                  <div key={j}>+ {line || '\u00A0'}</div>
                ))}
                {op.tag === 'replace' && (
                  <>
                    {op.left_lines.map((line, j) => (
                      <div key={`l${j}`} className="bg-red-900/30 text-red-300">- {line || '\u00A0'}</div>
                    ))}
                    {op.right_lines.map((line, j) => (
                      <div key={`r${j}`} className="bg-green-900/30 text-green-300">+ {line || '\u00A0'}</div>
                    ))}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      );
    }

    // OCR result
    if (result.type === 'ocr-enhance' && d) {
      return (
        <div className="mt-4 space-y-3">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-400">Text OCR brut</h4>
              </div>
              <pre className="bg-gray-900 rounded-xl p-4 text-xs max-h-80 overflow-y-auto whitespace-pre-wrap">{d.raw_text || 'Niciun text detectat'}</pre>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-green-400">Text corectat AI</h4>
                <button onClick={() => copyResult(d.enhanced_text)}
                  className="p-1 hover:text-blue-400 text-gray-500">
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>
              <pre className="bg-gray-900 rounded-xl p-4 text-xs max-h-80 overflow-y-auto whitespace-pre-wrap border border-green-900/50">{d.enhanced_text || d.raw_text}</pre>
            </div>
          </div>
          {d.provider && <p className="text-xs text-gray-500">Provider: {d.provider}</p>}
        </div>
      );
    }

    // Classify result
    if (result.type === 'classify' && d?.classification) {
      const c = typeof d.classification === 'object' && !d.classification.raw ? d.classification : null;
      return (
        <div className="mt-4 p-4 bg-gray-900 rounded-xl">
          {c ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Tag size={16} className="text-blue-400" />
                <span className="font-medium text-lg">{c.type}</span>
                {c.confidence && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    c.confidence === 'high' ? 'bg-green-900 text-green-300' :
                    c.confidence === 'medium' ? 'bg-yellow-900 text-yellow-300' :
                    'bg-gray-700 text-gray-300'
                  }`}>{c.confidence}</span>
                )}
              </div>
              {c.domain && <p className="text-sm text-gray-400">Domeniu: <span className="text-gray-200">{c.domain}</span></p>}
              {c.language && <p className="text-sm text-gray-400">Limbă: <span className="text-gray-200">{c.language}</span></p>}
              {c.description && <p className="text-sm text-gray-300 mt-2">{c.description}</p>}
            </div>
          ) : (
            <pre className="text-sm whitespace-pre-wrap">{d.classification.raw || JSON.stringify(d.classification, null, 2)}</pre>
          )}
          <p className="text-xs text-gray-500 mt-2">Provider: {d.provider}</p>
        </div>
      );
    }

    // Extract result
    if (result.type === 'extract' && d?.data) {
      const extracted = d.data;
      return (
        <div className="mt-4 p-4 bg-gray-900 rounded-xl">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium flex items-center gap-2">
              <Database size={16} className="text-blue-400" /> Date extrase
            </h4>
            <button onClick={() => copyResult(JSON.stringify(extracted, null, 2))}
              className="p-1 hover:text-blue-400 text-gray-500">
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
          {typeof extracted === 'object' && !extracted.raw ? (
            <div className="space-y-1 text-sm">
              {Object.entries(extracted).map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-gray-400 min-w-[120px]">{k}:</span>
                  <span className="text-gray-200">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                </div>
              ))}
            </div>
          ) : (
            <pre className="text-sm whitespace-pre-wrap">{extracted.raw || JSON.stringify(extracted, null, 2)}</pre>
          )}
          <p className="text-xs text-gray-500 mt-2">Provider: {d.provider}</p>
        </div>
      );
    }

    // Suggest name result
    if (result.type === 'suggest-name' && d) {
      return (
        <div className="mt-4 p-4 bg-gray-900 rounded-xl flex items-center gap-3">
          <PenTool size={16} className="text-blue-400" />
          <div>
            <p className="text-sm text-gray-400">{d.original} →</p>
            <p className="font-medium text-green-400">{d.suggested}</p>
          </div>
          <button onClick={() => copyResult(d.suggested)}
            className="ml-auto p-2 hover:text-blue-400 text-gray-500">
            {copied ? <Check size={16} /> : <Copy size={16} />}
          </button>
        </div>
      );
    }

    // Generic text result (summarize, qa)
    if (d?.text) {
      return (
        <div className="mt-4 p-4 bg-gray-900 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-500">Provider: {d.provider}</p>
            <button onClick={() => copyResult(d.text)}
              className="p-1 hover:text-blue-400 text-gray-500">
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
          <div className="text-sm whitespace-pre-wrap leading-relaxed">{d.text}</div>
        </div>
      );
    }

    return null;
  };

  const ActionBtn = ({ label, icon: Icon, action, endpoint, disabled }) => (
    <button onClick={() => action ? action() : runAction(endpoint, label)}
      disabled={disabled || !!loading}
      className="flex items-center gap-2 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-sm font-medium transition-colors">
      {loading === label ? <Loader2 size={16} className="animate-spin" /> : <Icon size={16} />}
      {label}
    </button>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Instrumente AI Documente</h1>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-xl p-1">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => { setActiveTab(tab.id); setResult(null); }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}>
            <tab.icon size={16} /> {tab.label}
          </button>
        ))}
      </div>

      {/* Analyze tab */}
      {activeTab === 'analyze' && (
        <div className="space-y-4">
          <DropZone fileState={file} setter={setFile} inputRef={fileRef}
            accept=".pdf,.docx,.txt,.md,.csv,.json"
            label="Trage un document (PDF, DOCX, TXT) sau click pentru a selecta" />

          {file && (
            <>
              <div className="flex flex-wrap gap-2">
                <ActionBtn label="Rezumă" icon={FileText} endpoint="summarize" disabled={!file} />
                <ActionBtn label="Clasifică" icon={Tag} endpoint="classify" disabled={!file} />
                <ActionBtn label="Extrage Date" icon={Database} endpoint="extract" disabled={!file} />
                <ActionBtn label="Sugerează Nume" icon={PenTool} endpoint="suggest-name" disabled={!file} />
              </div>

              <div className="flex gap-2">
                <input type="text" value={question} onChange={e => setQuestion(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && question.trim() && runAction('qa', 'Q&A')}
                  placeholder="Întreabă ceva despre document..."
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500" />
                <ActionBtn label="Q&A" icon={FileText} endpoint="qa" disabled={!file || !question.trim()} />
              </div>
            </>
          )}

          {renderResult()}
        </div>
      )}

      {/* OCR tab */}
      {activeTab === 'ocr' && (
        <div className="space-y-4">
          <DropZone fileState={file} setter={setFile} inputRef={fileRef}
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
            label="Trage o imagine sau PDF scanat" />

          {file && (
            <div className="flex gap-2">
              <ActionBtn label="OCR" icon={ScanLine} action={runOCR} disabled={!file} />
            </div>
          )}

          {renderResult()}
        </div>
      )}

      {/* Diff tab */}
      {activeTab === 'diff' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-400 mb-2">Document 1 (original)</p>
              <DropZone fileState={file} setter={setFile} inputRef={fileRef}
                accept=".pdf,.docx,.txt,.md" label="Document original" />
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-2">Document 2 (modificat)</p>
              <DropZone fileState={file2} setter={setFile2} inputRef={file2Ref}
                accept=".pdf,.docx,.txt,.md" label="Document modificat" />
            </div>
          </div>

          {file && file2 && (
            <ActionBtn label="Comparare" icon={GitCompare} action={runDiff} disabled={!file || !file2} />
          )}

          {renderResult()}
        </div>
      )}
    </div>
  );
}
