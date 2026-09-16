import React from "react";
import { cn } from "@/lib/utils/cn";
import { ChartWrapper } from "./ChartWrapper";
import type { ChartDataPoint } from "@/types/domain";

interface BarChartProps {
  title: string;
  subtitle?: string;
  data: ChartDataPoint[];
  height?: number;
  className?: string;
  color?: string;
}

export function BarChart({
  title,
  subtitle,
  data,
  height = 220,
  className,
  color = "bg-indigo-600",
}: BarChartProps) {
  const maxValue = Math.max(...data.map((d) => d.value), 1);

  return (
    <ChartWrapper title={title} subtitle={subtitle} className={className}>
      <div
        className="flex items-end justify-between gap-2 pt-4 pb-2"
        style={{ height: `${height}px` }}
      >
        {data.map((item, idx) => {
          const heightPercent = Math.max(5, (item.value / maxValue) * 100);
          return (
            <div key={idx} className="group relative flex flex-1 flex-col items-center h-full justify-end">
              {/* Tooltip */}
              <div className="pointer-events-none absolute -top-8 hidden rounded bg-slate-900 px-2 py-1 text-xs text-white shadow group-hover:block z-10">
                {item.label}: {item.value}
              </div>

              {/* Bar */}
              <div
                className={cn(
                  "w-full max-w-[36px] rounded-t-md transition-all duration-300 hover:opacity-80",
                  color
                )}
                style={{ height: `${heightPercent}%` }}
              />

              {/* Label */}
              <span className="mt-2 text-[10px] text-slate-500 truncate max-w-[48px]">
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </ChartWrapper>
  );
}
