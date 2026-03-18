import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import CalibrationPanel from '../components/Calibration/CalibrationPanel';
import AccuracyChart from '../components/Calibration/AccuracyChart';
import { getCalibrationStatus } from '../api/client';

export default function CalibrationPage() {
  const [calibrationData, setCalibrationData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    setLoading(true);
    getCalibrationStatus()
      .then((data) => {
        // Extrage per_file_errors din accuracy (dacă există)
        const perFile = data.accuracy?.per_file_errors || data.per_file_accuracy || [];
        // Transformă în formatul așteptat de AccuracyChart
        const chartData = perFile.map((item) => ({
          name: item.filename,
          known_price: item.actual_price,
          calculated_price: item.predicted_price,
          error: item.absolute_error,
        }));
        setCalibrationData(chartData);
      })
      .catch(() => setCalibrationData([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      <CalibrationPanel onCalibrationChange={fetchData} />

      {loading ? (
        <div className="card flex items-center justify-center py-12">
          <Loader2 className="animate-spin text-primary-400" size={24} />
        </div>
      ) : (
        <AccuracyChart calibrationData={calibrationData} />
      )}
    </div>
  );
}
