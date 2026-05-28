import os
import pandas as pd
import matplotlib.pyplot as plt

REPO_ROOT = r"C:\Users\HOANG TUNG\TPT_Data-Explorers-2026"
REPORT_DIR = os.path.join(REPO_ROOT, "docs/reports/technical_report")
TABLES_DIR = os.path.join(REPORT_DIR, "tables")
FIGURES_EN_DIR = os.path.join(REPORT_DIR, "figures", "en")
OUTPUTS_MOD = os.path.join(REPO_ROOT, "outputs/modeling")

os.makedirs(TABLES_DIR, exist_ok=True)
os.makedirs(FIGURES_EN_DIR, exist_ok=True)
os.makedirs(os.path.join(REPORT_DIR, "en", "sections"), exist_ok=True)

# Set matplotlib fonts to Arial (safe for ASCII)
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False


def to_apa_table(df, caption, label, note=None):
    tex = "\\begin{table}[H]\n\\centering\n"
    tex += "\\small\n"
    tex += "\\caption{" + caption + "}\n\\label{" + label + "}\n"
    tex += "\\resizebox{\\linewidth}{!}{\n"

    col_format = "l" * len(df.columns)
    tex += "\\begin{tabular}{" + col_format + "}\n\\toprule\n"
    escaped_columns = [
        str(c).replace('_', r'\_').replace('&', r'\&').replace('%', r'\%').replace('$', r'\$')
        for c in df.columns
    ]
    tex += " & ".join([f"\\textbf{{{c}}}" for c in escaped_columns]) + " \\\\\n\\midrule\n"
    for _, row in df.iterrows():
        escaped_values = [
            str(val).replace('_', r'\_').replace('&', r'\&').replace('%', r'\%').replace('$', r'\$')
            for val in row.values
        ]
        tex += " & ".join(escaped_values) + " \\\\\n"
    tex += "\\bottomrule\n\\end{tabular}\n}\n"
    if note:
        escaped_note = note.replace('Note.', '').strip()
        escaped_note = escaped_note.replace('_', r'\_').replace('&', r'\&').replace('%', r'\%').replace('$', r'\$')
        tex += "\\begin{flushleft}\n\\footnotesize \\textit{Note.} " + escaped_note + "\n\\end{flushleft}\n"
    tex += "\\end{table}\n"
    return tex


