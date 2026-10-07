import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Communication Error',
  message,
  onRetry,
}) => {
  return (
    <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 flex items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
        <div>
          <h4 className="text-sm font-semibold text-rose-200">{title}</h4>
          <p className="text-xs text-rose-300/90 mt-0.5">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/40 transition flex items-center gap-1.5 shrink-0 cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </button>
      )}
    </div>
  );
};
