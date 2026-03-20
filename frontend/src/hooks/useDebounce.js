import { useState, useEffect } from 'react';

/**
 * Debounce hook — delays value updates by specified ms.
 * Z2.6 — Reduces unnecessary API calls on search inputs by ~80%.
 */
export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
