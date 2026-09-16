"use client";

import React, { useState, useEffect } from "react";
import { Bell, RefreshCw } from "lucide-react";
import { Badge } from "../common/Badge";
import { checkBackendHealth } from "@/lib/api/client";

export function Header() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  const verifyHealth = async () => {
    try {
      setBackendStatus("checking");
      const health = await checkBackendHealth();
      if (health?.status === "healthy") {
        setBackendStatus("online");
      } else {
        setBackendStatus("offline");
      }
    } catch {
      setBackendStatus("offline");
    }
  };

  useEffect(() => {
    verifyHealth();
  }, []);

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-8 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <h2 className="text-base font-semibold text-slate-800">
          Decision Intelligence Platform
        </h2>
        <span className="hidden text-xs text-slate-400 sm:inline">•</span>
        <span className="hidden text-xs text-slate-500 sm:inline">
          Small & Medium Enterprise Edition
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend API Connectivity Indicator */}
        <button
          onClick={verifyHealth}
          title="Click to re-check backend connection"
          className="flex items-center gap-1.5 cursor-pointer"
        >
          {backendStatus === "online" && (
            <Badge variant="success">API Online</Badge>
          )}
          {backendStatus === "offline" && (
            <Badge variant="warning">API Standby</Badge>
          )}
          {backendStatus === "checking" && (
            <Badge variant="neutral">
              <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
              Connecting...
            </Badge>
          )}
        </button>

        {/* Notifications Icon */}
        <div className="relative rounded-lg border border-slate-200 p-2 text-slate-500 hover:bg-slate-50 cursor-pointer">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-indigo-600" />
        </div>

        {/* User Pill */}
        <div className="flex items-center gap-2 border-l border-slate-200 pl-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
            SME
          </div>
          <div className="hidden text-left md:block">
            <p className="text-xs font-semibold text-slate-800">Executive User</p>
            <p className="text-[10px] text-slate-400">Enterprise Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
}
