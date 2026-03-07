import { useState } from 'react';
import { Wand2, Loader2, Copy, Check } from 'lucide-react';
import { creativeService } from '../services/api';

type CreativeMode = 'copy' | 'image' | 'ab-test';

export default function CreativePage() {
  const [mode, setMode] = useState<CreativeMode>('copy');
  const [brief, setBrief] = useState('');
  const [tone, setTone] = useState('professional');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    if (!brief.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      let response;
      switch (mode) {
        case 'copy':
          response = await creativeService.generateCopy(brief, tone);
          setResult(response.content || JSON.stringify(response, null, 2));
          break;
        case 'image':
          response = await creativeService.generateImage(brief);
          setResult(response.content || JSON.stringify(response, null, 2));
          break;
        case 'ab-test':
          response = await creativeService.suggestABTests(brief);
          setResult(
            response.alternatives
              ? response.alternatives.join('\n\n---\n\n')
              : JSON.stringify(response, null, 2)
          );
          break;
      }
    } catch {
      setResult('Error: Could not generate content. Please check that the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (result) {
      navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Creative Studio</h2>
        <p className="text-sm text-gray-500">Generate marketing copy, images, and A/B test variants</p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-2">
        {([
          { key: 'copy', label: 'Marketing Copy' },
          { key: 'image', label: 'Image Prompt' },
          { key: 'ab-test', label: 'A/B Variants' },
        ] as const).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setMode(key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === key
                ? 'bg-primary-600 text-white'
                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="card space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {mode === 'ab-test' ? 'Base Copy' : 'Brief / Description'}
          </label>
          <textarea
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            placeholder={
              mode === 'copy'
                ? 'Describe what you need: e.g. LinkedIn post about AI trends in marketing'
                : mode === 'image'
                ? 'Describe the image: e.g. Modern tech banner with blue gradient'
                : 'Paste your existing copy to generate A/B variants'
            }
            rows={4}
            className="input-field resize-none"
          />
        </div>

        {mode === 'copy' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tone</label>
            <select value={tone} onChange={(e) => setTone(e.target.value)} className="input-field">
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="playful">Playful</option>
              <option value="urgent">Urgent</option>
              <option value="inspirational">Inspirational</option>
            </select>
          </div>
        )}

        <button onClick={generate} disabled={loading || !brief.trim()} className="btn-primary flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
          Generate
        </button>
      </div>

      {/* Output */}
      {result && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Generated Content</h3>
            <button onClick={copyToClipboard} className="btn-secondary flex items-center gap-2 text-xs">
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-sm text-gray-800">
            {result}
          </div>
        </div>
      )}
    </div>
  );
}
