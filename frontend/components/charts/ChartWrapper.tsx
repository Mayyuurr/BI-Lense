import React from "react";
import { cn } from "@/lib/utils/cn";
import { Card, CardHeader, CardTitle } from "../common/Card";

interface ChartWrapperProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function ChartWrapper({
  title,
  subtitle,
  action,
  children,
  className,
}: ChartWrapperProps) {
  return (
    <Card className={cn("flex flex-col justify-between", className)}>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </CardHeader>

      <div className="w-full flex-1 pt-2">{children}</div>
    </Card>
  );
}
