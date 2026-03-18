import React from 'react';

const METHOD_LABELS = {
  rule_based: 'Bazat pe reguli',
  similarity: 'Similaritate',
  statistical: 'Statistic',
};

const METHOD_COLORS = {
  rule_based: { bg: 'bg-blue-500', bar: 'bg-blue-500/60', text: 'text-blue-400' },
  similarity: { bg: 'bg-emerald-500', bar: 'bg-emerald-500/60', text: 'text-emerald-400' },
  statistical: { bg: 'bg-amber-500', bar: 'bg-amber-500/60', text: 'text-amber-400' },
};

export default function MethodComparison({ methodDetails }) {
  if (!methodDetails || methodDetails.length === 0) return null;

  const maxPrice = Math.max(...methodDetails.map((m) => m.price || 0));

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Comparație Metode de Calcul</h3>

      <div className="space-y-4">
        {methodDetails.map((method) => {
          const key = method.method || method.name;
          const colors = METHOD_COLORS[key] || METHOD_COLORS.rule_based;
          const label = METHOD_LABELS[key] || key;
          const percentage = maxPrice > 0 ? ((method.price / maxPrice) * 100).toFixed(0) : 0;
          const weight = method.weight ? (method.weight * 100).toFixed(0) : '?';

          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${colors.bg}`} />
                  <span className="text-sm text-slate-300">{label}</span>
                  <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
                    pondere: {weight}%
                  </span>
                </div>
                <span className={`text-sm font-semibold ${colors.text}`}>
                  {Number(method.price).toFixed(2)} RON
                </span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${colors.bar} transition-all duration-500`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
