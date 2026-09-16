import React from "react";
import { cn } from "@/lib/utils/cn";
import { ChartWrapper } from "./ChartWrapper";
import type { FeatureDriver } from "@/types/domain";

interface FeatureImportanceChartProps {
  title?: string;
  subtitle?: string;
  drivers: FeatureDriver[];
  className?: string;
}

export function FeatureImportanceChart({
  title = "SHAP Feature Attribution (Drivers)",
  subtitle = "Impact of top model features on predicted outcome",
  drivers,
  className,
}: FeatureImportanceChartProps) {
  const maxImportance = Math.max(...drivers.map((d) => Math.abs(d.importance)), 0.01);

  return (
    <ChartWrapper title={title} subtitle={subtitle} className={className}>
      <div className="space-y-3 pt-2">
        {drivers.map((driver, idx) => {
          const widthPercent = Math.min(100, Math.max(10, (Math.abs(driver.importance) / maxImportance) * 100));
          const isPositive = driver.impactDirection === "positive";

          return (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-slate-700">{driver.feature}</span>
                <span
                  className={cn(
                    "font-mono font-semibold",
                    isPositive ? "text-emerald-600" : "text-rose-600"
                  )}
                >
                  {isPositive ? "+" : ""}
                  {driver.importance.toFixed(3)}
                </span>
              </div>

              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-300",
                    isPositive ? "bg-emerald-500" : "bg-rose-500"
                  )}
                  style={{ width: `${widthPercent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </ChartWrapper>
  );
}
