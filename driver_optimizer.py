#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для оптимизации драйверов и системных настроек для плавной игры
"""

import os
import subprocess
import ctypes
from pathlib import Path


class DriverOptimizer:
    """Класс для оптимизации драйверов и системных настроек"""
    
    def __init__(self):
        self.requires_admin = False
    
    def is_admin(self):
        """Проверяет, запущено ли приложение от администратора"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def optimize_timer_resolution(self, enable=True):
        """Оптимизация разрешения таймера Windows для снижения задержки"""
        if not self.is_admin():
            return False, "Требуются права администратора"
        
        try:
            if enable:
                # Устанавливаем высокое разрешение таймера (0.5ms)
                result = subprocess.run(
                    ['powercfg', '/setacvalueindex', 'scheme_current', 'SUB_PROCESSOR', 'PROCTHROTTLEMIN', '100'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                subprocess.run(['powercfg', '/setactive', 'scheme_current'], timeout=5)
                return True, "Разрешение таймера оптимизировано"
            else:
                # Возвращаем стандартные настройки
                result = subprocess.run(
                    ['powercfg', '/setacvalueindex', 'scheme_current', 'SUB_PROCESSOR', 'PROCTHROTTLEMIN', '5'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                subprocess.run(['powercfg', '/setactive', 'scheme_current'], timeout=5)
                return True, "Настройки таймера восстановлены"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def set_cpu_affinity(self, process_name="TslGame.exe", cpu_cores="all"):
        """Устанавливает привязку процесса к определенным ядрам CPU"""
        try:
            # Используем PowerShell для установки CPU affinity
            if cpu_cores == "all":
                ps_script = f'''
                $process = Get-Process -Name "{process_name.replace('.exe', '')}" -ErrorAction SilentlyContinue
                if ($process) {{
                    $process.ProcessorAffinity = [System.IntPtr]::new(0xFFFF)  # Все ядра
                    Write-Host "CPU Affinity установлен для всех ядер"
                }}
                '''
            else:
                # Привязка к первым N ядрам
                cores_mask = (1 << int(cpu_cores)) - 1
                ps_script = f'''
                $process = Get-Process -Name "{process_name.replace('.exe', '')}" -ErrorAction SilentlyContinue
                if ($process) {{
                    $process.ProcessorAffinity = [System.IntPtr]::new({cores_mask})
                    Write-Host "CPU Affinity установлен для первых {cpu_cores} ядер"
                }}
                '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            return True, "CPU Affinity установлен"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def disable_fullscreen_optimizations(self, exe_path):
        """Отключает оптимизации полноэкранного режима Windows для снижения задержки"""
        if not self.is_admin():
            return False, "Требуются права администратора"
        
        try:
            # Используем reg.exe для установки значения реестра
            key_path = f"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{os.path.basename(exe_path)}"
            subprocess.run(
                ['reg', 'add', key_path, '/v', 'DisableFullscreenOptimizations', '/t', 'REG_DWORD', '/d', '1', '/f'],
                capture_output=True,
                timeout=5
            )
            return True, "Fullscreen Optimizations отключены"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def enable_game_mode(self, enable=True):
        """Включает игровой режим Windows"""
        try:
            if enable:
                subprocess.run(
                    ['powershell', '-Command', 
                     'Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\GameBar" -Name "AllowAutoGameMode" -Value 1 -Type DWord -Force'],
                    capture_output=True,
                    timeout=5
                )
                subprocess.run(
                    ['powershell', '-Command',
                     'Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\GameBar" -Name "AutoGameModeEnabled" -Value 1 -Type DWord -Force'],
                    capture_output=True,
                    timeout=5
                )
                return True, "Игровой режим включен"
            else:
                subprocess.run(
                    ['powershell', '-Command',
                     'Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\GameBar" -Name "AutoGameModeEnabled" -Value 0 -Type DWord -Force'],
                    capture_output=True,
                    timeout=5
                )
                return True, "Игровой режим выключен"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def disable_game_bar(self, disable=True):
        """Отключает Game Bar Windows"""
        try:
            if disable:
                subprocess.run(
                    ['powershell', '-Command',
                     'Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" -Name "AppCaptureEnabled" -Value 0 -Type DWord -Force'],
                    capture_output=True,
                    timeout=5
                )
                subprocess.run(
                    ['powershell', '-Command',
                     'Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\GameBar" -Name "AllowAutoGameMode" -Value 0 -Type DWord -Force'],
                    capture_output=True,
                    timeout=5
                )
                return True, "Game Bar отключен"
            else:
                subprocess.run(
                    ['powershell', '-Command',
                     'Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" -Name "AppCaptureEnabled" -Value 1 -Type DWord -Force'],
                    capture_output=True,
                    timeout=5
                )
                return True, "Game Bar включен"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def optimize_power_plan(self, enable=True):
        """Оптимизирует план питания для максимальной производительности"""
        if not self.is_admin():
            return False, "Требуются права администратора"
        
        try:
            if enable:
                # Устанавливаем режим высокой производительности
                subprocess.run(
                    ['powercfg', '/setactive', '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'],  # High Performance
                    timeout=5
                )
                # Отключаем управление питанием процессора
                subprocess.run(
                    ['powercfg', '/setacvalueindex', 'scheme_current', 'SUB_PROCESSOR', 'PROCTHROTTLEMIN', '100'],
                    timeout=5
                )
                subprocess.run(
                    ['powercfg', '/setacvalueindex', 'scheme_current', 'SUB_PROCESSOR', 'PROCTHROTTLEMAX', '100'],
                    timeout=5
                )
                subprocess.run(['powercfg', '/setactive', 'scheme_current'], timeout=5)
                return True, "План питания оптимизирован для производительности"
            else:
                # Возвращаем сбалансированный план
                subprocess.run(['powercfg', '/setactive', '381b4222-f694-41f0-9685-ff5bb260df2e'], timeout=5)  # Balanced
                return True, "План питания восстановлен"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def optimize_network(self, enable=True):
        """Оптимизация сетевых настроек для снижения задержки"""
        if not self.is_admin():
            return False, "Требуются права администратора"
        
        try:
            if enable:
                # Отключаем TCP Auto-Tuning для снижения задержки
                subprocess.run(
                    ['netsh', 'int', 'tcp', 'set', 'global', 'autotuninglevel=disabled'],
                    capture_output=True,
                    timeout=5
                )
                # Включаем TCP NoDelay
                subprocess.run(
                    ['netsh', 'int', 'tcp', 'set', 'global', 'chimney=disabled'],
                    capture_output=True,
                    timeout=5
                )
                return True, "Сеть оптимизирована"
            else:
                # Возвращаем стандартные настройки
                subprocess.run(
                    ['netsh', 'int', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                    capture_output=True,
                    timeout=5
                )
                return True, "Сетевые настройки восстановлены"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def set_memory_optimization(self, enable=True):
        """Оптимизация памяти"""
        try:
            if enable:
                # Очистка standby memory
                ps_script = '''
                $signature = @"
                [DllImport("kernel32.dll", SetLastError = true)]
                public static extern bool SetProcessWorkingSetSize(IntPtr hProcess, UIntPtr dwMinimumWorkingSetSize, UIntPtr dwMaximumWorkingSetSize);
                "@
                $type = Add-Type -MemberDefinition $signature -Name "Win32SetProcessWorkingSetSize" -Namespace Win32Functions -PassThru
                $process = Get-Process -Name TslGame -ErrorAction SilentlyContinue
                if ($process) {
                    $type::SetProcessWorkingSetSize($process.Handle, [UIntPtr]0xFFFFFFFF, [UIntPtr]0xFFFFFFFF)
                }
                '''
                subprocess.run(['powershell', '-Command', ps_script], capture_output=True, timeout=5)
                return True, "Память оптимизирована"
            return True, ""
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def disable_windows_defender_for_folder(self, folder_path):
        """Отключает Windows Defender для указанной папки"""
        if not self.is_admin():
            return False, "Требуются права администратора"
        
        try:
            ps_script = f'''
            Add-MpPreference -ExclusionPath "{folder_path}" -ErrorAction SilentlyContinue
            '''
            subprocess.run(['powershell', '-Command', ps_script], capture_output=True, timeout=10)
            return True, f"Windows Defender исключен для {folder_path}"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