def build_tables_and_figures():
    # =========================================================================
    # 1. Key Data Facts (English only)
    # =========================================================================
    df_facts_en = pd.DataFrame([
        ['Order lines', '25,754', 'Transactional', 'Revenue calculation base'],
        ['Sales Orders', '2,759', 'Transactional', 'Frequency evaluation'],
        ['Dealers', '798', 'Master Data', 'Primary RFM B2B input'],
        ['SKUs (Products)', '265', 'Master Data', 'Target universe'],
        ['Total Quantity', '72,146', 'Transactional', 'Historical volume'],
        ['Mar 2026 Orders', '1,132', 'Demand Shock', 'Creates March Shock'],
        ['Data Gap', '04/25 - 12/25', 'Limitation', 'Needs block-aware lag'],
        ['Unknown Hierarchy', '55', 'Metadata Error', 'Tagged UNKNOWN']
    ], columns=['Metric', 'Value', 'Characteristic', 'Implication'])

    with open(os.path.join(TABLES_DIR, "key_facts_en.tex"), "w", encoding="utf-8") as f:
        f.write(to_apa_table(df_facts_en, "Key Data Facts and Implications", "tab:key_facts"))

    # =========================================================================
    # 2. Pipeline Components (English only)
    # =========================================================================
    df_pipe_en = pd.DataFrame([
        ['Database Init', 'create-tables.sql', 'Initializes PostgreSQL schema'],
        ['Historical Seed', 'import-data.sql', 'Ingests historical data'],
        ['ETL Parser', 'extract-validate.py', 'Automated PDF/Email parsing'],
        ['Data Patches', 'sql-patches.sql', 'Fixes geo and color errors'],
        ['Feature Store', 'build-features.py', 'Constructs Time-series'],
        ['Track 1 Model', 'core-baselines.py', 'Group-Share Forecast'],
        ['Track 2 Model', 'color-trends.py', 'Color trend allocation'],
        ['Track 3 Model', 'rfm-track3.py', 'RFM B2B ranking'],
        ['BI Dashboard', 'v-rfm-analysis.sql', 'Direct views for Power BI']
    ], columns=['Component', 'Script Alias', 'Role'])

    with open(os.path.join(TABLES_DIR, "pipeline_en.tex"), "w", encoding="utf-8") as f:
        f.write(to_apa_table(df_pipe_en, "Pipeline Components and ETL Scripts", "tab:pipeline"))

    # =========================================================================
    # 3. Feature Guardrails (English only)
    # =========================================================================
    df_guard_en = pd.DataFrame([
        ['Zero-sales Panel', 'is-zero-sales', 'Mandatory', 'Ensures continuous time-series'],
        ['Gap-crossing Lags', 'qty-lag-1', 'Restricted', 'Prevents signal leakage'],
        ['Current Price', 'current-price', 'Banned', 'Causes forward-looking bias'],
        ['Schema Alignment', 'is-aligned', 'Mandatory', 'Schema must match exactly']
    ], columns=['Feature Family', 'Alias', 'Rule', 'Reason'])

    with open(os.path.join(TABLES_DIR, "guardrails_en.tex"), "w", encoding="utf-8") as f:
        f.write(to_apa_table(df_guard_en, "Feature Engineering Guardrails", "tab:guardrails"))

    # =========================================================================
    # 4. UNKNOWN Impact (English only)
    # =========================================================================
    df_unknown_en = pd.DataFrame([
        ['Group-Share Allocation', 'These 55 SKUs cannot be assigned to any product group, reducing group-share precision'],
        ['Color Trend Analysis', 'Missing hierarchy prevents proper color-category cross-tabulation'],
        ['Feature Engineering', 'line_id_clean and group_code_encoded default to UNKNOWN, weakening ML signal']
    ], columns=['Impact Area', 'Description'])

    with open(os.path.join(TABLES_DIR, "unknown_impact_en.tex"), "w", encoding="utf-8") as f:
        f.write(to_apa_table(df_unknown_en, "Impact of UNKNOWN Hierarchy on Downstream Analytics", "tab:unknown"))

    # =========================================================================
    # 5. Model Comparison (Table 5) — Bold best model
    # =========================================================================
    comp_file = os.path.join(OUTPUTS_MOD, "phase3c_ml_model_comparison.csv")
    if os.path.exists(comp_file):
        df_comp = pd.read_csv(comp_file)
        df_overall = df_comp[df_comp['Segment'] == 'Overall'] if 'Segment' in df_comp.columns else df_comp.head(8)
        df_out = df_overall[['Model', 'MAE', 'RMSE', 'WMAPE', 'Bias_Ratio']].copy()

        rows_en = []
        for _, row in df_out.iterrows():
            model_name = str(row['Model'])
            mae_str = f"{row['MAE']:,.2f}"
            rmse_str = f"{row['RMSE']:,.2f}"
            wmape_str = f"{row['WMAPE']:,.4f}"
            bias_str = f"{row['Bias_Ratio']:,.4f}"

            # Bold the best model row
            if model_name == 'CatBoost_monthly_minimal_features':
                model_name = "\\textbf{" + model_name + "}"
                wmape_str = "\\textbf{" + wmape_str + "}"

            rows_en.append([model_name, mae_str, rmse_str, wmape_str, bias_str])

        df_out_en = pd.DataFrame(rows_en, columns=['Model Variant', 'MAE', 'RMSE', 'WMAPE', 'Bias Ratio'])
        note_en = "WMAPE is the primary normalized metric for comparison."
        with open(os.path.join(TABLES_DIR, "model_comparison_en.tex"), "w", encoding="utf-8") as f:
            f.write(to_apa_table(df_out_en, "Model Comparison Metrics (Overall)", "tab:model_comp", note_en))

    # =========================================================================
    # 6. Feature Importance (Table 6) — Fix #7 interpretations
    # =========================================================================
    fi_file = os.path.join(OUTPUTS_MOD, "phase3c_ml_feature_importance.csv")
    if os.path.exists(fi_file):
        df_fi = pd.read_csv(fi_file)
        if 'Importance' in df_fi.columns:
            top_fi = df_fi.groupby('Feature')['Importance'].mean().reset_index()
            top_fi = top_fi.sort_values('Importance', ascending=False).head(5)

            interp_map = {
                'qty_roll_mean_4w': 'Rolling weekly demand momentum',
                'qty_lag_2w': 'Two-week lagged demand signal',
                'qty_lag_1': 'Immediate short-term demand momentum',
                'qty_lag_4w': 'Four-week lagged demand signal',
                'line_id_clean': 'Product hierarchy / category proxy',
                'qty_lag_3': 'Quarterly momentum',
                'qty_lag_12': 'Annual seasonal baseline',
                'month': 'General seasonality index',
                'base_color_encoded': 'Base color preference signal',
                'group_code_encoded': 'Product group category signal',
                'is_weekend': 'Weekend transaction behavior',
            }
            fi_show = []
            for _, r in top_fi.iterrows():
                feat = r['Feature']
                fi_show.append([feat, f"{r['Importance']:.4f}", interp_map.get(feat, 'Auxiliary signal')])
            df_fi_out = pd.DataFrame(fi_show, columns=['Feature', 'Avg Importance', 'Interpretation'])
            note_fi = "Feature importance averaged across LightGBM/XGBoost variants. Feature importance is directional and should not be interpreted causally."
            with open(os.path.join(TABLES_DIR, "feature_importance_en.tex"), "w", encoding="utf-8") as f:
                f.write(to_apa_table(df_fi_out, "Top ML Features by Importance", "tab:feat_imp", note_fi))

    # =========================================================================
    # 7. Scenario Delta (Table 7) — Fix #8: add Delta Revenue vs Base
    # =========================================================================
    scen_file = os.path.join(OUTPUTS_MOD, "phase3_scenario_summary_q2_2026.csv")
    if os.path.exists(scen_file):
        df_scen = pd.read_csv(scen_file)

        base_qty = df_scen.loc[df_scen['Scenario'] == 'Base', 'Total_Q2_Qty'].values[0] if 'Base' in df_scen['Scenario'].values else 0
        base_rev = df_scen.loc[df_scen['Scenario'] == 'Base', 'Total_Q2_Revenue'].values[0] if 'Base' in df_scen['Scenario'].values else 0

        df_en = []
        for _, r in df_scen.iterrows():
            delta_qty = r['Total_Q2_Qty'] - base_qty
            delta_rev = r['Total_Q2_Revenue'] - base_rev
            delta_qty_str = f"+{delta_qty:,.0f}" if delta_qty > 0 else (f"{delta_qty:,.0f}" if delta_qty < 0 else "0")
            delta_rev_str = f"+{delta_rev:,.0f} VND" if delta_rev > 0 else (f"{delta_rev:,.0f} VND" if delta_rev < 0 else "0 VND")
            plan_use = "Financial risk control" if "Conserv" in r['Scenario'] else ("Primary baseline" if "Base" in r['Scenario'] else "Capacity buffer")
            df_en.append([
                r['Scenario'],
                f"{r['Total_Q2_Qty']:,.0f}",
                f"{r['Total_Q2_Revenue']:,.0f} VND",
                delta_qty_str,
                delta_rev_str,
                plan_use
            ])

        df_en_out = pd.DataFrame(df_en, columns=[
            'Scenario', 'Q2 Quantity', 'Q2 Revenue (VND)',
            'Delta Qty vs Base', 'Delta Revenue vs Base (VND)', 'Planning Use'
        ])
        note_en = "Conservative controls financial downside risk. Aggressive prepares for sales upside."
        with open(os.path.join(TABLES_DIR, "scenario_en.tex"), "w", encoding="utf-8") as f:
            f.write(to_apa_table(df_en_out, "Scenario Delta and Planning Implication", "tab:scenario", note_en))

        # Scenario Figure (EN only)
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(df_scen['Scenario'], df_scen['Total_Q2_Qty'], color=['#C44E52', '#4C72B0', '#55A868'], width=0.4)
        ax.set_title('Q2 2026 Group-Share Forecast Scenarios', fontsize=12, fontweight='bold', pad=15)
        ax.set_ylabel('Total Quantity')
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2.0, yval + max(df_scen['Total_Q2_Qty']) * 0.02,
                    f'{int(yval):,}', ha='center', va='bottom', fontsize=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_EN_DIR, "scenario_forecast.pdf"))
        plt.close()

    # =========================================================================
    # 8. Color Contribution (Table 8) — Fix #1: revenue from source data
    # =========================================================================
    cfile = os.path.join(OUTPUTS_MOD, "phase3_color_summary_q2_2026.csv")
    if os.path.exists(cfile):
        df_color = pd.read_csv(cfile)
        if 'base_color' in df_color.columns and 'Group_Share_Base_Qty' in df_color.columns:
            agg_cols = ['Group_Share_Base_Qty']
            has_rev = 'Group_Share_Base_Rev' in df_color.columns
            if has_rev:
                agg_cols.append('Group_Share_Base_Rev')

            top_colors = df_color.groupby('base_color')[agg_cols].sum()
            top_colors = top_colors.sort_values(by='Group_Share_Base_Qty', ascending=False).head(10).reset_index()
            total_qty = top_colors['Group_Share_Base_Qty'].sum()
            total_rev = top_colors['Group_Share_Base_Rev'].sum() if has_rev else 0

            # English translation map
            color_map_en = {
                'Kem': 'Cream', '\u0110en': 'Black', 'Ghi': 'Gray', 'H\u1ed3ng': 'Pink',
                'Xanh': 'Green', 'Xanh D\u01b0\u01a1ng': 'Blue', 'Tr\u1eafng': 'White',
                'N\u00e2u': 'Brown', 'Xanh Ng\u1ecdc/Mint': 'Mint', '\u0110\u1ecf': 'Red'
            }
            top_colors['en_color'] = top_colors['base_color'].apply(lambda x: color_map_en.get(x, x))

            # Build table rows
            en_table_data = []
            for _, r in top_colors.iterrows():
                share_pct = (r['Group_Share_Base_Qty'] / total_qty) * 100 if total_qty > 0 else 0
                row_data = [
                    r['en_color'],
                    f"{r['Group_Share_Base_Qty']:,.0f}",
                    f"{share_pct:.1f}%",
                ]
                if has_rev:
                    r_share = (r['Group_Share_Base_Rev'] / total_rev) * 100 if total_rev > 0 else 0
                    row_data.append(f"{r['Group_Share_Base_Rev']:,.0f}")
                    row_data.append(f"{r_share:.1f}%")
                en_table_data.append(row_data)

            if has_rev:
                cols = ['Color', 'Forecast Qty', 'Qty Share', 'Forecast Rev (VND)', 'Rev Share']
            else:
                cols = ['Color', 'Forecast Qty', 'Qty Share']

            df_en_out = pd.DataFrame(en_table_data, columns=cols)
            note_en = "Color revenue is derived from Group-Share proportional allocation applied to each base color. Procurement strategies should prioritize top colors to avoid stockouts while maintaining lean inventory for long-tail variants."
            with open(os.path.join(TABLES_DIR, "color_en.tex"), "w", encoding="utf-8") as f:
                f.write(to_apa_table(df_en_out, "Top Color Contribution Summary", "tab:color", note_en))

            # English Color Figure
            top_colors_plot = top_colors.sort_values(by='Group_Share_Base_Qty', ascending=True)
            fig, ax = plt.subplots(figsize=(7, 4.5))
            bars = ax.barh(top_colors_plot['en_color'], top_colors_plot['Group_Share_Base_Qty'],
                           color='#55A868', height=0.6)
            ax.set_title('Top 10 Base Colors by Forecasted Quantity', fontsize=12, fontweight='bold', pad=15)
            ax.set_xlabel('Forecasted Quantity')
            for bar in bars:
                wval = bar.get_width()
                ax.text(wval + max(top_colors_plot['Group_Share_Base_Qty']) * 0.01,
                        bar.get_y() + bar.get_height() / 2.0,
                        f'{int(wval):,}', ha='left', va='center', fontsize=10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURES_EN_DIR, "color_summary.pdf"))
            plt.close()

    # =========================================================================
    # 9. Dealer Segment (Table 9) — Fix #2: no empty columns, add reconciliation note
    # =========================================================================
    dfile = os.path.join(OUTPUTS_MOD, "phase3_dealer_priority_ranking_q2_2026.csv")
    if os.path.exists(dfile):
        df_dealer = pd.read_csv(dfile)
        if 'rfm_segment' in df_dealer.columns:
            # Build aggregation
            has_monetary = 'monetary' in df_dealer.columns
            has_priority = 'marketing_priority_score' in df_dealer.columns

            agg_dict = {'customer_code': 'nunique'}
            if has_monetary:
                agg_dict['monetary'] = 'sum'
            if has_priority:
                agg_dict['marketing_priority_score'] = 'mean'

            seg_agg = df_dealer.groupby('rfm_segment').agg(agg_dict).reset_index()
            total_monetary = seg_agg['monetary'].sum() if has_monetary else 0

            en_dealer_data = []
            for _, r in seg_agg.iterrows():
                seg = r['rfm_segment']
                count = r['customer_code']
                row = [seg, f"{count}"]

                if has_monetary:
                    rev = r['monetary']
                    rev_share = (rev / total_monetary) * 100 if total_monetary > 0 else 0
                    avg_rev = rev / count if count > 0 else 0
                    row.append(f"{rev:,.0f}")
                    row.append(f"{rev_share:.1f}%")
                    row.append(f"{avg_rev:,.0f}")

                if has_priority:
                    score = r['marketing_priority_score']
                    row.append(f"{score:.2f}")

                en_dealer_data.append(row)

            # Build column list dynamically — no empty columns
            col_list = ['Segment', 'Dealer Count']
            if has_monetary:
                col_list += ['Historical Revenue (VND)', 'Revenue Share', 'Avg Revenue per Dealer (VND)']
            if has_priority:
                col_list += ['Avg Priority']

            df_en_dealer = pd.DataFrame(en_dealer_data, columns=col_list)

            # Sort by revenue share descending
            if 'Revenue Share' in df_en_dealer.columns:
                df_en_dealer['_sort'] = df_en_dealer['Revenue Share'].str.replace('%', '').astype(float)
                df_en_dealer = df_en_dealer.sort_values('_sort', ascending=False).drop(columns=['_sort'])

            # Build note with reconciliation
            reconcile_note = f"Source: outputs/modeling/phase3_dealer_priority_ranking_q2_2026.csv. "
            reconcile_note += f"Segment monetary totals reconcile to the historical revenue total of {total_monetary:,.0f} VND."
            with open(os.path.join(TABLES_DIR, "dealer_en.tex"), "w", encoding="utf-8") as f:
                f.write(to_apa_table(df_en_dealer, "Dealer Segment Value Summary", "tab:dealer", reconcile_note))

            # Dealer segmentation figure
            seg_counts = df_dealer['rfm_segment'].value_counts().reset_index()
            seg_counts.columns = ['RFM Segment', 'Dealer Count']
            seg_counts_plot = seg_counts.sort_values(by='Dealer Count', ascending=True)

            fig, ax = plt.subplots(figsize=(7, 4.5))
            bars = ax.barh(seg_counts_plot['RFM Segment'], seg_counts_plot['Dealer Count'],
                           color='#C44E52', height=0.6)
            ax.set_title('Dealer Distribution by RFM Segment', fontsize=12, fontweight='bold', pad=15)
            ax.set_xlabel('Dealer Count')
            for bar in bars:
                wval = bar.get_width()
                ax.text(wval + max(seg_counts_plot['Dealer Count']) * 0.01,
                        bar.get_y() + bar.get_height() / 2.0,
                        f'{int(wval)}', ha='left', va='center', fontsize=10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURES_EN_DIR, "dealer_segmentation.pdf"))
            plt.close()

    # =========================================================================
    # 10. Dealer Action Matrix (Table 10) — 8 segments, all columns filled
    # =========================================================================
    matrix_data = [
        ['Champions', 'High value, frequent', 'Low', 'Retain and protect', 'Retention rate / Repeat revenue'],
        ['Loyal', 'Steady buyers', 'Low', 'Maintain engagement', 'Order frequency'],
        ['Big Spender', 'High value, rare', 'Medium', 'Dedicated account care', 'Total revenue / Account retention'],
        ['Potential', 'Promising buyers', 'Medium', 'Nurture and convert', 'Conversion to Loyal/Champion'],
        ['At Risk', 'Dropping frequency', 'High', 'Reactivation campaign', 'Reactivation rate'],
        ['Lost', 'Inactive long term', 'Very High', 'Low-cost reactivation or deprioritize', 'Response rate'],
        ['Hibernating', 'Inactive', 'High', 'Periodic nurture', 'Reactivation signal'],
        ['New', 'Just onboarded', 'Unknown', 'Onboarding', 'Second order rate']
    ]
    df_matrix = pd.DataFrame(matrix_data, columns=['Segment', 'Business Meaning', 'Risk', 'Recommended Action', 'KPI to Monitor'])
    with open(os.path.join(TABLES_DIR, "dealer_matrix_en.tex"), "w", encoding="utf-8") as f:
        f.write(to_apa_table(df_matrix, "Dealer Action Matrix", "tab:dealer_matrix",
                             "Strategic actions and KPIs tailored to each RFM B2B segment."))

    # =========================================================================
    # 11. Stakeholder Artifacts (English only)
    # =========================================================================
    artifacts_en = pd.DataFrame([
        ['Executive Team', 'Strategic overview', 'Executive Summary, Scenario Delta Table'],
        ['Supply Chain / Procurement', 'Volume planning', 'Group-Share Forecast, Color Forecast'],
        ['Sales / Trade Marketing', 'Dealer prioritization', 'Dealer Priority Ranking, Action Matrix'],
        ['Data Science', 'Model stability', 'Feature Importance, ML Model Comparison']
    ], columns=['Stakeholder', 'Primary Need', 'Recommended Artifacts'])

    with open(os.path.join(TABLES_DIR, "artifacts_en.tex"), "w", encoding="utf-8") as f:
        f.write(to_apa_table(artifacts_en, "Which Artifact Should Each Stakeholder Use?", "tab:artifacts",
                             "Maps final outputs to specific operational workflows."))


if __name__ == "__main__":
    build_tables_and_figures()
