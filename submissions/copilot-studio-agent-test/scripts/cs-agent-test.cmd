@echo off
REM Launcher for cs-agent-test on Windows.
REM Keeps callers from having to type "node scripts\cs-agent-test.cjs" every time.

setlocal
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo Node.js was not found on PATH.
  echo.
  echo This tool needs Node.js 22 or later. Install it from https://nodejs.org
  echo then open a new terminal and try again.
  echo.
  exit /b 1
)

node "%~dp0cs-agent-test.cjs" %*
exit /b %errorlevel%
