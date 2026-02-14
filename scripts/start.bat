@echo off
REM FastAPI Docker startup script for Windows
REM Usage: scripts\start.bat [--fast] [--build] [--down]

setlocal

REM Default flags
set "FAST=0"
set "BUILD=0"
set "DOWN=0"

REM Parse arguments
:parse_args
if "%1"=="" goto args_done
if "%1"=="--fast" set FAST=1
if "%1"=="--build" set BUILD=1
if "%1"=="--down" set DOWN=1
shift
goto parse_args

:args_done
REM Check if docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed
    exit /b 1
)

REM Check if Docker Compose v2 is installed
docker compose version >nul 2>&1
if errorlevel 1 (
    echo Docker Compose is not installed
    exit /b 1
)

echo.
echo ================================================
echo FastAPI Docker Compose Manager
echo ================================================
echo.

REM Get project root directory
set "SCRIPT_DIR=%~dp0"
for %%A in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fA"

cd /d "%PROJECT_ROOT%"

REM Handle --down flag
if "%DOWN%"=="1" (
    echo Stopping all services...
    docker compose down -v
    echo Services stopped
    exit /b 0
)

REM Create logs directory
if not exist "logs" mkdir logs
echo Logs directory created

REM Start services
if "%FAST%"=="1" goto start_fast
if "%BUILD%"=="1" goto start_build
goto start_default

:start_fast
echo.
echo Starting services (fast mode - no rebuild)...
docker compose up -d
goto start_done

:start_build
echo.
echo Building images and starting services...
docker compose up -d --build
goto start_done

:start_default
echo.
echo Starting services...
docker compose up -d

:start_done

if errorlevel 1 (
    echo Failed to start services
    exit /b 1
)

echo Waiting for services to be ready...
timeout /t 5 /nobreak

echo Running database migrations...
docker compose exec -T app alembic -c alembic.ini upgrade head

echo.
echo ================================================
echo Service Status
echo ================================================
echo.

REM Check services
docker compose ps | find "postgres" >nul
if %errorlevel%==0 (
    echo PostgreSQL - localhost:5432
) else (
    echo PostgreSQL - not running
)

docker compose ps | find "app" >nul
if %errorlevel%==0 (
    echo FastAPI App - http://localhost:8000
) else (
    echo FastAPI App - not running
)

docker compose ps | find "pgadmin" >nul
if %errorlevel%==0 (
    echo pgAdmin - http://localhost:5050
) else (
    echo pgAdmin - not running
)

docker compose ps | find "grafana" >nul
if %errorlevel%==0 (
    echo Grafana - http://localhost:3000
) else (
    echo Grafana - not running
)

docker compose ps | find "loki" >nul
if %errorlevel%==0 (
    echo Loki - http://localhost:3100
) else (
    echo Loki - not running
)

docker compose ps | find "prometheus" >nul
if %errorlevel%==0 (
    echo Prometheus - http://localhost:9090
) else (
    echo Prometheus - not running
)

echo.
echo ================================================
echo Access Points
echo ================================================
echo.
echo FastAPI:      http://localhost:8000
echo pgAdmin:      http://localhost:5050/browser/
echo Grafana:      http://localhost:3000 (admin/admin123)
echo Prometheus:   http://localhost:9090
echo Loki:         http://localhost:3100
echo PostgreSQL:   localhost:5432
echo.
echo View logs:    docker compose logs -f [service]
echo Stop all:     scripts\start.bat --down
echo ================================================
echo.
