import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { KPICard } from "@/components/kpi/KPICard";
import { ScoreCard } from "@/components/kpi/ScoreCard";
import { BarChart } from "@/components/charts/BarChart";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import { RestockAlert } from "@/components/alerts/RestockAlert";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { Package, AlertTriangle } from "lucide-react";

export default function InventoryPage() {
  const stockoutRiskByCategory = [
    { label: "Raw Materials", value: 32 },
    { label: "Hardware", value: 68 },
    { label: "Finished Goods", value: 14 },
    { label: "Packaging", value: 8 },
  ];

  const shapDrivers = [
    { feature: "Supplier_Lead_Time_Days", importance: 0.38, impactDirection: "positive" as const },
    { feature: "Daily_Depletion_Velocity", importance: 0.29, impactDirection: "positive" as const },
    { feature: "Buffer_Safety_Stock_Level", importance: -0.34, impactDirection: "negative" as const },
    { feature: "Supplier_Fulfillment_Reliability", importance: -0.21, impactDirection: "negative" as const },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="Inventory & Stockout Risk" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Inventory Health & Stockout Risk</h1>
            <p className="mt-1 text-xs text-slate-500">
              Estimates stockout probability prior to supplier deliveries using hybrid ML modeling.
            </p>
          </div>
        </div>

        {/* Inventory Score & Metrics */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ScoreCard
            title="Inventory Health (I)"
            domainLetter="I"
            score={68.0}
            description="Buffer stability & replenishment"
          />
          <KPICard
            title="Mean Stockout Probability"
            value="14.8%"
            change={{ value: 2.1, isPositive: false }}
            subtitle="Across active SKU portfolio"
            icon={<AlertTriangle className="h-5 w-5" />}
          />
          <KPICard
            title="Active SKUs Monitored"
            value="340 SKUs"
            subtitle="Full warehouse coverage"
            icon={<Package className="h-5 w-5" />}
          />
          <KPICard
            title="Avg Supplier Lead Time"
            value="8.4 Days"
            subtitle="Historical 90-day mean"
          />
        </div>

        {/* Restocking Alerts List */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
            Critical Stockout Risk SKUs (Pre-Delivery)
          </h2>
          <RestockAlert
            skuId="SKU-9042"
            productName="Industrial Filter Assembly"
            currentStock={18}
            reorderPoint={50}
            suggestedOrderQty={82}
          />
          <RestockAlert
            skuId="SKU-3120"
            productName="Stainless Steel Fastener Pack (M8)"
            currentStock={45}
            reorderPoint={100}
            suggestedOrderQty={155}
          />
        </div>

        {/* Visualizations */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <BarChart
            title="Stockout Risk Probability by Category (%)"
            subtitle="Probability of buffer exhaustion before next supplier shipment"
            data={stockoutRiskByCategory}
            color="bg-amber-500"
          />
          <FeatureImportanceChart
            title="Inventory SHAP Feature Drivers"
            subtitle="Key factors driving stockout risk predictions"
            drivers={shapDrivers}
          />
        </div>
      </div>
    </DashboardShell>
  );
}
