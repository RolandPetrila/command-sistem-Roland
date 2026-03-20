import React, { useState, useEffect, useCallback } from 'react';
import { Activity } from 'lucide-react';

const PAYLOAD_SIZE_BYTES = 500 * 1024; // must match backend
const MEASURE_INTERVAL = 60000; // 60 seconds

function getColor(mbps) {
  if (mbps >= 10) return 'text-emerald-400';
  if (mbps >= 3) return 'text-yellow-400';
  return 'text-red-400';
}

function getLatencyColor(ms) {
  if (ms <= 50) return 'text-emerald-400';
  if (ms <= 150) return 'text-yellow-400';
  return 'text-red-400';
}

export default function NetworkSpeedIndicator() {
  const [speed, setSpeed] = useState(null); // Mbps
  const [latency, setLatency] = useState(null); // ms
  const [measuring, setMeasuring] = useState(false);

  const measure = useCallback(async () => {
    if (measuring) return;
    setMeasuring(true);

    try {
      // 1. Measure latency (ping health endpoint)
      const pingStart = performance.now();
      await fetch(`${window.location.origin}/api/health`, { cache: 'no-store' });
      const pingMs = Math.round(performance.now() - pingStart);
      setLatency(pingMs);

      // 2. Try Navigator.connection API first (instant, no extra request)
      const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (conn && conn.downlink) {
        setSpeed(conn.downlink); // already in Mbps
      } else {
        // 3. Fallback: download payload and measure
        const dlStart = performance.now();
        const resp = await fetch(`${window.location.origin}/api/network/speed-payload`, { cache: 'no-store' });
        await resp.arrayBuffer();
        const dlMs = performance.now() - dlStart;
        const mbps = ((PAYLOAD_SIZE_BYTES * 8) / (dlMs / 1000)) / 1_000_000;
        setSpeed(Math.round(mbps * 10) / 10);
      }
    } catch {
      setSpeed(null);
      setLatency(null);
    }

    setMeasuring(false);
  }, [measuring]);

  useEffect(() => {
    measure();
    const interval = setInterval(measure, MEASURE_INTERVAL);
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (speed === null && latency === null) return null;

  return (
    <button
      onClick={measure}
      disabled={measuring}
      className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] font-medium bg-slate-800/60 hover:bg-slate-700/60 transition-colors cursor-pointer border border-slate-700/50"
      title={`Viteza retea (click pt remesurare)\n${measuring ? 'Se masoara...' : `${speed ?? '?'} Mbps | ${latency ?? '?'} ms`}`}
    >
      <Activity size={12} className={measuring ? 'animate-pulse text-blue-400' : (speed !== null ? getColor(speed) : 'text-slate-500')} />
      {speed !== null && (
        <span className={getColor(speed)}>{speed} <span className="text-slate-500">Mbps</span></span>
      )}
      {latency !== null && (
        <span className={getLatencyColor(latency)}>{latency}<span className="text-slate-500">ms</span></span>
      )}
    </button>
  );
}
