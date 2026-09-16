import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { KPICard } from "@/components/kpi/KPICard";
import { ScoreCard } from "@/components/kpi/ScoreCard";
import { LineChart } from "@/components/charts/LineChart";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { TrendingUp, UploadCloud } from "lucide-react";

export default function SalesPage() {
  const demandTrend = [
    { label: "Jan", value: 38000 },
    { label: "Feb", value: 41200 },
    { label: "Mar", value: 39500 },
    { label: "Apr", value: 44800 },
    { label: "May (Pred)", value: 47200 },
  ];

  const shapDrivers = [
    { feature: "Lag_30D_Sales_Volume", importance: 0.42, impactDirection: "positive" as const },
    { feature: "Promotional_Discount_Ratio", importance: 0.28, impactDirection: "positive" as const },
    { feature: "Regional_GDP_Growth_Index", importance: 0.15, impactDirection: "positive" as const },
    { feature: "Competitor_Price_Variance", importance: -0.19, impactDirection: "negative" as const },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="Sales & Demand Intelligence" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Sales & Demand Forecasting</h1>
            <p className="mt-1 text-xs text-slate-500">
              Hybrid ensemble predictions (Random Forest + XGBoost + ANN) for next-period demand.
            </p>
          </div>
          <button className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50">
            <UploadCloud className="h-4 w-4" />
            Upload Sales Data (CSV)
          </button>
        </div>

        {/* Sales Score & Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ScoreCard
            title="Sales Health (S)"
            domainLetter="S"
            score={82.0}
            description="Overall Sales Domain Score"
          />
          <KPICard
            title="Projected Next-Period Demand"
            value="47,200 units"
            change={{ value: 5.4, isPositive: true }}
            subtitle="Next 30-day forecast"
            icon={<TrendingUp className="h-5 w-5" />}
          />
          <KPICard
            title="Ensemble Confidence"
            value="91.4%"
            subtitle="Constrained validation fit"
          />
          <KPICard
            title="Active SKU Categories"
            value="18"
            subtitle="Catalog coverage"
          />
        </div>

        {/* Charts: Demand Forecast & SHAP Attribution */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <LineChart
            title="Historical Sales & Next-Period Forecast"
            subtitle="Monthly aggregated unit sales with ensemble projection"
            data={demandTrend}
          />
          <FeatureImportanceChart
            title="Sales SHAP Feature Drivers"
            subtitle="Key attributes influencing the demand forecast"
            drivers={shapDrivers}
          />
        </div>
      </div>
    </DashboardShell>
  );
}
