import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ErrorBar,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-slate-400 mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} className="text-sm" style={{ color: p.color }}>
            {p.name}: {Number(p.value).toFixed(2)} RON
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function AccuracyChart({ calibrationData }) {
  // calibrationData expected format:
  // [{name: "file.pdf", known_price: 100, calculated_price: 95, error: 5}, ...]

  if (!calibrationData || calibrationData.length === 0) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">
          Acuratețe per Fișier Reper
        </h3>
        <div className="py-12 text-center text-slate-400 text-sm">
          Nu sunt date de calibrare disponibile. Rulați calibrarea mai întâi.
        </div>
      </div>
    );
  }

  const data = calibrationData.map((item) => ({
    name: item.name?.length > 20 ? item.name.substring(0, 18) + '...' : item.name,
    fullName: item.name,
    'Preț cunoscut': item.known_price,
    'Preț calculat': item.calculated_price,
    error: item.error || Math.abs(item.known_price - item.calculated_price),
  }));

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">
        Acuratețe per Fișier Reper
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={{ stroke: '#334155' }}
            angle={-20}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            label={{ value: 'RON', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
          <Bar dataKey="Preț cunoscut" fill="#3B82F6" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Preț calculat" fill="#10B981" radius={[3, 3, 0, 0]}>
            <ErrorBar dataKey="error" width={4} strokeWidth={1.5} stroke="#F59E0B" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Accuracy summary */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        {(() => {
          const errors = data.map((d) => d.error);
          const avgError = errors.reduce((a, b) => a + b, 0) / errors.length;
          const maxError = Math.max(...errors);
          const minError = Math.min(...errors);
          return (
            <>
              <div className="bg-slate-800/60 rounded-lg p-3 text-center">
                <p className="text-xs text-slate-400">Eroare medie</p>
                <p className="text-sm font-semibold text-amber-400">{avgError.toFixed(2)} RON</p>
              </div>
              <div className="bg-slate-800/60 rounded-lg p-3 text-center">
                <p className="text-xs text-slate-400">Eroare maximă</p>
                <p className="text-sm font-semibold text-red-400">{maxError.toFixed(2)} RON</p>
              </div>
              <div className="bg-slate-800/60 rounded-lg p-3 text-center">
                <p className="text-xs text-slate-400">Eroare minimă</p>
                <p className="text-sm font-semibold text-emerald-400">{minError.toFixed(2)} RON</p>
              </div>
            </>
          );
        })()}
      </div>
    </div>
  );
}
