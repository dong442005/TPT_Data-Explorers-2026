# 📊 TNBike Data Analytics — Data Explorers 2026 (National Finals)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1.svg?logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811.svg?logo=powerbi&logoColor=black)
![Machine Learning](https://img.shields.io/badge/Machine_Learning-XGBoost_|_CatBoost-FF6F00.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)
[![Python Checks](https://github.com/dong442005/TPT_Data-Explorers-2026/actions/workflows/python-check.yml/badge.svg)](https://github.com/dong442005/TPT_Data-Explorers-2026/actions/workflows/python-check.yml)

This is the official repository for the **Data Explorers** team participating in the National Finals of the Data Explorers 2026 competition. The project solves supply chain optimization, demand forecasting, and B2B dealer behavior analysis for TNBike through an **End-to-End Data Pipeline**.

---

## 🏆 Key Results & Metrics

This project processes **109.4 Billion VND** in revenue across **798 B2B dealers** and **265 SKUs**.

### 1. Data Pipeline & ETL
- **100% Automation Success:** Successfully parsed and loaded 1,132 unstructured PDF/email invoices using `pdfplumber` and Regex.
- **Data Recovery:** Recovered 90 previously unclassified SKUs representing **23% of total revenue (25.28B VND)** through fuzzy matching and SQL patching.

### 2. Machine Learning Forecasting (Track 1)
Evaluated 12 model variants (XGBoost, CatBoost, LightGBM) on the March 2026 hold-out dataset.
- **Best Model:** `CatBoost_monthly_minimal`
- **WMAPE:** **0.429** (Reduced error by 24% compared to the 0.564 naive baseline)
- **Bias Ratio:** **-0.36%** (Near perfect, eliminating the -56.4% under-forecasting bias of baselines)

### 3. Dealer Churn Classification (Track 3)
Developed a proprietary 8-segment B2B RFM model to replace the statistically flawed NTILE method, scoring 798 wholesale dealers.
- **ROC-AUC:** **0.9007**
- **PR-AUC:** **0.8055**
- **Precision@100:** **85%**
- **Business Impact:** Identified 357 high-churn-risk dealers for targeted marketing interventions.

---

## 🌟 Key Highlights

- **100% Automated ETL:** Extracts, normalizes, and loads data from thousands of PDF/Email invoices directly into PostgreSQL. Thoroughly handles edge cases like font corruption and misspellings.
- **Advanced ML Forecasting System:** Builds a complete forecasting pipeline (Feature Store to Modeling) using Gradient Boosting algorithms (XGBoost, CatBoost) to forecast SKU-level demand and allocate color variants for production optimization.
- **Deep Dealer Analytics:** Applies a custom B2B RFM model to assess dealer health, forecast churn risk, and recommend resource allocation.
- **AI Business Assistant (LLM Chatbot):** A Streamlit chatbot allowing the Board of Directors to query the PostgreSQL database dynamically using natural Vietnamese language (Text-to-SQL).
- **Enterprise-Grade BI & Reporting:** Integrates a 6-page interactive Power BI dashboard. All technical designs, methodologies, and data leakage prevention strategies are auto-compiled into a LaTeX Technical Report.

---

## 📖 Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Project Structure](#2-project-structure)
3. [Database Schema](#3-database-schema)
4. [Machine Learning Forecasting](#4-machine-learning-forecasting-tracks-1-2-3)
5. [AI Business Assistant](#5-ai-business-assistant-llm-chatbot)
6. [Power BI Dashboard](#6-power-bi-dashboard)
7. [Getting Started](#7-getting-started)

---

## 1. System Architecture

The project follows a strict One-way Data Flow architecture to ensure raw data immutability and complete data lineage.

| Layer | Technology | Key Function |
|---|---|---|
| **Data Ingestion (ETL)** | Python (`pdfplumber`, `pandas`) | Reads `.eml`/PDF invoices, parses tables, normalizes corrupt data. |
| **Data Storage (DWH)** | PostgreSQL | Stores Snowflake schema and Denormalized Fact tables for BI. |
| **Feature Store & ML** | Python (`scikit-learn`, `xgboost`) | Feature Engineering (Lag, Momentum, RFM), Leakage prevention, Training. |
| **Business Intelligence** | Power BI | DirectQuery/Import from DB to render 6 interactive dashboards. |
| **AI Assistant** | Streamlit, Gemini LLM | Translates natural language into SQL to query the database. |

---

## 2. Project Structure

> [!NOTE]
> To comply with security rules and save space, some raw data or binary folders (marked `[Ignored]`) are not committed. Run the pipeline to generate them automatically.

```text
TPT_Data-Explorers-2026/
│
├── app.py                              # Streamlit Frontend for LLM Chatbot
├── README.md                           # Project overview
│
├── database/                           # SQL Schemas and Patches
│   ├── 01_create_tables.sql            # DDL: Create tnbike schema
│   ├── 02_import_data.sql              # Seed historical data
│   ├── patches/                        # SQL Patches for data quality
│   └── views/                          # Power BI Views definitions
│
├── src/                                # Core Python Pipeline
│   ├── extract_validate.py             # [ETL-E] Extract from PDF/Email
│   ├── normalize.py                    # [ETL-T] Cleanse and map categories
│   ├── load_to_database.py             # [ETL-L] Load into PostgreSQL
│   ├── business_assistant.py           # Core AI Chatbot Backend
│   ├── models/                         # Core Machine Learning & Feature Store
│   ├── eda/                            # Exploratory Data Analysis scripts
│   └── utils/                          # Shared utilities
│
├── outputs/                            # Auto-generated ML Outputs
│   ├── audit/                          # Data Quality & Leakage Audits
│   └── modeling/                       # Forecast CSVs & Markdown Reports
│
├── docs/                               # Technical Documentation
│
├── bi/                                 # Power BI (`.pbix`) files
├── notebooks/                          # [Ignored] EDA Notebooks
├── models/                             # [Ignored] Model weights (.pkl)
└── data/                               # [Ignored] Raw and Processed data
```

---

## 3. Database Schema

Data is stored in the `tnbike` PostgreSQL schema. The central `fact_sales` table is denormalized to optimize Power BI and ML queries.

**Optimized BI SQL Views (`database/views/powerbi_views.sql`):**
- `tnbike.v_rfm_analysis`: RFM scoring, groups dealers into 8 B2B segments.
- `tnbike.v_bcg_matrix`: BCG matrix for SKUs based on market share and growth.
- `tnbike.v_pipeline_status`: Tracks email processing success rates.

---

## 4. Machine Learning Forecasting (Tracks 1, 2, 3)

Located in `src/models/forecasting/` and orchestrated by `run_end_to_end.py`, the ML pipeline runs in 3 phases:
1. **Phase 1: Data Foundation:** Cleanses SKU data and aggregates revenue by time dimensions.
2. **Phase 2: Feature Store:** Engineers Lag (1M-12M), Momentum, and Cyclical features, ensuring temporal alignment to prevent data leakage.
3. **Phase 3: Modeling:** Trains ML algorithms (CatBoost, XGBoost, LightGBM) to forecast demand, allocate colors, and predict dealer churn risk.

---

## 5. AI Business Assistant (LLM Chatbot)

An integrated Streamlit Chatbot acts as a **Data Query Engine**. Managers can ask questions in natural Vietnamese, and the LLM (`src/business_assistant.py`) translates them into SQL queries executed directly against the PostgreSQL database.

---

## 6. Power BI Dashboard

The system includes a **6-page interactive dashboard** connected via DirectQuery:
1. **Executive Overview:** Revenue, volume, dealer KPIs.
2. **Time Analysis:** Seasonality and YoY/MoM trends.
3. **Product & BCG Matrix:** Evaluates 265 SKUs using the BCG matrix.
4. **Dealer RFM:** Visualizes RFM scores, Churn Risk, and VIP dealers.
5. **Geographic:** Revenue heatmaps across 63 provinces.
6. **Pipeline Operations:** ETL monitoring with 100% success tracking.

---

## 7. Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

### Setup Database
Execute the following in DBeaver/pgAdmin:
1. `database/01_create_tables.sql`
2. `database/02_import_data.sql`

Create a `.env` file for DB credentials and `GEMINI_API_KEY`:
```bash
cp .env.example .env
```

### Run Full ML Pipeline
```bash
python src/models/forecasting/run_end_to_end.py --allow-modeling --allow-overwrite
```

### Launch AI Chatbot
```bash
streamlit run app.py
```
*(Opens locally at `http://localhost:8501`)*
