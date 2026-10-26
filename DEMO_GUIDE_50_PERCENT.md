# BI-Lense: 50% Implementation Live Demonstration Guide
## Step-by-Step Presenter Script & Evaluation Walkthrough (Terminal Track)

**Platform:** `BI-Lense` (AI-Driven Decision Intelligence & Decision Support Platform for SMEs)  
**Milestone:** 50% Backend Implementation Review  
**Presenter Goal:** Confidently demonstrate the entire end-to-end intelligence pipeline using just the **Terminal** and **FastAPI Interactive Swagger UI**.

---

## 📋 Pre-Demo Preparation Checklist (Do this 2 minutes before)

- [ ] Open PowerShell / Terminal in `e:\BI-Lense\backend`.
- [ ] Ensure the virtual environment is ready.
- [ ] Have your browser open at `http://localhost:8000/docs`.

---

## 🎬 Live Demo Walkthrough (Step-by-Step)

```
  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
  │  Stage 1:       │      │  Stage 2:       │      │  Stage 3:       │      │  Stage 4:       │
  │  Code Quality   │ ───► │  Start Server   │ ───► │  "One-Shot"     │ ───► │  Deep-Dive      │
  │  & Test Suite   │      │  & Swagger UI   │      │  Unified Engine │      │  Technical Demo │
  └─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

### STAGE 1: Code Quality & Mathematical Correctness Proof
**Goal:** Prove to evaluators right away that the system is fully functional, stable, and backed by robust engineering (not mock code).

#### Action:
In your terminal (`e:\BI-Lense\backend`), run:
```powershell
.venv\Scripts\pytest -v
```

#### What to Say to Evaluators:
> *"Before we test live endpoints, we want to show the test coverage and regression safety of our platform. We have built 32 automated unit and integration tests covering data validation, hybrid ensemble inference, exact linear SHAP attributions, dynamic business performance scoring, and LLaMA narrative generation. All 32 tests execute in under 25 seconds with a 100% pass rate."*

---

### STAGE 2: Start Backend Server & Open Interactive UI
**Goal:** Launch the FastAPI application directly from the terminal.

#### Action:
Run the server:
```powershell
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```
Open **`http://localhost:8000/docs`** in your browser.

#### What to Say to Evaluators:
> *"FastAPI automatically generates interactive OpenAPI/Swagger documentation for our platform. Every component—from hybrid ML inference and SHAP explainability to business health scoring and LLaMA natural-language synthesis—is accessible through documented REST APIs."*

---

### STAGE 3: The Star Demonstration — "One-Shot" Unified Intelligence Engine
**Endpoint:** `POST /api/v1/insights/dashboard-summary`  
**Goal:** Show that all modules communicate with each other in a single request.

#### Action:
1. In Swagger UI, expand **`POST /api/v1/insights/dashboard-summary`**.
2. Click **"Try it out"**.
3. Leave the Request body as `{}` (it uses built-in realistic SME defaults) and click **"Execute"**.

#### Output to Highlight on Screen:
Show the response JSON sections:
1. **`business_health`**:
   - `bp_score`: **82.33**
   - `alert_tier`: **STABLE** (Blue operating band)
   - `primary_bottleneck`: **employee** (lowest scoring domain: 67.20)
   - `domain_scores`: Sales (**91.92**), Inventory (**90.20**), Finance (**80.00**), Employee (**67.20**)
2. **`sales_forecast`**:
   - `predicted_demand`: **59.74 units** (baseline: ~55.57 units)
   - `ensemble_weights`: $w_{\text{RF}}=0.1812, w_{\text{XGB}}=0.3143, w_{\text{ANN}}=0.5046$
   - `top_positive_driver`: *"30-Day Moving Average Demand (+6.88)"*
   - `top_negative_driver`: *"Active Discount / Promotional Event (-2.89)"*
3. **`inventory_risk`**:
   - `stockout_probability`: **0.999 (99.9% - CRITICAL RISK)**
   - `restock_triggered`: **true** ($s \le R$)
   - `suggested_order_quantity`: **115.0 units**
4. **`executive_narrative`**:
   - Structured plain-language briefing with `headline`, `summary`, `key_drivers`, and `suggested_actions`.
   - `source`: `"llm_generated"` (if remote LLaMA connected) or `"deterministic_fallback"` (if offline).

