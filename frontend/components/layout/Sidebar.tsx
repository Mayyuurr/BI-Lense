"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  DollarSign,
  Users,
  UserCheck,
  ShoppingCart,
  Lightbulb,
  FileText,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

const navigationItems = [
  { name: "Executive Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Sales & Demand", href: "/sales", icon: TrendingUp },
  { name: "Inventory Health", href: "/inventory", icon: Package },
  { name: "Financial Risk", href: "/finance", icon: DollarSign },
  { name: "HR & Productivity", href: "/hr", icon: Users },
  { name: "CRM & Customers", href: "/crm", icon: UserCheck },
  { name: "Procurement Triggers", href: "/procurement", icon: ShoppingCart },
  { name: "Decision Insights", href: "/insights", icon: Lightbulb },
  { name: "Reports & Audits", href: "/reports", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-200 bg-white">
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-100 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <span className="text-sm font-bold tracking-tight text-slate-900">
            BI-Lense
          </span>
          <span className="block text-[10px] font-medium text-slate-400">
            SME Decision Intelligence
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-colors",
                isActive
                  ? "bg-indigo-50 text-indigo-700 font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-600"
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="border-t border-slate-100 p-4">
        <div className="rounded-lg bg-slate-50 p-3 text-[11px] text-slate-500">
          <p className="font-semibold text-slate-700">Platform Status</p>
          <p className="mt-0.5">Modular AI Foundation (Active)</p>
        </div>
      </div>
    </aside>
  );
}
