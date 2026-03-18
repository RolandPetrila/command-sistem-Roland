import React, { useState } from 'react';
import { ThumbsUp, Check, Loader2 } from 'lucide-react';
import { validatePrice } from '../../api/client';

export default function SelfLearnButton({ uploadId, marketPrice }) {
  const [status, setStatus] = useState('idle'); // idle | loading | success | error

  const handleValidate = async () => {
    setStatus('loading');
    try {
      await validatePrice(uploadId, marketPrice);
      setStatus('success');
    } catch (err) {
      console.error('Eroare la validarea prețului:', err);
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
        <Check size={18} className="text-emerald-400" />
        <span className="text-sm font-medium text-emerald-400">
          Preț validat! Sistemul va învăța din această confirmare.
        </span>
      </div>
    );
  }

  return (
    <button
      onClick={handleValidate}
      disabled={status === 'loading'}
      className="btn-primary flex items-center gap-2"
    >
      {status === 'loading' ? (
        <Loader2 size={16} className="animate-spin" />
      ) : (
        <ThumbsUp size={16} />
      )}
      <span>{status === 'loading' ? 'Se procesează...' : 'Validez acest preț'}</span>
    </button>
  );
}
