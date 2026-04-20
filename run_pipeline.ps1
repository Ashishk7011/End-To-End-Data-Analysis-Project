Write-Host "Starting Pipeline..."

python .\EDA.py
if ($LASTEXITCODE -ne 0) { exit }

python .\vendor_analysis.py
if ($LASTEXITCODE -ne 0) { exit }

Write-Host "Pipeline Completed Successfully!"