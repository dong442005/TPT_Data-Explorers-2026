import os

REPO_ROOT = r"C:\Users\HOANG TUNG\TPT_Data-Explorers-2026"
REPORT_DIR = os.path.join(REPO_ROOT, "docs/reports/technical_report")


def create_main_en():
    tex = r"""\documentclass[12pt,a4paper]{article}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\usepackage{fontspec}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{caption}
\usepackage{titlesec}
\usepackage{float}
\usepackage{placeins}
\usepackage{listings}

\lstset{
    basicstyle=\ttfamily,
    breaklines=true,
    columns=fullflexible,
    keepspaces=true,
    upquote=true,
    literate={-}{-}1
}

% APA-inspired settings
\setstretch{1.25}
\setlength{\parindent}{0.5in}

% Font Policy: Times New Roman for body, serif for title
\setmainfont{Times New Roman}
\setsansfont{Times New Roman}

\title{Technical Report \\ \large TPT Data Explorers 2026}
\author{Data Explorers Team}
\date{\today}

\begin{document}

\begin{titlepage}
    \centering
    \vspace*{2in}
    {\Huge \bfseries Technical Report \par}
    \vspace{0.5in}
    {\Large \bfseries TPT Data Explorers 2026 \par}
    \vspace{1.5in}
    {\large Data Explorers Team \par}
    \vspace{0.5in}
    {\large \today \par}
    \vfill
\end{titlepage}

\newpage
\input{sections/00_abstract.tex}

\newpage
\tableofcontents
\newpage

\input{sections/01_intro.tex}
\input{sections/02_architecture.tex}
\input{sections/03_database_etl.tex}
\input{sections/04_data_quality.tex}
\input{sections/05_features.tex}
\input{sections/06_strategy.tex}
\input{sections/07_results.tex}
\input{sections/08_track2.tex}
\input{sections/09_track3.tex}
\input{sections/10_deliverables.tex}
\input{sections/11_reproducibility.tex}
\input{sections/12_limitations.tex}

\end{document}
"""
    return tex


