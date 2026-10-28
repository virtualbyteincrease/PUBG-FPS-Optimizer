#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для сохранения и загрузки настроек
"""

import json
from pathlib import Path


class SettingsManager:
    """Менеджер настроек приложения"""
    
    def __init__(self, settings_file="settings.json"):
        self.settings_file = Path(settings_file)
        self.default_settings = {
            "graphics": {
                "remove_grass": True,
                "grass_distance": 0,
                "potato_landscape": True,
                "clear_players": True,
                "low_shadows": True,
                "low_effects": True,
                "disable_antialiasing": True,
                "uncapped_fps": True
            },
            "audio": {
                "optimize_audio": True
            },
            "input": {
                "optimize_input": True
            },
            "performance": {
                "optimize_performance": True,
                "set_high_priority": True
            },
            "driver_optimization": {
                "timer_resolution": True,
                "cpu_affinity": True,
                "cpu_cores": "all",
                "disable_fullscreen_optimizations": True,
                "enable_game_mode": True,
                "disable_game_bar": True,
                "optimize_power_plan": True,
                "optimize_network": True,
                "memory_optimization": True,
                "disable_windows_defender": False
            },
            "last_config_path": ""
        }
    
    def load_settings(self):
        """Загружает настройки из файла"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # Объединяем с дефолтными настройками для обратной совместимости
                merged = self.default_settings.copy()
                merged.update(settings)
                # Объединяем вложенные словари
                for key in merged:
                    if isinstance(merged[key], dict) and key in settings:
                        merged[key].update(settings[key])
                return merged
            except Exception as e:
                print(f"Ошибка загрузки настроек: {e}")
                return self.default_settings.copy()
        return self.default_settings.copy()
    
    def save_settings(self, settings):
        """Сохраняет настройки в файл"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False
    
    def get_setting(self, category, key, default=None):
        """Получает значение настройки"""
        settings = self.load_settings()
        if category in settings and key in settings[category]:
            return settings[category][key]
        return default
    
    def set_setting(self, category, key, value):
        """Устанавливает значение настройки"""
        settings = self.load_settings()
        if category not in settings:
            settings[category] = {}
        settings[category][key] = value
        self.save_settings(settings)

