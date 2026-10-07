import React, { useState, useEffect } from 'react';
import { Header, PageId } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { UploadLogsPage } from './pages/UploadLogsPage';
import { UsersPage } from './pages/UsersPage';
import { RiskAnalysisPage } from './pages/RiskAnalysisPage';
import { AlertsPage } from './pages/AlertsPage';
import { RiskAssistantPage } from './pages/RiskAssistantPage';
import { SettingsPage } from './pages/SettingsPage';
import { fetchAlerts } from './services/api';

export default function App() {
  const [activePage, setActivePage] = useState<PageId>('dashboard');
  const [navParams, setNavParams] = useState<Record<string, any>>({});
  const [criticalCount, setCriticalCount] = useState<number>(0);

  const handleNavigate = (page: string, params?: Record<string, any>) => {
    setActivePage(page as PageId);
    if (params) {
      setNavParams(params);
    } else {
      setNavParams({});
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Poll or check critical alerts count on mount
  useEffect(() => {
    async function checkCriticalAlerts() {
      try {
        const res = await fetchAlerts();
        setCriticalCount(res.critical_count || 0);
      } catch {
        // Fallback silently if still starting
      }
    }
    checkCriticalAlerts();
  }, [activePage]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      <Header
        activePage={activePage}
        onNavigate={handleNavigate}
        criticalAlertCount={criticalCount}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {activePage === 'dashboard' && <DashboardPage onNavigate={handleNavigate} />}
        {activePage === 'upload' && <UploadLogsPage onNavigate={handleNavigate} />}
        {activePage === 'users' && (
          <UsersPage onNavigate={handleNavigate} initialUserId={navParams?.userId} />
        )}
        {activePage === 'analysis' && <RiskAnalysisPage />}
        {activePage === 'alerts' && <AlertsPage onNavigate={handleNavigate} />}
        {activePage === 'assistant' && <RiskAssistantPage />}
        {activePage === 'settings' && <SettingsPage />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            Privacy-Preserving Adaptive Insider Threat Detection and Early Warning System
          </span>
          <span className="font-mono text-slate-400">
            Final-Year Engineering Project &bull; Isolation Forest &bull; EWMA &bull; SHAP XAI
          </span>
        </div>
      </footer>
    </div>
  );
}
