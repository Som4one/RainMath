@echo off
rem Double-clique ce fichier pour tout installer (Python, pip, bibliotheques).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
