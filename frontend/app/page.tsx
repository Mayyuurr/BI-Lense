import React from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  TrendingUp,
  Package,
  DollarSign,
  Users,
  Lightbulb,
  Layers,
} from "lucide-react";

export default function HomePage() {
  const domains = [
    { title: "Sales & Demand", desc: "Next-period demand prediction & trend analysis", href: "/sales", icon: TrendingUp },
    { title: "Inventory Health", desc: "Stockout probability before supplier deliveries", href: "/inventory", icon: Package },
    { title: "Financial Risk", desc: "30-day operating cash-flow deficit forecasting", href: "/finance", icon: DollarSign },
    { title: "HR & Productivity", desc: "Task delay risk & workload distribution metrics", href: "/hr", icon: Users },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-100">
      {/* Navigation */}
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-md">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900">BI-Lense</h1>
            <p className="text-xs text-slate-500">SME Decision Intelligence</p>
          </div>
        </div>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
        >
          Open Dashboard
          <ArrowRight className="h-4 w-4" />
        </Link>
      </header>

      {/* Hero Section */}
      <main className="mx-auto max-w-7xl px-6 pt-16 pb-24 text-center lg:px-8">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50/70 px-4 py-1.5 text-xs font-medium text-indigo-700">
          <Layers className="h-3.5 w-3.5" />
          Modular AI-Driven Decision Support System
        </div>

        <h2 className="mt-6 text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          Unified Decision Intelligence <br />
          <span className="text-indigo-600">for Growing Enterprises</span>
        </h2>

        <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-slate-600">
          Transform disparate ERP and CRM tabular records into predictive domain metrics,
          explainable SHAP factor breakdowns, and executive natural-language decision narratives.
        </p>

        <div className="mt-8 flex justify-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow hover:bg-indigo-700 transition-colors"
          >
            Launch Executive Dashboard
          </Link>
          <Link
            href="/insights"
            className="rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Explore Decision Insights
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="mt-20 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 text-left">
          {domains.map((dom) => {
            const Icon = dom.icon;
            return (
              <Link
                key={dom.title}
                href={dom.href}
                className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  {dom.title}
                </h3>
                <p className="mt-1 text-xs text-slate-500 leading-5">{dom.desc}</p>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
