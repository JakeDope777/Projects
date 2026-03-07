import { useState } from 'react';
import { Search, Loader2, FileText } from 'lucide-react';
import { analysisService } from '../services/api';
import ReactMarkdown from 'react-markdown';

type AnalysisType = 'market' | 'swot' | 'pestel' | 'competitor' | 'persona';

const analysisTypes: { key: AnalysisType; label: string; placeholder: string }[] = [
  { key: 'market', label: 'Market Research', placeholder: 'e.g. SaaS market in Europe 2026' },
  { key: 'swot', label: 'SWOT Analysis', placeholder: 'e.g. Our new product launch' },
  { key: 'pestel', label: 'PESTEL Analysis', placeholder: 'e.g. European tech market' },
  { key: 'competitor', label: 'Competitor Analysis', placeholder: 'e.g. Company A, Company B' },
  { key: 'persona', label: 'Buyer Personas', placeholder: 'e.g. B2B SaaS decision makers' },
];

export default function AnalysisPage() {
  const [selectedType, setSelectedType] = useState<AnalysisType>('market');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      let response;
      switch (selectedType) {
        case 'market':
          response = await analysisService.marketResearch(query);
          break;
        case 'swot':
          response = await analysisService.swotAnalysis(query);
          break;
        case 'pestel':
          response = await analysisService.pestelAnalysis(query);
          break;
        case 'competitor':
          response = await analysisService.competitorAnalysis(query.split(',').map((s) => s.trim()));
          break;
        case 'persona':
          response = await analysisService.createPersonas(query);
          break;
      }
      setResult(JSON.stringify(response, null, 2));
    } catch {
      setResult('Error: Could not complete analysis. Please check that the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const current = analysisTypes.find((t) => t.key === selectedType)!;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Business Analysis</h2>
        <p className="text-sm text-gray-500">Run strategic analyses powered by AI</p>
      </div>

      {/* Type selector */}
      <div className="flex flex-wrap gap-2">
        {analysisTypes.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setSelectedType(key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedType === key
                ? 'bg-primary-600 text-white'
                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="card">
        <label className="block text-sm font-medium text-gray-700 mb-2">{current.label}</label>
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runAnalysis()}
            placeholder={current.placeholder}
            className="input-field"
          />
          <button onClick={runAnalysis} disabled={loading || !query.trim()} className="btn-primary flex items-center gap-2 px-5">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Analyse
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-primary-600" />
            <h3 className="text-sm font-semibold text-gray-700">Analysis Results</h3>
          </div>
          <div className="prose prose-sm max-w-none bg-gray-50 rounded-lg p-4 overflow-auto max-h-[500px]">
            <pre className="text-xs whitespace-pre-wrap">{result}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
