import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subMessage?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading live telemetry...',
  subMessage = 'Querying detection pipeline and MySQL models',
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800/80">
      <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mb-3" />
      <h4 className="text-sm font-semibold text-slate-200">{message}</h4>
      {subMessage && (
        <p className="text-xs text-slate-400 mt-1">{subMessage}</p>
      )}
    </div>
  );
};
