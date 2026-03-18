import React, { useState, useEffect } from 'react';
import { TrendingUp, Receipt, Layers } from 'lucide-react';

const DTP_COLORS = {
  none: 'text-slate-500',
  light: 'text-blue-400',
  medium: 'text-amber-400',
  heavy: 'text-red-400',
};

const DTP_BG = {
  none: 'bg-slate-500/10 border-slate-500/20',
  light: 'bg-blue-500/10 border-blue-500/20',
  medium: 'bg-amber-500/10 border-amber-500/20',
  heavy: 'bg-red-500/10 border-red-500/20',
};

export default function PriceCard({ marketPrice, defaultPercent = 75, dtp, basePriceBeforeDtp }) {
  const [percent, setPercent] = useState(defaultPercent);
  const invoicePrice = ((marketPrice * percent) / 100).toFixed(2);

  useEffect(() => {
    setPercent(defaultPercent);
  }, [defaultPercent]);

  const hasDtp = dtp && dtp.level && dtp.level !== 'none';

  return (
    <div className="card glow-primary">
      {/* Market Price */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="text-sm text-slate-400 mb-1 flex items-center gap-1.5">
            <TrendingUp size={14} />
            Preț piață {hasDtp ? '(cu DTP)' : ''}
          </p>
          <p className="text-4xl font-bold text-white">
            {Number(marketPrice).toFixed(2)}{' '}
            <span className="text-lg text-slate-400 font-normal">RON</span>
          </p>
          {hasDtp && basePriceBeforeDtp && (
            <p className="text-xs text-slate-500 mt-1">
              Preț traducere: {Number(basePriceBeforeDtp).toFixed(2)} RON × {dtp.factor} DTP
            </p>
          )}
        </div>
      </div>

      {/* DTP Badge */}
      {dtp && dtp.level && (
        <div className={`rounded-lg border p-3 mb-4 ${DTP_BG[dtp.level] || DTP_BG.none}`}>
          <div className="flex items-center gap-2 mb-1">
            <Layers size={14} className={DTP_COLORS[dtp.level] || DTP_COLORS.none} />
            <span className={`text-sm font-semibold ${DTP_COLORS[dtp.level] || DTP_COLORS.none}`}>
              {dtp.label}
            </span>
            {hasDtp && (
              <span className="text-xs text-slate-400 ml-auto">
                +{Math.round((dtp.factor - 1) * 100)}%
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">{dtp.reason}</p>
        </div>
      )}

      {/* Divider */}
      <div className="border-t border-slate-800 my-4" />

      {/* Invoice Price */}
      <div className="mb-4">
        <p className="text-sm text-slate-400 mb-1 flex items-center gap-1.5">
          <Receipt size={14} />
          Preț facturat
        </p>
        <p className="text-3xl font-bold text-emerald-400">
          {invoicePrice} <span className="text-base text-slate-400 font-normal">RON</span>
        </p>
      </div>

      {/* Percentage slider */}
      <div className="bg-slate-800/60 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm text-slate-300 font-medium">Procent facturare</label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={1}
              max={100}
              value={percent}
              onChange={(e) => {
                const val = Math.min(100, Math.max(1, Number(e.target.value) || 1));
                setPercent(val);
              }}
              className="w-16 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white text-center focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
            <span className="text-sm text-slate-400">%</span>
          </div>
        </div>
        <input
          type="range"
          min={1}
          max={100}
          value={percent}
          onChange={(e) => setPercent(Number(e.target.value))}
          className="w-full h-1.5 rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-500
            [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:cursor-pointer
            bg-gradient-to-r from-slate-700 to-primary-600"
        />
        <div className="flex justify-between text-[10px] text-slate-500 mt-1">
          <span>1%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  );
}
