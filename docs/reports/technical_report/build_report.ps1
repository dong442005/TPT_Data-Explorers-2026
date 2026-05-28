$ReportDir = $PSScriptRoot
Set-Location $ReportDir

Write-Host "Generating tables and figures..."
python scripts/build_figures_tables.py

Write-Host "Generating TeX sections..."
python scripts/build_tex_sections.py


Write-Host "Compiling EN..."
Set-Location "en"
xelatex -interaction=nonstopmode main_en.tex
xelatex -interaction=nonstopmode main_en.tex
Copy-Item main_en.pdf ../technical_report_en.pdf -Force
Set-Location ..

Write-Host "Done!"
