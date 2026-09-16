import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { KPICard } from "@/components/kpi/KPICard";
import { BarChart } from "@/components/charts/BarChart";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { Card, CardHeader, CardTitle } from "@/components/common/Card";
import { UserCheck, Users, ShoppingBag } from "lucide-react";

export default function CRMPage() {
  const customerSegmentData = [
    { label: "Enterprise", value: 45 },
    { label: "Mid-Market", value: 85 },
    { label: "Small Biz", value: 160 },
    { label: "Direct", value: 92 },
  ];

  const recentAccounts = [
    { name: "Apex Industrial Logistics", segment: "Enterprise", orders: 34, status: "Active", recency: "2 days ago" },
    { name: "Beacon Retail Corp", segment: "Mid-Market", orders: 19, status: "Active", recency: "5 days ago" },
    { name: "Crestview Manufacturing", segment: "Enterprise", orders: 48, status: "Active", recency: "1 day ago" },
    { name: "Delta Distribution Partners", segment: "Small Biz", orders: 12, status: "Review", recency: "18 days ago" },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="CRM & Customer Intelligence (Supporting Source)" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">CRM & Customer Supporting Insights</h1>
            <p className="mt-1 text-xs text-slate-500">
              Customer segments and transaction frequency serving as foundational features for Sales & Demand forecasts.
            </p>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title="Total Active SME Accounts"
            value="382 Accounts"
            change={{ value: 4.8, isPositive: true }}
            subtitle="Engaged in last 90 days"
            icon={<UserCheck className="h-5 w-5" />}
          />
          <KPICard
            title="Repeat Purchase Frequency"
            value="2.8x / Mo"
            subtitle="Historical customer cadence"
            icon={<ShoppingBag className="h-5 w-5" />}
          />
          <KPICard
            title="Avg Customer Order Value"
            value="$4,280"
            subtitle="Median transaction size"
          />
          <KPICard
            title="Customer Retention Rate"
            value="92.4%"
            subtitle="Annualized cohort health"
            icon={<Users className="h-5 w-5" />}
          />
        </div>

        {/* Segment Chart & Accounts Table */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <BarChart
            title="Customer Accounts by Segment"
            subtitle="Distribution of SME buyer classifications"
            data={customerSegmentData}
          />

          <Card>
            <CardHeader>
              <CardTitle>High-Velocity SME Customer Accounts</CardTitle>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="border-b border-slate-200 text-slate-400">
                  <tr>
                    <th className="pb-2">Account Name</th>
                    <th className="pb-2">Segment</th>
                    <th className="pb-2 text-right">Orders</th>
                    <th className="pb-2 text-right">Last Activity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentAccounts.map((acc) => (
                    <tr key={acc.name} className="hover:bg-slate-50">
                      <td className="py-2.5 font-medium text-slate-800">{acc.name}</td>
                      <td className="py-2.5">{acc.segment}</td>
                      <td className="py-2.5 text-right font-mono">{acc.orders}</td>
                      <td className="py-2.5 text-right text-slate-400">{acc.recency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
