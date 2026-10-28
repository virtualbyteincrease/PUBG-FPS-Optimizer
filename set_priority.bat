@echo off
title PUBG High Priority - Установка приоритета
color 0A
echo.
echo ========================================
echo  УСТАНОВКА ВЫСОКОГО ПРИОРИТЕТА ДЛЯ PUBG
echo ========================================
echo.
echo Этот скрипт установит высокий приоритет для процесса TslGame.exe
echo.
echo ВАЖНО: Запустите этот скрипт ПОСЛЕ запуска PUBG!
echo.
pause

:: Ищем процесс TslGame.exe
tasklist /FI "IMAGENAME eq TslGame.exe" 2>NUL | find /I /N "TslGame.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Найден процесс TslGame.exe
    echo Устанавливаю высокий приоритет...
    
    :: Используем PowerShell для установки приоритета
    powershell -Command "Get-Process -Name TslGame -ErrorAction SilentlyContinue | ForEach-Object { $_.PriorityClass = 'High'; Write-Host 'Приоритет установлен на HIGH для PID:' $_.Id }"
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ========================================
        echo  УСПЕШНО! Приоритет установлен на HIGH
        echo ========================================
    ) else (
        echo.
        echo ОШИБКА: Не удалось установить приоритет
        echo Попробуйте запустить от имени администратора
    )
) else (
    echo.
    echo ОШИБКА: Процесс TslGame.exe не найден!
    echo Убедитесь, что PUBG запущен.
)

echo.
pause