def write_en_sections():
    secs = os.path.join(REPORT_DIR, "en", "sections")
    os.makedirs(secs, exist_ok=True)

    with open(os.path.join(secs, "00_abstract.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\begin{center}
\textbf{Abstract}
\end{center}
\addcontentsline{toc}{section}{Abstract}

The TPT Data Explorers 2026 project addresses crucial supply chain management and dealer behavior analysis challenges for Thong Nhat Bike. Amidst market volatility and a severe 9-month data gap spanning from April 2025 to December 2025, this technical report presents three core analytical tracks intended to stabilize the business forecasting baseline. First, the Product Demand Forecasting track for Q2 2026 navigates the March 2026 Demand Shock to optimize procurement. Second, an in-depth trend analysis of product colors and variants provides actionable inventory insights. Third, the prediction of dealer ordering behavior leverages RFM B2B segmentation coupled with classification modeling. A hybrid approach utilizing Group-Share Proportional methodologies alongside experimental Machine Learning sets provides a reproducible operational baseline, while strictly acknowledging systemic constraints due to historical data sparsity.

\vspace{0.5in}
\noindent \textbf{Keywords:} Supply Chain, Demand Forecasting, RFM B2B, Machine Learning, Inventory Optimization.
\FloatBarrier
""")

    with open(os.path.join(secs, "01_intro.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Introduction}
Thong Nhat Bike faces an immediate operational need to systematically forecast the ordering behavior of its diverse B2B dealer network. Accurate forecasting not only optimizes working capital tied up in inventory but also directs targeted customer care campaigns efficiently. A successful forecasting system must delicately balance algorithmic sensitivity with clear business interpretability.

The project structurally focuses on three primary tracks. Track 1 forecasts volume allocation by SKU to preempt supply chain disruptions. Track 2 analyzes underlying color trends, acting as a critical attribute affecting stock turnover rates. Track 3 systematically scores and ranks dealer priorities to support customer care resource allocation, leveraging behavioral RFM modeling to personalize engagement strategies.
\FloatBarrier
""")

    with open(os.path.join(secs, "02_architecture.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{System Architecture}
The system is designed with a strict modular approach, ensuring individual components can evolve independently. The Database Layer utilizes PostgreSQL as the central reliable storage mechanism. Ingestion processes handle both historical data seeds and automated pipelines that extract unstructured transactions from emails and PDFs.

Figure \ref{fig:arch} illustrates the holistic Data Flow. Extracted data undergoes a robust ETL layer to patch structural and historical inconsistencies. The Feature Store systematically transforms transactional records into continuous Time-series Panels. All forecasting artifacts are eventually exported as CSV datasets and accessible SQL Views.

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{../figures/en/architecture.pdf}
\caption{System Architecture and Data Flow Diagram}
\label{fig:arch}
\end{figure}

The clear separation of concerns inherent in this layered architecture supports maintainability and codebase reusability for future cyclical updates.
\FloatBarrier
""")

    with open(os.path.join(secs, "03_database_etl.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Database and ETL Pipeline}
Raw data processing is split into historical seeding and real-time ingestion protocols. Table \ref{tab:pipeline} lists the primary scripts orchestrating these operations and their specific roles within the ecosystem.

\input{../tables/pipeline_en.tex}

Manual Data Quality Patches (SQL) addressed known color and geographic inconsistencies. For example, harmonizing misspelled color variants prevented the artificial splintering of a single product's demand signal into multiple disjointed time-series.
\FloatBarrier
""")

    with open(os.path.join(secs, "04_data_quality.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Data Quality Audit}
A Data Quality Audit clarified the overarching data landscape, exposing both structural strengths and historical flaws. Table \ref{tab:key_facts} itemizes critical metrics shaping the system's design constraints.

\input{../tables/key_facts_en.tex}

The massive temporal gap spanning from April 2025 to December 2025 posed a substantial modeling challenge. Rather than imputing false zeros and distorting the signal, the pipeline enforces strict block-aware lag restrictions to isolate 2025 data.

\subsection{UNKNOWN Hierarchy Impact}
The audit additionally identified 55 SKUs lacking proper hierarchy assignment; these were tagged as UNKNOWN to reduce downstream hierarchy distortion. The implications of this missing metadata are significant across multiple business streams, as outlined in Table \ref{tab:unknown}.

\input{../tables/unknown_impact_en.tex}

Until the master data is corrected, these products are segregated into a pseudo-group to ensure they do not contaminate the primary group-share allocation metrics.
\FloatBarrier
""")

    with open(os.path.join(secs, "05_features.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Feature Engineering and Leakage Prevention}
To prevent Data Leakage---an algorithmic flaw where models are implicitly fed future information---the system enacted leakage guardrails. These defenses are summarized in Table \ref{tab:guardrails}.

\input{../tables/guardrails_en.tex}

Zero-sales panelization ensures that SKUs experiencing temporary transaction droughts remain continuously tracked with zero values, preventing popularity-biased distortions. Furthermore, any variables reflecting current-period pricing are strictly prohibited to reduce forward-looking bias during historical training phases.
\FloatBarrier
""")

    with open(os.path.join(secs, "06_strategy.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Forecasting Strategy}
Due to the severely truncated historical timeframe and the 9-month data blackout in 2025, cyclical models such as ARIMA or Prophet are not statistically reliable under the current data constraints. Deploying them would invite significant forecast risk. The primary business forecasting methodology deployed is Group-Share Proportional allocation.

In parallel, Machine Learning tree-based models (LightGBM/CatBoost) are deployed as an Enhanced Baseline experiment to capture non-linear relationships. However, due to the unprecedented March 2026 Demand Shock, utilizing March as a validation set introduces substantial noise, causing the models to potentially overreact. Consequently, Group-Share remains the primary operational forecast, while ML results serve exclusively as volatility reference material.
\FloatBarrier
""")

    # Fix #6: "Random Forest" -> "XGBoost" to match actual table contents
    with open(os.path.join(secs, "07_results.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Modeling Results}
During the Machine Learning evaluation phase, variants including LightGBM, XGBoost, and CatBoost were cross-validated. Table \ref{tab:model_comp} compares these models across the overall segment using WMAPE (Weighted Mean Absolute Percentage Error).

\input{../tables/model_comparison_en.tex}

CatBoost\_monthly\_minimal\_features achieved the lowest validation WMAPE among the evaluated ML variants; however, Group-Share remains the primary operational forecast.

It is important to interpret these metrics with caution. While weekly models utilize a larger volume of data points, their WMAPE is often worse than monthly models because demand is highly volatile at the weekly grain, leading to higher variance in error margins. Furthermore, absolute metrics like MAE and RMSE are not directly comparable between weekly and monthly models due to the differing magnitudes of aggregated volumes.

\subsection{Machine Learning Insights}
Despite the aforementioned volatility, the Machine Learning experiments extracted valuable feature importance signals. Table \ref{tab:feat_imp} highlights the core features driving the ML algorithms.

\input{../tables/feature_importance_en.tex}

\subsection{Business Scenario Planning}
Due to ML volatility caused by the March shock, Group-Share remains the primary operational forecast. Table \ref{tab:scenario} and Figure \ref{fig:scenario} summarize the Group-Share allocation scenarios for Q2 2026.

\input{../tables/scenario_en.tex}

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{../figures/en/scenario_forecast.pdf}
\caption{Q2 2026 Group-Share Forecasted Quantity Scenarios}
\label{fig:scenario}
\end{figure}

The Base scenario anchors standard material procurement planning. The Aggressive scenario serves as a strategic capacity buffer for supply chain resilience. Finally, the Conservative scenario assists executive management in controlling cash flow and inventory risks.
\FloatBarrier
""")

    # Fix #9: tone - "highly potent order signal" -> "useful dealer order signal"
    with open(os.path.join(secs, "08_track2.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Track 2: Color Analysis}
Within the bicycle distribution industry, the base color attribute acts as a useful dealer order signal reflecting localized predictions of end-consumer preferences by dealers. Table \ref{tab:color} and Figure \ref{fig:color} illustrate the Top 10 primary colors dominating the upcoming procurement cycle.

\subsection{Color Contribution and Inventory Implications}
Top colors listed below serve as strong candidates for procurement assurance, heavily driving the bulk of inventory planning. Conversely, low or declining colors require an inventory watch to mitigate stagnant stock. It is crucial to note that this color forecast exclusively reflects a dealer order signal, and should not be perfectly conflated with absolute end-consumer preference.

\input{../tables/color_en.tex}

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{../figures/en/color_summary.pdf}
\caption{Top 10 Base Colors by Forecasted Quantity (Base Scenario)}
\label{fig:color}
\end{figure}

Colors falling outside this Top 10 tier, or those exhibiting severe historical demand slumps, are systematically flagged as slow-moving SKUs. This automated flagging empowers the sales department to execute early inventory liquidations, phasing out unviable variants before they negatively impact warehouse capacity.
\FloatBarrier
""")

    with open(os.path.join(secs, "09_track3.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Track 3: Dealer Ranking}
Based on the established RFM B2B (Recency, Frequency, Monetary) paradigm, the system categorized the entire network of 798 dealers into 8 strategic segments. These segments were combined with a risk classification model to establish a unified Priority Ranking.

\subsection{Dealer Segment Value Analysis}
To understand the financial implications of these segments, Table \ref{tab:dealer} and Figure \ref{fig:dealer} describe the monetary distribution across the network. Revenue by dealer segment is directly calculated using available monetary metrics from the RFM processing phase.

\input{../tables/dealer_en.tex}

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{../figures/en/dealer_segmentation.pdf}
\caption{Dealer Distribution by RFM Segment}
\label{fig:dealer}
\end{figure}

The Champions and Loyal segments act as the primary, stable revenue drivers. The Big Spender demographic requires a dedicated Key Account Care approach, as their purchasing patterns are voluminous but infrequent. Forcing aggressive sales frequency upon this group could prove counterproductive. Conversely, the high volume of Lost and At Risk accounts necessitates immediate reactivation campaigns.

\subsection{Strategic Action Matrix}
To translate these insights into actionable business strategies, Table \ref{tab:dealer_matrix} outlines the recommended approaches and Key Performance Indicators (KPIs) to monitor for each primary segment.

\input{../tables/dealer_matrix_en.tex}
\FloatBarrier
""")

    with open(os.path.join(secs, "10_deliverables.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Dashboard and Deliverables}
All analytical pipelines converge into final output Artifacts designed for immediate business consumption. Table \ref{tab:artifacts} outlines which artifacts are designated for various stakeholder groups.

\input{../tables/artifacts_en.tex}

For BI visualization, the system architecture connects Power BI directly into the data warehouse via optimized views such as \texttt{v-rfm-analysis}. This ensures dashboards reflect real-time analytical updates.
\FloatBarrier
""")

    with open(os.path.join(secs, "11_reproducibility.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Reproducibility}
Pipeline reproducibility ensures that historical validations can be re-run consistently. The Python environment is locked via the project's \texttt{requirements.txt}. All Machine Learning variants employ strict \texttt{random\_state} seed settings to eliminate stochastic divergence during re-training. Additionally, strict \texttt{.gitignore} policies ensure local metadata artifacts are not committed to the shared repository.

Below are the standard operational execution commands, presented in strict ASCII syntax:

\begin{itemize}
    \item To execute a syntax check and pipeline simulation without saving outputs:
\begin{lstlisting}
python src/models/forecasting/run_end_to_end.py --dry-run
\end{lstlisting}

    \item To execute the full pipeline end-to-end, permitting ML model overwrites:
\begin{lstlisting}
python src/models/forecasting/run_end_to_end.py \
    --allow-modeling --allow-overwrite
\end{lstlisting}
\end{itemize}
\FloatBarrier
""")

    with open(os.path.join(secs, "12_limitations.tex"), "w", encoding="utf-8") as f:
        f.write(r"""\section{Limitations and Future Work}
While providing a stable operational baseline, the system carries fundamental technical limitations that dictate clear avenues for future enhancement:
\begin{itemize}
    \item \textbf{Short History}: The absence of 9 core months of data in 2025 severely restricts cyclical analysis, requiring additional real historical data or carefully documented scenario assumptions in future iterations.
    \item \textbf{March Shock}: The sudden demand surge may incite overfitting phenomena in short-term forecasting if tree weights are not heavily regularized.
    \item \textbf{Cold-start Problem}: Newly onboarded dealers lack sufficient transactional history, inhibiting the generation of meaningful RFM behavioral scores.
    \item \textbf{Probability Calibration}: The Track 3 Classifier currently emits uncalibrated probabilities. Integrating Isotonic Regression or Platt Scaling is necessary to improve churn risk reliability.
\end{itemize}
\FloatBarrier
""")


if __name__ == "__main__":
    write_en_sections()

    with open(os.path.join(REPORT_DIR, "en", "main_en.tex"), "w", encoding="utf-8") as f:
        f.write(create_main_en())

    print("TeX structural files and sections written successfully.")
