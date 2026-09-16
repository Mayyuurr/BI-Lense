import React from "react";
import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface PlaceholderNoticeProps {
  moduleName?: string;
  className?: string;
}

export function PlaceholderNotice({
  moduleName = "This module",
  className,
}: PlaceholderNoticeProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-xs text-amber-800",
        className
      )}
    >
      <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
      <span>
        <strong>UI Foundation Phase:</strong> {moduleName} currently displays prototype layout structures. Analytical models, calibrated score weights, and live backend connections will be integrated cleanly in subsequent phases.
      </span>
    </div>
  );
}
