import React, { useState, useEffect } from 'react';
import { Calculator, Loader2, AlertTriangle, FileText } from 'lucide-react';
import DropZone from '../components/Upload/DropZone';
import FileList from '../components/Upload/FileList';
import ProgressBar from '../components/Upload/ProgressBar';
import PriceCard from '../components/Price/PriceCard';
import BreakdownTable from '../components/Price/BreakdownTable';
import MethodComparison from '../components/Price/MethodComparison';
import CompetitorComparison from '../components/Price/CompetitorComparison';
import ConfidenceBadge from '../components/Price/ConfidenceBadge';
import SelfLearnButton from '../components/Price/SelfLearnButton';
import PriceExplanation from '../components/Price/PriceExplanation';
import CompetitorAnalysis from '../components/Price/CompetitorAnalysis';
import { uploadFile, calculatePrice, getSettings, createProgressWebSocket } from '../api/client';

export default function UploadPage() {
  const [files, setFiles] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [percentage, setPercentage] = useState(0);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [currentFileName, setCurrentFileName] = useState('');
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [invoicePercent, setInvoicePercent] = useState(75);

  // Load default invoice percent from settings
  useEffect(() => {
    getSettings()
      .then((data) => {
        if (data.invoice_percent) setInvoicePercent(data.invoice_percent);
      })
      .catch(() => {});
  }, []);

  const handleFilesAdded = (newFiles) => {
    const updated = [...files, ...newFiles];
    setFiles(updated);
    setSelectedIds(updated.map((_, i) => i));
    setResults([]);
    setError('');
  };

  const handleToggleSelect = (idx) => {
    setSelectedIds((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  const handleSelectAll = () => {
    if (selectedIds.length === files.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(files.map((_, i) => i));
    }
  };

  const handleRemove = (idx) => {
    const newFiles = files.filter((_, i) => i !== idx);
    setFiles(newFiles);
    setSelectedIds((prev) =>
      prev.filter((i) => i !== idx).map((i) => (i > idx ? i - 1 : i))
    );
    if (newFiles.length === 0) {
      setResults([]);
    }
  };

  const handleCalculate = async () => {
    if (selectedIds.length === 0) return;

    setProcessing(true);
    setError('');
    setResults([]);
    setCurrentFileIndex(0);

    const totalFiles = selectedIds.length;
    const allResults = [];

    for (let i = 0; i < totalFiles; i++) {
      const fileIdx = selectedIds[i];
      const file = files[fileIdx];

      setCurrentFileIndex(i);
      setCurrentFileName(file.name);
      setCurrentStep('analyzing');
      setPercentage(Math.round((i / totalFiles) * 100));

      try {
        // Upload
        const uploadResult = await uploadFile(file);
        const currentUploadId = uploadResult.upload_id || uploadResult.id;

        setCurrentStep('calculating');
        setPercentage(Math.round(((i + 0.5) / totalFiles) * 100));

        // Calculate
        const calcResult = await calculatePrice(currentUploadId);

        allResults.push({
          ...calcResult,
          _uploadId: currentUploadId,
          _filename: file.name,
          _error: null,
        });
      } catch (err) {
        const msg = err.response?.data?.detail || err.message || 'Eroare necunoscută';
        allResults.push({
          _filename: file.name,
          _error: msg,
          _uploadId: null,
        });
      }
    }

    setPercentage(100);
    setCurrentStep('complete');
    setResults(allResults);
    setProcessing(false);
  };

  const totalMarketPrice = results
    .filter((r) => !r._error)
    .reduce((sum, r) => sum + (r.market_price || 0), 0);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Upload Section */}
      <DropZone onFilesAdded={handleFilesAdded} disabled={processing} />

      <FileList
        files={files}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
        onSelectAll={handleSelectAll}
        onRemove={handleRemove}
      />

      {/* Calculate Button */}
      {files.length > 0 && !processing && results.length === 0 && (
        <div className="flex justify-center">
          <button
            onClick={handleCalculate}
            disabled={selectedIds.length === 0}
            className="btn-primary flex items-center gap-2 text-lg px-8 py-3"
          >
            <Calculator size={20} />
            Calculează Prețul
            {selectedIds.length > 1 && (
              <span className="text-sm opacity-80">({selectedIds.length} fișiere)</span>
            )}
          </button>
        </div>
      )}

      {/* Progress */}
      {processing && (
        <div className="space-y-2">
          {selectedIds.length > 1 && (
            <div className="flex items-center justify-between text-sm text-slate-400 px-1">
              <span className="flex items-center gap-2">
                <Loader2 size={14} className="animate-spin" />
                Fișier {currentFileIndex + 1} / {selectedIds.length}: {currentFileName}
              </span>
              <span>{percentage}%</span>
            </div>
          )}
          <ProgressBar currentStep={currentStep} percentage={percentage} />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle size={20} className="text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-400">Eroare</p>
            <p className="text-sm text-red-300/80 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-8">
          {/* Total summary for multiple files */}
          {results.filter((r) => !r._error).length > 1 && (
            <div className="card glow-primary">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Total preț piață ({results.filter((r) => !r._error).length} fișiere)</p>
                  <p className="text-3xl font-bold text-white">
                    {totalMarketPrice.toFixed(2)}{' '}
                    <span className="text-lg text-slate-400 font-normal">RON</span>
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400 mb-1">Total facturat (75%)</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {(totalMarketPrice * (invoicePercent / 100)).toFixed(2)}{' '}
                    <span className="text-base text-slate-400 font-normal">RON</span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Individual results */}
          {results.map((result, idx) => (
            <div key={idx} className="space-y-4">
              {/* File header */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-primary-400" />
                  <h2 className="text-lg font-bold text-slate-100">{result._filename}</h2>
                </div>
                {!result._error && (
                  <ConfidenceBadge confidence={result.confidence} />
                )}
              </div>

              {/* Error for this file */}
              {result._error ? (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
                  <AlertTriangle size={18} className="text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-400">Eroare la procesare</p>
                    <p className="text-sm text-red-300/80 mt-1">{result._error}</p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <PriceCard
                      marketPrice={result.market_price}
                      defaultPercent={result.invoice_percent || invoicePercent}
                      dtp={result.dtp}
                      basePriceBeforeDtp={result.base_price_before_dtp}
                    />
                    <BreakdownTable breakdown={result.breakdown} />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <MethodComparison methodDetails={result.method_details} />
                    <CompetitorComparison marketPrice={result.market_price} />
                  </div>

                  {/* Warnings */}
                  {result.warnings && result.warnings.length > 0 && (
                    <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
                      <h4 className="text-sm font-semibold text-amber-400 mb-2">Avertismente</h4>
                      <ul className="space-y-1">
                        {result.warnings.map((w, i) => (
                          <li key={i} className="text-sm text-amber-300/80 flex items-start gap-2">
                            <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                            {w}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* AI Price Explanation */}
                  <PriceExplanation
                    calculationId={result._uploadId}
                    features={{ pages: result.pages, words: result.words, images: result.images, tables: result.tables }}
                    price={result.market_price}
                    confidence={result.confidence}
                  />

                  {/* AI Competitor Comparison */}
                  <CompetitorAnalysis
                    price={result.market_price}
                    pages={result.pages}
                    words={result.words}
                    docType={result.doc_type || 'general'}
                  />

                  {/* Self-learn button */}
                  <div className="flex justify-center">
                    <SelfLearnButton uploadId={result._uploadId} marketPrice={result.market_price} />
                  </div>
                </>
              )}

              {/* Separator between files */}
              {idx < results.length - 1 && (
                <div className="border-t border-slate-700/50 mt-4" />
              )}
            </div>
          ))}

          {/* Calculate another */}
          <div className="flex justify-center pt-2">
            <button
              onClick={() => {
                setFiles([]);
                setSelectedIds([]);
                setResults([]);
                setCurrentStep('');
                setPercentage(0);
                setError('');
                setCurrentFileName('');
                setCurrentFileIndex(0);
              }}
              className="btn-secondary"
            >
              Calculează alte fișiere
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
