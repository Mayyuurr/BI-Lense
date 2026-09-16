import React from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { Card, CardHeader, CardTitle } from "@/components/common/Card";
import { PlaceholderNotice } from "@/components/common/PlaceholderNotice";
import { FileText, Download, Calendar, CheckCircle } from "lucide-react";

export default function ReportsPage() {
  const generatedReports = [
    { title: "Monthly Business Performance Scorecard (Bp)", date: "Sep 15, 2026", type: "PDF / JSON", size: "1.8 MB", status: "Ready" },
    { title: "Sales & Demand Ensemble Forecast Report", date: "Sep 14, 2026", type: "PDF / CSV", size: "3.2 MB", status: "Ready" },
    { title: "Inventory Buffer & Stockout Risk Audit", date: "Sep 10, 2026", type: "PDF", size: "1.4 MB", status: "Ready" },
    { title: "30-Day Operating Cash-Flow Deficit Analysis", date: "Sep 01, 2026", type: "PDF / Excel", size: "2.1 MB", status: "Ready" },
  ];

  return (
    <DashboardShell>
      <div className="space-y-6">
        <PlaceholderNotice moduleName="Reports & Performance Audits" />

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Executive Performance Reports</h1>
            <p className="mt-1 text-xs text-slate-500">
              Download and schedule periodic decision intelligence audits across domains.
            </p>
          </div>
          <button className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors">
            <FileText className="h-4 w-4" />
            Generate New Report
          </button>
        </div>

        {/* Reports Archive Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Decision Intelligence Summaries</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="border-b border-slate-200 text-slate-400">
                <tr>
                  <th className="pb-2">Report Document</th>
                  <th className="pb-2">Generated Date</th>
                  <th className="pb-2">Formats</th>
                  <th className="pb-2">File Size</th>
                  <th className="pb-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {generatedReports.map((rep, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-3 font-medium text-slate-900 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-indigo-600 shrink-0" />
                      {rep.title}
                    </td>
                    <td className="py-3 text-slate-500">{rep.date}</td>
                    <td className="py-3 font-mono text-[11px]">{rep.type}</td>
                    <td className="py-3">{rep.size}</td>
                    <td className="py-3 text-right">
                      <button className="inline-flex items-center gap-1 rounded bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-200 transition-colors">
                        <Download className="h-3 w-3" /> Download
                      </button>
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
