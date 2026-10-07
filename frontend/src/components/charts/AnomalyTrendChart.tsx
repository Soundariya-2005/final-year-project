import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface AnomalyTrendItem {
  date: string;
  anomalies: number;
}

interface AnomalyTrendChartProps {
  data: AnomalyTrendItem[];
  title?: string;
  height?: number;
}

export const AnomalyTrendChart: React.FC<AnomalyTrendChartProps> = ({
  data,
  title = 'Daily Behavioral Anomaly Timeline',
  height = 240,
}) => {
  const formatted = (data || []).map((d) => ({
    ...d,
    displayDate: d.date.length > 5 ? d.date.slice(5) : d.date,
  }));

  return (
    <div className="w-full">
      <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400 mb-3">
        {title}
      </h4>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <AreaChart data={formatted} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="anomalyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="displayDate"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              allowDecimals={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#f8fafc',
              }}
              formatter={(val: any) => [`${val} Outliers Detected`, 'Anomalies']}
            />
            <Area
              type="monotone"
              dataKey="anomalies"
              stroke="#f43f5e"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#anomalyGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
