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

interface FactorItem {
  feature: string;
  mean_absolute_shap?: number;
  contribution?: number;
  direction?: string;
}

interface ShapContributingFactorsChartProps {
  factors: FactorItem[];
  title?: string;
  height?: number;
}

export const ShapContributingFactorsChart: React.FC<ShapContributingFactorsChartProps> = ({
  factors,
  title = 'Top Contributing Factors (SHAP Feature Attribution)',
  height = 280,
}) => {
  const chartData = (factors || []).map((f) => {
    const value = f.mean_absolute_shap !== undefined ? f.mean_absolute_shap : (f.contribution || 0);
    // Format label for display
    const readable = f.feature
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
    return {
      feature: readable,
      rawFeature: f.feature,
      value: Number(value.toFixed(4)),
      direction: f.direction || 'INCREASES_RISK',
    };
  });

  return (
    <div className="w-full">
      <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400 mb-3">
        {title}
      </h4>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
            <XAxis
              type="number"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="feature"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              width={130}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#f8fafc',
              }}
              formatter={(val: any) => [`${val} |SHAP| (Game-Theoretic Impact)`, 'Attribution']}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {chartData.map((_, index) => {
                const color = index === 0 ? '#f43f5e' : index === 1 ? '#f97316' : '#06b6d4';
                return <Cell key={`shap-cell-${index}`} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
