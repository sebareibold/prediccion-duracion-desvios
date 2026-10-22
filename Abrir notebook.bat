@echo off
rem Doble clic: prepara el entorno (solo la primera vez) y abre el notebook en marimo.
cd /d "%~dp0"

set "NOTEBOOK=notebooks\01_exploracion_y_modelos.py"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Primera vez: creando el entorno de Python en .venv ...
    where py >nul 2>nul && (py -3 -m venv .venv) || (python -m venv .venv)
    if not exist "%PYTHON%" goto error
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto error
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Se creo .env a partir de .env.example. Revisa DATOS_DIR ahi.
)

set "DATOS_DIR="
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="DATOS_DIR" set "DATOS_DIR=%%b"
)

if not exist "%DATOS_DIR%\desviosHojaRuta.json" (
    echo.
    echo AVISO: no estan los datos en DATOS_DIR=%DATOS_DIR% ^(definido en .env^).
    echo Extrae data-fixed.zip ahi ^(hojaDeRuta.json, desviosHojaRuta.json y rastreoSatelital.json^).
    echo Marimo se abre igual, pero las celdas de carga van a fallar.
    echo.
)

echo Abriendo marimo en el navegador. Para cerrarlo, cerra esta ventana.
"%PYTHON%" -m marimo edit "%NOTEBOOK%"
goto fin

:error
echo.
echo No se pudo preparar el entorno. Hace falta Python 3.11 o superior instalado.

:fin
pause
