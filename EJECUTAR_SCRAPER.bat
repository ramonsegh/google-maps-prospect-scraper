@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Ejecutar - Google Maps Prospect Scraper
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo El proyecto todavia no esta instalado.
    echo Ejecuta primero INSTALAR_WINDOWS.bat.
    pause
    exit /b 1
)

echo ============================================================
echo              GOOGLE MAPS PROSPECT SCRAPER
echo ============================================================
echo.
set /p "GIRO=Escribe el giro o tipo de negocio: "
set /p "UBICACION=Escribe la ciudad o ubicacion: "
set /p "MAXIMO=Numero maximo de resultados [20]: "

if not defined GIRO (
    echo Debes escribir un giro.
    pause
    exit /b 1
)
if not defined UBICACION (
    echo Debes escribir una ubicacion.
    pause
    exit /b 1
)
if not defined MAXIMO set "MAXIMO=20"

echo.
echo Iniciando busqueda...
".venv\Scripts\python.exe" "scraper_google_maps.py" --giro "%GIRO%" --ubicacion "%UBICACION%" --max "%MAXIMO%"

if errorlevel 1 (
    echo.
    echo El scraper termino con un error. Revisa el mensaje anterior.
) else (
    echo.
    echo Proceso terminado. Consulta la carpeta results.
)
pause

