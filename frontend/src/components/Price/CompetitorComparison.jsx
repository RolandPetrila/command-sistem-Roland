import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { getCompetitorComparison } from '../../api/client';

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
        <p className="text-sm font-medium text-slate-200">{payload[0].payload.name}</p>
        <p className="text-sm text-primary-400 font-semibold">{payload[0].value.toFixed(2)} RON</p>
      </div>
    );
  }
  return null;
};

export default function CompetitorComparison({ marketPrice }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!marketPrice) return;
    let mounted = true;
    setLoading(true);

    getCompetitorComparison(marketPrice)
      .then((res) => {
        if (mounted) setData(res);
      })
      .catch(() => {
        // Use fallback data if endpoint not available
        if (mounted) {
          setData({
            our_price: marketPrice * 0.75,
            competitor_avg: marketPrice,
            competitors: [],
          });
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [marketPrice]);

  if (loading) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Comparație cu Concurența</h3>
        <div className="h-48 flex items-center justify-center">
          <div className="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  const ourPrice = data?.our_price || marketPrice * 0.75;
  const competitorAvg = data?.competitor_avg || marketPrice;
  const savings = competitorAvg - ourPrice;
  const savingsPercent = competitorAvg > 0 ? ((savings / competitorAvg) * 100).toFixed(0) : 0;

  const chartData = [
    { name: 'Prețul nostru', price: ourPrice, color: '#10B981' },
    { name: 'Media concurență', price: competitorAvg, color: '#3B82F6' },
  ];

  // Add individual competitors if available
  if (data?.competitors) {
    data.competitors.forEach((c) => {
      chartData.push({ name: c.name, price: c.price, color: '#64748B' });
    });
  }

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Comparație cu Concurența</h3>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: '#334155' }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: '#334155' }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="price" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {savings > 0 && (
        <div className="mt-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 text-center">
          <p className="text-sm text-emerald-400 font-medium">
            Economie client: {savings.toFixed(2)} RON ({savingsPercent}% sub piață)
          </p>
        </div>
      )}
    </div>
  );
}
