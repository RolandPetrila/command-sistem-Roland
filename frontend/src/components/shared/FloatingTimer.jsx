import React, { useState, useEffect, useRef } from 'react';
import { Clock, Square } from 'lucide-react';
import api from '../../api/client';

function formatHMS(seconds) {
  if (!seconds || seconds < 0) return '00:00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function FloatingTimer() {
  const [activeTimer, setActiveTimer] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [stopping, setStopping] = useState(false);
  const tickRef = useRef(null);
  const pollRef = useRef(null);

  // Poll for active timer every 30 seconds
  useEffect(() => {
    const checkActive = async () => {
      try {
        const { data } = await api.get('/api/time/active');
        if (data && data.id) {
          setActiveTimer(data);
        } else {
          setActiveTimer(null);
        }
      } catch {
        // Endpoint might not exist yet or timer inactive — silent
        setActiveTimer(null);
      }
    };

    checkActive();
    pollRef.current = setInterval(checkActive, 30000);
    return () => clearInterval(pollRef.current);
  }, []);

  // Live tick every second when timer is active
  useEffect(() => {
    if (activeTimer && activeTimer.start_time) {
      const startTime = new Date(activeTimer.start_time).getTime();
      const tick = () => {
        setElapsed(Math.floor((Date.now() - startTime) / 1000));
      };
      tick();
      tickRef.current = setInterval(tick, 1000);
      return () => clearInterval(tickRef.current);
    } else {
      setElapsed(0);
      if (tickRef.current) clearInterval(tickRef.current);
    }
  }, [activeTimer]);

  // Listen for timer updates from TimeTrackingPage
  useEffect(() => {
    const handleTimerUpdate = (e) => {
      if (e.detail && e.detail.id) {
        setActiveTimer(e.detail);
      } else {
        setActiveTimer(null);
      }
    };
    window.addEventListener('timer-update', handleTimerUpdate);
    return () => window.removeEventListener('timer-update', handleTimerUpdate);
  }, []);

  const handleStop = async () => {
    if (!confirm('Opresti cronometrul?')) return;
    setStopping(true);
    try {
      await api.post('/api/time/stop');
      setActiveTimer(null);
      setElapsed(0);
      // Notify other components
      window.dispatchEvent(new CustomEvent('timer-update', { detail: null }));
    } catch {
      // Toast handles it
    }
    setStopping(false);
  };

  if (!activeTimer) return null;

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <div className="flex items-center gap-2 bg-blue-600/90 hover:bg-blue-600 backdrop-blur-sm text-white px-4 py-2.5 rounded-full shadow-lg border border-blue-500/50 transition-colors cursor-default">
        <Clock size={16} className="animate-pulse flex-shrink-0" />
        <span className="font-mono text-sm font-bold tabular-nums">{formatHMS(elapsed)}</span>
        <span className="text-sm text-blue-100 max-w-[150px] truncate hidden sm:inline">
          {activeTimer.project}
        </span>
        <button
          onClick={handleStop}
          disabled={stopping}
          className="ml-1 p-1 rounded-full hover:bg-blue-700/80 transition-colors"
          title="Opreste cronometrul"
        >
          <Square size={14} className={stopping ? 'opacity-50' : ''} />
        </button>
      </div>
    </div>
  );
}