#### What to Say to Evaluators:
> *"This single endpoint demonstrates the entire AI decision pipeline. When an SME owner opens their dashboard, the system doesn't just display a raw prediction. In one shot, it combines hybrid ML forecasting, exact SHAP driver analysis, multi-criteria business performance scoring ($B_p$), automated bottleneck detection, procurement restock checks, and a natural-language executive briefing."*

---

### STAGE 4: Technical Deep-Dive 1 — Exact Linear SHAP Attribution
**Endpoint:** `POST /api/v1/predictions/sales`  
**Goal:** Demonstrate explainability that solves the "black-box AI" problem for SMEs.

#### Action:
1. In Swagger UI, expand **`POST /api/v1/predictions/sales`**.
2. Click **"Try it out"**.
3. In the JSON body, you can either keep the prefilled payload or use:
   ```json
   {
     "sku_id": "SKU-001",
     "unit_price": 120.0,
     "sales_lag_1": 65.0,
     "sales_lag_7": 60.0,
     "sales_lag_30": 58.0,
     "rolling_avg_30": 62.0,
     "discount_rate": 0.10,
     "promotional_flag": 1,
     "day_of_week": 2,
     "month": 6,
     "product_category": "Hardware",
     "include_explanation": true
   }
   ```
4. Click **"Execute"**.

#### Output to Highlight on Screen:
Show the returned prediction and `"explanation"` object:
- `predicted_demand`: **59.74 units** (from Base Value of **55.57 units**)
- `ensemble_weights`: `RF: 0.1812, XGB: 0.3143, ANN: 0.5046`
- `explanation.attributions`: Array of 10 features with human-readable labels, raw feature values, SHAP values, and relative percentage impact.
- `explanation.top_positive_drivers`:
  - `rolling_avg_30` (+6.88 impact) — *"30-Day Moving Average Demand"*
- `explanation.top_negative_drivers`:
  - `promotional_flag` (-2.89 impact)
  - `discount_rate` (-0.01 impact)

#### What to Say to Evaluators:
> *"SME owners will not trust a number if they don't understand why the model predicted it. Here, we implemented Option A: Exact Linear Ensemble SHAP. By the Lundberg & Lee Additivity Axiom, the SHAP value of an ensemble equals the weighted sum of the SHAP values of its constituent models ($\phi_j = \sum w_i \phi_j^{(i)}$). Notice the base demand expectation is 55.57 units; the positive 30-day moving average pushes demand up by +6.88 units to yield our final prediction of 59.74 units. We also map cryptic feature names into executive-friendly labels."*

---

### STAGE 5: Technical Deep-Dive 2 — Dynamic Business Performance Scoring ($B_p$)
**Endpoint:** `POST /api/v1/scores/compute`  
**Goal:** Demonstrate dynamic weight redistribution when an SME has missing data.

#### Action:
1. In Swagger UI, expand **`POST /api/v1/scores/compute`**.
2. Click **"Try it out"**.
3. Supply ONLY Sales and Inventory data (leave Finance and HR as null):
   ```json
   {
     "sales_data": {
       "actual_sales": 150.0,
       "target_sales": 130.0,
       "sales_growth_rate": 12.0
     },
     "inventory_data": {
       "stockout_probability": 0.10,
       "inventory_turnover_ratio": 8.0
     }
   }
   ```
4. Click **"Execute"**.

#### Output to Highlight on Screen:
- `bp_score`: Calculated cleanly (e.g. **86.4**).
- `alert_tier`: **OPTIMAL**.
- `metadata.weights_applied`: `{"sales": 0.5, "inventory": 0.5}`.

#### What to Say to Evaluators:
> *"A major issue in real-world SME software is partial data. A small business might not have their accounting or HR software connected yet. Under standard static weighting, missing domains would give zeros and artificially drag the business health score to near zero. Our engine uses dynamic proportional weight redistribution ($w_i' = w_i / \sum_{k \in \mathcal{A}} w_k$). As you can see, the score is calculated purely across available feeds without bias."*

---

### STAGE 6: Technical Deep-Dive 3 — Remote LLaMA / Tailscale Diagnostics
**Endpoint:** `GET /api/v1/explanations/llm-status`  
**Goal:** Demonstrate host-agnostic LLM connectivity and network diagnostics.

