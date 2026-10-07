import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  CartesianGrid,
} from 'recharts';

interface RiskDistributionChartProps {
  distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  title?: string;
  height?: number;
}

const COLORS: Record<string, string> = {
  LOW: '#10b981',      // Emerald
  MEDIUM: '#eab308',   // Yellow
  HIGH: '#f97316',     // Orange
  CRITICAL: '#f43f5e', // Rose
};

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({
  distribution,
  title = 'Risk-Level Distribution',
  height = 280,
}) => {
  const chartData = [
    { tier: 'LOW', count: distribution?.LOW || 0, color: COLORS.LOW },
    { tier: 'MEDIUM', count: distribution?.MEDIUM || 0, color: COLORS.MEDIUM },
    { tier: 'HIGH', count: distribution?.HIGH || 0, color: COLORS.HIGH },
    { tier: 'CRITICAL', count: distribution?.CRITICAL || 0, color: COLORS.CRITICAL },
  ];

  const total = chartData.reduce((acc, curr) => acc + curr.count, 0);

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400">
          {title}
        </h4>
        <span className="text-xs font-mono text-slate-500">Total: {total} Users</span>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="tier"
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
              formatter={(value: any) => [`${value} Users (${total > 0 ? ((Number(value) / total) * 100).toFixed(1) : 0}%)`, 'Count']}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
