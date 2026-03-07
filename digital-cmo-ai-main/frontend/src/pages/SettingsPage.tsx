import { useState } from 'react';
import { Save, Key, Database, Brain } from 'lucide-react';

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || 'http://localhost:8000');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Settings</h2>
        <p className="text-sm text-gray-500">Configure your Digital CMO AI instance</p>
      </div>

      {/* API Configuration */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-700">API Configuration</h3>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">Backend API URL</label>
          <input value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} className="input-field" />
        </div>
      </div>

      {/* Integration Keys */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <Key className="w-5 h-5 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-700">Integration Keys</h3>
        </div>
        <p className="text-sm text-gray-500">
          API keys are configured on the backend via environment variables. See the
          <code className="mx-1 px-1.5 py-0.5 bg-gray-100 rounded text-xs">.env.example</code>
          file for all available settings.
        </p>
        <div className="bg-gray-50 rounded-lg p-4 text-xs font-mono text-gray-600 space-y-1">
          <p>OPENAI_API_KEY=sk-...</p>
          <p>HUBSPOT_API_KEY=pat-...</p>
          <p>SENDGRID_API_KEY=SG....</p>
          <p>GOOGLE_ADS_CLIENT_ID=...</p>
          <p>GOOGLE_ANALYTICS_PROPERTY_ID=...</p>
          <p>LINKEDIN_CLIENT_ID=...</p>
        </div>
      </div>

      {/* Model Configuration */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-700">AI Model</h3>
        </div>
        <p className="text-sm text-gray-500">
          The default model is <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">gpt-4</code>.
          Change the <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">OPENAI_MODEL</code> environment
          variable to use a different model.
        </p>
      </div>

      <button onClick={handleSave} className="btn-primary flex items-center gap-2">
        <Save className="w-4 h-4" />
        {saved ? 'Saved!' : 'Save Settings'}
      </button>
    </div>
  );
}
