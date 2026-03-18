import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import StatsCards from '../components/Dashboard/StatsCards';
import RecentActivity from '../components/Dashboard/RecentActivity';
import ActivityLog from '../components/Dashboard/ActivityLog';
import { getHistory, getCalibrationStatus } from '../api/client';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      try {
        const [historyData, calibrationData] = await Promise.allSettled([
          getHistory(),
          getCalibrationStatus(),
        ]);

        if (!mounted) return;

        const histVal = historyData.status === 'fulfilled' ? historyData.value : {};
        const entries = Array.isArray(histVal) ? histVal : (histVal.items || histVal.entries || []);
        const calibration = calibrationData.status === 'fulfilled' ? calibrationData.value : {};

        setHistory(entries);

        // Compute stats from history
        const totalCalc = entries.length;
        const avgPrice =
          totalCalc > 0
            ? entries.reduce((sum, e) => sum + (e.market_price || 0), 0) / totalCalc
            : 0;
        const avgAccuracy =
          totalCalc > 0
            ? entries.reduce((sum, e) => sum + (e.confidence || 0), 0) / totalCalc
            : 0;

        setStats({
          total_calculations: totalCalc,
          avg_price: avgPrice,
          avg_accuracy: avgAccuracy,
          reference_files: calibration.reference_count || 0,
        });
      } catch {
        if (mounted) {
          setStats({ total_calculations: 0, avg_price: 0, avg_accuracy: 0, reference_files: 0 });
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    fetchData();
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary-400" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <StatsCards stats={stats} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentActivity entries={history} />
        <ActivityLog />
      </div>
    </div>
  );
}
