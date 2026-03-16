import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LayoutDashboard, 
  PlusCircle, 
  Send, 
  CheckCircle2, 
  AlertCircle, 
  Settings,
  ArrowRight,
  ExternalLink,
  Loader2,
  Edit3,
  Trash2,
  X,
  FileText,
  Sparkles
} from 'lucide-react';
import './index.css';

const API_BASE = '';

function App() {
  const [view, setView] = useState('dashboard'); // dashboard, create, settings, edit
  const [selectedIssueId, setSelectedIssueId] = useState(null);
  const [pendingIssues, setPendingIssues] = useState([]);
  const [uploadedIssues, setUploadedIssues] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setError(null);
      const [pRes, uRes, tRes] = await Promise.all([
        axios.get(`${API_BASE}/issues/pending`),
        axios.get(`${API_BASE}/issues/uploaded`),
        axios.get(`${API_BASE}/templates`)
      ]);
      setPendingIssues(pRes.data);
      setUploadedIssues(uRes.data);
      setTemplates(tRes.data);
    } catch (err) {
      console.error("Fetch failed", err);
      setError("Connect fail. Make sure backend is running.");
    }
  };

  const handleUpload = async (id) => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE}/issues/upload/${id}`);
      fetchData();
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure?")) return;
    try {
      await axios.delete(`${API_BASE}/issues/${id}`);
      fetchData();
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo">
          <Sparkles size={24} color="#818cf8" />
          <span>Issue Helper</span>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <div className={`nav-item ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}>
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </div>
          <div className={`nav-item ${view === 'create' ? 'active' : ''}`} onClick={() => setView('create')}>
            <PlusCircle size={20} />
            <span>New Issue</span>
          </div>
          <div className={`nav-item ${view === 'settings' ? 'active' : ''}`} onClick={() => setView('settings')}>
            <Settings size={20} />
            <span>Settings</span>
          </div>
        </nav>
        <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--glass-border)' }}>
          <div className="nav-item" style={{ fontSize: '0.85rem' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: error ? 'var(--error-color)' : 'var(--success-color)' }} />
            <span>{error ? 'Offline' : 'Connected'}</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        {error && <div className="status-badge status-failed" style={{ marginBottom: '2rem', padding: '1rem' }}>{error}</div>}
        
        {view === 'dashboard' && (
          <div className="fade-in">
            <div className="title-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
              <div>
                <h1>Workspace</h1>
                <p>You have {pendingIssues.length} issues waiting for upload.</p>
              </div>
              <button className="btn-primary" onClick={() => setView('create')}>
                <PlusCircle size={18} /> New Draft
              </button>
            </div>
            
            <div className="dashboard-grid">
              <section className="glass-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                  <h2 style={{ fontSize: '1.25rem' }}>Pending Drafts</h2>
                </div>
                <div className="issue-list">
                  {pendingIssues.map(issue => (
                    <div key={issue.system.id} className="issue-item">
                      <div onClick={() => { setSelectedIssueId(issue.system.id); setView('edit'); }} style={{ cursor: 'pointer' }}>
                        <div style={{ fontWeight: 600 }}>{issue.content.original_title}</div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                          {issue.system.template_name} • {new Date(issue.system.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                        <button className="nav-item" onClick={() => handleDelete(issue.system.id)} style={{ color: 'var(--error-color)' }}>
                          <Trash2 size={16} />
                        </button>
                        <button className="btn-primary" style={{ padding: '0.5rem 1rem' }} onClick={() => handleUpload(issue.system.id)}>
                          {loading ? <Loader2 className="spin" size={16} /> : <Send size={16} />}
                        </button>
                      </div>
                    </div>
                  ))}
                  {pendingIssues.length === 0 && <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Empty</p>}
                </div>
              </section>

              <section className="glass-card">
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>Recently Uploaded</h2>
                <div className="issue-list">
                  {uploadedIssues.slice(0, 8).map(issue => (
                    <div key={issue.system.id} className="issue-item">
                      <div>
                        <div style={{ fontWeight: 600 }}>{issue.content.english_title}</div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>#{issue.system.redmine_issue_id}</div>
                      </div>
                      <a href={issue.system.redmine_issue_url} target="_blank" rel="noreferrer" className="nav-item">
                        <ExternalLink size={16} />
                      </a>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
        )}

        {view === 'create' && <CreateWizard templates={templates} onSaved={() => { fetchData(); setView('dashboard'); }} />}
        {view === 'edit' && <EditMode issueId={selectedIssueId} onSaved={() => { fetchData(); setView('dashboard'); }} onCancel={() => setView('dashboard')} />}
        {view === 'settings' && <SettingsView />}
      </main>
    </div>
  );
}

function CreateWizard({ templates, onSaved }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({ title: '', template: 'bug_report', fields: {} });
  const [preview, setPreview] = useState({ english_title: '', description: '' });
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/issues/generate`, formData);
      setPreview(res.data);
      setStep(2);
    } catch (err) {
      alert("Generate fail: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Use the preview values instead of raw generation
      const finalData = {
        ...formData,
        english_title: preview.english_title,
        description: preview.description
      };
      await axios.post(`${API_BASE}/issues/draft`, finalData);
      onSaved();
    } catch (err) {
      alert("Save fail: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const activeTemplate = templates.find(t => t.name === formData.template);

  return (
    <div className="glass-card fade-in" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
        <div style={{ opacity: step === 1 ? 1 : 0.4 }}>1. Input Details</div>
        <div style={{ opacity: step === 2 ? 1 : 0.4 }}>2. Review & Refine</div>
      </div>

      {step === 1 ? (
        <div className="fade-in">
          <div className="input-group">
            <label className="input-label">Chinese Title</label>
            <input className="input-field" autoFocus value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} placeholder="e.g. 登入失敗並顯示 500 錯誤" />
          </div>
          <div className="input-group">
            <label className="input-label">Tracker / Category</label>
            <select className="input-field" value={formData.template} onChange={e => setFormData({...formData, template: e.target.value})}>
              {templates.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
            </select>
          </div>
          {activeTemplate?.questions && Object.entries(activeTemplate.questions).map(([k, q]) => (
            <div className="input-group" key={k}>
              <label className="input-label">{q}</label>
              <textarea className="input-field" rows={2} value={formData.fields[k] || ''} onChange={e => setFormData({...formData, fields: {...formData.fields, [k]: e.target.value}})} />
            </div>
          ))}
          <button className="btn-primary" style={{ width: '100%' }} onClick={handleGenerate} disabled={!formData.title || loading}>
            {loading ? <Loader2 className="spin" /> : "Generate Preview"}
          </button>
        </div>
      ) : (
        <div className="fade-in">
          <div className="input-group">
            <label className="input-label">Final English Title</label>
            <input className="input-field" value={preview.english_title} onChange={e => setPreview({...preview, english_title: e.target.value})} />
          </div>
          <div className="input-group">
            <label className="input-label">Final Description</label>
            <textarea className="input-field" rows={12} style={{ fontFamily: 'monospace' }} value={preview.description} onChange={e => setPreview({...preview, description: e.target.value})} />
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="btn-primary" style={{ flex: 1 }} onClick={handleSave} disabled={loading}>Save to Pending</button>
            <button className="btn-primary" style={{ background: 'transparent', border: '1px solid var(--glass-border)' }} onClick={() => setStep(1)}>Back</button>
          </div>
        </div>
      )}
    </div>
  );
}

function EditMode({ issueId, onSaved, onCancel }) {
  const [issue, setIssue] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/issues/${issueId}`).then(res => setIssue(res.data));
  }, [issueId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API_BASE}/issues/${issueId}`, issue);
      onSaved();
    } catch (err) {
      alert("Save fail: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!issue) return <div className="glass-card">Loading...</div>;

  return (
    <div className="glass-card fade-in" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' }}>
        <h2>Edit Draft</h2>
        <button className="nav-item" onClick={onCancel}><X /></button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div>
          <div className="input-group">
            <label className="input-label">English Title</label>
            <input className="input-field" value={issue.content.english_title} onChange={e => setIssue({...issue, content: {...issue.content, english_title: e.target.value}})} />
          </div>
          <div className="input-group">
            <label className="input-label">Description</label>
            <textarea className="input-field" rows={15} style={{ fontFamily: 'monospace' }} value={issue.content.description} onChange={e => setIssue({...issue, content: {...issue.content, description: e.target.value}})} />
          </div>
        </div>
        <div>
           <div className="input-group">
            <label className="input-label">Original Title (CN)</label>
            <div style={{ padding: '0.8rem', background: 'rgba(0,0,0,0.1)', borderRadius: '10px', color: 'var(--text-secondary)' }}>{issue.content.original_title}</div>
          </div>
          <div className="input-group">
            <label className="input-label">Redmine Project ID</label>
            <input className="input-field" value={issue.redmine_fields.project_id} onChange={e => setIssue({...issue, redmine_fields: {...issue.redmine_fields, project_id: e.target.value}})} />
          </div>
          <div className="input-group">
            <label className="input-label">Tracker ID</label>
            <input className="input-field" value={issue.redmine_fields.tracker_id} onChange={e => setIssue({...issue, redmine_fields: {...issue.redmine_fields, tracker_id: e.target.value}})} />
          </div>
        </div>
      </div>
      <button className="btn-primary" style={{ width: '100%', marginTop: '1rem' }} onClick={handleSave} disabled={saving}>
        {saving ? <Loader2 className="spin" /> : "Confirm and Save"}
      </button>
    </div>
  );
}

function SettingsView() {
  const [config, setConfig] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/config`).then(res => setConfig(res.data));
  }, []);

  if (!config) return <div className="glass-card">Loading...</div>;

  return (
    <div className="glass-card fade-in" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1>System Settings</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Configuration loaded from config/app.yaml and .env</p>
      
      <div className="input-group">
        <label className="input-label">Redmine Base URL</label>
        <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '12px' }}>{config.redmine_url}</div>
      </div>
      
      <div className="input-group">
        <label className="input-label">Default Project</label>
        <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '12px' }}>{config.project}</div>
      </div>
      
      <div className="input-group">
        <label className="input-label">Pending Directory</label>
        <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', fontFamily: 'monospace', fontSize: '0.85rem' }}>{config.pending_dir}</div>
      </div>

      <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid var(--glass-border)', borderRadius: '12px', background: 'rgba(79, 70, 229, 0.05)' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          To change these settings, please edit the <code>config/app.yaml</code> or <code>.env</code> file directly on the server and restart the application.
        </p>
      </div>
    </div>
  );
}

export default App;
