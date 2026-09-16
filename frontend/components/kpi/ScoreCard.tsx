import React from "react";
import { cn } from "@/lib/utils/cn";
import { Card } from "../common/Card";
import { getScoreBadgeColor } from "@/lib/utils/formatters";

interface ScoreCardProps {
  title: string;
  domainLetter: "S" | "I" | "F" | "E" | "Bp";
  score: number | null;
  description: string;
  className?: string;
}

export function ScoreCard({
  title,
  domainLetter,
  score,
  description,
  className,
}: ScoreCardProps) {
  const badgeStyle = getScoreBadgeColor(score);

  return (
    <Card className={cn("relative overflow-hidden p-5", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600 font-bold text-white text-sm">
            {domainLetter}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
            <p className="text-xs text-slate-500">{description}</p>
          </div>
        </div>

        <div
          className={cn(
            "rounded-lg border px-3 py-1 font-bold text-lg",
            badgeStyle.bg,
            badgeStyle.text,
            badgeStyle.border
          )}
        >
          {score !== null && score !== undefined ? `${score.toFixed(1)}` : "--"}
        </div>
      </div>

      <div className="mt-4">
        <div className="flex justify-between text-xs text-slate-500 mb-1">
          <span>Target / Health Scale</span>
          <span>{score !== null ? `${Math.round(score)}/100` : "Awaiting Calibration"}</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={cn(
              "h-full transition-all duration-500",
              score === null
                ? "w-0 bg-slate-300"
                : score >= 75
                ? "bg-emerald-500"
                : score >= 50
                ? "bg-amber-500"
                : "bg-rose-500"
            )}
            style={{ width: score !== null ? `${Math.min(100, Math.max(0, score))}%` : "0%" }}
          />
        </div>
      </div>
    </Card>
  );
}
