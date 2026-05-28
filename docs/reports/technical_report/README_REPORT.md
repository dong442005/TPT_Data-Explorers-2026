# Technical Report Generation

This directory contains the scripts and assets to generate the APA-inspired final technical reports in English and Vietnamese.

## Prerequisites
- A working LaTeX distribution with `xelatex` (e.g., MiKTeX or TeX Live).
- Required LaTeX packages: `geometry`, `fontspec`, `hyperref`, `graphicx`, `booktabs`, `longtable`, `array`, `xcolor`, `setspace`, `caption`, `titlesec`, `float`, `placeins`.
- Python 3 with `pandas` and `matplotlib` for generating the tables and figures.
- Arial font installed on the system (for Vietnamese Unicode support).

## Structure
- `scripts/build_figures_tables.py`: Extracts modeling output data and generates `.tex` tables and `.pdf` figures in `tables/` and `figures/`.
- `scripts/build_tex_sections.py`: Generates the modular `.tex` report sections in `en/sections/` and `vi/sections/`.
- `build_report.ps1`: The main orchestration script that runs the Python scripts and compiles the final PDFs (`technical_report_en.pdf` and `technical_report_vi.pdf`).

## Usage
Run the PowerShell script from the repository root or the report directory:

```powershell
cd docs/reports/technical_report
./build_report.ps1
```

## Note on Dependencies
The report utilizes `matplotlib` purely to avoid `seaborn` dependency issues, maintaining maximum compatibility. Tables are formatted using the `booktabs` package for professional APA-style rendering.