@echo off
chcp 65001 > nul
powershell -ExecutionPolicy Bypass -File "%~dp0generate-and-sync.ps1" %*
pause
