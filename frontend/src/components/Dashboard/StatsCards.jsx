import React from 'react';
import { Calculator, TrendingUp, Target, FileStack } from 'lucide-react';

const CARD_CONFIG = [
  {
    key: 'total_calculations',
    label: 'Total Calcule',
    icon: Calculator,
    color: 'text-primary-400',
    bgColor: 'bg-primary-500/10',
    borderColor: 'border-primary-500/20',
    format: (v) => String(v ?? 0),
  },
  {
    key: 'avg_price',
    label: 'Preț Mediu',
    icon: TrendingUp,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    format: (v) => `${Number(v ?? 0).toFixed(2)} RON`,
  },
  {
    key: 'avg_accuracy',
    label: 'Acuratețe Medie',
    icon: Target,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    format: (v) => `${Number(v ?? 0).toFixed(1)}%`,
  },
  {
    key: 'reference_files',
    label: 'Fișiere Reper',
    icon: FileStack,
    color: 'text-violet-400',
    bgColor: 'bg-violet-500/10',
    borderColor: 'border-violet-500/20',
    format: (v) => String(v ?? 0),
  },
];

export default function StatsCards({ stats }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {CARD_CONFIG.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.key} className={`card-hover border ${card.borderColor}`}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-slate-400 mb-1">{card.label}</p>
                <p className="text-2xl font-bold text-slate-100">
                  {card.format(stats?.[card.key])}
                </p>
              </div>
              <div className={`w-10 h-10 rounded-xl ${card.bgColor} flex items-center justify-center`}>
                <Icon size={20} className={card.color} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
