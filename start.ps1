# מרים את הבאק ואת הפרונט בשני חלונות נפרדים
$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "& '$root\venv\Scripts\Activate.ps1'; Set-Location '$root\BACK'; uvicorn api:app --reload --port 8000"
)

Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "Set-Location '$root\frontend'; npm run dev"
)

Write-Host "Backend: http://localhost:8000  |  Frontend: http://localhost:3000"