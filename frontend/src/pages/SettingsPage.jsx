import React from 'react';
import InvoicePercent from '../components/Settings/InvoicePercent';
import SystemConfig from '../components/Settings/SystemConfig';

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <InvoicePercent />
      <SystemConfig />
    </div>
  );
}
