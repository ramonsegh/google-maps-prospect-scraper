@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Instalador - Google Maps Prospect Scraper
cd /d "%~dp0"

echo ============================================================
echo     GOOGLE MAPS PROSPECT SCRAPER - INSTALADOR WINDOWS
echo ============================================================
echo.
echo Este instalador preparara Python, Visual Studio Code,
echo el entorno virtual y las dependencias del proyecto.
echo.

where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontro winget.
    echo Instala o actualiza "App Installer" desde Microsoft Store
    echo y vuelve a ejecutar este archivo.
    goto :error
)

call :buscar_python
if not defined PYTHON_EXE (
    echo [1/5] Python no esta instalado. Instalando Python 3.13...
    winget install --exact --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar Python.
        goto :error
    )
    call :buscar_python
)

if not defined PYTHON_EXE (
    echo [ERROR] Python se instalo, pero Windows aun no actualizo las rutas.
    echo Cierra esta ventana y ejecuta INSTALAR_WINDOWS.bat nuevamente.
    goto :error
)

echo [1/5] Python disponible:
"%PYTHON_EXE%" --version

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" goto :chrome_listo
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" goto :chrome_listo
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" goto :chrome_listo

echo.
echo [2/5] Instalando Google Chrome...
winget install --exact --id Google.Chrome --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [ERROR] No se pudo instalar Google Chrome.
    goto :error
)
goto :despues_chrome

:chrome_listo
echo [2/5] Google Chrome ya esta instalado.

:despues_chrome
where code >nul 2>&1
if errorlevel 1 (
    echo.
    echo [3/5] Instalando Visual Studio Code...
    winget install --exact --id Microsoft.VisualStudioCode --scope user --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [AVISO] VS Code no pudo instalarse. El scraper puede funcionar sin el editor.
    )
) else (
    echo [3/5] Visual Studio Code ya esta instalado.
)

echo.
echo [4/5] Creando el entorno virtual...
if not exist ".venv\Scripts\python.exe" (
    "%PYTHON_EXE%" -m venv ".venv"
    if errorlevel 1 goto :error
) else (
    echo El entorno .venv ya existe. Se reutilizara.
)

echo.
echo [5/5] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist ".env" copy /y ".env.example" ".env" >nul

echo.
echo ============================================================
echo                 INSTALACION COMPLETADA
echo ============================================================
echo.
echo Para buscar prospectos abre EJECUTAR_SCRAPER.bat.
echo Tambien puedes usar este comando:
echo.
echo .venv\Scripts\python.exe scraper_google_maps.py --giro "dentistas" --ubicacion "Monterrey, Nuevo Leon" --max 100 --calificacion-minima 4.5 --min-calificaciones 20
echo.
pause
exit /b 0

:buscar_python
set "PYTHON_EXE="
where py >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%P in ('py -3.13 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)
if defined PYTHON_EXE exit /b 0

where python >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)
if defined PYTHON_EXE exit /b 0

if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python313\python.exe"
)
exit /b 0

:error
echo.
echo La instalacion no pudo completarse.
echo Revisa el mensaje anterior y vuelve a intentarlo.
pause
exit /b 1
