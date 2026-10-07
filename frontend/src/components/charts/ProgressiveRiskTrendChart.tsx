import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

interface DailyTrendPoint {
  date: string;
  avg_risk: number;
  max_risk: number;
  anomalies?: number;
}

interface ProgressiveRiskTrendChartProps {
  data: DailyTrendPoint[];
  title?: string;
  height?: number;
}

export const ProgressiveRiskTrendChart: React.FC<ProgressiveRiskTrendChartProps> = ({
  data,
  title = 'Progressive Risk Score Trend (Organizational Timeline)',
  height = 280,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 text-xs">
        No trend records available
      </div>
    );
  }

  // Format date display for cleaner axis
  const formattedData = data.map((d) => ({
    ...d,
    displayDate: d.date.length > 5 ? d.date.slice(5) : d.date,
  }));

  return (
    <div className="w-full">
      {title && (
        <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400 mb-3">
          {title}
        </h4>
      )}
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <LineChart data={formattedData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
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
              domain={[0, 100]}
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
              labelFormatter={(_, arr) => {
                const item = arr?.[0]?.payload;
                return item ? `Date: ${item.date}` : '';
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="max_risk"
              name="Peak User Risk"
              stroke="#f43f5e"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="avg_risk"
              name="Org Average Risk"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
