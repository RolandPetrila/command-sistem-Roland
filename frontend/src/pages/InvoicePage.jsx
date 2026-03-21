import React, { useState, useEffect } from 'react';
import { Receipt, Plus, Trash2, Pencil, Download, Send, Check, X, Users, FileText, Loader2, Bot, DollarSign, AlertTriangle, List } from 'lucide-react';
import api from '../api/client';

export default function InvoicePage() {
  const [tab, setTab] = useState('invoices'); // invoices | clients | create | series | overdue | offer
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
  const [clientForm, setClientForm] = useState({ name: '', cui: '', address: '', email: '', phone: '', notes: '' });
  const [showClientForm, setShowClientForm] = useState(false);
  // F3: Series
  const [series, setSeries] = useState([]);
  const [newSeries, setNewSeries] = useState({ prefix: '', name: '', description: '' });
  // F4: Overdue
  const [overdue, setOverdue] = useState([]);
  // F9: Offer PDF
  const [offerForm, setOfferForm] = useState({ client_name: '', client_address: '', items: [{ description: '', quantity: 1, unit_price: 0 }], notes: '', validity_days: 30 });

  useEffect(() => { loadData(); loadSeries(); loadOverdue(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [inv, cli] = await Promise.allSettled([
        api.get('/api/invoice/list'),
        api.get('/api/invoice/clients'),
      ]);
      if (inv.status === 'fulfilled') setInvoices(inv.value.data || []);
      if (cli.status === 'fulfilled') setClients(cli.value.data || []);
    } catch { /* toast handles it */ }
    setLoading(false);
  };

  // Invoice CRUD
  const handleCreateInvoice = async () => {
    if (!selectedClient || items.every(i => !i.description)) return;
    setSaving(true);
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
        await api.post('/api/invoice/create', payload);
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
      setClientForm({ name: '', cui: '', address: '', email: '', phone: '', notes: '' });
      loadData();
    } catch { /* toast handles it */ }
  };

  const handleEditClient = (client) => {
    setEditClient(client.id);
    setClientForm({ name: client.name, cui: client.cui || '', address: client.address || '', email: client.email || '', phone: client.phone || '', notes: client.notes || '' });
    setShowClientForm(true);
    setTab('clients');
  };

  const handleDeleteClient = async (id) => {
    try {
      await api.delete(`/api/invoice/clients/${id}`);
      loadData();
    } catch { /* toast handles it */ }
  };

  // AI generate from calculation
  const handleAiGenerate = async () => {
    try {
      const calcId = prompt('ID calcul de preț (din Istoric):');
      if (!calcId) return;
      const { data } = await api.post('/api/invoice/generate-from-calc', { calculation_id: parseInt(calcId) });
      if (data.client_id) setSelectedClient(String(data.client_id));
      if (data.items) setItems(data.items);
      if (data.notes) setNotes(data.notes);
      setTab('create');
    } catch { /* toast handles it */ }
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

  const statusColors = { draft: 'text-gray-400 bg-gray-800', sent: 'text-blue-400 bg-blue-900/30', paid: 'text-green-400 bg-green-900/30', cancelled: 'text-red-400 bg-red-900/30' };
  const statusLabels = { draft: 'Ciornă', sent: 'Trimisă', paid: 'Plătită', cancelled: 'Anulată' };

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

      {/* INVOICES LIST */}
      {tab === 'invoices' && (
        <div className="space-y-2">
          {invoices.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Receipt size={48} className="mx-auto mb-3 opacity-30" />
              <p>Nicio factură. Creează prima factură!</p>
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
                <button onClick={() => handleGeneratePdf(inv.id)} className="p-2 hover:bg-gray-800 rounded-lg" title="Descarcă PDF"><Download size={16} /></button>
                {inv.status === 'draft' && (
                  <>
                    <button onClick={() => handleEditInvoice(inv.id)} className="p-2 hover:bg-gray-800 rounded-lg" title="Editează"><Pencil size={16} /></button>
                    <button onClick={() => handleStatusChange(inv.id, 'sent')} className="p-2 hover:bg-gray-800 rounded-lg text-blue-400" title="Marchează trimisă"><Send size={16} /></button>
                    <button onClick={() => handleDeleteInvoice(inv.id)} className="p-2 hover:bg-gray-800 rounded-lg text-red-400" title="Șterge"><Trash2 size={16} /></button>
                  </>
                )}
                {inv.status === 'sent' && (
                  <button onClick={() => handleStatusChange(inv.id, 'paid')} className="p-2 hover:bg-gray-800 rounded-lg text-green-400" title="Marchează plătită"><Check size={16} /></button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CLIENTS LIST */}
      {tab === 'clients' && (
        <div className="space-y-3">
          <button onClick={() => { setShowClientForm(true); setEditClient(null); setClientForm({ name: '', cui: '', address: '', email: '', phone: '', notes: '' }); }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
            <Plus size={14} /> Client nou
          </button>
          {showClientForm && (
            <div className="bg-gray-900 rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input value={clientForm.name} onChange={e => setClientForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="Nume / Firmă *" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <input value={clientForm.cui} onChange={e => setClientForm(p => ({ ...p, cui: e.target.value }))}
                  placeholder="CUI" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <input value={clientForm.address} onChange={e => setClientForm(p => ({ ...p, address: e.target.value }))}
                  placeholder="Adresă" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <input value={clientForm.email} onChange={e => setClientForm(p => ({ ...p, email: e.target.value }))}
                  placeholder="Email" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <input value={clientForm.phone} onChange={e => setClientForm(p => ({ ...p, phone: e.target.value }))}
                  placeholder="Telefon" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
                <input value={clientForm.notes} onChange={e => setClientForm(p => ({ ...p, notes: e.target.value }))}
                  placeholder="Note" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div className="flex gap-2">
                <button onClick={handleSaveClient} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm">
                  {editClient ? 'Actualizează' : 'Salvează'}
                </button>
                <button onClick={() => { setShowClientForm(false); setEditClient(null); }}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm">Anulează</button>
              </div>
            </div>
          )}
          {clients.map(client => (
            <div key={client.id} className="bg-gray-900 rounded-xl p-4 flex items-center gap-4 group">
              <Users size={18} className="text-gray-500" />
              <div className="flex-1">
                <div className="font-medium">{client.name}</div>
                <div className="text-xs text-gray-500">
                  {[client.cui, client.email, client.phone].filter(Boolean).join(' | ')}
                </div>
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
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
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Client *</label>
              <select value={selectedClient} onChange={e => setSelectedClient(e.target.value)}
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
            <div className="grid grid-cols-3 gap-3">
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
