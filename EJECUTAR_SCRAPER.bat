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
set /p "MAXIMO=Numero maximo de resultados [100]: "
echo La calificacion minima debe estar entre 0 y 5 y puede tener decimales.
set /p "CALIFICACION_MINIMA=Calificacion minima [0]: "
set /p "MIN_CALIFICACIONES=Minimo de calificaciones o resenas [0]: "

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
if not defined MAXIMO set "MAXIMO=100"
if not defined CALIFICACION_MINIMA set "CALIFICACION_MINIMA=0"
if not defined MIN_CALIFICACIONES set "MIN_CALIFICACIONES=0"

echo.
echo Iniciando busqueda...
".venv\Scripts\python.exe" "scraper_google_maps.py" --giro "%GIRO%" --ubicacion "%UBICACION%" --max "%MAXIMO%" --calificacion-minima "%CALIFICACION_MINIMA%" --min-calificaciones "%MIN_CALIFICACIONES%"

if errorlevel 1 (
    echo.
    echo El scraper termino con un error. Revisa el mensaje anterior.
) else (
    echo.
    echo Proceso terminado. Consulta la carpeta results.
)
pause
