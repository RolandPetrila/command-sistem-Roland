import React, { useState, useEffect } from 'react';
import { Receipt, Plus, Trash2, Pencil, Download, Send, Check, X, Users, FileText, Loader2, Bot, DollarSign, AlertTriangle, List, Mail, FileSpreadsheet, History, Search, ChevronLeft, ChevronRight, Shield, Copy, CreditCard, BarChart3, RefreshCw, Pause, Play, Archive, Clock } from 'lucide-react';
import api from '../api/client';

export default function InvoicePage() {
  const [tab, setTab] = useState('invoices'); // invoices | clients | create | series | overdue | offer | presets | recurring | payments | reports
  const [invoices, setInvoices] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  // Create invoice state
  const [editInvoice, setEditInvoice] = useState(null);
  const [items, setItems] = useState([{ description: '', quantity: 1, unit_price: 0 }]);
  const [selectedClient, setSelectedClient] = useState('');
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [vatPercent, setVatPercent] = useState(0);
  const [saving, setSaving] = useState(false);
  // Client form
  const [editClient, setEditClient] = useState(null);
  const [clientForm, setClientForm] = useState({ name: '', cui: '', address: '', email: '', phone: '', notes: '', default_payment_terms: '' });
  const [showClientForm, setShowClientForm] = useState(false);
  // F3: Series
  const [series, setSeries] = useState([]);
  const [newSeries, setNewSeries] = useState({ prefix: '', name: '', description: '' });
  // F4: Overdue
  const [overdue, setOverdue] = useState([]);
  // F9: Offer PDF
  const [offerForm, setOfferForm] = useState({ client_name: '', client_address: '', items: [{ description: '', quantity: 1, unit_price: 0 }], notes: '', validity_days: 30 });
  // R3-20: Email send
  const [emailModal, setEmailModal] = useState(null);
  const [emailTo, setEmailTo] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailSending, setEmailSending] = useState(false);
  // R3-22: Client history
  const [historyClient, setHistoryClient] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  // R3-23: CUI verify
  const [cuiVerifying, setCuiVerifying] = useState(false);
  const [cuiResult, setCuiResult] = useState(null);
  // R3-30: Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalInvoices, setTotalInvoices] = useState(0);
  const perPage = 20;
  // R3-17: AI generate modal
  const [showCalcModal, setShowCalcModal] = useState(false);
  const [recentCalcs, setRecentCalcs] = useState([]);
  // R3-31: Presets/templates
  const [presets, setPresets] = useState([]);
  const [presetsLoading, setPresetsLoading] = useState(false);
  const [newPreset, setNewPreset] = useState({ name: '', items: [{ description: '', quantity: 1, unit_price: 0 }], notes: '' });
  // R3-32: Recurring invoices
  const [recurring, setRecurring] = useState([]);
  const [recurringLoading, setRecurringLoading] = useState(false);
  const [newRecurring, setNewRecurring] = useState({ client_id: '', preset_id: '', interval_days: 30, next_date: '', enabled: true });
  // R3-33: Payments tracking
  const [paymentsInvoice, setPaymentsInvoice] = useState(null);
  const [payments, setPayments] = useState([]);
  const [paymentsLoading, setPaymentsLoading] = useState(false);
  const [newPayment, setNewPayment] = useState({ amount: '', date: new Date().toISOString().split('T')[0], method: 'transfer', notes: '' });
  // R3-34: Reports
  const [reports, setReports] = useState(null);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportPeriod, setReportPeriod] = useState('monthly');
  // R3-35: Search + filter
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  // R4-27: Duplicate warning
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  // R4-28: Batch PDF ZIP
  const [batchExporting, setBatchExporting] = useState(false);
  // R4-30: Recent items per client
  const [recentItems, setRecentItems] = useState([]);
  // Comm log
  const [commLog, setCommLog] = useState([]);
  const [newComm, setNewComm] = useState({ comm_type: 'note', summary: '', details: '' });

  useEffect(() => { loadData(); loadSeries(); loadOverdue(); }, [page, searchQuery, statusFilter, dateFrom, dateTo]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [inv, cli] = await Promise.allSettled([
        api.get('/api/invoice/list', { params: { page, per_page: perPage, ...(searchQuery && { search: searchQuery }), ...(statusFilter && { status: statusFilter }), ...(dateFrom && { date_from: dateFrom }), ...(dateTo && { date_to: dateTo }) } }),
        api.get('/api/invoice/clients'),
      ]);
      if (inv.status === 'fulfilled') {
        const d = inv.value.data;
        if (d?.items) {
          setInvoices(d.items);
          setTotalPages(d.pages || 1);
          setTotalInvoices(d.total || 0);
        } else {
          setInvoices(Array.isArray(d) ? d : []);
        }
      }
      if (cli.status === 'fulfilled') setClients(cli.value.data || []);
    } catch { /* toast handles it */ }
    setLoading(false);
  };

  // Invoice CRUD
  const handleCreateInvoice = async () => {
    if (!selectedClient || items.every(i => !i.description)) return;
    setSaving(true);
    setDuplicateWarning(null);
    try {
      const payload = {
        client_id: parseInt(selectedClient),
        date: invoiceDate,
        due_date: dueDate || null,
        items: items.filter(i => i.description),
        vat_percent: vatPercent,
        notes,
      };
      if (editInvoice) {
        await api.put(`/api/invoice/${editInvoice}`, payload);
      } else {
        const { data } = await api.post('/api/invoice/create', payload);
        // R4-27: Show duplicate warning if returned
        if (data?.warning) {
          setDuplicateWarning({ message: data.warning, duplicate_id: data.duplicate_id });
        }
      }
      setTab('invoices');
      resetInvoiceForm();
      loadData();
    } catch { /* toast handles it */ }
    setSaving(false);
  };

  const resetInvoiceForm = () => {
    setEditInvoice(null);
    setItems([{ description: '', quantity: 1, unit_price: 0 }]);
    setSelectedClient('');
    setNotes('');
    setVatPercent(0);
    setDuplicateWarning(null);
    setRecentItems([]);
  };

  const handleDeleteInvoice = async (id) => {
    try {
      await api.delete(`/api/invoice/${id}`);
      loadData();
    } catch { /* toast handles it */ }
  };

  const handleGeneratePdf = async (id) => {
    try {
      const { data } = await api.post(`/api/invoice/${id}/pdf`, {}, { responseType: 'blob' });
      const url = URL.createObjectURL(data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `factura_${id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* toast handles it */ }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await api.put(`/api/invoice/${id}/status`, { status });
      loadData();
    } catch { /* toast handles it */ }
  };

  const handleEditInvoice = async (id) => {
    try {
      const { data } = await api.get(`/api/invoice/${id}`);
      setEditInvoice(id);
      setSelectedClient(String(data.client_id || ''));
      setInvoiceDate(data.date);
      setDueDate(data.due_date || '');
      setItems(JSON.parse(data.items_json || '[]'));
      setNotes(data.notes || '');
      setVatPercent(data.vat_percent || 0);
      setTab('create');
    } catch { /* toast handles it */ }
  };

  // Client CRUD
  const handleSaveClient = async () => {
    if (!clientForm.name.trim()) return;
    try {
      if (editClient) {
        await api.put(`/api/invoice/clients/${editClient}`, clientForm);
      } else {
        await api.post('/api/invoice/clients', clientForm);
      }
      setShowClientForm(false);
      setEditClient(null);
      setClientForm({ name: '', cui: '', address: '', email: '', phone: '', notes: '', default_payment_terms: '' });
      loadData();
    } catch { /* toast handles it */ }
  };

  const handleEditClient = (client) => {
    setEditClient(client.id);
    setClientForm({ name: client.name, cui: client.cui || '', address: client.address || '', email: client.email || '', phone: client.phone || '', notes: client.notes || '', default_payment_terms: client.default_payment_terms || '' });
    setShowClientForm(true);
    setTab('clients');
  };

  const handleDeleteClient = async (id) => {
    try {
      await api.delete(`/api/invoice/clients/${id}`);
      loadData();
    } catch { /* toast handles it */ }
  };

  // R3-17: AI generate from calculation (modal instead of prompt)
  const handleAiGenerate = async () => {
    try {
      const { data } = await api.get('/api/price/history', { params: { limit: 10 } });
      setRecentCalcs(data?.calculations || data || []);
      setShowCalcModal(true);
    } catch { setShowCalcModal(true); setRecentCalcs([]); }
  };
  const selectCalc = async (calcId) => {
    setShowCalcModal(false);
    try {
      const { data } = await api.post('/api/invoice/generate-from-calc', { calculation_id: calcId });
      if (data.client_id) setSelectedClient(String(data.client_id));
      if (data.items) setItems(data.items);
      if (data.notes) setNotes(data.notes);
      setTab('create');
    } catch { /* toast handles it */ }
  };

  // R3-20: Send email
  const handleSendEmail = async (inv) => {
    const clientEmail = clients.find(c => c.id === inv.client_id)?.email || '';
    setEmailTo(clientEmail);
    setEmailSubject(`Factura ${inv.invoice_number} — CIP Inspection SRL`);
    setEmailModal(inv);
  };
  const sendEmail = async () => {
    if (!emailTo || !emailModal) return;
    setEmailSending(true);
    try {
      await api.post(`/api/invoice/${emailModal.id}/send-email`, { to_email: emailTo, subject: emailSubject });
      setEmailModal(null);
    } catch { /* toast handles it */ }
    setEmailSending(false);
  };

  // R3-21: Export CSV/Excel
  const handleExport = async (format) => {
    try {
      const endpoint = format === 'excel' ? '/api/invoice/export/excel' : '/api/invoice/export/csv';
      const { data } = await api.get(endpoint, { responseType: 'blob' });
      const url = URL.createObjectURL(data);
      const a = document.createElement('a'); a.href = url; a.download = `facturi.${format === 'excel' ? 'xlsx' : 'csv'}`; a.click(); URL.revokeObjectURL(url);
    } catch { /* toast handles it */ }
  };

  // R4-28: Batch PDF ZIP export
  const handleBatchPdfExport = async () => {
    setBatchExporting(true);
    try {
      const payload = {};
      const visibleIds = invoices.map(i => i.id);
      if (visibleIds.length > 0) {
        payload.invoice_ids = visibleIds;
      } else if (dateFrom || dateTo) {
        if (dateFrom) payload.date_from = dateFrom;
        if (dateTo) payload.date_to = dateTo;
      }
      if (!payload.invoice_ids && !payload.date_from && !payload.date_to) {
        payload.date_from = '2000-01-01';
      }
      const { data } = await api.post('/api/invoice/export-batch-pdf', payload, { responseType: 'blob' });
      if (data.type && data.type.includes('json')) {
        const text = await data.text();
        const parsed = JSON.parse(text);
        return;
      }
      const url = URL.createObjectURL(data);
      const a = document.createElement('a'); a.href = url; a.download = `facturi_${new Date().toISOString().split('T')[0]}.zip`; a.click(); URL.revokeObjectURL(url);
    } catch { /* toast handles it */ }
    setBatchExporting(false);
  };

  // R4-30: Load recent items for selected client
  const loadRecentItems = async (clientId) => {
    if (!clientId) { setRecentItems([]); return; }
    try {
      const { data } = await api.get(`/api/invoice/items/recent/${clientId}`);
      setRecentItems(data || []);
    } catch { setRecentItems([]); }
  };

  // R4-29: Auto-fill due_date from client payment terms
  const autoFillDueDate = (clientId) => {
    const client = clients.find(c => c.id === parseInt(clientId));
    if (client?.default_payment_terms && !dueDate) {
      const termsMap = { immediate: 0, net_15: 15, net_30: 30, net_45: 45 };
      const days = termsMap[client.default_payment_terms];
      if (days !== undefined) {
        const d = new Date(invoiceDate || new Date());
        d.setDate(d.getDate() + days);
        setDueDate(d.toISOString().split('T')[0]);
      }
    }
  };

  // R3-22: Client history
  const showHistory = async (client) => {
    setHistoryClient(client);
    setHistoryLoading(true);
    try {
      const { data } = await api.get(`/api/invoice/clients/${client.id}/history`);
      setHistoryData(data?.invoices || data || []);
    } catch { setHistoryData([]); }
    setHistoryLoading(false);
    loadCommLog(client.id);
  };

  // Comm log functions
  const loadCommLog = async (clientId) => {
    try {
      const { data } = await api.get(`/api/invoice/clients/${clientId}/comm-log`);
      setCommLog(data.entries || []);
    } catch { setCommLog([]); }
  };
  const addCommEntry = async (clientId) => {
    if (!newComm.summary.trim()) return;
    try {
      await api.post(`/api/invoice/clients/${clientId}/comm-log`, newComm);
      setNewComm({ comm_type: 'note', summary: '', details: '' });
      loadCommLog(clientId);
    } catch { /* toast handles it */ }
  };

  // R3-23: CUI verify ANAF
  const verifyCUI = async () => {
    if (!clientForm.cui) return;
    setCuiVerifying(true);
    setCuiResult(null);
    try {
      const { data } = await api.get('/api/anaf/verify', { params: { cui: clientForm.cui } });
      setCuiResult(data);
      if (data?.name) setClientForm(p => ({ ...p, name: p.name || data.name, address: p.address || data.address || '' }));
    } catch { setCuiResult({ error: 'Eroare verificare ANAF' }); }
    setCuiVerifying(false);
  };

  // R3-31: Presets/templates
  const loadPresets = async () => {
    setPresetsLoading(true);
    try { const { data } = await api.get('/api/invoice/presets'); setPresets(data?.presets || data || []); } catch { setPresets([]); }
    setPresetsLoading(false);
  };
  const savePreset = async () => {
    if (!newPreset.name.trim()) return;
    try {
      await api.post('/api/invoice/presets', newPreset);
      setNewPreset({ name: '', items: [{ description: '', quantity: 1, unit_price: 0 }], notes: '' });
      loadPresets();
    } catch { /* toast handles it */ }
  };
  const deletePreset = async (id) => {
    try { await api.delete(`/api/invoice/presets/${id}`); loadPresets(); } catch { /* toast handles it */ }
  };
  const applyPreset = (preset) => {
    if (preset.items) setItems(JSON.parse(typeof preset.items === 'string' ? preset.items : JSON.stringify(preset.items)));
    if (preset.notes) setNotes(preset.notes);
    setTab('create');
  };

  // R3-32: Recurring invoices
  const loadRecurring = async () => {
    setRecurringLoading(true);
    try { const { data } = await api.get('/api/invoice/recurring'); setRecurring(data?.items || data || []); } catch { setRecurring([]); }
    setRecurringLoading(false);
  };
  const saveRecurring = async () => {
    if (!newRecurring.client_id) return;
    try {
      await api.post('/api/invoice/recurring', newRecurring);
      setNewRecurring({ client_id: '', preset_id: '', interval_days: 30, next_date: '', enabled: true });
      loadRecurring();
    } catch { /* toast handles it */ }
  };
  const toggleRecurring = async (id, enabled) => {
    try { await api.put(`/api/invoice/recurring/${id}`, { enabled: !enabled }); loadRecurring(); } catch { /* toast handles it */ }
  };
  const deleteRecurring = async (id) => {
    try { await api.delete(`/api/invoice/recurring/${id}`); loadRecurring(); } catch { /* toast handles it */ }
  };

  // R3-33: Payments tracking
  const loadPayments = async (inv) => {
    setPaymentsInvoice(inv);
    setPaymentsLoading(true);
    try { const { data } = await api.get(`/api/invoice/${inv.id}/payments`); setPayments(data?.payments || data || []); } catch { setPayments([]); }
    setPaymentsLoading(false);
  };
  const addPayment = async () => {
    if (!newPayment.amount || !paymentsInvoice) return;
    try {
      await api.post(`/api/invoice/${paymentsInvoice.id}/payments`, { ...newPayment, amount: parseFloat(newPayment.amount) });
      setNewPayment({ amount: '', date: new Date().toISOString().split('T')[0], method: 'transfer', notes: '' });
      loadPayments(paymentsInvoice);
      loadData();
    } catch { /* toast handles it */ }
  };

  // R3-34: Invoice reports
  const loadReports = async () => {
    setReportsLoading(true);
    try { const { data } = await api.get('/api/invoice/reports', { params: { period: reportPeriod } }); setReports(data); } catch { setReports(null); }
    setReportsLoading(false);
  };

  // F3: Series management
  const loadSeries = async () => {
    try { const { data } = await api.get('/api/invoice/series'); setSeries(data || []); } catch { /* toast handles it */ }
  };
  const createSeries = async () => {
    if (!newSeries.prefix.trim() || !newSeries.name.trim()) return;
    try {
      await api.post('/api/invoice/series', newSeries);
      setNewSeries({ prefix: '', name: '', description: '' });
      loadSeries();
    } catch { /* toast handles it */ }
  };
  const setDefault = async (id) => {
    try { await api.put(`/api/invoice/series/${id}/default`); loadSeries(); } catch { /* toast handles it */ }
  };

  // F4: Overdue
  const loadOverdue = async () => {
    try { const { data } = await api.get('/api/invoice/overdue'); setOverdue(data || []); } catch { /* toast handles it */ }
  };
  const markPaid = async (id) => {
    try { await api.put(`/api/invoice/${id}/payment`); loadData(); loadOverdue(); } catch { /* toast handles it */ }
  };

  // F9: Generate offer PDF
  const generateOffer = async () => {
    try {
      const { data } = await api.post('/api/invoice/offer-pdf', offerForm, { responseType: 'blob' });
      const url = URL.createObjectURL(data);
      const a = document.createElement('a'); a.href = url; a.download = `oferta_${offerForm.client_name}.pdf`; a.click(); URL.revokeObjectURL(url);
    } catch { /* toast handles it */ }
  };

  const addItem = () => setItems([...items, { description: '', quantity: 1, unit_price: 0 }]);
  const removeItem = (i) => setItems(items.filter((_, idx) => idx !== i));
  const updateItem = (i, field, value) => {
    const updated = [...items];
    updated[i] = { ...updated[i], [field]: field === 'description' ? value : parseFloat(value) || 0 };
    setItems(updated);
  };

  const subtotal = items.reduce((sum, i) => sum + (i.quantity || 0) * (i.unit_price || 0), 0);
  const vatAmount = subtotal * (vatPercent / 100);
  const total = subtotal + vatAmount;

  const statusColors = {
    draft:     'bg-gray-700 text-gray-400',
    sent:      'bg-blue-900/50 text-blue-400',
    paid:      'bg-green-900/50 text-green-400',
    cancelled: 'bg-red-900/50 text-red-400',
    overdue:   'bg-red-900/50 text-red-400',
    partial:   'bg-yellow-900/50 text-yellow-400',
  };
  const statusLabels = { draft: 'Ciornă', sent: 'Trimisă', paid: 'Plătită', cancelled: 'Anulată', overdue: 'Scadentă', partial: 'Parțial' };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-blue-400" size={32} /></div>;

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-xl p-1 overflow-x-auto">
        {[
          { id: 'invoices', label: 'Facturi', icon: Receipt },
          { id: 'clients', label: 'Clienti', icon: Users },
          { id: 'create', label: editInvoice ? 'Editeaza' : 'Factura Noua', icon: Plus },
          { id: 'overdue', label: `Scadente${overdue.length ? ` (${overdue.length})` : ''}`, icon: AlertTriangle },
          { id: 'series', label: 'Serii', icon: List },
          { id: 'offer', label: 'Oferta PDF', icon: FileText },
          { id: 'presets', label: 'Sabloane', icon: Copy },
          { id: 'recurring', label: 'Recurente', icon: RefreshCw },
          { id: 'reports', label: 'Rapoarte', icon: BarChart3 },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${tab === t.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
            <t.icon size={14} /> {t.label}
          </button>
        ))}
        <button onClick={handleAiGenerate}
          className="ml-auto flex items-center gap-1 px-3 py-2 text-xs text-purple-400 hover:bg-purple-900/20 rounded-lg transition-colors">
          <Bot size={14} /> AI
        </button>
      </div>

      {/* R4-27: Duplicate warning banner */}
      {duplicateWarning && (
        <div className="flex items-center gap-3 bg-yellow-900/30 border border-yellow-700/40 rounded-xl px-4 py-3 text-yellow-300 text-sm">
          <AlertTriangle size={18} className="shrink-0" />
          <span className="flex-1">{duplicateWarning.message}</span>
          {duplicateWarning.duplicate_id && (
            <button onClick={() => { handleEditInvoice(duplicateWarning.duplicate_id); setDuplicateWarning(null); }}
              className="px-3 py-1 bg-yellow-800/50 hover:bg-yellow-800 rounded-lg text-xs whitespace-nowrap">
              Vezi factura
            </button>
          )}
          <button onClick={() => setDuplicateWarning(null)} className="p-1 hover:bg-yellow-800/50 rounded"><X size={14} /></button>
        </div>
      )}

      {/* INVOICES LIST */}
      {tab === 'invoices' && (
        <div className="space-y-2">
          {/* R3-35: Search + filter bar */}
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
              <input value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
                placeholder="Cauta numar factura, client..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none" />
            </div>
            <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs">
              <option value="">Toate statusurile</option>
              <option value="draft">Ciorna</option>
              <option value="sent">Trimisa</option>
              <option value="paid">Platita</option>
              <option value="cancelled">Anulata</option>
            </select>
            <input type="date" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPage(1); }}
              className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs" title="De la data" />
            <input type="date" value={dateTo} onChange={e => { setDateTo(e.target.value); setPage(1); }}
              className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs" title="Pana la data" />
            {(searchQuery || statusFilter || dateFrom || dateTo) && (
              <button onClick={() => { setSearchQuery(''); setStatusFilter(''); setDateFrom(''); setDateTo(''); setPage(1); }}
                className="px-2 py-1.5 text-xs text-gray-400 hover:text-white"><X size={14} /></button>
            )}
          </div>
          {/* R3-21: Export toolbar */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">{totalInvoices} facturi total</span>
            <div className="flex gap-2">
              <button onClick={() => handleExport('csv')} className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs text-gray-300">
                <Download size={12} /> CSV
              </button>
              <button onClick={() => handleExport('excel')} className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs text-gray-300">
                <FileSpreadsheet size={12} /> Excel
              </button>
              <button onClick={handleBatchPdfExport} disabled={batchExporting || invoices.length === 0}
                className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 rounded-lg text-xs text-gray-300">
                {batchExporting ? <Loader2 size={12} className="animate-spin" /> : <Archive size={12} />} PDF-uri (ZIP)
              </button>
            </div>
          </div>
          {invoices.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Receipt size={48} className="mx-auto mb-3 opacity-30" />
              <p>Nicio factura. Creeaza prima factura!</p>
            </div>
          )}
          {invoices.map(inv => (
            <div key={inv.id} className="bg-gray-900 rounded-xl p-4 flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{inv.invoice_number}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[inv.status] || ''}`}>
                    {statusLabels[inv.status] || inv.status}
                  </span>
                </div>
                <div className="text-sm text-gray-400">{inv.client_name || 'Client necunoscut'} — {inv.date}</div>
              </div>
              <div className="text-right">
                <div className="font-bold text-lg">{inv.total?.toFixed(2)} {inv.currency}</div>
              </div>
              <div className="flex gap-1">
                <button onClick={() => handleGeneratePdf(inv.id)} className="p-2 hover:bg-gray-800 rounded-lg" title="Descarca PDF"><Download size={16} /></button>
                <button onClick={() => window.open(`/api/invoice/${inv.id}/efactura-xml`, '_blank')}
                  className="p-2 hover:bg-gray-800 rounded-lg text-green-400" title="Download e-Factura XML">
                  <FileText size={16} />
                </button>
                <button onClick={() => handleSendEmail(inv)} className="p-2 hover:bg-gray-800 rounded-lg text-blue-400" title="Trimite email"><Mail size={16} /></button>
                <button onClick={() => loadPayments(inv)} className="p-2 hover:bg-gray-800 rounded-lg text-green-400" title="Plati"><CreditCard size={16} /></button>
                {inv.status === 'draft' && (
                  <>
                    <button onClick={() => handleEditInvoice(inv.id)} className="p-2 hover:bg-gray-800 rounded-lg" title="Editeaza"><Pencil size={16} /></button>
                    <button onClick={() => handleStatusChange(inv.id, 'sent')} className="p-2 hover:bg-gray-800 rounded-lg text-blue-400" title="Marcheaza trimisa"><Send size={16} /></button>
                    <button onClick={() => handleDeleteInvoice(inv.id)} className="p-2 hover:bg-gray-800 rounded-lg text-red-400" title="Sterge"><Trash2 size={16} /></button>
                  </>
                )}
                {inv.status === 'sent' && (
                  <button onClick={() => handleStatusChange(inv.id, 'paid')} className="p-2 hover:bg-gray-800 rounded-lg text-green-400" title="Marcheaza platita"><Check size={16} /></button>
                )}
              </div>
            </div>
          ))}
          {/* R3-30: Pagination controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-gray-500">Pagina {page} din {totalPages}</span>
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
                  className="p-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 rounded text-gray-400"><ChevronLeft size={16} /></button>
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                  className="p-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 rounded text-gray-400"><ChevronRight size={16} /></button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* CLIENTS LIST */}
      {tab === 'clients' && (
        <div className="space-y-3">
          <button onClick={() => { setShowClientForm(true); setEditClient(null); setClientForm({ name: '', cui: '', address: '', email: '', phone: '', notes: '', default_payment_terms: '' }); }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
            <Plus size={14} /> Client nou
          </button>
          {showClientForm && (
            <div className="bg-gray-900 rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input value={clientForm.name} onChange={e => setClientForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="Nume / Firma *" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <div className="flex gap-1">
                  <input value={clientForm.cui} onChange={e => setClientForm(p => ({ ...p, cui: e.target.value }))}
                    placeholder="CUI" className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                  <button onClick={verifyCUI} disabled={cuiVerifying || !clientForm.cui}
                    className="px-2 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded-lg text-xs flex items-center gap-1" title="Verifica ANAF">
                    {cuiVerifying ? <Loader2 size={12} className="animate-spin" /> : <Shield size={12} />} ANAF
                  </button>
                </div>
                <input value={clientForm.address} onChange={e => setClientForm(p => ({ ...p, address: e.target.value }))}
                  placeholder="Adresa" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <input value={clientForm.email} onChange={e => setClientForm(p => ({ ...p, email: e.target.value }))}
                  placeholder="Email" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <input value={clientForm.phone} onChange={e => setClientForm(p => ({ ...p, phone: e.target.value }))}
                  placeholder="Telefon" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <select value={clientForm.default_payment_terms} onChange={e => setClientForm(p => ({ ...p, default_payment_terms: e.target.value }))}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                  <option value="">Termen plata implicit</option>
                  <option value="immediate">Imediat</option>
                  <option value="net_15">Net 15 zile</option>
                  <option value="net_30">Net 30 zile</option>
                  <option value="net_45">Net 45 zile</option>
                </select>
                <input value={clientForm.notes} onChange={e => setClientForm(p => ({ ...p, notes: e.target.value }))}
                  placeholder="Note" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              {cuiResult && (
                <div className={`text-xs p-2 rounded ${cuiResult.error ? 'bg-red-900/20 text-red-400' : 'bg-green-900/20 text-green-400'}`}>
                  {cuiResult.error || `${cuiResult.name || 'OK'} — ${cuiResult.address || ''}`}
                </div>
              )}
              <div className="flex gap-2">
                <button onClick={handleSaveClient} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm">
                  {editClient ? 'Actualizeaza' : 'Salveaza'}
                </button>
                <button onClick={() => { setShowClientForm(false); setEditClient(null); setCuiResult(null); }}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm">Anuleaza</button>
              </div>
            </div>
          )}
          {clients.map(client => (
            <div key={client.id} className="bg-gray-900 rounded-xl p-4 flex items-center gap-4 group">
              <Users size={18} className="text-gray-500" />
              <div className="flex-1">
                <div className="font-medium">{client.name}</div>
                <div className="text-xs text-gray-500">
                  {[client.cui, client.email, client.phone, client.default_payment_terms && `Termen: ${client.default_payment_terms.replace('_', ' ')}`].filter(Boolean).join(' | ')}
                </div>
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => showHistory(client)} className="p-2 hover:bg-gray-800 rounded-lg text-blue-400" title="Istoric facturi"><History size={14} /></button>
                <button onClick={() => handleEditClient(client)} className="p-2 hover:bg-gray-800 rounded-lg"><Pencil size={14} /></button>
                <button onClick={() => handleDeleteClient(client.id)} className="p-2 hover:bg-gray-800 rounded-lg text-red-400"><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
          {clients.length === 0 && !showClientForm && (
            <p className="text-center py-8 text-gray-500">Niciun client. Adaugă primul client!</p>
          )}
        </div>
      )}

      {/* CREATE INVOICE */}
      {tab === 'create' && (
        <div className="bg-gray-900 rounded-xl p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Client *</label>
              <select value={selectedClient} onChange={e => { setSelectedClient(e.target.value); loadRecentItems(e.target.value); autoFillDueDate(e.target.value); }}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                <option value="">— Selectează client —</option>
                {clients.map(c => <option key={c.id} value={c.id}>{c.name}{c.cui ? ` (${c.cui})` : ''}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Data facturii</label>
              <input type="date" value={invoiceDate} onChange={e => setInvoiceDate(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Scadență</label>
              <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>

          {/* Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium">Articole</label>
              <button onClick={addItem} className="text-xs text-blue-400 hover:text-blue-300">+ Adaugă rând</button>
            </div>
            <div className="space-y-2">
              {items.map((item, i) => (
                <div key={i} className="grid grid-cols-12 gap-2 items-center">
                  <input value={item.description} onChange={e => updateItem(i, 'description', e.target.value)}
                    placeholder="Descriere serviciu..." className="col-span-6 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                  <input type="number" value={item.quantity} onChange={e => updateItem(i, 'quantity', e.target.value)}
                    className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-center" min="1" />
                  <input type="number" value={item.unit_price} onChange={e => updateItem(i, 'unit_price', e.target.value)}
                    className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-right" step="0.01" />
                  <span className="col-span-1 text-sm text-right text-gray-400">{((item.quantity || 0) * (item.unit_price || 0)).toFixed(2)}</span>
                  <button onClick={() => removeItem(i)} className="col-span-1 text-red-400 hover:text-red-300 justify-self-center">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* R4-30: Recent items for selected client */}
          {selectedClient && recentItems.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Clock size={14} className="text-gray-500" />
                <label className="text-xs text-gray-500 font-medium">Articole recente ale clientului</label>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {recentItems.map((ri, idx) => (
                  <button key={idx} onClick={() => setItems(prev => [...prev.filter(i => i.description), { description: ri.description, quantity: ri.quantity, unit_price: ri.unit_price }])}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-xs text-gray-300 transition-colors"
                    title={`${ri.quantity} x ${ri.unit_price} RON`}>
                    <Plus size={10} className="text-blue-400" />
                    <span className="max-w-[200px] truncate">{ri.description}</span>
                    <span className="text-gray-500">{ri.unit_price} RON</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Totals */}
          <div className="flex justify-end">
            <div className="w-64 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">Subtotal:</span><span>{subtotal.toFixed(2)} RON</span></div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">TVA:</span>
                <div className="flex items-center gap-2">
                  <input type="number" value={vatPercent} onChange={e => setVatPercent(parseFloat(e.target.value) || 0)}
                    className="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-right" />
                  <span className="text-xs text-gray-500">%</span>
                  <span>{vatAmount.toFixed(2)} RON</span>
                </div>
              </div>
              <div className="flex justify-between font-bold text-lg border-t border-gray-700 pt-2">
                <span>Total:</span><span className="text-green-400">{total.toFixed(2)} RON</span>
              </div>
            </div>
          </div>

          {/* Notes + Save */}
          <textarea value={notes} onChange={e => setNotes(e.target.value)}
            placeholder="Note adiționale (opțional)..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm resize-none h-20" />
          <InvoicePreview
            client={clients.find(c => c.id == selectedClient)?.name}
            items={items}
            invoiceDate={invoiceDate}
            dueDate={dueDate}
            notes={notes}
            vatPercent={vatPercent}
          />
          <div className="flex gap-3">
            <button onClick={handleCreateInvoice} disabled={saving || !selectedClient}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl text-sm font-medium transition-colors">
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Receipt size={16} />}
              {editInvoice ? 'Actualizează Factura' : 'Creează Factura'}
            </button>
            <button onClick={() => { setTab('invoices'); resetInvoiceForm(); }}
              className="px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-xl text-sm">Anulează</button>
          </div>
        </div>
      )}

      {/* OVERDUE INVOICES (F4) */}
      {tab === 'overdue' && (
        <div className="space-y-2">
          {overdue.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertTriangle size={48} className="mx-auto mb-3 opacity-30" />
              <p>Nicio factura scadenta. Totul e la zi!</p>
            </div>
          ) : (
            overdue.map(inv => (
              <div key={inv.id} className="bg-gray-900 rounded-xl p-4 flex items-center gap-4 border border-red-900/30">
                <AlertTriangle size={18} className="text-red-400 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{inv.invoice_number}</span>
                    <span className="text-xs text-red-400">Scadenta: {inv.due_date}</span>
                  </div>
                  <div className="text-sm text-gray-400">{inv.client_name || 'Client necunoscut'}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-lg text-red-400">{inv.total?.toFixed(2)} RON</div>
                  <div className="text-xs text-gray-500">{inv.days_overdue} zile intarziere</div>
                </div>
                <button onClick={() => markPaid(inv.id)}
                  className="flex items-center gap-1 px-3 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm">
                  <DollarSign size={14} /> Platita
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* SERIES MANAGEMENT (F3) */}
      {tab === 'series' && (
        <div className="space-y-4">
          <div className="bg-gray-900 rounded-xl p-4 space-y-3">
            <h3 className="text-sm font-medium text-gray-300">Adauga serie noua</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              <input value={newSeries.prefix} onChange={e => setNewSeries(p => ({ ...p, prefix: e.target.value.toUpperCase() }))}
                placeholder="Prefix (ex: RCC)" maxLength={10}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono" />
              <input value={newSeries.name} onChange={e => setNewSeries(p => ({ ...p, name: e.target.value }))}
                placeholder="Nume serie"
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              <input value={newSeries.description} onChange={e => setNewSeries(p => ({ ...p, description: e.target.value }))}
                placeholder="Descriere (optional)"
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <button onClick={createSeries} disabled={!newSeries.prefix.trim() || !newSeries.name.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm">
              <Plus size={14} /> Adauga serie
            </button>
          </div>
          <div className="space-y-2">
            {series.map(s => (
              <div key={s.id} className={`bg-gray-900 rounded-xl p-4 flex items-center gap-4 ${s.is_default ? 'border border-blue-500/30' : ''}`}>
                <div className="w-16 text-center font-mono text-sm font-bold text-blue-400 bg-blue-900/20 rounded-lg py-1">{s.prefix}</div>
                <div className="flex-1">
                  <div className="font-medium">{s.name}</div>
                  {s.description && <div className="text-xs text-gray-500">{s.description}</div>}
                </div>
                <div className="text-sm text-gray-400">Nr. urmator: {s.next_number}</div>
                {s.is_default ? (
                  <span className="text-xs px-2 py-1 bg-blue-900/30 text-blue-400 rounded-full">Implicita</span>
                ) : (
                  <button onClick={() => setDefault(s.id)}
                    className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded-full text-gray-400">
                    Seteaza implicita
                  </button>
                )}
              </div>
            ))}
            {series.length === 0 && (
              <p className="text-center py-8 text-gray-500">Nicio serie configurata.</p>
            )}
          </div>
        </div>
      )}

      {/* R3-20: Email modal */}
      {emailModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md space-y-4">
            <h3 className="text-sm font-medium">Trimite factura {emailModal.invoice_number} pe email</h3>
            <input value={emailTo} onChange={e => setEmailTo(e.target.value)} placeholder="Email destinatar *"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <input value={emailSubject} onChange={e => setEmailSubject(e.target.value)} placeholder="Subiect"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setEmailModal(null)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm">Anuleaza</button>
              <button onClick={sendEmail} disabled={emailSending || !emailTo}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm">
                {emailSending ? <Loader2 size={14} className="animate-spin" /> : <Mail size={14} />} Trimite
              </button>
            </div>
          </div>
        </div>
      )}

      {/* R3-17: Calculation picker modal */}
      {showCalcModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-xl p-6 w-full max-w-lg space-y-4">
            <h3 className="text-sm font-medium">Selecteaza calcul de pret</h3>
            {recentCalcs.length === 0 ? (
              <p className="text-sm text-gray-500 py-4 text-center">Niciun calcul recent gasit.</p>
            ) : (
              <div className="max-h-64 overflow-y-auto space-y-2">
                {recentCalcs.map(c => (
                  <button key={c.id} onClick={() => selectCalc(c.id)}
                    className="w-full text-left bg-gray-800 hover:bg-gray-700 rounded-lg p-3 transition-colors">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">{c.filename || `Calcul #${c.id}`}</span>
                      <span className="text-sm text-green-400">{c.market_price?.toFixed(2) || c.price?.toFixed(2)} RON</span>
                    </div>
                    <div className="text-xs text-gray-500">{c.created_at || c.date}</div>
                  </button>
                ))}
              </div>
            )}
            <div className="flex justify-end">
              <button onClick={() => setShowCalcModal(false)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm">Inchide</button>
            </div>
          </div>
        </div>
      )}

      {/* R3-22: Client history slide-in */}
      {historyClient && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end">
          <div className="bg-gray-900 w-full max-w-md h-full overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Istoric facturi — {historyClient.name}</h3>
              <button onClick={() => setHistoryClient(null)} className="p-1.5 hover:bg-gray-800 rounded"><X size={16} /></button>
            </div>
            {historyLoading ? (
              <div className="flex justify-center py-8"><Loader2 size={20} className="animate-spin text-gray-500" /></div>
            ) : historyData.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">Nicio factura gasita pentru acest client.</p>
            ) : (
              <div className="space-y-2">
                {historyData.map(inv => (
                  <div key={inv.id} className="bg-gray-800 rounded-lg p-3">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">{inv.invoice_number}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[inv.status] || ''}`}>{statusLabels[inv.status] || inv.status}</span>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-gray-400">{inv.date}</span>
                      <span className="text-sm font-bold">{inv.total?.toFixed(2)} RON</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {/* Jurnal comunicare client */}
            <div className="border-t border-gray-800 pt-4 mt-4 space-y-3">
              <h4 className="text-sm font-medium text-gray-300">Jurnal comunicare</h4>
              {commLog.length > 0 && (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {commLog.map((entry, i) => (
                    <div key={i} className="bg-gray-800 rounded-lg p-2.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-1.5 py-0.5 bg-gray-700 rounded text-gray-400">{entry.comm_type}</span>
                        <span className="text-xs text-gray-500">{entry.created_at}</span>
                      </div>
                      <p className="text-sm text-gray-300 mt-1">{entry.summary}</p>
                      {entry.details && <p className="text-xs text-gray-500 mt-0.5">{entry.details}</p>}
                    </div>
                  ))}
                </div>
              )}
              <div className="space-y-2">
                <select value={newComm.comm_type} onChange={e => setNewComm(p => ({ ...p, comm_type: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs">
                  <option value="note">Nota</option>
                  <option value="email">Email</option>
                  <option value="phone">Telefon</option>
                  <option value="meeting">Intalnire</option>
                </select>
                <input value={newComm.summary} onChange={e => setNewComm(p => ({ ...p, summary: e.target.value }))}
                  placeholder="Sumar comunicare *" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs" />
                <input value={newComm.details} onChange={e => setNewComm(p => ({ ...p, details: e.target.value }))}
                  placeholder="Detalii (optional)" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs" />
                <button onClick={() => historyClient && addCommEntry(historyClient.id)} disabled={!newComm.summary.trim()}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-xs">
                  Adauga nota
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* R3-31: PRESETS / TEMPLATES */}
      {tab === 'presets' && (
        <div className="space-y-4" onFocus={() => { if (presets.length === 0 && !presetsLoading) loadPresets(); }}>
          {presetsLoading && presets.length === 0 ? (
            <div className="flex justify-center py-8"><Loader2 size={24} className="animate-spin text-gray-500" /></div>
          ) : (
            <>
              {presets.length === 0 && !presetsLoading && (
                <div className="text-center py-8 text-gray-500" onMouseEnter={loadPresets}>
                  <Copy size={32} className="mx-auto mb-2 opacity-30" />
                  <p className="text-sm">Niciun sablon. Creeaza primul!</p>
                </div>
              )}
              {presets.map(p => (
                <div key={p.id} className="bg-gray-900 rounded-xl p-4 flex items-center gap-4">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{p.name}</div>
                    <div className="text-xs text-gray-500">{p.notes || 'Fara note'}</div>
                  </div>
                  <button onClick={() => applyPreset(p)} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs">Aplica</button>
                  <button onClick={() => deletePreset(p.id)} className="p-1.5 hover:bg-red-700/30 rounded text-red-400"><Trash2 size={14} /></button>
                </div>
              ))}
              {/* New preset form */}
              <div className="bg-gray-900 rounded-xl p-4 space-y-3">
                <h4 className="text-sm font-medium text-gray-300">Sablon nou</h4>
                <input value={newPreset.name} onChange={e => setNewPreset(p => ({ ...p, name: e.target.value }))}
                  placeholder="Nume sablon *" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                {newPreset.items.map((item, i) => (
                  <div key={i} className="grid grid-cols-12 gap-2 items-center">
                    <input value={item.description} onChange={e => { const u = [...newPreset.items]; u[i] = { ...u[i], description: e.target.value }; setNewPreset(p => ({ ...p, items: u })); }}
                      placeholder="Descriere..." className="col-span-6 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                    <input type="number" value={item.quantity} onChange={e => { const u = [...newPreset.items]; u[i] = { ...u[i], quantity: parseFloat(e.target.value) || 0 }; setNewPreset(p => ({ ...p, items: u })); }}
                      className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-center" />
                    <input type="number" value={item.unit_price} onChange={e => { const u = [...newPreset.items]; u[i] = { ...u[i], unit_price: parseFloat(e.target.value) || 0 }; setNewPreset(p => ({ ...p, items: u })); }}
                      className="col-span-3 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-right" step="0.01" />
                    <button onClick={() => setNewPreset(p => ({ ...p, items: p.items.filter((_, idx) => idx !== i) }))} className="col-span-1 text-red-400"><X size={14} /></button>
                  </div>
                ))}
                <button onClick={() => setNewPreset(p => ({ ...p, items: [...p.items, { description: '', quantity: 1, unit_price: 0 }] }))}
                  className="text-xs text-blue-400">+ Rand</button>
                <input value={newPreset.notes} onChange={e => setNewPreset(p => ({ ...p, notes: e.target.value }))}
                  placeholder="Note (optional)" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <button onClick={savePreset} disabled={!newPreset.name.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm">Salveaza sablon</button>
              </div>
            </>
          )}
        </div>
      )}

      {/* R3-32: RECURRING INVOICES */}
      {tab === 'recurring' && (
        <div className="space-y-4" onFocus={() => { if (recurring.length === 0 && !recurringLoading) loadRecurring(); }}>
          {recurringLoading && recurring.length === 0 ? (
            <div className="flex justify-center py-8"><Loader2 size={24} className="animate-spin text-gray-500" /></div>
          ) : (
            <>
              {recurring.length === 0 && !recurringLoading && (
                <div className="text-center py-8 text-gray-500" onMouseEnter={loadRecurring}>
                  <RefreshCw size={32} className="mx-auto mb-2 opacity-30" />
                  <p className="text-sm">Nicio factura recurenta configurata.</p>
                </div>
              )}
              {recurring.map(r => (
                <div key={r.id} className="bg-gray-900 rounded-xl p-4 flex items-center gap-4">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{clients.find(c => c.id === r.client_id)?.name || `Client #${r.client_id}`}</div>
                    <div className="text-xs text-gray-500">La fiecare {r.interval_days} zile | Urmatoarea: {r.next_date || '-'}</div>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${r.enabled ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
                    {r.enabled ? 'Activa' : 'Inactiva'}
                  </span>
                  <button onClick={() => toggleRecurring(r.id, r.enabled)} className="p-1.5 hover:bg-gray-700 rounded text-gray-400" title="Toggle">
                    {r.enabled ? <Pause size={14} /> : <Play size={14} />}
                  </button>
                  <button onClick={() => deleteRecurring(r.id)} className="p-1.5 hover:bg-red-700/30 rounded text-red-400"><Trash2 size={14} /></button>
                </div>
              ))}
              {/* New recurring form */}
              <div className="bg-gray-900 rounded-xl p-4 space-y-3">
                <h4 className="text-sm font-medium text-gray-300">Factura recurenta noua</h4>
                <div className="grid grid-cols-2 gap-3">
                  <select value={newRecurring.client_id} onChange={e => setNewRecurring(p => ({ ...p, client_id: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                    <option value="">— Client —</option>
                    {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                  <input type="number" value={newRecurring.interval_days} onChange={e => setNewRecurring(p => ({ ...p, interval_days: parseInt(e.target.value) || 30 }))}
                    placeholder="Interval zile" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                  <input type="date" value={newRecurring.next_date} onChange={e => setNewRecurring(p => ({ ...p, next_date: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                </div>
                <button onClick={saveRecurring} disabled={!newRecurring.client_id}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm">Adauga recurenta</button>
              </div>
            </>
          )}
        </div>
      )}

      {/* R3-34: REPORTS DASHBOARD */}
      {tab === 'reports' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <select value={reportPeriod} onChange={e => setReportPeriod(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
              <option value="monthly">Lunar</option>
              <option value="quarterly">Trimestrial</option>
              <option value="yearly">Anual</option>
              <option value="by-client">Per client</option>
            </select>
            <button onClick={loadReports} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
              <BarChart3 size={14} /> Genereaza raport
            </button>
          </div>
          {reportsLoading ? (
            <div className="flex justify-center py-8"><Loader2 size={24} className="animate-spin text-gray-500" /></div>
          ) : reports ? (
            <div className="space-y-3">
              {/* Summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-gray-900 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-500">Total facturi</p>
                  <p className="text-xl font-bold text-white">{reports.total_invoices || 0}</p>
                </div>
                <div className="bg-gray-900 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-500">Total incasat</p>
                  <p className="text-xl font-bold text-green-400">{(reports.total_paid || 0).toFixed(2)} RON</p>
                </div>
                <div className="bg-gray-900 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-500">De incasat</p>
                  <p className="text-xl font-bold text-amber-400">{(reports.total_outstanding || 0).toFixed(2)} RON</p>
                </div>
                <div className="bg-gray-900 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-500">Rata incasare</p>
                  <p className="text-xl font-bold text-blue-400">{(reports.collection_rate || 0).toFixed(0)}%</p>
                </div>
              </div>
              {/* Detailed data */}
              {reports.data && Array.isArray(reports.data) && (
                <div className="bg-gray-900 rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead><tr className="bg-gray-800 text-gray-400 text-xs">
                      <th className="text-left p-3">{reportPeriod === 'by-client' ? 'Client' : 'Perioada'}</th>
                      <th className="text-right p-3">Facturi</th>
                      <th className="text-right p-3">Total</th>
                      <th className="text-right p-3">Incasat</th>
                    </tr></thead>
                    <tbody>
                      {reports.data.map((row, i) => (
                        <tr key={i} className="border-t border-gray-800">
                          <td className="p-3 text-white">{row.label || row.period || row.client_name || '-'}</td>
                          <td className="p-3 text-right text-gray-400">{row.count || 0}</td>
                          <td className="p-3 text-right">{(row.total || 0).toFixed(2)} RON</td>
                          <td className="p-3 text-right text-green-400">{(row.paid || 0).toFixed(2)} RON</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <BarChart3 size={48} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">Selecteaza perioada si genereaza raportul</p>
            </div>
          )}
        </div>
      )}

      {/* R3-33: Payments modal */}
      {paymentsInvoice && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end">
          <div className="bg-gray-900 w-full max-w-md h-full overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Plati — {paymentsInvoice.invoice_number}</h3>
              <button onClick={() => setPaymentsInvoice(null)} className="p-1.5 hover:bg-gray-800 rounded"><X size={16} /></button>
            </div>
            <div className="text-xs text-gray-400">Total factura: <span className="text-white font-bold">{paymentsInvoice.total?.toFixed(2)} RON</span></div>
            {paymentsLoading ? (
              <div className="flex justify-center py-8"><Loader2 size={20} className="animate-spin text-gray-500" /></div>
            ) : (
              <>
                {payments.length > 0 ? (
                  <div className="space-y-2">
                    {payments.map((p, i) => (
                      <div key={i} className="bg-gray-800 rounded-lg p-3 flex justify-between">
                        <div>
                          <div className="text-sm font-medium text-green-400">+{p.amount?.toFixed(2)} RON</div>
                          <div className="text-xs text-gray-500">{p.date} — {p.method || 'transfer'}</div>
                          {p.notes && <div className="text-xs text-gray-500">{p.notes}</div>}
                        </div>
                      </div>
                    ))}
                    <div className="text-xs text-gray-400 text-right">
                      Platit: {payments.reduce((s, p) => s + (p.amount || 0), 0).toFixed(2)} / {paymentsInvoice.total?.toFixed(2)} RON
                    </div>
                  </div>
                ) : <p className="text-sm text-gray-500 text-center py-4">Nicio plata inregistrata</p>}
                {/* Add payment */}
                <div className="border-t border-gray-800 pt-3 space-y-2">
                  <h4 className="text-xs text-gray-400 font-medium">Adauga plata</h4>
                  <div className="grid grid-cols-2 gap-2">
                    <input type="number" value={newPayment.amount} onChange={e => setNewPayment(p => ({ ...p, amount: e.target.value }))}
                      placeholder="Suma RON *" step="0.01" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                    <input type="date" value={newPayment.date} onChange={e => setNewPayment(p => ({ ...p, date: e.target.value }))}
                      className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                    <select value={newPayment.method} onChange={e => setNewPayment(p => ({ ...p, method: e.target.value }))}
                      className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                      <option value="transfer">Transfer bancar</option>
                      <option value="cash">Numerar</option>
                      <option value="card">Card</option>
                    </select>
                    <input value={newPayment.notes} onChange={e => setNewPayment(p => ({ ...p, notes: e.target.value }))}
                      placeholder="Note" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                  </div>
                  <button onClick={addPayment} disabled={!newPayment.amount}
                    className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded-lg text-sm flex items-center justify-center gap-2">
                    <CreditCard size={14} /> Inregistreaza plata
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* OFFER PDF (F9) */}
      {tab === 'offer' && (
        <div className="bg-gray-900 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-medium text-gray-300">Genereaza Nota Oferta PDF — CIP Inspection SRL</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Nume client *</label>
              <input value={offerForm.client_name} onChange={e => setOfferForm(p => ({ ...p, client_name: e.target.value }))}
                placeholder="SC Exemplu SRL" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Adresa client</label>
              <input value={offerForm.client_address} onChange={e => setOfferForm(p => ({ ...p, client_address: e.target.value }))}
                placeholder="Strada, nr, oras" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          {/* Offer items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium">Articole oferta</label>
              <button onClick={() => setOfferForm(p => ({ ...p, items: [...p.items, { description: '', quantity: 1, unit_price: 0 }] }))}
                className="text-xs text-blue-400 hover:text-blue-300">+ Adauga rand</button>
            </div>
            <div className="space-y-2">
              {offerForm.items.map((item, i) => (
                <div key={i} className="grid grid-cols-12 gap-2 items-center">
                  <input value={item.description}
                    onChange={e => { const upd = [...offerForm.items]; upd[i] = { ...upd[i], description: e.target.value }; setOfferForm(p => ({ ...p, items: upd })); }}
                    placeholder="Descriere serviciu..."
                    className="col-span-6 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                  <input type="number" value={item.quantity}
                    onChange={e => { const upd = [...offerForm.items]; upd[i] = { ...upd[i], quantity: parseFloat(e.target.value) || 0 }; setOfferForm(p => ({ ...p, items: upd })); }}
                    className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-center" min="1" />
                  <input type="number" value={item.unit_price}
                    onChange={e => { const upd = [...offerForm.items]; upd[i] = { ...upd[i], unit_price: parseFloat(e.target.value) || 0 }; setOfferForm(p => ({ ...p, items: upd })); }}
                    className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-right" step="0.01" />
                  <span className="col-span-1 text-sm text-right text-gray-400">{((item.quantity || 0) * (item.unit_price || 0)).toFixed(2)}</span>
                  <button onClick={() => setOfferForm(p => ({ ...p, items: p.items.filter((_, idx) => idx !== i) }))}
                    className="col-span-1 text-red-400 hover:text-red-300 justify-self-center">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Valabilitate (zile)</label>
              <input type="number" value={offerForm.validity_days}
                onChange={e => setOfferForm(p => ({ ...p, validity_days: parseInt(e.target.value) || 30 }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Note</label>
              <input value={offerForm.notes} onChange={e => setOfferForm(p => ({ ...p, notes: e.target.value }))}
                placeholder="Observatii..." className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="flex justify-between items-center pt-2 border-t border-gray-800">
            <div className="text-sm text-gray-400">
              Total oferta: <span className="text-white font-bold">
                {offerForm.items.reduce((s, i) => s + (i.quantity || 0) * (i.unit_price || 0), 0).toFixed(2)} RON
              </span>
            </div>
            <button onClick={generateOffer} disabled={!offerForm.client_name.trim() || offerForm.items.every(i => !i.description)}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded-xl text-sm font-medium">
              <Download size={16} /> Descarca Oferta PDF
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function InvoicePreview({ client, items, invoiceDate, dueDate, notes, vatPercent }) {
  const subtotal = items.reduce((s, i) => s + (i.quantity || 0) * (i.unit_price || 0), 0);
  const vat = subtotal * ((vatPercent || 0) / 100);
  const total = subtotal + vat;
  if (subtotal === 0) return null;
  return (
    <div className="bg-white text-gray-900 rounded-lg p-4 text-xs mt-4 max-w-md">
      <div className="text-center border-b pb-2 mb-2">
        <p className="font-bold text-sm">CIP Inspection SRL</p>
        <p className="text-gray-500">CUI: 43978110</p>
      </div>
      <div className="flex justify-between mb-3">
        <div><p className="font-medium">Client:</p><p>{client || '\u2014'}</p></div>
        <div className="text-right"><p>Data: {invoiceDate || '\u2014'}</p><p>Scadenta: {dueDate || '\u2014'}</p></div>
      </div>
      <table className="w-full mb-2">
        <thead><tr className="border-b text-left"><th className="py-1">Desc.</th><th className="text-right">Cant.</th><th className="text-right">Pret</th><th className="text-right">Total</th></tr></thead>
        <tbody>
          {items.filter(i => i.description).map((i, idx) => (
            <tr key={idx} className="border-b border-gray-200">
              <td className="py-1">{i.description}</td><td className="text-right">{i.quantity}</td>
              <td className="text-right">{i.unit_price}</td><td className="text-right">{((i.quantity || 0) * (i.unit_price || 0)).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-right">
        <p>Subtotal: {subtotal.toFixed(2)} RON</p>
        {vatPercent > 0 && <p>TVA ({vatPercent}%): {vat.toFixed(2)} RON</p>}
        <p className="font-bold text-sm">Total: {total.toFixed(2)} RON</p>
      </div>
    </div>
  );
}
