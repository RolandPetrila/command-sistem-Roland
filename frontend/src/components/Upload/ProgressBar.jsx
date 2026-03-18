import React from 'react';
import { Loader2, CheckCircle2 } from 'lucide-react';

const STEPS = [
  { key: 'analyzing', label: 'Analizare' },
  { key: 'calculating', label: 'Calcul' },
  { key: 'validating', label: 'Validare' },
  { key: 'complete', label: 'Complet' },
];

export default function ProgressBar({ currentStep, percentage }) {
  const currentIdx = STEPS.findIndex((s) => s.key === currentStep);
  const isComplete = currentStep === 'complete';

  return (
    <div className="card mt-4">
      {/* Progress bar */}
      <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden mb-5">
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out ${
            isComplete
              ? 'bg-gradient-to-r from-primary-500 to-emerald-500'
              : 'bg-gradient-to-r from-primary-600 to-primary-400'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Steps */}
      <div className="flex justify-between">
        {STEPS.map((step, idx) => {
          const isDone = idx < currentIdx || isComplete;
          const isActive = idx === currentIdx && !isComplete;

          return (
            <div key={step.key} className="flex flex-col items-center gap-1.5">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isDone
                    ? 'bg-emerald-500/20 border border-emerald-500/40'
                    : isActive
                    ? 'bg-primary-500/20 border border-primary-500/40'
                    : 'bg-slate-800 border border-slate-700'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 size={16} className="text-emerald-400" />
                ) : isActive ? (
                  <Loader2 size={16} className="text-primary-400 animate-spin" />
                ) : (
                  <span className="text-xs text-slate-500">{idx + 1}</span>
                )}
              </div>
              <span
                className={`text-xs font-medium ${
                  isDone
                    ? 'text-emerald-400'
                    : isActive
                    ? 'text-primary-400'
                    : 'text-slate-500'
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Percentage */}
      <div className="text-center mt-3">
        <span className="text-2xl font-bold text-slate-200">{Math.round(percentage)}%</span>
      </div>
    </div>
  );
}
