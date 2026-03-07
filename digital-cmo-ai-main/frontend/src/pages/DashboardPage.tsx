import { useState, useEffect } from 'react';
import {
  TrendingUp, Users, DollarSign, Target, Eye, MousePointer,
  Mail, BarChart3, RefreshCw, Loader2,
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { analyticsService } from '../services/api';
import type { DashboardMetrics, ChartData } from '../types';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  change?: string;
}

function MetricCard({ label, value, icon, change }: MetricCardProps) {
  return (
    <div className="card flex items-start gap-4">
      <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center text-primary-600 flex-shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {change && <p className="text-xs text-accent-600 mt-1">{change}</p>}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [charts, setCharts] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await analyticsService.getDashboard();
      setMetrics(data.metrics);
      setCharts(data.charts || []);
    } catch {
      // Use placeholder data when backend is unavailable
      setMetrics({
        total_leads: 342, new_leads_period: 47, total_spend: 12450.00,
        conversions: 28, conversion_rate: 4.2, cac: 125.50, ltv: 1250.00,
        roas: 5.3, ctr: 3.1, impressions: 125000, clicks: 3875,
        email_open_rate: 24.5, email_click_rate: 4.8,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  const m = metrics!;

  // Transform chart data for Recharts
  const spendChart = charts.find((c) => c.id === 'spend_over_time');
  const spendData = spendChart
    ? spendChart.data.x!.map((date, i) => ({ date: date.slice(5), spend: spendChart.data.y![i] }))
    : [];

  const channelChart = charts.find((c) => c.id === 'conversions_by_channel');
  const channelData = channelChart
    ? channelChart.data.x!.map((name, i) => ({ name, conversions: channelChart.data.y![i] }))
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Marketing Dashboard</h2>
          <p className="text-sm text-gray-500">Overview of key marketing metrics (last 30 days)</p>
        </div>
        <button onClick={fetchData} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Total Leads" value={m.total_leads} icon={<Users className="w-5 h-5" />} change={`+${m.new_leads_period} this period`} />
        <MetricCard label="Total Spend" value={`$${m.total_spend.toLocaleString()}`} icon={<DollarSign className="w-5 h-5" />} />
        <MetricCard label="Conversions" value={m.conversions} icon={<Target className="w-5 h-5" />} change={`${m.conversion_rate}% rate`} />
        <MetricCard label="ROAS" value={`${m.roas}x`} icon={<TrendingUp className="w-5 h-5" />} />
        <MetricCard label="Impressions" value={m.impressions.toLocaleString()} icon={<Eye className="w-5 h-5" />} />
        <MetricCard label="Clicks" value={m.clicks.toLocaleString()} icon={<MousePointer className="w-5 h-5" />} change={`${m.ctr}% CTR`} />
        <MetricCard label="Email Open Rate" value={`${m.email_open_rate}%`} icon={<Mail className="w-5 h-5" />} />
        <MetricCard label="CAC / LTV" value={`$${m.cac} / $${m.ltv}`} icon={<BarChart3 className="w-5 h-5" />} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {spendData.length > 0 && (
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Marketing Spend Over Time</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={spendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="spend" stroke="#2563eb" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {channelData.length > 0 && (
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Conversions by Channel</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={channelData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="conversions" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
