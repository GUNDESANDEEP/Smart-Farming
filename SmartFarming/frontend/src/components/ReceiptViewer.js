import React, { useState, useRef } from 'react';
import { FiDownload, FiPrinter, FiShare2, FiMail, FiPhone, FiMessageCircle, FiCheck, FiX } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { paymentsAPI } from '../services/api';

// ─── Receipt Viewer Component ─────────────────────────────────────────────
const ReceiptViewer = ({ receipt, onClose }) => {
  const [sending, setSending] = useState(false);
  const [sendModal, setSendModal] = useState(false);
  const [sendForm, setSendForm] = useState({
    sms: false, whatsapp: false, email: false,
    phone: receipt?.buyer_phone || '',
    email_address: receipt?.buyer_email || ''
  });
  const receiptRef = useRef(null);

  if (!receipt) return null;

  const items = receipt.items || [];
  const subtotal = items.reduce((sum, i) => sum + (i.item_total || i.quantity_kg * i.price_per_kg), 0);

  const handlePrint = () => {
    const printContent = receiptRef.current;
    const win = window.open('', '_blank');
    win.document.write(`
      <html><head><title>Receipt - ${receipt.receipt_id}</title>
      <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
        body { padding:30px; color:#1a1a1a; }
        .header { text-align:center; margin-bottom:20px; border-bottom:2px solid #166534; padding-bottom:15px; }
        .header h1 { color:#166534; font-size:24px; }
        .header p { color:#666; font-size:12px; }
        .info-row { display:flex; justify-content:space-between; margin:10px 0; font-size:13px; }
        .section { margin:15px 0; }
        .section h3 { color:#166534; font-size:14px; margin-bottom:8px; border-bottom:1px solid #eee; padding-bottom:4px; }
        table { width:100%; border-collapse:collapse; margin:10px 0; }
        th, td { padding:8px 12px; text-align:left; border-bottom:1px solid #eee; font-size:13px; }
        th { background:#f0fdf4; color:#166534; font-weight:600; }
        .totals { text-align:right; margin-top:15px; }
        .totals .row { display:flex; justify-content:flex-end; gap:30px; margin:4px 0; font-size:13px; }
        .totals .grand { font-size:18px; font-weight:700; color:#166534; border-top:2px solid #166534; padding-top:8px; }
        .footer { text-align:center; margin-top:25px; padding-top:15px; border-top:1px solid #ddd; color:#888; font-size:11px; }
        .qr { text-align:center; margin:15px 0; padding:10px; background:#f8f8f8; border-radius:8px; }
      </style></head><body>
      ${printContent.innerHTML}
      </body></html>
    `);
    win.document.close();
    win.print();
  };

  const handleDownloadPDF = async () => {
    try {
      // For now, use print-to-PDF approach
      handlePrint();
      toast.success('Use "Save as PDF" in print dialog');
    } catch (e) {
      toast.error('Failed to generate PDF');
    }
  };

  const handleSend = async () => {
    if (!sendForm.sms && !sendForm.whatsapp && !sendForm.email) {
      toast.error('Select at least one delivery method');
      return;
    }
    if ((sendForm.sms || sendForm.whatsapp) && !sendForm.phone) {
      toast.error('Please enter phone number');
      return;
    }
    if (sendForm.email && !sendForm.email_address) {
      toast.error('Please enter email address');
      return;
    }
    setSending(true);
    try {
      const res = await paymentsAPI.sendReceipt(receipt.receipt_id, sendForm);
      const results = res.data?.results || {};
      
      // Show per-channel results
      let allSent = true;
      let messages = [];
      if (results.sms) {
        if (results.sms.sent) messages.push('✅ SMS sent');
        else { allSent = false; messages.push(`❌ SMS: ${results.sms.error || 'failed'}`); }
      }
      if (results.whatsapp) {
        if (results.whatsapp.sent) messages.push('✅ WhatsApp sent');
        else { allSent = false; messages.push(`❌ WhatsApp: ${results.whatsapp.error || 'failed'}`); }
      }
      if (results.email) {
        if (results.email.sent) messages.push('✅ Email sent');
        else { allSent = false; messages.push(`❌ Email: ${results.email.error || 'failed'}`); }
      }
      
      if (allSent) {
        toast.success(messages.join('\n'), { duration: 4000 });
        setSendModal(false);
      } else {
        toast.error(messages.join('\n'), { duration: 6000 });
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed to send receipt');
    } finally {
      setSending(false);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: `Receipt ${receipt.receipt_id}`,
        text: `SmartFarming Receipt\nTotal: ₹${receipt.grand_total}\nReceipt ID: ${receipt.receipt_id}`,
      });
    } else {
      setSendModal(true);
    }
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        {/* Action Bar */}
        <div style={styles.actionBar}>
          <h3 style={{ margin: 0, color: '#14532d' }}>Receipt</h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button style={styles.actionBtn} onClick={handleDownloadPDF} title="Download PDF">
              <FiDownload /> PDF
            </button>
            <button style={styles.actionBtn} onClick={handlePrint} title="Print">
              <FiPrinter /> Print
            </button>
            <button style={styles.actionBtn} onClick={handleShare} title="Share">
              <FiShare2 /> Share
            </button>
            <button style={styles.actionBtn}
              onClick={() => { setSendForm(f => ({ ...f, whatsapp: true, phone: f.phone || receipt.buyer_phone || '' })); setSendModal(true); }} title="WhatsApp">
              <FiMessageCircle /> WhatsApp
            </button>
            <button style={styles.actionBtn}
              onClick={() => { setSendForm(f => ({ ...f, email: true, email_address: f.email_address || receipt.buyer_email || '' })); setSendModal(true); }} title="Email">
              <FiMail /> Email
            </button>
            <button style={styles.actionBtn}
              onClick={() => { setSendForm(f => ({ ...f, sms: true, phone: f.phone || receipt.buyer_phone || '' })); setSendModal(true); }} title="SMS">
              <FiPhone /> SMS
            </button>
            <button style={styles.closeBtn} onClick={onClose}><FiX /></button>
          </div>
        </div>

        {/* Receipt Content */}
        <div ref={receiptRef} style={styles.receipt}>
          {/* Header */}
          <div className="header" style={styles.receiptHeader}>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#166534' }}>🌾 SmartFarming Market Place</div>
            <p style={{ color: '#888', fontSize: '0.8rem', marginTop: '4px' }}>Your Trusted Farming Partner</p>
          </div>

          {/* Receipt Meta */}
          <div style={styles.metaGrid}>
            <div style={styles.metaItem}>
              <span style={styles.metaLabel}>Receipt ID</span>
              <span style={styles.metaValue}>{receipt.receipt_id}</span>
            </div>
            <div style={styles.metaItem}>
              <span style={styles.metaLabel}>Transaction ID</span>
              <span style={styles.metaValue}>{receipt.transaction_id || 'N/A'}</span>
            </div>
            <div style={styles.metaItem}>
              <span style={styles.metaLabel}>📅 Date</span>
              <span style={styles.metaValue}>{new Date(receipt.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
            </div>
            <div style={styles.metaItem}>
              <span style={styles.metaLabel}>🕐 Time</span>
              <span style={styles.metaValue}>{new Date(receipt.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}</span>
            </div>
            <div style={styles.metaItem}>
              <span style={styles.metaLabel}>Payment</span>
              <span style={{ ...styles.metaValue, color: receipt.payment_status === 'completed' ? '#16a34a' : '#d97706' }}>
                {receipt.payment_type?.toUpperCase()} • {receipt.payment_status?.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Farmer & Buyer Details */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', margin: '16px 0' }}>
            <div className="section" style={styles.infoCard}>
              <h3 style={styles.sectionTitle}>Farmer Details</h3>
              <p style={styles.infoText}><strong>{receipt.farmer_name}</strong></p>
              <p style={styles.infoText}>📱 {receipt.farmer_phone || 'N/A'}</p>
              <p style={styles.infoText}>📧 {receipt.farmer_email || 'N/A'}</p>
            </div>
            <div className="section" style={styles.infoCard}>
              <h3 style={styles.sectionTitle}>Buyer Details</h3>
              <p style={styles.infoText}><strong>{receipt.buyer_name}</strong></p>
              <p style={styles.infoText}>📱 {receipt.buyer_phone || 'N/A'}</p>
              <p style={styles.infoText}>📧 {receipt.buyer_email || 'N/A'}</p>
            </div>
          </div>

          {/* Items Table */}
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>#</th>
                <th style={styles.th}>Product</th>
                <th style={styles.th}>Quality</th>
                <th style={styles.th}>Qty (KG)</th>
                <th style={styles.th}>Price/KG</th>
                <th style={{ ...styles.th, textAlign: 'right' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => (
                <tr key={idx}>
                  <td style={styles.td}>{idx + 1}</td>
                  <td style={styles.td}><strong>{item.product_name}</strong></td>
                  <td style={styles.td}>{item.product_quality || 'Standard'}</td>
                  <td style={styles.td}>{item.quantity_kg}</td>
                  <td style={styles.td}>₹{item.price_per_kg}</td>
                  <td style={{ ...styles.td, textAlign: 'right', fontWeight: 600 }}>₹{parseFloat(item.item_total || item.total || (parseFloat(item.quantity_kg || item.quantity || 0) * parseFloat(item.price_per_kg || 0)) || 0).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Totals */}
          <div className="totals" style={styles.totals}>
            <div style={styles.totalRow}>
              <span>Subtotal</span>
              <span>₹{parseFloat(receipt.subtotal || subtotal || 0).toFixed(2)}</span>
            </div>
            {receipt.discount > 0 && (
              <div style={styles.totalRow}>
                <span>Discount</span>
                <span style={{ color: '#16a34a' }}>-₹{parseFloat(receipt.discount || 0).toFixed(2)}</span>
              </div>
            )}
            {receipt.tax_amount > 0 && (
              <div style={styles.totalRow}>
                <span>Tax</span>
                <span>₹{parseFloat(receipt.tax_amount || 0).toFixed(2)}</span>
              </div>
            )}
            <div style={styles.grandTotal}>
              <span>Grand Total</span>
              <span>₹{parseFloat(receipt.grand_total || receipt.total_amount || 0).toFixed(2)}</span>
            </div>
          </div>

          {/* QR Code */}
          <div className="qr" style={styles.qrSection}>
            <p style={{ fontSize: '0.75rem', color: '#888' }}>QR Verification Code</p>
            <div style={styles.qrBox}>
              <svg viewBox="0 0 100 100" width="80" height="80">
                <rect x="10" y="10" width="30" height="30" fill="#166534" rx="3"/>
                <rect x="60" y="10" width="30" height="30" fill="#166534" rx="3"/>
                <rect x="10" y="60" width="30" height="30" fill="#166534" rx="3"/>
                <rect x="45" y="45" width="10" height="10" fill="#22c55e"/>
                <rect x="65" y="65" width="25" height="25" fill="#166534" rx="3"/>
              </svg>
              <p style={{ fontSize: '0.7rem', color: '#666', marginTop: '4px' }}>{receipt.receipt_id}</p>
            </div>
          </div>

          {/* Footer */}
          <div className="footer" style={styles.footer}>
            <p style={{ fontWeight: 600, color: '#166534', fontSize: '0.9rem' }}>Thank you for choosing SmartFarming! 🌱</p>
            <p style={{ fontSize: '0.75rem', color: '#999', marginTop: '4px' }}>This is a computer-generated receipt. No signature required.</p>
          </div>
        </div>

        {/* Send Modal */}
        {sendModal && (
          <div style={styles.sendOverlay}>
            <div style={styles.sendModal}>
              <h3 style={{ color: '#14532d', marginBottom: '16px' }}>Send Receipt</h3>
              
              <label style={styles.checkbox}>
                <input type="checkbox" checked={sendForm.sms} onChange={e => setSendForm(f => ({ ...f, sms: e.target.checked }))} />
                <FiPhone /> Send via SMS
              </label>
              <label style={styles.checkbox}>
                <input type="checkbox" checked={sendForm.whatsapp} onChange={e => setSendForm(f => ({ ...f, whatsapp: e.target.checked }))} />
                <FiMessageCircle /> Send via WhatsApp
              </label>
              <label style={styles.checkbox}>
                <input type="checkbox" checked={sendForm.email} onChange={e => setSendForm(f => ({ ...f, email: e.target.checked }))} />
                <FiMail /> Send via Email
              </label>

              {(sendForm.sms || sendForm.whatsapp) && (
                <input style={styles.sendInput} placeholder="Phone number" value={sendForm.phone}
                  onChange={e => setSendForm(f => ({ ...f, phone: e.target.value }))} />
              )}
              {sendForm.email && (
                <input style={styles.sendInput} placeholder="Email address" value={sendForm.email_address}
                  onChange={e => setSendForm(f => ({ ...f, email_address: e.target.value }))} />
              )}

              <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                <button style={styles.sendBtn} onClick={handleSend} disabled={sending}>
                  {sending ? 'Sending...' : 'Send'} <FiCheck />
                </button>
                <button style={styles.cancelSendBtn} onClick={() => setSendModal(false)}>Cancel</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Styles ──────────────────────────────────────────────────────────────
const styles = {
  overlay: {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 9999, backdropFilter: 'blur(4px)',
  },
  modal: {
    background: '#fff', borderRadius: '16px', width: '90%', maxWidth: '700px',
    maxHeight: '90vh', overflow: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  actionBar: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '16px 20px', borderBottom: '1px solid #e5e7eb', position: 'sticky',
    top: 0, background: '#fff', borderRadius: '16px 16px 0 0', zIndex: 1, flexWrap: 'wrap', gap: '8px',
  },
  actionBtn: {
    display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px',
    borderRadius: '8px', border: '1px solid #e5e7eb', background: '#f9fafb',
    cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, fontFamily: 'Poppins, sans-serif',
  },
  closeBtn: {
    background: '#fee2e2', color: '#dc2626', border: 'none', borderRadius: '8px',
    padding: '8px', cursor: 'pointer', display: 'flex',
  },
  receipt: { padding: '30px' },
  receiptHeader: {
    textAlign: 'center', paddingBottom: '16px', borderBottom: '2px solid #166534', marginBottom: '16px',
  },
  metaGrid: {
    display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', margin: '16px 0',
    background: '#f0fdf4', padding: '16px', borderRadius: '10px',
  },
  metaItem: { display: 'flex', flexDirection: 'column', gap: '2px' },
  metaLabel: { fontSize: '0.7rem', color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px' },
  metaValue: { fontSize: '0.85rem', fontWeight: 600, color: '#14532d' },
  infoCard: {
    background: '#fafafa', padding: '14px', borderRadius: '10px', border: '1px solid #e5e7eb',
  },
  sectionTitle: {
    fontSize: '0.8rem', color: '#166534', fontWeight: 700, marginBottom: '8px',
    paddingBottom: '4px', borderBottom: '1px solid #eee',
  },
  infoText: { fontSize: '0.82rem', color: '#555', margin: '3px 0' },
  table: { width: '100%', borderCollapse: 'collapse', margin: '16px 0' },
  th: {
    padding: '10px 12px', textAlign: 'left', background: '#f0fdf4', color: '#166534',
    fontWeight: 600, fontSize: '0.8rem', borderBottom: '2px solid #dcfce7',
  },
  td: { padding: '10px 12px', borderBottom: '1px solid #f3f4f6', fontSize: '0.85rem', color: '#374151' },
  totals: { textAlign: 'right', marginTop: '12px' },
  totalRow: {
    display: 'flex', justifyContent: 'flex-end', gap: '40px', margin: '4px 0',
    fontSize: '0.9rem', color: '#555',
  },
  grandTotal: {
    display: 'flex', justifyContent: 'flex-end', gap: '40px', marginTop: '8px',
    fontSize: '1.2rem', fontWeight: 700, color: '#166534',
    borderTop: '2px solid #166534', paddingTop: '10px',
  },
  qrSection: { textAlign: 'center', margin: '20px 0', padding: '16px', background: '#f8f8f8', borderRadius: '10px' },
  qrBox: { display: 'inline-block', marginTop: '8px' },
  footer: {
    textAlign: 'center', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #ddd',
  },
  sendOverlay: {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10000,
  },
  sendModal: {
    background: '#fff', borderRadius: '14px', padding: '24px', width: '360px', boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
  },
  checkbox: {
    display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 0',
    fontSize: '0.9rem', cursor: 'pointer', color: '#333',
  },
  sendInput: {
    width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #d1d5db',
    fontSize: '0.9rem', marginTop: '8px', fontFamily: 'Poppins, sans-serif',
  },
  sendBtn: {
    background: 'linear-gradient(135deg, #166534, #22c55e)', color: '#fff', border: 'none',
    padding: '10px 24px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
    display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'Poppins, sans-serif',
  },
  cancelSendBtn: {
    background: '#f3f4f6', color: '#555', border: 'none', padding: '10px 20px',
    borderRadius: '8px', cursor: 'pointer', fontFamily: 'Poppins, sans-serif',
  },
};

export default ReceiptViewer;
