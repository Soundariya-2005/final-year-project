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
import { UserSummaryItem } from '../../services/api';

interface UsersRankedByRiskChartProps {
  users: UserSummaryItem[];
  title?: string;
  height?: number;
  maxUsers?: number;
}

export const UsersRankedByRiskChart: React.FC<UsersRankedByRiskChartProps> = ({
  users,
  title = 'Top Users Ranked by Progressive Risk',
  height = 280,
  maxUsers = 8,
}) => {
  const topUsers = (users || []).slice(0, maxUsers).map((u) => ({
    id: u.pseudonymous_id,
    risk: u.latest_risk_score,
    level: u.latest_risk_level,
    anomalies: u.anomaly_count,
  }));

  const getColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return '#f43f5e';
      case 'HIGH':
        return '#f97316';
      case 'MEDIUM':
        return '#eab308';
      default:
        return '#10b981';
    }
  };

  return (
    <div className="w-full">
      <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400 mb-3">
        {title}
      </h4>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <BarChart
            data={topUsers}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 100]}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="id"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              width={75}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#f8fafc',
              }}
              formatter={(value: any, _, item: any) => [
                `${Number(value).toFixed(1)} / 100 (${item.payload.level}) - ${item.payload.anomalies} Anomalies`,
                'Risk Score',
              ]}
            />
            <Bar dataKey="risk" radius={[0, 4, 4, 0]}>
              {topUsers.map((entry, index) => (
                <Cell key={`ranked-cell-${index}`} fill={getColor(entry.level)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
