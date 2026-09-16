/**
 * API Contracts & Response Interfaces.
 * Matches backend endpoints exposed under /api/v1
 */

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  database: string;
}

export interface IngestRequest {
  file_path: string;
  domain: string;
  filename?: string;
}

export interface IngestResponse {
  dataset_id?: number;
  filename: string;
  domain: string;
  initial_rows: number;
  cleaned_rows: number;
  columns: string[];
  schema_inference: Record<string, string>;
  cleaning_notes: string[];
}

export interface PredictionRequest {
  domain: "sales" | "inventory" | "finance" | "hr";
  features: Record<string, unknown>;
  target_metric?: string;
}

export interface PredictionResponse {
  domain: string;
  status: string;
  message: string;
  features_received: string[];
}

export interface ScoreComputeRequest {
  sales_data?: Record<string, unknown>;
  inventory_data?: Record<string, unknown>;
  finance_data?: Record<string, unknown>;
  hr_data?: Record<string, unknown>;
}

export interface ScoreResponse {
  bp_score: number;
  sales_score?: number | null;
  inventory_score?: number | null;
  finance_score?: number | null;
  employee_score?: number | null;
  metadata?: Record<string, unknown> | null;
}

export interface ExplanationRequest {
  domain: string;
  predicted_value: number;
  target_metric: string;
  shap_feature_importance: Record<string, number>;
  business_score?: number;
}

export interface ExplanationResponse {
  domain: string;
  headline: string;
  summary: string;
  key_drivers: string[];
  suggested_actions: string[];
  raw_response?: string | null;
}

export interface RestockCheckRequest {
  sku_id: string;
  product_name: string;
  current_stock: number;
  reorder_point?: number;
  safety_stock?: number;
  lead_time_days?: number;
  daily_demand?: number;
}

export interface RestockCheckResponse {
  sku_id: string;
  product_name: string;
  current_stock: number;
  reorder_point: number;
  suggested_order_quantity: number;
  is_triggered: boolean;
}

export interface RecommendationItem {
  domain: string;
  title: string;
  description: string;
  urgency: "low" | "medium" | "high" | "critical";
  trigger_reason: string;
  suggested_action: string;
}
