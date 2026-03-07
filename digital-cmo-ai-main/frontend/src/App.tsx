import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import AnalysisPage from './pages/AnalysisPage';
import CreativePage from './pages/CreativePage';
import CRMPage from './pages/CRMPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<ChatPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="analysis" element={<AnalysisPage />} />
        <Route path="creative" element={<CreativePage />} />
        <Route path="crm" element={<CRMPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
