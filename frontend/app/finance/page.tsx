import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { KPICard } from "@/components/kpi/KPICard";
import { ScoreCard } from "@/components/kpi/ScoreCard";
import { LineChart } from "@/components/charts/LineChart";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { DollarSign, ShieldCheck } from "lucide-react";

export default function FinancePage() {
  const cashFlowForecast = [
    { label: "Day 1", value: 120000 },
    { label: "Day 7", value: 114000 },
    { label: "Day 14", value: 108000 },
    { label: "Day 21", value: 135000 },
    { label: "Day 30", value: 142000 },
  ];

  const shapDrivers = [
    { feature: "Accounts_Receivable_Aging_Days", importance: 0.35, impactDirection: "positive" as const },
    { feature: "Operating_Burn_Rate_Ratio", importance: 0.26, impactDirection: "positive" as const },
    { feature: "Cash_Reserve_Buffer_Ratio", importance: -0.41, impactDirection: "negative" as const },
    { feature: "Recurring_Customer_Inflow_Rate", importance: -0.22, impactDirection: "negative" as const },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="Financial Risk & Cash Flow Intelligence" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Financial Health & Cash-Flow Risk</h1>
            <p className="mt-1 text-xs text-slate-500">
              Forecasts probability of operating cash-flow deficit over the upcoming 30-day cycle.
            </p>
          </div>
        </div>

        {/* Financial Score & KPIs */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ScoreCard
            title="Financial Health (F)"
            domainLetter="F"
            score={86.0}
            description="30-Day Liquidity & Solvency"
          />
          <KPICard
            title="30-Day Deficit Probability"
            value="8.2%"
            change={{ value: 1.4, isPositive: true }}
            subtitle="Low deficit risk category"
            icon={<ShieldCheck className="h-5 w-5" />}
          />
          <KPICard
            title="Projected Net Cash Runway"
            value="4.6 Months"
            subtitle="At current burn rate"
            icon={<DollarSign className="h-5 w-5" />}
          />
          <KPICard
            title="Days Sales Outstanding (DSO)"
            value="34.2 Days"
            subtitle="Target DSO: < 40 Days"
          />
        </div>

        {/* Visualizations */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <LineChart
            title="30-Day Operating Cash Flow Trajectory"
            subtitle="Projected net balance factoring expected receivables and payables"
            data={cashFlowForecast}
          />
          <FeatureImportanceChart
            title="Financial Risk SHAP Feature Drivers"
            subtitle="Key drivers impacting cash deficit probability"
            drivers={shapDrivers}
          />
        </div>
      </div>
    </DashboardShell>
  );
}
