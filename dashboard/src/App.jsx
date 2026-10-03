import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardHome from './pages/DashboardHome';
import ConsumersList from './pages/ConsumersList';
import ConsumerDetailView from './pages/ConsumerDetailView';
import FeedersList from './pages/FeedersList';
import FeederDetailView from './pages/FeederDetailView';
import AlertsView from './pages/AlertsView';
import { useWebSocket } from './hooks/useWebSocket';

export default function App() {
  const { alerts, clearAlerts } = useWebSocket();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout alerts={alerts} clearAlerts={clearAlerts} />}>
          <Route index element={<DashboardHome />} />
          <Route path="consumers" element={<ConsumersList />} />
          <Route path="consumers/:id" element={<ConsumerDetailView />} />
          <Route path="feeders" element={<FeedersList />} />
          <Route path="feeders/:id" element={<FeederDetailView />} />
          <Route
            path="alerts"
            element={<AlertsView alerts={alerts} clearAlerts={clearAlerts} />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
