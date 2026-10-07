$ErrorActionPreference = "Stop"

py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-test.txt

if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

python manage.py migrate
python manage.py seed_data

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run: python manage.py runserver"
Write-Host "Swagger: http://127.0.0.1:8000/api/docs/"
