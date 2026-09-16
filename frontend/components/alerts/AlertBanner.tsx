import React from "react";
import { AlertTriangle, Info, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface AlertBannerProps {
  title: string;
  message: string;
  type?: "info" | "warning" | "critical" | "success";
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export function AlertBanner({
  title,
  message,
  type = "info",
  actionText,
  onAction,
  className,
}: AlertBannerProps) {
  const typeConfig = {
    info: {
      icon: <Info className="h-5 w-5 text-indigo-600" />,
      style: "bg-indigo-50 border-indigo-200 text-indigo-900",
      btnStyle: "bg-indigo-600 text-white hover:bg-indigo-700",
    },
    warning: {
      icon: <AlertTriangle className="h-5 w-5 text-amber-600" />,
      style: "bg-amber-50 border-amber-200 text-amber-900",
      btnStyle: "bg-amber-600 text-white hover:bg-amber-700",
    },
    critical: {
      icon: <XCircle className="h-5 w-5 text-rose-600" />,
      style: "bg-rose-50 border-rose-200 text-rose-900",
      btnStyle: "bg-rose-600 text-white hover:bg-rose-700",
    },
    success: {
      icon: <CheckCircle2 className="h-5 w-5 text-emerald-600" />,
      style: "bg-emerald-50 border-emerald-200 text-emerald-900",
      btnStyle: "bg-emerald-600 text-white hover:bg-emerald-700",
    },
  };

  const config = typeConfig[type];

  return (
    <div
      className={cn(
        "flex items-start justify-between rounded-xl border p-4 shadow-sm",
        config.style,
        className
      )}
    >
      <div className="flex gap-3">
        <div className="mt-0.5 shrink-0">{config.icon}</div>
        <div>
          <h4 className="text-sm font-semibold">{title}</h4>
          <p className="mt-0.5 text-xs opacity-90">{message}</p>
        </div>
      </div>

      {actionText && (
        <button
          onClick={onAction}
          className={cn(
            "ml-4 shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
            config.btnStyle
          )}
        >
          {actionText}
        </button>
      )}
    </div>
  );
}
