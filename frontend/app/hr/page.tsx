import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { KPICard } from "@/components/kpi/KPICard";
import { ScoreCard } from "@/components/kpi/ScoreCard";
import { BarChart } from "@/components/charts/BarChart";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { Users, CheckCircle2 } from "lucide-react";

export default function HRPage() {
  const workloadByDepartment = [
    { label: "Engineering", value: 88 },
    { label: "Operations", value: 72 },
    { label: "Sales/Support", value: 65 },
    { label: "Logistics", value: 81 },
  ];

  const shapDrivers = [
    { feature: "Work_In_Progress_Task_Density", importance: 0.39, impactDirection: "positive" as const },
    { feature: "Overtime_Hours_Per_Employee", importance: 0.28, impactDirection: "positive" as const },
    { feature: "Cross_Functional_Resource_Availability", importance: -0.31, impactDirection: "negative" as const },
    { feature: "Historical_Sprint_Completion_Rate", importance: -0.25, impactDirection: "negative" as const },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="HR & Productivity Intelligence" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">HR & Operational Productivity</h1>
            <p className="mt-1 text-xs text-slate-500">
              Evaluates task delivery velocity and backlog risk across departments.
              <em> (Note: Task delay vs. backlog probability target metric is pending research finalization).</em>
            </p>
          </div>
        </div>

        {/* HR Score & Metrics */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ScoreCard
            title="Employee Performance (E)"
            domainLetter="E"
            score={78.0}
            description="Task velocity & completion rate"
          />
          <KPICard
            title="Mean Task Delay Risk"
            value="1.8 Days"
            subtitle="Projected schedule slippage"
            icon={<Users className="h-5 w-5" />}
          />
          <KPICard
            title="Active Operational Teams"
            value="6 Teams"
            subtitle="48 Full-time equivalents"
          />
          <KPICard
            title="Sprint Velocity Completion"
            value="89.5%"
            subtitle="On-time delivery index"
            icon={<CheckCircle2 className="h-5 w-5" />}
          />
        </div>

        {/* Visualizations */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <BarChart
            title="Capacity Utilization / Workload by Department (%)"
            subtitle="Current workload density against baseline team capacity"
            data={workloadByDepartment}
            color="bg-indigo-500"
          />
          <FeatureImportanceChart
            title="Productivity SHAP Feature Drivers"
            subtitle="Factors impacting task completion slippage"
            drivers={shapDrivers}
          />
        </div>
      </div>
    </DashboardShell>
  );
}
