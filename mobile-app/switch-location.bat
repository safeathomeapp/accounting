@echo off
REM ============================================================================
REM Switch Location Script for Windows
REM
REM This script makes it easy to switch between Location 1 and Location 2
REM
REM Usage:
REM   switch-location.bat location1
REM   switch-location.bat location2
REM
REM Examples:
REM   switch-location.bat location1  -> Uses 192.168.1.143
REM   switch-location.bat location2  -> Uses 192.168.0.37
REM ============================================================================

setlocal enabledelayedexpansion

REM Check if argument provided
if "%1"=="" (
    echo.
    echo ============================================================================
    echo  Environment Location Switcher
    echo ============================================================================
    echo.
    echo Usage: switch-location.bat [location1 or location2]
    echo.
    echo Examples:
    echo   switch-location.bat location1  - Switch to Location 1 (192.168.1.143)
    echo   switch-location.bat location2  - Switch to Location 2 (192.168.0.37)
    echo.
    echo Current .env.local:
    if exist ".env.local" (
        type .env.local | findstr /r "^API_BASE_URL"
    ) else (
        echo   [Not set yet]
    )
    echo.
    goto :end
)

REM Get the location argument
set LOCATION=%1

REM Validate argument
if /i "%LOCATION%"=="location1" (
    echo Switching to Location 1 (192.168.1.143)...
    copy /y ".env.location1" ".env.local" >nul
    echo.
    echo SUCCESS: Switched to Location 1
    echo API_BASE_URL=http://192.168.1.143:8000/api/mobile
    echo.
    echo Next steps:
    echo   1. Stop npm start (Ctrl+C)
    echo   2. Run: npm start
    echo.
    goto :end
)

if /i "%LOCATION%"=="location2" (
    echo Switching to Location 2 (192.168.0.37)...
    copy /y ".env.location2" ".env.local" >nul
    echo.
    echo SUCCESS: Switched to Location 2
    echo API_BASE_URL=http://192.168.0.37:8000/api/mobile
    echo.
    echo Next steps:
    echo   1. Stop npm start (Ctrl+C)
    echo   2. Run: npm start
    echo.
    goto :end
)

REM Invalid argument
echo.
echo ERROR: Invalid location "%LOCATION%"
echo.
echo Valid options:
echo   location1 - Use 192.168.1.143
echo   location2 - Use 192.168.0.37
echo.
echo Example: switch-location.bat location1
echo.

:end
endlocal
