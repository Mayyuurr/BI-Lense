import React from "react";
import { cn } from "@/lib/utils/cn";
import { ChartWrapper } from "./ChartWrapper";
import type { ChartDataPoint } from "@/types/domain";

interface LineChartProps {
  title: string;
  subtitle?: string;
  data: ChartDataPoint[];
  height?: number;
  className?: string;
  showForecastBoundary?: boolean;
}

export function LineChart({
  title,
  subtitle,
  data,
  height = 220,
  className,
  showForecastBoundary,
}: LineChartProps) {
  if (!data.length) return null;

  const maxValue = Math.max(...data.map((d) => d.value), 1);
  const minValue = Math.min(...data.map((d) => d.value), 0);
  const range = maxValue - minValue || 1;

  const points = data.map((d, idx) => {
    const x = (idx / (data.length - 1 || 1)) * 100;
    const y = 100 - ((d.value - minValue) / range) * 85 - 10;
    return `${x},${y}`;
  }).join(" ");

  return (
    <ChartWrapper title={title} subtitle={subtitle} className={className}>
      <div className="relative w-full" style={{ height: `${height}px` }}>
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="h-full w-full overflow-visible"
        >
          {/* Grid lines */}
          <line x1="0" y1="20" x2="100" y2="20" stroke="#f1f5f9" strokeWidth="0.8" />
          <line x1="0" y1="50" x2="100" y2="50" stroke="#f1f5f9" strokeWidth="0.8" />
          <line x1="0" y1="80" x2="100" y2="80" stroke="#f1f5f9" strokeWidth="0.8" />

          {/* Polyline */}
          <polyline
            fill="none"
            stroke="#6366f1"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />

          {/* Data Points */}
          {data.map((d, idx) => {
            const x = (idx / (data.length - 1 || 1)) * 100;
            const y = 100 - ((d.value - minValue) / range) * 85 - 10;
            return (
              <circle
                key={idx}
                cx={x}
                cy={y}
                r="2"
                className="fill-white stroke-indigo-600 stroke-[1.5] transition-transform hover:scale-150"
              />
            );
          })}
        </svg>

        {/* X-axis labels */}
        <div className="mt-2 flex justify-between text-[10px] text-slate-400">
          <span>{data[0]?.label}</span>
          {data.length > 2 && <span>{data[Math.floor(data.length / 2)]?.label}</span>}
          <span>{data[data.length - 1]?.label}</span>
        </div>
      </div>
    </ChartWrapper>
  );
}
