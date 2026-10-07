import React from 'react';
import {
  ShieldCheck,
  LayoutDashboard,
  UploadCloud,
  Users,
  TrendingUp,
  ShieldAlert,
  Zap,
  Sliders,
  Lock,
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'upload'
  | 'users'
  | 'analysis'
  | 'alerts'
  | 'assistant'
  | 'settings';

interface HeaderProps {
  activePage: PageId;
  onNavigate: (page: PageId, params?: Record<string, any>) => void;
  criticalAlertCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  activePage,
  onNavigate,
  criticalAlertCount = 0,
}) => {
  const navItems: { id: PageId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload Logs', icon: UploadCloud },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'analysis', label: 'Risk Analysis', icon: TrendingUp },
    { id: 'alerts', label: 'Alerts', icon: ShieldAlert },
    { id: 'assistant', label: 'Risk Assistant', icon: Zap },
    { id: 'settings', label: 'Settings', icon: Sliders },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/95 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        {/* Top Branding Bar */}
        <div className="py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 text-cyan-400 border border-cyan-500/30 rounded-xl shadow-inner">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm sm:text-base font-bold text-white tracking-tight leading-snug">
                  Privacy-Preserving Adaptive Insider Threat Detection
                </h1>
                <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  <Lock className="w-2.5 h-2.5 mr-1" />
                  SHA-256 Masked
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                EWMA Behavioral Baselines &bull; Unsupervised Isolation Forest &bull; SHAP Explainability
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            {criticalAlertCount > 0 && (
              <button
                onClick={() => onNavigate('alerts')}
                className="px-2.5 py-1 bg-rose-500/15 text-rose-400 rounded-lg border border-rose-500/30 font-mono font-semibold flex items-center gap-1.5 animate-pulse cursor-pointer"
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>{criticalAlertCount} Critical Threats</span>
              </button>
            )}

            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-mono font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800/80">
              <span className="w-1.5 h-1.5 mr-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
              Live Pipeline Active
            </span>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <nav className="flex items-center space-x-1 py-1.5 overflow-x-auto scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition flex items-center gap-2 whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-slate-800 text-cyan-400 font-semibold border border-slate-700 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {item.id === 'alerts' && criticalAlertCount > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-rose-500 text-white">
                    {criticalAlertCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
