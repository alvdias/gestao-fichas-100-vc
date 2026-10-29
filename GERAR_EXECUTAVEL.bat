@echo off
chcp 65001 >nul
title Gerar executavel - Gestao de Comandas
cd /d "%~dp0"

echo ==========================================================
echo   Gerando o executavel GestaoComandas.exe
echo ==========================================================
echo.

set PY=
where py >nul 2>nul && set PY=py -3
if "%PY%"=="" (
    where python >nul 2>nul && set PY=python
)
if "%PY%"=="" (
    echo [ERRO] Python nao encontrado.
    echo Instale o Python 3.12 64 bits em https://www.python.org/downloads/windows/
    echo e marque a opcao "Add python.exe to PATH" na instalacao.
    pause
    exit /b 1
)

echo [1/3] Instalando o PyInstaller...
%PY% -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto erro

echo.
echo [2/3] Empacotando o sistema (pode levar 1-2 minutos)...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --noupx --name GestaoComandas main.py
if errorlevel 1 goto erro

echo.
echo [3/3] Copiando o executavel para esta pasta...
copy /Y "dist\GestaoComandas.exe" "GestaoComandas.exe" >nul
rmdir /S /Q build 2>nul
del /Q GestaoComandas.spec 2>nul

echo.
echo ==========================================================
echo   PRONTO! O arquivo GestaoComandas.exe esta nesta pasta.
echo   Copie ele para qualquer computador com Windows 11.
echo ==========================================================
pause
exit /b 0

:erro
echo.
echo [ERRO] Algo deu errado. Veja as mensagens acima.
pause
exit /b 1
