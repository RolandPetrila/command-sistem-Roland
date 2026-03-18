import React from 'react';
import { ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react';

export default function ConfidenceBadge({ confidence }) {
  const pct = typeof confidence === 'number' ? confidence : 0;

  let color, bgColor, borderColor, Icon, label;

  if (pct >= 90) {
    color = 'text-emerald-400';
    bgColor = 'bg-emerald-500/10';
    borderColor = 'border-emerald-500/30';
    Icon = ShieldCheck;
    label = 'Încredere ridicată';
  } else if (pct >= 70) {
    color = 'text-amber-400';
    bgColor = 'bg-amber-500/10';
    borderColor = 'border-amber-500/30';
    Icon = ShieldAlert;
    label = 'Încredere medie';
  } else {
    color = 'text-red-400';
    bgColor = 'bg-red-500/10';
    borderColor = 'border-red-500/30';
    Icon = ShieldX;
    label = 'Încredere scăzută';
  }

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${bgColor} ${borderColor}`}>
      <Icon size={18} className={color} />
      <div>
        <span className={`text-lg font-bold ${color}`}>{pct.toFixed(0)}%</span>
        <span className="text-xs text-slate-400 ml-2">{label}</span>
      </div>
    </div>
  );
}
