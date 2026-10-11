$ErrorActionPreference = 'Stop'

$hostName = if ($env:HOST) { $env:HOST } else { '0.0.0.0' }
$port = if ($env:PORT) { $env:PORT } else { '5000' }

Write-Host "Starting School Management app on $hostName:$port"
& ".\.venv\Scripts\python.exe" wsgi.py
