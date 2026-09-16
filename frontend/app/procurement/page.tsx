import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { KPICard } from "@/components/kpi/KPICard";
import { RestockAlert } from "@/components/alerts/RestockAlert";
import { Card, CardHeader, CardTitle } from "@/components/common/Card";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { ShoppingCart, Clock, CheckCircle2, ShieldAlert } from "lucide-react";

export default function ProcurementPage() {
  const procurementTriggers = [
    {
      sku: "SKU-9042",
      name: "Industrial Filter Assembly",
      current: 18,
      reorderPoint: 50,
      safetyStock: 15,
      leadTime: 7,
      suggestedQty: 82,
      supplier: "Global Filtration Ltd",
      status: "Triggered",
    },
    {
      sku: "SKU-3120",
      name: "Stainless Steel Fastener Pack (M8)",
      current: 45,
      reorderPoint: 100,
      safetyStock: 30,
      leadTime: 5,
      suggestedQty: 155,
      supplier: "Apex Fasteners Inc",
      status: "Triggered",
    },
    {
      sku: "SKU-1088",
      name: "Hydraulic Seal Kit (Type B)",
      current: 120,
      reorderPoint: 80,
      safetyStock: 25,
      leadTime: 10,
      suggestedQty: 0,
      supplier: "Precision Seals Co",
      status: "Adequate",
    },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="Procurement Restocking-Trigger Logic" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Procurement & Replenishment Triggers</h1>
            <p className="mt-1 text-xs text-slate-500">
              Deterministic reorder point calculations: <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[11px]">ReorderPoint = (Daily Demand × Lead Time) + Safety Stock</code>.
            </p>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title="Pending Restock Triggers"
            value="2 SKUs"
            subtitle="Immediate purchase required"
            icon={<ShieldAlert className="h-5 w-5 text-amber-600" />}
          />
          <KPICard
            title="Estimated Reorder Outlay"
            value="$18,450"
            subtitle="To restore safety buffers"
            icon={<ShoppingCart className="h-5 w-5" />}
          />
          <KPICard
            title="Avg Supplier Lead Time"
            value="7.3 Days"
            subtitle="Average across primary vendors"
            icon={<Clock className="h-5 w-5" />}
          />
          <KPICard
            title="Replenishment On-Time Rate"
            value="94.1%"
            subtitle="Last 90-day fulfillment"
            icon={<CheckCircle2 className="h-5 w-5" />}
          />
        </div>

        {/* Active Triggers */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
            Active Replenishment Alerts
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

        {/* Master Replenishment Table */}
        <Card>
          <CardHeader>
            <CardTitle>Procurement Threshold Monitoring Table</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="border-b border-slate-200 text-slate-400">
                <tr>
                  <th className="pb-2">SKU ID</th>
                  <th className="pb-2">Product Name</th>
                  <th className="pb-2 text-right">Current Stock</th>
                  <th className="pb-2 text-right">Reorder Point</th>
                  <th className="pb-2 text-right">Lead Time</th>
                  <th className="pb-2 text-right">Suggested Qty</th>
                  <th className="pb-2 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {procurementTriggers.map((item) => (
                  <tr key={item.sku} className="hover:bg-slate-50">
                    <td className="py-2.5 font-mono text-slate-700">{item.sku}</td>
                    <td className="py-2.5 font-medium text-slate-900">{item.name}</td>
                    <td className="py-2.5 text-right font-semibold">{item.current}</td>
                    <td className="py-2.5 text-right text-slate-500">{item.reorderPoint}</td>
                    <td className="py-2.5 text-right">{item.leadTime}d</td>
                    <td className="py-2.5 text-right font-bold text-indigo-600">{item.suggestedQty || "--"}</td>
                    <td className="py-2.5 text-right">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          item.status === "Triggered"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-emerald-100 text-emerald-800"
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </DashboardShell>
  );
}
