import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardHome from './pages/DashboardHome';
import ConsumersList from './pages/ConsumersList';
import ConsumerDetailView from './pages/ConsumerDetailView';
import FeedersList from './pages/FeedersList';
import FeederDetailView from './pages/FeederDetailView';
import AlertsView from './pages/AlertsView';
import CasesList from './pages/CasesList';
import ScenarioLab from './pages/ScenarioLab';
import ModelMetrics from './pages/ModelMetrics';
import { useWebSocket } from './hooks/useWebSocket';

export default function App() {
  const { alerts, clearAlerts } = useWebSocket();

  // Initialize theme class on html tag from localStorage or system preference
  useEffect(() => {
    try {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    } catch (_) {}
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout alerts={alerts} clearAlerts={clearAlerts} />}>
          <Route index element={<DashboardHome />} />
          <Route path="consumers" element={<ConsumersList />} />
          <Route path="consumers/:id" element={<ConsumerDetailView />} />
          <Route path="cases" element={<CasesList />} />
          <Route path="consumption" element={<ConsumerDetailView />} />
          <Route path="feeders" element={<FeedersList />} />
          <Route path="feeders/:id" element={<FeederDetailView />} />
          <Route
            path="alerts"
            element={<AlertsView alerts={alerts} clearAlerts={clearAlerts} />}
          />
          <Route path="simulator" element={<ScenarioLab />} />
          <Route path="metrics" element={<ModelMetrics />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
