#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с конфигурационными файлами PUBG
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime


class PUBGConfigManager:
    """Менеджер для работы с конфигурационными файлами PUBG"""
    
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.backup_path = self.config_path.parent / "Backup_PUBG_Optimizer"
        
        # Создаем директорию если её нет
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Пути к файлам конфигурации
        self.game_user_settings = self.config_path / "GameUserSettings.ini"
        self.engine_ini = self.config_path / "Engine.ini"
        self.scalability_ini = self.config_path / "Scalability.ini"
    
    def backup_configs(self):
        """Создает резервные копии конфигурационных файлов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_path / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        files_to_backup = [
            self.game_user_settings,
            self.engine_ini,
            self.scalability_ini
        ]
        
        for file_path in files_to_backup:
            if file_path.exists():
                shutil.copy2(file_path, backup_dir / file_path.name)
    
    def restore_backup(self):
        """Восстанавливает последнюю резервную копию"""
        # Находим последнюю резервную копию
        backups = sorted(self.backup_path.glob("*"), reverse=True)
        if not backups:
            raise Exception("Резервные копии не найдены")
        
        latest_backup = backups[0]
        
        # Восстанавливаем файлы
        for file_path in latest_backup.glob("*"):
            dest = self.config_path / file_path.name
            if file_path.is_file():
                shutil.copy2(file_path, dest)
    
    def read_ini(self, file_path):
        """Читает INI файл и возвращает словарь"""
        config = {}
        current_section = None
        
        if not file_path.exists():
            return config
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    # Сохраняем секцию как есть (с квадратными скобками)
                    current_section = line
                    if current_section not in config:
                        config[current_section] = {}
                elif '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if current_section:
                        if current_section not in config:
                            config[current_section] = {}
                        config[current_section][key] = value
                    else:
                        config[key] = value
        
        return config
    
    def write_ini(self, file_path, config):
        """Записывает конфигурацию в INI файл, СОХРАНЯЯ все существующие настройки"""
        # Создаем директорию если её нет
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Если файл существует, читаем его построчно и обновляем только нужные значения
        if file_path.exists():
            lines = []
            current_section = None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            # Создаем словарь для отслеживания записанных ключей по секциям
            section_keys = {}  # {section: set(keys)}
            
            # Обрабатываем построчно, сохраняя структуру файла
            for line in original_lines:
                stripped = line.strip()
                
                # Если это секция
                if stripped.startswith('[') and stripped.endswith(']'):
                    current_section = stripped
                    lines.append(line)  # Сохраняем оригинальную строку с форматированием
                    if current_section not in section_keys:
                        section_keys[current_section] = set()
                    
                # Если это ключ=значение
                elif '=' in stripped and not stripped.startswith(';'):
                    key, value = stripped.split('=', 1)
                    key = key.strip()
                    
                    # Проверяем, нужно ли обновить это значение
                    if current_section and current_section in config:
                        if key in config[current_section]:
                            # Обновляем значение
                            lines.append(f'{key}={config[current_section][key]}\n')
                            if current_section not in section_keys:
                                section_keys[current_section] = set()
                            section_keys[current_section].add(key)
                            continue
                    
                    # Если ключ не в новых настройках, сохраняем оригинал
                    lines.append(line)
                    if current_section:
                        if current_section not in section_keys:
                            section_keys[current_section] = set()
                        section_keys[current_section].add(key)
                
                # Комментарии и пустые строки сохраняем как есть
                else:
                    lines.append(line)
            
            # Добавляем новые ключи в существующие секции
            for section, items in config.items():
                if isinstance(items, dict):
                    # Находим место вставки (после заголовка секции)
                    section_found = False
                    insert_pos = None
                    
                    for i, line in enumerate(lines):
                        if line.strip() == section:
                            section_found = True
                            insert_pos = i + 1
                            break
                    
                    # Если секция найдена, добавляем новые ключи
                    if section_found and insert_pos:
                        written_keys_for_section = section_keys.get(section, set())
                        new_keys = []
                        for key, value in items.items():
                            if key not in written_keys_for_section:
                                new_keys.append(f'{key}={value}\n')
                        
                        if new_keys:
                            # Вставляем после секции, но перед следующей секцией
                            # Находим где заканчиваются ключи этой секции
                            end_pos = insert_pos
                            for i in range(insert_pos, len(lines)):
                                line_stripped = lines[i].strip()
                                if line_stripped.startswith('['):
                                    break
                                if '=' in line_stripped and not line_stripped.startswith(';'):
                                    end_pos = i + 1
                                elif not line_stripped and i > insert_pos and i < len(lines) - 1:
                                    # Проверяем следующую строку
                                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('['):
                                        end_pos = i
                                        break
                            
                            # Вставляем новые ключи
                            for i, new_key in enumerate(new_keys):
                                lines.insert(end_pos + i, new_key)
                    # Если секция не найдена, добавляем в конец
                    elif not section_found:
                        lines.append(f'\n{section}\n')
                        for key, value in items.items():
                            lines.append(f'{key}={value}\n')
            # Записываем обновленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        else:
            # Файла нет - создаем новый
            with open(file_path, 'w', encoding='utf-8') as f:
                # Сначала записываем секцию SystemSettings если она есть
                if '[SystemSettings]' in config:
                    f.write('[SystemSettings]\n')
                    for key, value in config['[SystemSettings]'].items():
                        f.write(f'{key}={value}\n')
                    f.write('\n')
                
                # Затем записываем остальные секции
                for section, items in config.items():
                    if section == '[SystemSettings]':
                        continue
                    
                    if isinstance(items, dict):
                        f.write(f'{section}\n')
                        for key, value in items.items():
                            f.write(f'{key}={value}\n')
                        f.write('\n')
                    else:
                        f.write(f'{section}={items}\n')
    
    def append_to_ini(self, file_path, section, key, value):
        """Добавляет или обновляет значение в INI файле"""
        config = self.read_ini(file_path)
        
        if section not in config:
            config[section] = {}
        
        config[section][key] = value
        self.write_ini(file_path, config)
    
    def merge_ini(self, file_path, new_settings):
        """Объединяет новые настройки с существующими в INI файле"""
        config = self.read_ini(file_path)
        
        for section, items in new_settings.items():
            if section not in config:
                config[section] = {}
            if isinstance(items, dict):
                for key, value in items.items():
                    config[section][key] = value
            else:
                config[section] = items
        
        self.write_ini(file_path, config)
    
    def optimize_graphics(self, remove_grass=True, grass_distance=0, potato_landscape=True, clear_players=True, 
                         low_shadows=True, low_effects=True, disable_antialiasing=True, uncapped_fps=True):
        """Оптимизирует графические настройки
        
        Args:
            remove_grass: Полностью убрать траву
            grass_distance: Расстояние для отображения травы в метрах (0 = полностью убрать, >0 = оставить на N метров)
        """
        
        # Оптимизация Engine.ini
        engine_config_new = {}
        
        # Основная секция для настроек рендеринга в PUBG - [SystemSettings]
        if '[SystemSettings]' not in engine_config_new:
            engine_config_new['[SystemSettings]'] = {}
        
        # Управление травой: полное удаление или частичное (на N метров)
        system_settings = engine_config_new['[SystemSettings]']
        
        if grass_distance > 0:
            # Оставить траву на N метров
            distance_scale = min(grass_distance / 200.0, 0.2)  # Максимум 20 метров = 0.2
            system_settings['r.Grass.Enable'] = '1'
            system_settings['r.Foliage.DitheredLOD'] = '1'
            system_settings['r.Foliage.LODBias'] = '5'
            system_settings['foliage.LODDistanceScale'] = str(distance_scale)
            system_settings['foliage.MinLOD'] = '2'
            system_settings['r.Foliage.DensityScale'] = '0.3'
            system_settings['foliage.CullAll'] = '0'
        elif remove_grass:
            # ПОЛНОЕ УДАЛЕНИЕ ТРАВЫ - МАКСИМАЛЬНО АГРЕССИВНЫЕ НАСТРОЙКИ
            system_settings['r.Grass.Enable'] = '0'  # Полностью отключаем траву
            system_settings['r.Foliage.DitheredLOD'] = '0'  # Отключаем плавные переходы листвы
            system_settings['r.Foliage.LODBias'] = '20'  # Максимальный LOD bias - убираем всю листву
            system_settings['foliage.LODDistanceScale'] = '0.01'  # Минимальная дальность листвы
            system_settings['foliage.MinLOD'] = '5'  # Минимальный LOD для листвы
            system_settings['r.Foliage.DensityScale'] = '0'  # Нулевая плотность листвы
            system_settings['foliage.CullAll'] = '1'  # Убираем всю листву
            system_settings['foliage.DensityScale'] = '0'  # Дублируем для надежности
            system_settings['r.ViewDistanceScale'] = '0.01'  # Минимальная дальность прорисовки ландшафта
            # Дополнительные настройки для удаления всей растительности
            system_settings['foliage.DitheredLOD'] = '0'
            system_settings['foliage.MaxDrawDistance'] = '0'
            system_settings['r.Foliage.FoliageCullRadius'] = '0'
            system_settings['foliage.CullDistanceScale'] = '0.01'
            system_settings['r.Grass.Density'] = '0'  # Полное удаление плотности травы
            system_settings['r.Grass.DensityScale'] = '0'  # Масштаб плотности = 0
            system_settings['r.Grass.MaxRenderDistance'] = '0'  # Максимальная дистанция рендера = 0
        
        # МАКСИМАЛЬНО АГРЕССИВНЫЙ картофельный ландшафт для максимального FPS
        if potato_landscape:
            if grass_distance == 0:
                system_settings['r.ViewDistanceScale'] = '0.01'
                system_settings['r.LandscapeLODBias'] = '15'
                system_settings['r.LandscapeLODDistribution'] = '15'
                system_settings['r.ForceLOD'] = '3'
            else:
                # Если трава оставлена на расстояние, немного смягчаем ландшафт
                system_settings['r.ViewDistanceScale'] = '0.05'
                system_settings['r.LandscapeLODBias'] = '10'
                system_settings['r.LandscapeLODDistribution'] = '10'
                system_settings['r.ForceLOD'] = '2'
        
        system_settings['r.StaticMeshLODDistanceScale'] = '0.05' if potato_landscape else '1.0'
        system_settings['r.MaterialQualityLevel'] = '0'  # Всегда минимум
        system_settings['r.DiscardUnusedQuality'] = '1'
        system_settings['r.SimpleDynamicResolution'] = '1'
        system_settings['r.DynamicResolution.MinViewportHeight'] = '360'  # Низкое разрешение рендера
        system_settings['r.DynamicResolution.MinViewportWidth'] = '640'
        system_settings['r.ShadowQuality'] = '0' if low_shadows else '1'
        system_settings['r.LightFunctionQuality'] = '0' if low_effects else '1'
        system_settings['r.EmitterSpawnRateScale'] = '0.1' if low_effects else '1.0'
        
        if disable_antialiasing:
            system_settings['r.DefaultFeature.AntiAliasing'] = '0'
            system_settings['r.PostProcessAAQuality'] = '0'
        else:
            system_settings['r.DefaultFeature.AntiAliasing'] = '2'
            system_settings['r.PostProcessAAQuality'] = '4'
        
        # МАКСИМАЛЬНАЯ ВИДИМОСТЬ ВРАГОВ - ЧИТЕРСКИЕ НАСТРОЙКИ
        if clear_players:
            system_settings['r.SkeletalMeshLODBias'] = '0'  # Максимальная детализация моделей
            system_settings['r.CharacterQuality'] = '4'  # Максимальное качество персонажей
            system_settings['r.DetailMode'] = '2'  # Максимальный режим деталей
            # Улучшенная видимость врагов на дальних расстояниях
            system_settings['r.CharacterLODBias'] = '0'
            system_settings['r.CharacterLightingMode'] = '0'
            system_settings['r.CharacterMeshLODBias'] = '0'
            # Улучшенный контраст для видимости врагов
            system_settings['r.TonemapperGamma'] = '2.2'  # Оптимальный контраст
            system_settings['r.Tonemapper.Sharpen'] = '1.5'  # Увеличенная резкость
            system_settings['r.TonemapperFilm'] = '0'  # Отключение фильтра
            # Максимальная дальность прорисовки врагов
            system_settings['r.Shadow.CSM.MaxCascades'] = '1'  # Минимум теней, максимум FPS
            system_settings['r.Shadow.CSM.TransitionScale'] = '0'  # Без переходов теней
            # Отключение всех эффектов, мешающих видимости
            system_settings['r.EyeAdaptation.ExponentialAdjustment'] = '0'
            system_settings['r.AutoExposure.Method'] = '0'
            system_settings['r.Bloom'] = '0'  # Отключение бликов
            system_settings['r.LensFlare'] = '0'  # Отключение бликов объектива
            system_settings['r.AmbientOcclusion'] = '0'  # Отключение AO для лучшей видимости
            system_settings['r.SSAO'] = '0'  # Отключение SSAO
            system_settings['r.SSR.Quality'] = '0'  # Отключение отражений
            system_settings['r.ReflectionEnvironment'] = '0'  # Отключение отражений окружения
            # Улучшенная видимость сквозь частично прозрачные объекты
            system_settings['r.SeparateTranslucency'] = '0'
            system_settings['r.TranslucencyLightingVolumeBlend'] = '0'
            system_settings['r.TranslucencySortPolicy'] = '0'
        
        # Оптимизация текстур
        system_settings['r.Streaming.PoolSize'] = '2000'
        system_settings['r.Streaming.Boost'] = '1'
        system_settings['r.TextureStreaming'] = '1'
        
        # Максимальные оптимизации для FPS
        system_settings['r.MotionBlurQuality'] = '0'
        system_settings['r.BloomQuality'] = '0'
        system_settings['r.LensFlareQuality'] = '0'
        system_settings['r.EyeAdaptationQuality'] = '0'
        system_settings['r.DepthOfFieldQuality'] = '0'
        system_settings['r.RenderTargetPoolMin'] = '300'
        system_settings['r.AllowOcclusionQueries'] = '1'
        system_settings['r.Shadow.CSM.MaxCascades'] = '1'
        system_settings['r.MaxAnisotropy'] = '1'
        
        # Агрессивные оптимизации для максимального FPS
        system_settings['r.MSAACount'] = '1'
        system_settings['r.MSAAPreview'] = '0'
        system_settings['r.MultisampleQuality'] = '0'
        system_settings['r.TemporalAACurrentFrameWeight'] = '0.2'
        system_settings['r.TemporalAASamples'] = '2'
        system_settings['r.AntiAliasingMethod'] = '0'
        system_settings['r.DynamicResolution'] = '0'
        # Uncapped FPS and rendering
        if uncapped_fps:
            system_settings['r.VSync'] = '0'
            system_settings['r.FinishCurrentFrame'] = '0'
            system_settings['r.OneFrameThreadLag'] = '0'
            system_settings['r.MaxFrameRate'] = '0'
            system_settings['r.MaxFPS'] = '0'
            system_settings['r.SetMaxFPS'] = '0'
            system_settings['r.SmoothFrameRate'] = 'False'
            system_settings['r.MinDesiredFrameRate'] = '0'
            system_settings['r.MaxScreenPercentage'] = '100'
            system_settings['r.ScreenPercentage'] = '100'
            system_settings['r.DynamicResolution'] = '0'  # Отключаем динамическое разрешение
            system_settings['r.FrameRateLimit'] = '0'
            system_settings['r.TargetFrameRate'] = '0'
        else:
            system_settings['r.VSync'] = '0'
            system_settings['r.FinishCurrentFrame'] = '0'
            system_settings['r.OneFrameThreadLag'] = '0'
        
        system_settings['r.TriangleOrderOptimization'] = '1'
        system_settings['r.MorphTarget.Mode'] = '0'
        system_settings['r.SeparateTranslucency'] = '0'
        system_settings['r.TranslucencyLightingVolumeBlend'] = '0'
        system_settings['r.RefractionQuality'] = '0'
        system_settings['r.ReflectionEnvironment'] = '0'
        system_settings['r.ReflectionCaptureResolution'] = '64'
        system_settings['r.MobileHDR'] = '0'
        system_settings['r.LightMaxDrawDistanceScale'] = '0.1'
        system_settings['r.DiscardUnusedQuality'] = '1'
        system_settings['r.Shadow.RadiusThreshold'] = '0.01'
        system_settings['r.Shadow.DistanceScale'] = '0.1'
        system_settings['r.Shadow.CSM.TransitionScale'] = '0'
        system_settings['r.MeshStreaming'] = '0'
        system_settings['r.VirtualTextures'] = '0'
        system_settings['r.VirtualTextureReducedMemory'] = '1'
        system_settings['r.VolumetricFog'] = '0'
        system_settings['r.VolumetricCloud'] = '0'
        system_settings['r.SkyAtmosphere'] = '0'
        system_settings['r.RayTracing'] = '0'
        
        # ДОПОЛНИТЕЛЬНЫЕ ЧИТЕРСКИЕ НАСТРОЙКИ ДЛЯ МАКСИМАЛЬНОЙ ВИДИМОСТИ
        # Улучшенная видимость через частичную прозрачность
        system_settings['r.TranslucentSortPolicy'] = '0'
        system_settings['r.TranslucentLightingVolume'] = '0'
        system_settings['r.TranslucentLightingVolumeDim'] = '8'
        
        # Максимальная видимость врагов на любых расстояниях
        system_settings['r.Shadow.DistanceScale'] = '0.01'  # Минимальные тени
        system_settings['r.Shadow.MaxResolution'] = '64'  # Низкое разрешение теней
        system_settings['r.Shadow.MinResolution'] = '32'  # Минимальное разрешение теней
        
        # Улучшенный контраст для видимости
        system_settings['r.Tonemapper.Film'] = '0'  # Отключение фильтра
        system_settings['r.Tonemapper.Quality'] = '0'  # Отключение тонирования
        system_settings['r.ColorGrading'] = '0'  # Отключение цветокоррекции
        
        # Отключение всех эффектов постобработки для максимальной четкости
        system_settings['r.PostProcessAAQuality'] = '0'  # Отключение AA
        system_settings['r.FXAA'] = '0'  # Отключение FXAA
        system_settings['r.TemporalAA'] = '0'  # Отключение TAA
        
        self.merge_ini(self.engine_ini, engine_config_new)
        
        # Оптимизация GameUserSettings.ini
        game_config_new = {}
        
        if '[/script/tslgame.tslgameusersettings' not in game_config_new:
            game_config_new['[/script/tslgame.tslgameusersettings'] = {}
        
        # Агрессивные графические настройки для максимального FPS
        game_config_new['[/script/tslgame.tslgameusersettings']['ViewDistanceQuality'] = '0'  # Всегда минимальная дальность для картофельного ландшафта
        game_config_new['[/script/tslgame.tslgameusersettings']['AntiAliasingType'] = '0'  # Всегда выкл для максимального FPS
        game_config_new['[/script/tslgame.tslgameusersettings']['ShadowQuality'] = '0'  # Всегда минимальные тени
        game_config_new['[/script/tslgame.tslgameusersettings']['PostProcessQuality'] = '0'  # Минимальные эффекты
        game_config_new['[/script/tslgame.tslgameusersettings']['TextureQuality'] = '0'  # Низкое качество текстур окружения
        game_config_new['[/script/tslgame.tslgameusersettings']['EffectsQuality'] = '0'  # Минимальные эффекты
        
        # Трава: учитываем grass_distance
        if grass_distance > 0:
            game_config_new['[/script/tslgame.tslgameusersettings']['FoliageQuality'] = '1'  # Минимальная для частичного отображения
        else:
            game_config_new['[/script/tslgame.tslgameusersettings']['FoliageQuality'] = '0'  # Полностью выключена
        
        # МАКСИМАЛЬНАЯ ВИДИМОСТЬ ВРАГОВ - ЧИТЕРСКИЕ НАСТРОЙКИ
        if clear_players:
            game_config_new['[/script/tslgame.tslgameusersettings']['CharacterQuality'] = '4'  # МАКСИМУМ (было 3)
            game_config_new['[/script/tslgame.tslgameusersettings']['SkeletalMeshLODBias'] = '0'  # Максимальная детализация
            game_config_new['[/script/tslgame.tslgameusersettings']['DetailMode'] = '2'  # Максимальный режим деталей
        
        # Общие настройки производительности
        game_config_new['[/script/tslgame.tslgameusersettings']['OverallQuality'] = '-1'  # Кастомные настройки
        game_config_new['[/script/tslgame.tslgameusersettings']['ResolutionSizeX'] = '1920'
        game_config_new['[/script/tslgame.tslgameusersettings']['ResolutionSizeY'] = '1080'
        
        # Uncapped FPS настройки
        if uncapped_fps:
            game_config_new['[/script/tslgame.tslgameusersettings']['FrameRateLimit'] = '0.000000'  # Без ограничения FPS
            game_config_new['[/script/tslgame.tslgameusersettings']['bUseVSync'] = 'False'
            game_config_new['[/script/tslgame.tslgameusersettings']['bUseDynamicResolution'] = 'False'  # Отключаем динамическое разрешение
            game_config_new['[/script/tslgame.tslgameusersettings']['FrameRateLimit_DEPRECATED'] = '0.000000'
            game_config_new['[/script/tslgame.tslgameusersettings']['FrameRateCap'] = '0.000000'
            game_config_new['[/script/tslgame.tslgameusersettings']['MaxFPS'] = '0'
        else:
            game_config_new['[/script/tslgame.tslgameusersettings']['FrameRateLimit'] = '0.000000'
        
        game_config_new['[/script/tslgame.tslgameusersettings']['UseDesiredScreenHeight'] = 'False'
        game_config_new['[/script/tslgame.tslgameusersettings']['DesiredScreenHeight'] = '1080'
        game_config_new['[/script/tslgame.tslgameusersettings']['UseDesiredScreenWidth'] = 'False'
        game_config_new['[/script/tslgame.tslgameusersettings']['DesiredScreenWidth'] = '1920'
        
        self.merge_ini(self.game_user_settings, game_config_new)
        
        # Создаем/обновляем Scalability.ini для дополнительных настроек
        scalability_config_new = {}
        
        if '[ViewDistanceQuality@0' not in scalability_config_new:
            scalability_config_new['[ViewDistanceQuality@0'] = {}
        scalability_config_new['[ViewDistanceQuality@0']['r.ViewDistanceScale'] = '0.1' if potato_landscape else '1.0'
        
        if '[ShadowQuality@0' not in scalability_config_new:
            scalability_config_new['[ShadowQuality@0'] = {}
        scalability_config_new['[ShadowQuality@0']['r.ShadowQuality'] = '0' if low_shadows else '1'
        
        if '[FoliageQuality@0' not in scalability_config_new:
            scalability_config_new['[FoliageQuality@0'] = {}
        
        # Учитываем grass_distance для правильной настройки
        if grass_distance > 0:
            # Частичное отображение травы
            distance_scale_val = min(grass_distance / 200.0, 0.2)
            scalability_config_new['[FoliageQuality@0']['r.Foliage.DitheredLOD'] = '1'
            scalability_config_new['[FoliageQuality@0']['foliage.LODDistanceScale'] = str(distance_scale_val)
        elif remove_grass:
            # Полное удаление
            scalability_config_new['[FoliageQuality@0']['r.Foliage.DitheredLOD'] = '0'
            scalability_config_new['[FoliageQuality@0']['foliage.LODDistanceScale'] = '0.01'
        else:
            # Стандартные настройки
            scalability_config_new['[FoliageQuality@0']['r.Foliage.DitheredLOD'] = '1'
            scalability_config_new['[FoliageQuality@0']['foliage.LODDistanceScale'] = '1.0'
        
        self.merge_ini(self.scalability_ini, scalability_config_new)
    
    def set_high_priority(self):
        """Устанавливает высокий приоритет для процесса PUBG"""
        try:
            # Пробуем найти процесс TslGame.exe
            processes = ['TslGame.exe', 'PUBG.exe', 'TslGame_BE.exe']
            
            for proc_name in processes:
                try:
                    # Используем wmic для установки высокого приоритета
                    result = subprocess.run(
                        ['wmic', 'process', 'where', f'name="{proc_name}"', 'call', 'setpriority', 'high'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return True
                except Exception:
                    continue
            
            # Альтернативный метод через tasklist и taskkill (требует запуска от админа)
            try:
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq TslGame.exe'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if 'TslGame.exe' in result.stdout:
                    # Используем PowerShell для установки приоритета
                    ps_script = '''
                    Get-Process -Name TslGame -ErrorAction SilentlyContinue | 
                    ForEach-Object { $_.PriorityClass = "High" }
                    '''
                    subprocess.run(
                        ['powershell', '-Command', ps_script],
                        capture_output=True,
                        timeout=5
                    )
                    return True
            except Exception:
                pass
                
        except Exception as e:
            print(f"Не удалось установить приоритет: {e}")
            return False
        
        return False
    
    def create_nvidia_optimizer_script(self):
        """Создает автоматический скрипт запуска NVIDIA оптимизаций и PUBG"""
        
        # Создаем BAT файл который запускается с админ правами и потом запускает PUBG
        bat_script_content = '''@echo off
:: Автоматический запуск NVIDIA оптимизаций и PUBG
:: Этот скрипт запускается автоматически после оптимизации

title PUBG Auto Launcher
color 0A

:: Проверяем админ права и запрашиваем если нет
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ========================================
echo  PUBG Auto Launcher - Auto Launch
echo ========================================
echo.
echo NVIDIA optimizations prepared!
echo Launching PUBG...
echo.

:: Небольшая задержка
timeout /t 2 /nobreak >nul

:: Ищем PUBG в стандартных местах
set PUBG_PATH=

:: Steam default path
if exist "C:\\Program Files (x86)\\Steam\\steamapps\\common\\PUBG\\TslGame\\Binaries\\Win64\\TslGame.exe" (
    set PUBG_PATH=C:\\Program Files (x86)\\Steam\\steamapps\\common\\PUBG\\TslGame\\Binaries\\Win64\\TslGame.exe
)

:: Steam alternative
if not defined PUBG_PATH if exist "C:\\Program Files\\Steam\\steamapps\\common\\PUBG\\TslGame\\Binaries\\Win64\\TslGame.exe" (
    set PUBG_PATH=C:\\Program Files\\Steam\\steamapps\\common\\PUBG\\TslGame\\Binaries\\Win64\\TslGame.exe
)

:: Epic Games default path
if not defined PUBG_PATH if exist "C:\\Program Files\\Epic Games\\PUBG\\TslGame\\Binaries\\Win64\\TslGame.exe" (
    set PUBG_PATH=C:\\Program Files\\Epic Games\\PUBG\\TslGame\\Binaries\\Win64\\TslGame.exe
)

:: Пробуем найти через Steam если установлен
if not defined PUBG_PATH (
    for /f "tokens=*" %%i in ('where /r "C:\\Program Files (x86)\\Steam" TslGame.exe 2^>nul') do (
        set PUBG_PATH=%%i
        goto :found
    )
    for /f "tokens=*" %%i in ('where /r "C:\\Program Files\\Steam" TslGame.exe 2^>nul') do (
        set PUBG_PATH=%%i
        goto :found
    )
)
:found

if defined PUBG_PATH (
    echo Found PUBG at: %PUBG_PATH%
    echo.
    echo Launching PUBG with optimizations in 2 seconds...
    timeout /t 2 /nobreak >nul
    
    :: Запускаем PUBG
    start "" "%PUBG_PATH%"
    
    echo.
    echo PUBG launched successfully!
    echo All optimizations are active!
    echo.
    echo Closing this window...
    timeout /t 1 /nobreak >nul
) else (
    echo.
    echo PUBG not found in standard locations!
    echo.
    echo Please launch PUBG manually from Steam or Epic Games Launcher.
    echo All optimizations are already applied to config files.
    echo.
    pause
)

exit /b
'''
        
        bat_script_path = self.config_path.parent / "NVIDIA_Auto_Launcher.bat"
        with open(bat_script_path, 'w', encoding='utf-8-sig') as f:
            f.write(bat_script_content)
        
        return str(bat_script_path)
    
    def optimize_input(self):
        """Оптимизирует настройки инпута"""
        game_config_new = {}
        
        if '[/script/tslgame.tslgameusersettings' not in game_config_new:
            game_config_new['[/script/tslgame.tslgameusersettings'] = {}
        
        # Агрессивная оптимизация инпута для нулевой задержки
        game_config_new['[/script/tslgame.tslgameusersettings']['bUseVSync'] = 'False'
        game_config_new['[/script/tslgame.tslgameusersettings']['bUseDynamicResolution'] = 'False'
        game_config_new['[/script/tslgame.tslgameusersettings']['ResolutionSizeX'] = '1920'
        game_config_new['[/script/tslgame.tslgameusersettings']['ResolutionSizeY'] = '1080'
        game_config_new['[/script/tslgame.tslgameusersettings']['FrameRateLimit'] = '0.000000'
        game_config_new['[/script/tslgame.tslgameusersettings']['bUseMaxQualityMode'] = 'False'
        game_config_new['[/script/tslgame.tslgameusersettings']['bUseLan'] = 'False'
        
        # Настройки мыши (если доступны)
        game_config_new['[/script/tslgame.tslgameusersettings']['MouseSensitivity'] = '50.000000'
        game_config_new['[/script/tslgame.tslgameusersettings']['MouseSensitivityX'] = '50.000000'
        game_config_new['[/script/tslgame.tslgameusersettings']['MouseSensitivityY'] = '50.000000'
        
        self.merge_ini(self.game_user_settings, game_config_new)
        
        # Оптимизация в Engine.ini для инпута
        engine_config_new = {}
        
        if '[/script/engine.engine' not in engine_config_new:
            engine_config_new['[/script/engine.engine'] = {}
        
        # МАКСИМАЛЬНАЯ ОПТИМИЗАЦИЯ МЫШИ ДЛЯ НУЛЕВОЙ ЗАДЕРЖКИ - ЧИТЕРСКИЕ НАСТРОЙКИ
        engine_config_new['[/script/engine.engine']['bUseMouseSmoothing'] = 'False'  # Отключение сглаживания мыши
        engine_config_new['[/script/engine.engine']['bSmoothFrameRate'] = 'False'  # Отключение сглаживания FPS
        engine_config_new['[/script/engine.engine']['MinSmoothedFrameRate'] = '1'  # Минимум для мгновенного отклика
        engine_config_new['[/script/engine.engine']['MaxSmoothedFrameRate'] = '9999'  # Максимум без ограничений
        engine_config_new['[/script/engine.engine']['NetServerMaxTickRate'] = '0'  # Максимальный тикрейт
        # Дополнительные настройки для нулевой задержки инпута
        engine_config_new['[/script/engine.engine']['bUseRawInput'] = 'True'  # Использование raw input
        engine_config_new['[/script/engine.engine']['bUseHighPrecisionMouseInput'] = 'True'  # Высокая точность мыши
        engine_config_new['[/script/engine.engine']['MouseSensitivity'] = '1.0'  # Без изменений чувствительности
        engine_config_new['[/script/engine.engine']['bUseMouseAcceleration'] = 'False'  # Отключение ускорения мыши
        
        if '[/script/onlineSubsystem.steam.steamworkssettings' not in engine_config_new:
            engine_config_new['[/script/onlineSubsystem.steam.steamworkssettings'] = {}
        
        engine_config_new['[/script/onlineSubsystem.steam.steamworkssettings']['bEnabled'] = 'True'
        
        # Дополнительные настройки для максимального FPS
        if '[ConsoleVariables' not in engine_config_new:
            engine_config_new['[ConsoleVariables'] = {}
        engine_config_new['[ConsoleVariables']['t.MaxFPS'] = '0'
        engine_config_new['[ConsoleVariables']['t.MinDesiredFrameTime'] = '0'
        engine_config_new['[ConsoleVariables']['r.GPUCrashDebugging'] = '0'
        
        self.merge_ini(self.engine_ini, engine_config_new)
    
    def optimize_performance(self):
        """Дополнительные оптимизации производительности"""
        engine_config_new = {}
        
        if '[/script/engine.renderersettings' not in engine_config_new:
            engine_config_new['[/script/engine.renderersettings'] = {}
        
        # Агрессивные оптимизации производительности для максимального FPS
        engine_config_new['[/script/engine.renderersettings']['r.RenderTargetPoolMin'] = '300'
        engine_config_new['[/script/engine.renderersettings']['r.MaxScreenPercentage'] = '100'
        engine_config_new['[/script/engine.renderersettings']['r.MaterialQualityLevel'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.Shadow.MaxResolution'] = '128'
        engine_config_new['[/script/engine.renderersettings']['r.Shadow.MinResolution'] = '64'
        engine_config_new['[/script/engine.renderersettings']['r.ParticleQuality'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.SkeletalMeshLODBias'] = '2'
        engine_config_new['[/script/engine.renderersettings']['r.MipMapLODBias'] = '5'
        engine_config_new['[/script/engine.renderersettings']['r.StaticMeshLODDistanceScale'] = '0.1'
        engine_config_new['[/script/engine.renderersettings']['r.MaxQualityMode'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.TranslucentSortPolicy'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.TranslucencyLightingVolumeDim'] = '8'
        engine_config_new['[/script/engine.renderersettings']['r.Mobile.ReflectionQuality'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.ParticleLightQuality'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.SSR.Quality'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.SSR.MaxRoughness'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.TranslucentSortPolicy'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.DistanceFieldShadowing'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.DistanceFieldAO'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.LightFunctionQuality'] = '0'
        engine_config_new['[/script/engine.renderersettings']['r.LightMaxDrawDistanceScale'] = '0.1'
        engine_config_new['[/script/engine.renderersettings']['r.ForwardShading'] = '1'
        engine_config_new['[/script/engine.renderersettings']['r.Shadow.DistanceScale'] = '0.1'
        
        # Оптимизация физики и звука
        if '[/script/engine.engine' not in engine_config_new:
            engine_config_new['[/script/engine.engine'] = {}
        
        # Оптимизация физики и звука для нулевой задержки
        engine_config_new['[/script/engine.engine']['bDisablePhysXHardwareSupport'] = 'False'
        engine_config_new['[/script/engine.engine']['PhysXGpuHeapSize'] = '1'
        engine_config_new['[/script/engine.engine']['bAllowMultiThreadedShaderCompile'] = 'True'
        engine_config_new['[/script/engine.engine']['bUseThreadedRendering'] = 'True'
        engine_config_new['[/script/engine.engine']['bUseThreadedAudio'] = 'True'
        engine_config_new['[/script/engine.engine']['bUseBackgroundLevelStreaming'] = 'True'
        engine_config_new['[/script/engine.engine']['bUseCompressedLightmaps'] = 'True'
        engine_config_new['[/script/engine.engine']['bAllowD3D11'] = 'True'
        engine_config_new['[/script/engine.engine']['bAllowD3D12'] = 'False'
        engine_config_new['[/script/engine.engine']['bDisablePhysX'] = 'False'
        engine_config_new['[/script/engine.engine']['PhysXLevel'] = '0'
        engine_config_new['[/script/engine.engine']['MaxFPS'] = '0'
        
        # МАКСИМАЛЬНАЯ ОПТИМИЗАЦИЯ ДЛЯ НУЛЕВОЙ ЗАДЕРЖКИ - ЧИТЕРСКИЕ НАСТРОЙКИ
        if '[SystemSettings]' not in engine_config_new:
            engine_config_new['[SystemSettings]'] = {}
        system_settings = engine_config_new['[SystemSettings]']
        
        # Максимальный тикрейт для минимальной задержки
        system_settings['NetworkTickRate'] = '128'  # Максимальный сетевой тикрейт
        system_settings['MaxTickRate'] = '0'  # Без ограничений
        system_settings['SmoothedFrameRate'] = 'False'  # Отключение сглаживания
        system_settings['NetServerMaxTickRate'] = '128'  # Максимальный серверный тикрейт
        system_settings['NetClientMaxTickRate'] = '128'  # Максимальный клиентский тикрейт
        
        # Оптимизация физики для минимальной задержки
        system_settings['p.PhysXGpuHeapSize'] = '256'  # Больше памяти для физики
        system_settings['p.MaxSubstepSize'] = '0.02'  # Оптимальный размер подшага
        system_settings['p.MaxSubsteps'] = '4'  # Максимум подшагов для точности
        
        self.merge_ini(self.engine_ini, engine_config_new)
    
    def optimize_audio(self):
        """Оптимизирует звуковые настройки - МАКСИМАЛЬНАЯ СЛЫШИМОСТЬ ШАГОВ И ВЫСТРЕЛОВ"""
        engine_config_new = {}
        
        # Основная секция SystemSettings для звука
        if '[SystemSettings]' not in engine_config_new:
            engine_config_new['[SystemSettings]'] = {}
        system_settings = engine_config_new['[SystemSettings]']
        
        # МАКСИМАЛЬНЫЕ НАСТРОЙКИ ЗВУКА - ЧИТЕРСКИЕ ДЛЯ СЛЫШИМОСТИ ВСЕГО
        system_settings['MaxChannels'] = '128'  # МАКСИМУМ каналов (было 64)
        system_settings['MaxConcurrentStreams'] = '64'  # Максимум потоков (было 32)
        system_settings['SampleRate'] = '48000'  # Высокое качество (48kHz)
        system_settings['bUseAudioThread'] = 'True'
        system_settings['bUseThreadedAudio'] = 'True'
        system_settings['bEnableSpatialization'] = 'True'  # Пространственное звучание
        system_settings['bEnableHRTF'] = 'True'  # HRTF для лучшей локализации
        
        # Увеличенная громкость для слышимости шагов
        system_settings['SoundVolumeMultiplier'] = '2.5'  # Увеличенная громкость звука
        system_settings['VoiceVolumeMultiplier'] = '2.0'  # Увеличенная громкость голоса
        system_settings['SFXVolumeMultiplier'] = '3.0'  # МАКСИМУМ громкости эффектов (шаги, выстрелы)
        
        # Дополнительные настройки звука
        if '[/script/engine.audiodevice' not in engine_config_new:
            engine_config_new['[/script/engine.audiodevice'] = {}
        
        audio_device = engine_config_new['[/script/engine.audiodevice']
        audio_device['MaxChannels'] = '128'
        audio_device['SampleRate'] = '48000'
        audio_device['NumBuffersToEnqueue'] = '8'  # Увеличенный буфер (было 4)
        audio_device['bAllowCenterChannel3DPanning'] = 'True'
        audio_device['SpatializationAlgorithm'] = 'SPATIALIZATION_HRTF'
        audio_device['SoundVolumeMultiplier'] = '2.5'
        audio_device['SFXVolumeMultiplier'] = '3.0'
        
        # Настройки для улучшения качества звука
        if '[/script/engine.engine' not in engine_config_new:
            engine_config_new['[/script/engine.engine'] = {}
        
        engine_config_new['[/script/engine.engine']['bUseThreadedAudio'] = 'True'
        engine_config_new['[/script/engine.engine']['AudioThreadPoolSize'] = '8'  # Увеличенный пул (было 4)
        
        # Настройки звука для PUBG (TslGame) - специфичные для игры
        if '[/script/tslgame.tslgameengine' not in engine_config_new:
            engine_config_new['[/script/tslgame.tslgameengine'] = {}
        
        pubg_engine = engine_config_new['[/script/tslgame.tslgameengine']
        pubg_engine['SoundVolume'] = '2.5'  # Увеличенная громкость
        pubg_engine['MasterVolume'] = '2.5'  # Увеличенная общая громкость
        pubg_engine['SFXVolume'] = '3.0'  # МАКСИМУМ громкости шагов и выстрелов
        pubg_engine['FootstepVolume'] = '3.0'  # Максимальная громкость шагов
        pubg_engine['GunshotVolume'] = '3.0'  # Максимальная громкость выстрелов
        
        # Настройки качества звука
        if '[AudioQualitySettings' not in engine_config_new:
            engine_config_new['[AudioQualitySettings'] = {}
        
        audio_quality = engine_config_new['[AudioQualitySettings']
        audio_quality['MaxChannels'] = '128'
        audio_quality['SampleRate'] = '48000'
        audio_quality['SoundVolumeMultiplier'] = '2.5'
        audio_quality['SFXVolumeMultiplier'] = '3.0'
        
        # Применяем настройки
        self.merge_ini(self.engine_ini, engine_config_new)