#### Action:
1. In Swagger UI, expand **`GET /api/v1/explanations/llm-status`**.
2. Click **"Try it out"** $\rightarrow$ **"Execute"**.

#### What to Say to Evaluators:
> *"Our LLaMA narrative layer is designed with cloud and mesh VPN flexibility. It can run locally, over Tailscale on a dedicated GPU workstation, or on an AWS instance. This endpoint performs a live health check and reports network latency in milliseconds. Crucially, if the remote model is offline or network fails, our system never crashes—it immediately switches to an internal deterministic executive rule generator."*

---

## 🛡️ Evaluator Q&A Defense Sheet (Tough Questions & Answers)

### Q1: "Why did you build a hybrid ensemble of RF, XGBoost, and PyTorch ANN instead of using just one algorithm?"
> **Answer:**  
> *"No single algorithm excels across all SME data regimes. Random Forest reduces variance and prevents overfitting on small datasets; XGBoost captures complex non-linear feature interactions and splits; PyTorch ANN models smooth continuous relationships and historical temporal lags. By taking an optimal convex combination, we minimize the overall Mean Squared Error compared to any individual base model."*

### Q2: "Why did you optimize weights using SLSQP instead of a simple 33% equal average?"
> **Answer:**  
> *"Simple averaging assumes all models have equal predictive capability on every domain. Sequential Least Squares Quadratic Programming (SLSQP) solves the bounded optimization problem: $\min_w \sum (y - \sum w_i \hat{y}_i)^2$ subject to $\sum w_i = 1$ and $w_i \ge 0$. For Inventory Stockout Risk, SLSQP discovered that XGBoost was significantly superior ($w=0.8749$) while Random Forest was redundant ($w=0.0000$). Using static averaging would have degraded prediction accuracy."*

### Q3: "How do you explain an ensemble? Isn't an ANN or XGBoost a black box?"
> **Answer:**  
> *"We implemented Lundberg & Lee (2017) Exact Linear SHAP. Because our ensemble is a linear combination of base models ($\hat{y} = \sum w_i f_i$), the Shapley Additivity Axiom guarantees that the ensemble SHAP value is exactly the weighted sum of base model SHAP values: $\phi_j = \sum w_i \phi_j^{(i)}$. We use TreeExplainer for RF and XGBoost and GradientExplainer for the PyTorch ANN, wrapped in a 2D tensor adapter. This gives exact mathematical attribution without sampling approximations."*

### Q4: "Why use LLaMA if you already have SHAP values?"
> **Answer:**  
> *"SHAP values are numerical ($\phi = +24.2, -12.8$). An SME owner or store manager doesn't want to parse raw float arrays. LLaMA acts strictly as an executive translator: it takes the exact verified SHAP values and translates them into plain English headlines, summaries, and concrete procurement action items. It is never allowed to hallucinate predictions; all numbers originate from our deterministic ML pipeline."*

### Q5: "What is remaining for the final 50%?"
> **Answer:**  
> *"The backend intelligence, mathematical models, explainability engines, and API interfaces are 100% complete. The remaining 50% focuses on the client-facing presentation layer: building the Next.js 14 frontend dashboard, radial health gauges for $B_p$, interactive SHAP waterfall and driver charts, and real-time inventory restock trigger notifications."*

---

## 🏁 Summary Table of Endpoints to Show

| Endpoint | Method | What it Demonstrates |
| :--- | :---: | :--- |
| `/insights/dashboard-summary` | `POST` | **Unified Intelligence Engine**: All-in-one predictions, SHAP, $B_p$, restock, and narrative. |
| `/predictions/sales` | `POST` | **Hybrid ML & SHAP**: Demand forecast with positive/negative driver breakdown. |
| `/predictions/inventory` | `POST` | **Stockout Risk**: Risk level classification and hybrid probability. |
| `/scores/compute` | `POST` | **$B_p$ Scoring**: Multi-criteria domain health with dynamic missing data handling. |
| `/insights/procurement/restock-check` | `POST` | **Procurement Trigger**: Deterministic reorder check ($s \le R$) and optimal order quantity. |
| `/explanations/llm-status` | `GET` | **Tailscale/AWS Diagnostics**: Health check, latency in ms, and loaded models. |
