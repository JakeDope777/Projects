import { useState, useEffect } from 'react';
import { Users, Megaphone, Plus, Loader2, ShieldCheck } from 'lucide-react';
import { crmService } from '../services/api';

export default function CRMPage() {
  const [tab, setTab] = useState<'leads' | 'campaigns' | 'compliance'>('leads');
  const [leads, setLeads] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Lead form
  const [leadName, setLeadName] = useState('');
  const [leadEmail, setLeadEmail] = useState('');

  // Campaign form
  const [campName, setCampName] = useState('');
  const [campChannel, setCampChannel] = useState('email');

  // Compliance form
  const [compMessage, setCompMessage] = useState('');
  const [compChannel, setCompChannel] = useState('email');
  const [compResult, setCompResult] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [leadsRes, campsRes] = await Promise.all([
        crmService.getLeads(),
        crmService.getCampaigns(),
      ]);
      setLeads(leadsRes.leads || []);
      setCampaigns(campsRes.campaigns || []);
    } catch {
      // Backend not available
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const addLead = async () => {
    if (!leadName.trim()) return;
    try {
      await crmService.createLead(`lead-${Date.now()}`, { name: leadName, email: leadEmail });
      setLeadName('');
      setLeadEmail('');
      fetchData();
    } catch {}
  };

  const addCampaign = async () => {
    if (!campName.trim()) return;
    try {
      await crmService.createCampaign(campName, campChannel);
      setCampName('');
      fetchData();
    } catch {}
  };

  const checkCompliance = async () => {
    if (!compMessage.trim()) return;
    try {
      const result = await crmService.checkCompliance(compMessage, compChannel);
      setCompResult(result);
    } catch {
      setCompResult({ status: 'error', details: { message: 'Backend unavailable' } });
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">CRM & Campaigns</h2>
        <p className="text-sm text-gray-500">Manage leads, campaigns, and compliance</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {([
          { key: 'leads', label: 'Leads', icon: Users },
          { key: 'campaigns', label: 'Campaigns', icon: Megaphone },
          { key: 'compliance', label: 'Compliance', icon: ShieldCheck },
        ] as const).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === key
                ? 'bg-primary-600 text-white'
                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {/* Leads Tab */}
      {tab === 'leads' && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Add Lead</h3>
            <div className="flex gap-3">
              <input value={leadName} onChange={(e) => setLeadName(e.target.value)} placeholder="Name" className="input-field" />
              <input value={leadEmail} onChange={(e) => setLeadEmail(e.target.value)} placeholder="Email" className="input-field" />
              <button onClick={addLead} className="btn-primary flex items-center gap-2 px-5">
                <Plus className="w-4 h-4" /> Add
              </button>
            </div>
          </div>
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Leads ({leads.length})</h3>
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            ) : leads.length === 0 ? (
              <p className="text-sm text-gray-400">No leads yet. Add one above or use the chat.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="pb-2">ID</th><th className="pb-2">Name</th><th className="pb-2">Email</th><th className="pb-2">Created</th>
                  </tr></thead>
                  <tbody>
                    {leads.map((l: any) => (
                      <tr key={l.id} className="border-b border-gray-100">
                        <td className="py-2 text-gray-600">{l.id}</td>
                        <td className="py-2">{l.name || '-'}</td>
                        <td className="py-2">{l.email || '-'}</td>
                        <td className="py-2 text-gray-400">{l.created_at?.slice(0, 10) || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Campaigns Tab */}
      {tab === 'campaigns' && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Create Campaign</h3>
            <div className="flex gap-3">
              <input value={campName} onChange={(e) => setCampName(e.target.value)} placeholder="Campaign name" className="input-field" />
              <select value={campChannel} onChange={(e) => setCampChannel(e.target.value)} className="input-field w-40">
                <option value="email">Email</option>
                <option value="social">Social</option>
                <option value="ads">Ads</option>
              </select>
              <button onClick={addCampaign} className="btn-primary flex items-center gap-2 px-5">
                <Plus className="w-4 h-4" /> Create
              </button>
            </div>
          </div>
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Campaigns ({campaigns.length})</h3>
            {campaigns.length === 0 ? (
              <p className="text-sm text-gray-400">No campaigns yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="pb-2">Name</th><th className="pb-2">Channel</th><th className="pb-2">Status</th><th className="pb-2">Created</th>
                  </tr></thead>
                  <tbody>
                    {campaigns.map((c: any) => (
                      <tr key={c.id} className="border-b border-gray-100">
                        <td className="py-2">{c.name}</td>
                        <td className="py-2">{c.channel}</td>
                        <td className="py-2"><span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">{c.status}</span></td>
                        <td className="py-2 text-gray-400">{c.created_at?.slice(0, 10) || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Compliance Tab */}
      {tab === 'compliance' && (
        <div className="space-y-4">
          <div className="card space-y-4">
            <h3 className="text-sm font-semibold text-gray-700">Compliance Checker</h3>
            <textarea
              value={compMessage}
              onChange={(e) => setCompMessage(e.target.value)}
              placeholder="Paste your marketing message here to check compliance..."
              rows={4}
              className="input-field resize-none"
            />
            <div className="flex gap-3">
              <select value={compChannel} onChange={(e) => setCompChannel(e.target.value)} className="input-field w-40">
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="social">Social</option>
              </select>
              <button onClick={checkCompliance} className="btn-primary flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" /> Check
              </button>
            </div>
          </div>
          {compResult && (
            <div className={`card border-l-4 ${compResult.status === 'compliant' || compResult.details?.is_compliant ? 'border-l-green-500' : 'border-l-red-500'}`}>
              <h3 className="text-sm font-semibold mb-2">
                {compResult.details?.is_compliant ? 'Compliant' : 'Issues Found'}
              </h3>
              <pre className="text-xs bg-gray-50 rounded p-3 overflow-auto">
                {JSON.stringify(compResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
