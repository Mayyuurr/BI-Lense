/**
 * Business Domain Entities & Dashboard UI Types.
 * Represents core concepts (Sales, Inventory, Finance, HR, Procurement, CRM).
 */

export type BusinessDomain =
  | "sales"
  | "inventory"
  | "finance"
  | "hr"
  | "crm"
  | "procurement";

export interface DomainScoreSummary {
  domain: BusinessDomain;
  score: number | null; // 0 to 100
  label: string;
  changePercent?: number;
  status: "healthy" | "warning" | "critical" | "uncalibrated";
}

export interface BusinessPerformanceSummary {
  bpScore: number; // Aggregate Bp = (S + I + F + E) / 4
  status: "healthy" | "moderate_risk" | "high_risk" | "uncalibrated";
  domainScores: {
    sales: number | null;
    inventory: number | null;
    finance: number | null;
    employee: number | null;
  };
}

export interface ChartDataPoint {
  label: string;
  value: number;
  secondaryValue?: number;
  category?: string;
}

export interface FeatureDriver {
  feature: string;
  importance: number;
  impactDirection: "positive" | "negative";
}

export interface RestockAlertItem {
  skuId: string;
  productName: string;
  currentStock: number;
  reorderPoint: number;
  suggestedOrderQty: number;
  urgency: "critical" | "warning" | "normal";
}
