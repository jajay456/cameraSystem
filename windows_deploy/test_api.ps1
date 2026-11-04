param(
  [string]$BaseUrl = "https://api.krosshighlight.com",
  [switch]$Trigger
)
$ErrorActionPreference = "Stop"
$envFile = Join-Path $PSScriptRoot "..\.env"
$key = ((Get-Content $envFile | Select-String '^TEST_API_KEY=(.+)$').Matches[0].Groups[1].Value).Trim()
$headers = @{ "x-api-key" = $key }

Write-Host "`n== GET $BaseUrl/api/status" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/api/status" -Headers $headers | Format-List

if ($Trigger) {
  Write-Host "== POST $BaseUrl/api/trigger" -ForegroundColor Cyan
  Invoke-RestMethod "$BaseUrl/api/trigger" -Method Post -Headers $headers -ContentType "application/json" -Body '{"court":"court_1"}' | Format-List
  Write-Host "Waiting 30s for the clip to upload..."
  Start-Sleep 30
}

Write-Host "== GET $BaseUrl/api/highlights" -ForegroundColor Cyan
(Invoke-RestMethod "$BaseUrl/api/highlights?limit=5" -Headers $headers).highlights | Format-Table claimCode, court, date, time, videoUrl -AutoSize
