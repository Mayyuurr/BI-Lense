import React from "react";
import { ShoppingCart, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "../common/Badge";

interface RestockAlertProps {
  skuId: string;
  productName: string;
  currentStock: number;
  reorderPoint: number;
  suggestedOrderQty: number;
  onOrderClick?: () => void;
  className?: string;
}

export function RestockAlert({
  skuId,
  productName,
  currentStock,
  reorderPoint,
  suggestedOrderQty,
  onOrderClick,
  className,
}: RestockAlertProps) {
  const isCritical = currentStock <= reorderPoint * 0.5;

  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border p-4 bg-white shadow-sm",
        isCritical ? "border-rose-300 bg-rose-50/30" : "border-slate-200",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "rounded-lg p-2.5",
            isCritical ? "bg-rose-100 text-rose-600" : "bg-amber-100 text-amber-600"
          )}
        >
          {isCritical ? (
            <AlertCircle className="h-5 w-5" />
          ) : (
            <ShoppingCart className="h-5 w-5" />
          )}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{productName}</h4>
            <Badge variant={isCritical ? "danger" : "warning"}>
              {isCritical ? "Critical Stockout Risk" : "Reorder Point Reached"}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            SKU: <span className="font-mono text-slate-700">{skuId}</span> • Current Stock:{" "}
            <span className="font-semibold text-slate-800">{currentStock}</span> (Threshold:{" "}
            {reorderPoint})
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
        <div className="text-right">
          <p className="text-xs text-slate-500">Suggested Restock</p>
          <p className="text-sm font-bold text-slate-900">{suggestedOrderQty} units</p>
        </div>
        <button
          onClick={onOrderClick}
          className="rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 transition-colors"
        >
          Create Purchase Order
        </button>
      </div>
    </div>
  );
}
