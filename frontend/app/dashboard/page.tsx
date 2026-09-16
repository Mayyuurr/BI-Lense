import React from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { ScoreCard } from "@/components/kpi/ScoreCard";
import { KPICard } from "@/components/kpi/KPICard";
import { RestockAlert } from "@/components/alerts/RestockAlert";
import { AlertBanner } from "@/components/alerts/AlertBanner";
import { LineChart } from "@/components/charts/LineChart";
import { BarChart } from "@/components/charts/BarChart";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { Card, CardHeader, CardTitle } from "@/components/common/Card";
import { ArrowRight, Lightbulb, Package, TrendingUp, DollarSign } from "lucide-react";

export default function DashboardPage() {
  // Prototype visualization data structure (clearly labeled placeholder)
  const salesTrendData = [
    { label: "W1", value: 4200 },
    { label: "W2", value: 4800 },
    { label: "W3", value: 4600 },
    { label: "W4", value: 5200 },
    { label: "W5 (Est)", value: 5500 },
  ];

  const inventoryTurnoverData = [
    { label: "Cat A", value: 85 },
    { label: "Cat B", value: 64 },
    { label: "Cat C", value: 42 },
    { label: "Cat D", value: 91 },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Top Notice */}
        <PlaceholderNotice moduleName="Executive Dashboard Shell" />

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Executive Performance Dashboard</h1>
            <p className="mt-1 text-xs text-slate-500">
              Aggregated domain performance indicators, predictive early warnings, and AI recommendations.
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              href="/insights"
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
            >
              <Lightbulb className="h-4 w-4" />
              View LLaMA Insights
            </Link>
          </div>
        </div>

        {/* 1. Overall Business Performance (Bp) and Core Domain Scores (S, I, F, E) */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
              Business Performance Indicators (Bp = [S + I + F + E] / 4)
            </h2>
            <span className="text-xs text-slate-400">Target Scale: 0 - 100</span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <ScoreCard
              title="Overall Performance"
              domainLetter="Bp"
              score={78.5}
              description="Composite Enterprise Score"
              className="border-indigo-200 bg-indigo-50/20"
            />
            <ScoreCard
              title="Sales Score"
              domainLetter="S"
              score={82.0}
              description="Demand stability & growth"
            />
            <ScoreCard
              title="Inventory Score"
              domainLetter="I"
              score={68.0}
              description="Buffer health & turnover"
            />
            <ScoreCard
              title="Financial Score"
              domainLetter="F"
              score={86.0}
              description="30-day cash flow safety"
            />
            <ScoreCard
              title="Employee Score"
              domainLetter="E"
              score={78.0}
              description="Task delivery & velocity"
            />
          </div>
        </div>

        {/* 2. Key Operational Metrics */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title="Next 30D Sales Forecast"
            value="$148,500"
            change={{ value: 6.4, isPositive: true }}
            subtitle="vs. previous 30-day cycle"
            icon={<TrendingUp className="h-5 w-5" />}
          />
          <KPICard
            title="Stockout Risk SKUs"
            value="3 SKUs"
            change={{ value: 2.0, isPositive: false }}
            subtitle="Requires supplier reorder"
            icon={<Package className="h-5 w-5" />}
          />
          <KPICard
            title="Cash Deficit Risk (30D)"
            value="8.2%"
            subtitle="Low deficit probability"
            icon={<DollarSign className="h-5 w-5" />}
          />
          <KPICard
            title="Backlog Risk Ratio"
            value="12.4%"
            subtitle="Normal throughput range"
          />
        </div>

        {/* 3. Operational Alerts & Procurement Restocking Triggers */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
            Critical Alerts & Procurement Triggers
          </h2>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <RestockAlert
              skuId="SKU-9042"
              productName="Industrial Filter Assembly"
              currentStock={18}
              reorderPoint={50}
              suggestedOrderQty={82}
            />
            <AlertBanner
              type="warning"
              title="Lead Time Variance Detected"
              message="Supplier delivery latency increased by 3.2 days for high-velocity hardware components."
              actionText="Review Schedule"
            />
          </div>
        </div>

        {/* 4. Domain Trend Charts */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <LineChart
            title="Sales Trend & Next-Period Forecast"
            subtitle="Weekly aggregate volume with hybrid ensemble forecast trajectory"
            data={salesTrendData}
          />
          <BarChart
            title="Inventory Health Score by Category"
            subtitle="Category-level buffer and stockout risk index"
            data={inventoryTurnoverData}
          />
        </div>

        {/* 5. Recent LLaMA Decision Intelligence Synthesis Preview */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-indigo-600" />
              <CardTitle>Latest LLaMA Decision Intelligence Synthesis</CardTitle>
            </div>
            <Link
              href="/insights"
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              Full Narrative Feed <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </CardHeader>
          <div className="rounded-lg border border-slate-100 bg-slate-50/80 p-4 text-xs leading-relaxed text-slate-700">
            <p className="font-semibold text-slate-900 mb-1">
              Executive Summary: Healthy Sales Demand with Targeted Inventory Replenishment Needed
            </p>
            <p>
              Sales volume shows steady +6.4% projected growth driven by regional distribution channels.
              However, Inventory Health (Score: 68.0) indicates localized stockout risk for 3 critical SKUs prior to the upcoming 7-day supplier delivery cycle. Operating cash flow remains robust with minimal 8.2% deficit probability over the next 30 days.
            </p>
          </div>
        </Card>
      </div>
    </DashboardShell>
  );
}
