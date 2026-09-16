import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { Card, CardHeader, CardTitle } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { Lightbulb, CheckCircle2, AlertTriangle, ArrowRight, MessageSquare } from "lucide-react";

export default function InsightsPage() {
  const recommendations = [
    {
      domain: "Inventory",
      title: "Expedite Purchase Orders for 2 Hardware SKUs",
      description: "Daily consumption velocity has exceeded forecasted baseline. Buffer stocks are projected to deplete 2.4 days before the supplier shipment arrival.",
      urgency: "high" as const,
      triggerReason: "Current stock (18) < Reorder threshold (50)",
      suggestedAction: "Trigger emergency restock PO with supplier Global Filtration Ltd.",
    },
    {
      domain: "Finance",
      title: "Follow up on Aged Accounts Receivable (> 45 Days)",
      description: "Operating cash-flow deficit probability will reduce from 8.2% to < 3.0% if $32,000 in outstanding 45-day invoices are collected within the next 10 business days.",
      urgency: "medium" as const,
      triggerReason: "Receivables Aging SHAP attribution is the top positive risk contributor.",
      suggestedAction: "Send automated statement reminders to top 4 delinquent SME accounts.",
    },
    {
      domain: "Sales",
      title: "Capitalize on Regional Demand Surge in Sector B",
      description: "Hybrid ML models project a +6.4% surge in regional demand. Ensure supply buffer alignment to avoid lost revenue opportunities.",
      urgency: "low" as const,
      triggerReason: "Historical lag volume and seasonal promotional elasticity.",
      suggestedAction: "Coordinate with distribution partners to scale logistics readiness.",
    },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="LLaMA-7B Explanation & Decision Insights" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Decision Intelligence & Explanations</h1>
            <p className="mt-1 text-xs text-slate-500">
              Natural-language synthesis translating hybrid ML predictions and SHAP factor breakdowns into executive actions.
            </p>
          </div>
        </div>

        {/* LLaMA Narrative Overview Card */}
        <Card className="border-indigo-200 bg-gradient-to-r from-indigo-50/50 via-white to-indigo-50/30">
          <CardHeader>
            <div className="flex items-center gap-2.5">
              <div className="rounded-lg bg-indigo-600 p-2 text-white">
                <MessageSquare className="h-5 w-5" />
              </div>
              <div>
                <CardTitle>Local LLaMA-7B Decision Explanation Summary</CardTitle>
                <p className="text-xs text-slate-500">Synthesized from current domain metrics & SHAP attribution vectors</p>
              </div>
            </div>
            <Badge variant="brand">Explanation Layer</Badge>
          </CardHeader>

          <div className="space-y-3 text-xs leading-relaxed text-slate-700">
            <p>
              <strong>Executive Briefing:</strong> Overall enterprise performance index sits at <strong>Bp = 78.5</strong>, indicating strong commercial demand and healthy financial buffers. The primary operational friction point is isolated in <strong>Inventory Replenishment (Score: 68.0)</strong> where supplier lead time variance threatens buffer depletion for 2 key assemblies.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="font-semibold text-slate-900">Top Opportunity</p>
                <p className="mt-0.5 text-slate-500">Capture +6.4% next-period sales growth via pre-positioned stock.</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="font-semibold text-slate-900">Primary Risk</p>
                <p className="mt-0.5 text-slate-500">Stockout on Filter Assembly before 7-day supplier replenishment.</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="font-semibold text-slate-900">Liquidity Status</p>
                <p className="mt-0.5 text-slate-500">Low 8.2% cash deficit risk; adequate 4.6-month operating runway.</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Actionable Recommendations Feed */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
            Prioritized Action Recommendations
          </h2>

          <div className="space-y-3">
            {recommendations.map((rec, idx) => (
              <Card key={idx} className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 rounded-lg bg-indigo-50 p-2 text-indigo-600">
                      <Lightbulb className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-900">{rec.title}</h3>
                        <Badge
                          variant={
                            rec.urgency === "high"
                              ? "danger"
                              : rec.urgency === "medium"
                              ? "warning"
                              : "neutral"
                          }
                        >
                          {rec.urgency.toUpperCase()} PRIORITY
                        </Badge>
                        <span className="text-xs font-mono text-slate-400">[{rec.domain}]</span>
                      </div>
                      <p className="mt-1.5 text-xs text-slate-600 leading-relaxed">{rec.description}</p>
                      
                      <div className="mt-3 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6 text-[11px] text-slate-500 border-t border-slate-100 pt-3">
                        <span><strong>Trigger Reason:</strong> {rec.triggerReason}</span>
                        <span><strong>Recommended Action:</strong> {rec.suggestedAction}</span>
                      </div>
                    </div>
                  </div>

                  <button className="hidden sm:inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shrink-0">
                    Apply Action <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
