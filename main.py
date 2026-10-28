#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PUBG Optimizer - Приложение для оптимизации настроек PUBG
"""

import sys
import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QGroupBox, QMessageBox, QFileDialog,
    QProgressBar, QTabWidget, QSpinBox, QComboBox, QScrollArea, QDialog,
    QGraphicsBlurEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap

from pubg_config import PUBGConfigManager
from driver_optimizer import DriverOptimizer
from settings_manager import SettingsManager


class OptimizationThread(QThread):
    """Поток для выполнения оптимизации"""
    progress = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, config_manager, optimizations, driver_optimizer):
        super().__init__()
        self.config_manager = config_manager
        self.optimizations = optimizations
        self.driver_optimizer = driver_optimizer
    
    def run(self):
        try:
            self.progress.emit(10)
            self.config_manager.backup_configs()
            self.progress.emit(30)
            
            # Применяем оптимизации
            if self.optimizations.get('graphics'):
                self.config_manager.optimize_graphics(
                    remove_grass=self.optimizations.get('remove_grass', False),
                    grass_distance=self.optimizations.get('grass_distance', 0),
                    potato_landscape=self.optimizations.get('potato_landscape', False),
                    clear_players=self.optimizations.get('clear_players', True),
                    low_shadows=self.optimizations.get('low_shadows', False),
                    low_effects=self.optimizations.get('low_effects', False),
                    disable_antialiasing=self.optimizations.get('disable_antialiasing', False),
                    uncapped_fps=self.optimizations.get('uncapped_fps', True)
                )
            self.progress.emit(60)
            
            if self.optimizations.get('input'):
                self.config_manager.optimize_input()
            self.progress.emit(80)
            
            if self.optimizations.get('performance'):
                self.config_manager.optimize_performance()
            self.progress.emit(90)
            
            # Устанавливаем высокий приоритет процесса
            self.config_manager.set_high_priority()
            self.progress.emit(95)
            
            # Применяем оптимизации драйверов
            driver_results = []
            if self.optimizations.get('driver_optimization', {}).get('timer_resolution', False):
                result, msg = self.driver_optimizer.optimize_timer_resolution(True)
                if result:
                    driver_results.append("✓ Таймер оптимизирован")
            
            if self.optimizations.get('driver_optimization', {}).get('cpu_affinity', False):
                cores = self.optimizations.get('driver_optimization', {}).get('cpu_cores', 'all')
                result, msg = self.driver_optimizer.set_cpu_affinity("TslGame.exe", cores)
                if result:
                    driver_results.append("✓ CPU Affinity установлен")
            
            if self.optimizations.get('driver_optimization', {}).get('disable_fullscreen_optimizations', False):
                result, msg = self.driver_optimizer.disable_fullscreen_optimizations("TslGame.exe")
                if result:
                    driver_results.append("✓ Fullscreen Optimizations отключены")
            
            if self.optimizations.get('driver_optimization', {}).get('enable_game_mode', False):
                result, msg = self.driver_optimizer.enable_game_mode(True)
                if result:
                    driver_results.append("✓ Игровой режим включен")
            
            if self.optimizations.get('driver_optimization', {}).get('disable_game_bar', False):
                result, msg = self.driver_optimizer.disable_game_bar(True)
                if result:
                    driver_results.append("✓ Game Bar отключен")
            
            if self.optimizations.get('driver_optimization', {}).get('optimize_power_plan', False):
                result, msg = self.driver_optimizer.optimize_power_plan(True)
                if result:
                    driver_results.append("✓ План питания оптимизирован")
            
            if self.optimizations.get('driver_optimization', {}).get('optimize_network', False):
                result, msg = self.driver_optimizer.optimize_network(True)
                if result:
                    driver_results.append("✓ Сеть оптимизирована")
            
            if self.optimizations.get('driver_optimization', {}).get('memory_optimization', False):
                result, msg = self.driver_optimizer.set_memory_optimization(True)
                if result:
                    driver_results.append("✓ Память оптимизирована")
            
            # Применяем оптимизацию звука
            if self.optimizations.get('audio', {}).get('optimize_audio', False):
                self.config_manager.optimize_audio()
            
            self.progress.emit(98)
            
            # Создаем и запускаем скрипт автоматического запуска PUBG с админ правами
            nvidia_script_path = self.config_manager.create_nvidia_optimizer_script()
            
            # Запускаем скрипт автоматически с админ правами
            try:
                import ctypes
                if ctypes.windll.shell32.IsUserAnAdmin():
                    # Если уже админ - запускаем напрямую
                    subprocess.Popen([nvidia_script_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # Запрашиваем админ права через PowerShell
                    ps_launch = f'''
                    Start-Process -FilePath "{nvidia_script_path}" -Verb RunAs -WindowStyle Hidden
                    '''
                    subprocess.run(['powershell', '-Command', ps_launch], timeout=3)
            except Exception as e:
                print(f"Could not auto-launch script: {e}")
            
            self.progress.emit(100)
            
            driver_msg = "\n".join(driver_results) if driver_results else ""
            final_msg = f"Оптимизация успешно завершена!\n\n{driver_msg}\n\nPUBG запускается автоматически с примененными оптимизациями!"
            self.finished.emit(True, final_msg)
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {str(e)}")


class DisclaimerDialog(QDialog):
    """Диалог с дисклеймером при запуске"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ ВНИМАНИЕ - ПРЕДУПРЕЖДЕНИЕ")
        self.setModal(True)
        self.setFixedSize(700, 550)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        # Стиль диалога в стиле glassmorphism
        self.setStyleSheet("""
            QDialog {
                background: rgba(26, 26, 46, 0.95);
                backdrop-filter: blur(30px);
                border-radius: 25px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Заголовок
        title = QLabel("⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ")
        title_font = QFont()
        title_font.setPointSizeF(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                background: rgba(211, 47, 47, 0.2);
                border-radius: 15px;
                padding: 15px;
                border: 2px solid rgba(255, 107, 107, 0.4);
            }
        """)
        layout.addWidget(title)
        
        # Текст дисклеймера
        disclaimer_text = QLabel(
            "ИСПОЛЬЗОВАНИЕ ДАННОГО ПРИЛОЖЕНИЯ НА ВАШУ ОТВЕТСТВЕННОСТЬ\n\n"
            
            "⚠️ ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ:\n\n"
            
            "1. РИСК БЛОКИРОВКИ АККАУНТА\n"
            "   • Изменение конфигурационных файлов игры может привести к блокировке аккаунта\n"
            "   • Античит системы могут распознать изменения как нарушение правил\n"
            "   • Разработчики НЕ НЕСУТ ОТВЕТСТВЕННОСТИ за возможные последствия\n\n"
            
            "2. РАЗЛИЧИЯ В РАБОТЕ\n"
            "   • Функциональность приложения может работать по-разному на разных устройствах\n"
            "   • Результаты оптимизации зависят от конфигурации вашего ПК\n"
            "   • Некоторые функции могут не работать на старых версиях Windows\n\n"
            
            "3. ИСПОЛЬЗОВАНИЕ НА ВАШ РИСК\n"
            "   • Вы используете это приложение на свой собственный риск\n"
            "   • Создавайте резервные копии перед применением изменений\n"
            "   • Рекомендуется тестировать на тестовом аккаунте\n\n"
            
            "Продолжая, вы подтверждаете, что понимаете все риски и принимаете полную ответственность."
        )
        disclaimer_text.setWordWrap(True)
        disclaimer_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        disclaimer_text.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                line-height: 1.6;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        layout.addWidget(disclaimer_text)
        
        # Кнопка ОК с таймером
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("ОК (5)")
        self.ok_button.setEnabled(False)
        self.ok_button.setMinimumSize(200, 50)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background: rgba(100, 100, 100, 0.4);
                backdrop-filter: blur(15px);
                border-radius: 12px;
                padding: 12px 30px;
                color: rgba(255, 255, 255, 0.5);
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:enabled {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.6), stop: 1 rgba(56, 142, 60, 0.6));
                color: white;
                border: 2px solid rgba(76, 175, 80, 0.8);
            }
            QPushButton:enabled:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(86, 185, 90, 0.7), stop: 1 rgba(66, 152, 70, 0.7));
                border: 2px solid rgba(76, 175, 80, 1);
                transform: scale(1.05);
            }
            QPushButton:enabled:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(66, 155, 70, 0.7), stop: 1 rgba(46, 132, 50, 0.7));
            }
        """)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Таймер для отсчета секунд
        self.seconds_left = 5
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_button)
        self.timer.start(1000)  # Каждую секунду
        self.update_button()  # Первое обновление
        
    def update_button(self):
        """Обновляет текст кнопки и разблокирует через 5 секунд"""
        if self.seconds_left > 0:
            self.ok_button.setText(f"ОК ({self.seconds_left})")
            self.seconds_left -= 1
        else:
            self.ok_button.setText("ОК")
            self.ok_button.setEnabled(True)
            self.timer.stop()


class PUBGOptimizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.optimization_thread = None
        self.driver_optimizer = DriverOptimizer()
        self.settings_manager = SettingsManager()
        
        # Сначала инициализируем UI (но не показываем окно)
        self.init_ui()
        
        # Применяем blur эффект к окну перед показом
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(20)
        self.setGraphicsEffect(self.blur_effect)
        
        # Показываем окно (с blur эффектом)
        self.show()
        
        # Показываем дисклеймер (модальный диалог)
        disclaimer = DisclaimerDialog(self)
        result = disclaimer.exec()
        
        # Убираем blur после закрытия дисклеймера
        self.setGraphicsEffect(None)
        
        self.auto_detect_config()
        
    def init_ui(self):
        self.setWindowTitle("PUBG Optimizer v3.0")
        self.setGeometry(100, 100, 900, 750)
        self.setMinimumSize(800, 650)
        
        # Базовый размер окна для масштабирования
        self.base_width = 900
        self.base_height = 750
        
        # Применяем стильный дизайн в стиле iOS с glassmorphism
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1a1a2e, stop: 0.5 #16213e, stop: 1 #0f3460);
            }
            QWidget {
                background: transparent;
            }
        """)
        
        # Центральный виджет с эффектом стекла
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        # Адаптивные отступы будут обновляться при resize
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Сохраняем layout для масштабирования
        self.main_layout = main_layout
        
        # Баннер с изображением
        banner_label = QLabel()
        self.banner_label = banner_label
        banner_label.setAlignment(Qt.AlignCenter)
        banner_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        # Загружаем баннер, если файл существует
        # Поддержка PyInstaller (EXE файл)
        if getattr(sys, 'frozen', False):
            # В EXE файле файлы находятся в sys._MEIPASS
            base_path = Path(sys._MEIPASS)
        else:
            # В обычном режиме - текущая директория
            base_path = Path(".")
        
        banner_path = base_path / "banner.png"
        if not banner_path.exists():
            banner_path = base_path / "banner.jpg"
        
        if banner_path.exists():
            pixmap = QPixmap(str(banner_path))
            # Масштабируем баннер до разумного размера (максимальная ширина 860px, высота пропорционально)
            if pixmap.width() > 860:
                pixmap = pixmap.scaledToWidth(860, Qt.SmoothTransformation)
            banner_label.setPixmap(pixmap)
        else:
            # Если баннера нет, показываем текст как fallback
            banner_label.setText("🎮 PUBG OPTIMIZER")
            banner_label.setStyleSheet("""
                QLabel {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(20px);
                    border-radius: 20px;
                    padding: 20px;
                    color: white;
                    font-weight: bold;
                    font-size: 32px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
            """)
        
        main_layout.addWidget(banner_label)
        
        # Кнопка выбора папки PUBG с эффектом стекла
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(15)
        self.path_label = QLabel("Путь не выбран")
        self.path_label.setWordWrap(True)  # Перенос длинных путей
        self.path_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(20px);
                border-radius: 12px;
                padding: 12px 18px;
                color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.15);
                min-height: 40px;
            }
        """)
        folder_btn = QPushButton("📁 Выбрать папку PUBG")
        folder_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(100, 100, 120, 0.6), stop: 1 rgba(60, 60, 80, 0.6));
                backdrop-filter: blur(20px);
                border-radius: 12px;
                padding: 12px 24px;
                color: white;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(120, 120, 140, 0.7), stop: 1 rgba(80, 80, 100, 0.7));
                border: 1px solid rgba(255, 255, 255, 0.3);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(80, 80, 100, 0.7), stop: 1 rgba(60, 60, 80, 0.7));
            }
        """)
        folder_btn.clicked.connect(self.select_pubg_folder)
        folder_layout.addWidget(self.path_label, 3)
        folder_layout.addWidget(folder_btn, 1)
        main_layout.addLayout(folder_layout)
        
        # Вкладки со стильным дизайном и адаптивным размером
        tabs = QTabWidget()
        self.tabs_widget = tabs  # Сохраняем для масштабирования
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(25px);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 10px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(15px);
                border-radius: 12px;
                padding: 10px 15px;
                margin-right: 6px;
                color: rgba(255, 255, 255, 0.7);
                font-weight: bold;
                font-size: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.4), stop: 1 rgba(56, 142, 60, 0.4));
                backdrop-filter: blur(20px);
                color: white;
                border: 1px solid rgba(76, 175, 80, 0.5);
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        main_layout.addWidget(tabs)
        
        # Вкладка Графика
        graphics_tab = self.create_graphics_tab()
        tabs.addTab(graphics_tab, "🎨 Графика")
        
        # Вкладка Инпута
        input_tab = self.create_input_tab()
        tabs.addTab(input_tab, "⌨️ Инпута")
        
        # Вкладка Производительность
        perf_tab = self.create_performance_tab()
        tabs.addTab(perf_tab, "⚡ Производительность")
        
        # Вкладка Звук
        audio_tab = self.create_audio_tab()
        tabs.addTab(audio_tab, "🔊 Звук")
        
        # Вкладка Драйверы и Система
        driver_tab = self.create_driver_tab()
        tabs.addTab(driver_tab, "🔧 Драйверы")
        
        # Прогресс бар со стилем glassmorphism
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(15px);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                text-align: center;
                color: white;
                font-weight: bold;
                height: 30px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                border-radius: 12px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Кнопки действий
        button_layout = QHBoxLayout()
        
        self.optimize_btn = QPushButton("🚀 Оптимизировать")
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                backdrop-filter: blur(20px);
                border-radius: 18px;
                padding: 18px 30px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(86, 195, 90, 0.9), stop: 1 rgba(66, 162, 70, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.4);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(66, 155, 70, 0.9), stop: 1 rgba(46, 122, 50, 0.9));
            }
            QPushButton:disabled {
                background: rgba(100, 100, 100, 0.3);
                color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.optimize_btn.clicked.connect(self.start_optimization)
        self.optimize_btn.setEnabled(False)
        
        self.restore_btn = QPushButton("↩️ Восстановить")
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 152, 0, 0.8), stop: 1 rgba(230, 137, 0, 0.8));
                backdrop-filter: blur(20px);
                border-radius: 18px;
                padding: 18px 30px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(265, 172, 10, 0.9), stop: 1 rgba(240, 157, 10, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.4);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(235, 142, 0, 0.9), stop: 1 rgba(210, 127, 0, 0.9));
            }
            QPushButton:disabled {
                background: rgba(100, 100, 100, 0.3);
                color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.restore_btn.clicked.connect(self.restore_backup)
        self.restore_btn.setEnabled(False)
        
        button_layout.addWidget(self.optimize_btn)
        button_layout.addWidget(self.restore_btn)
        main_layout.addLayout(button_layout)
        
        # Статус с эффектом стекла
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(15px);
                border-radius: 12px;
                padding: 12px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # Загружаем настройки после создания всех элементов UI
        self.load_settings()
        
        # Подключаем обработчик изменения размера окна для масштабирования текста
        from PySide6.QtCore import QEvent
        self.installEventFilter(self)
        
        # Применяем начальное масштабирование
        self.update_font_scaling()
    
    def auto_detect_config(self):
        """Автоматически определяет путь к конфигурации PUBG"""
        default_path = os.path.join(
            os.path.expanduser("~"),
            "AppData", "Local", "TslGame", "Saved", "Config", "WindowsNoEditor"
        )
        
        if os.path.exists(default_path):
            self.config_manager = PUBGConfigManager(default_path)
            self.path_label.setText(f"✓ Автоматически найдено: {default_path}")
            self.path_label.setStyleSheet("""
                QLabel {
                    background: rgba(76, 175, 80, 0.2);
                    backdrop-filter: blur(20px);
                    border-radius: 12px;
                    padding: 12px 18px;
                    color: rgba(200, 230, 201, 1);
                    border: 1px solid rgba(76, 175, 80, 0.4);
                }
            """)
            self.optimize_btn.setEnabled(True)
            self.restore_btn.setEnabled(True)
            self.status_label.setText("Конфигурация найдена! Можно оптимизировать.")
        else:
            self.status_label.setText("Конфигурация не найдена. Выберите папку вручную.")
        
    def create_graphics_tab(self):
        # Создаем ScrollArea для прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        # Важно: устанавливаем минимальный размер для прокрутки
        widget.setMinimumWidth(600)
        
        # Убрать траву
        grass_group = QGroupBox("🌿 Управление травой")
        grass_group.setStyleSheet("""
            QGroupBox {
                background: rgba(255, 255, 255, 0.06);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 20px;
                margin-top: 10px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background: transparent;
            }
        """)
        grass_layout = QVBoxLayout()
        
        self.remove_grass_cb = QCheckBox("Полностью убрать траву (максимальная производительность)")
        self.remove_grass_cb.setChecked(True)
        self.remove_grass_cb.setToolTip(
            "Полностью удаляет всю траву и листву из игры.\n\n"
            "Эффект:\n"
            "• Враги видны даже в высокой траве\n"
            "• Максимальный FPS за счет снижения нагрузки на GPU\n"
            "• Улучшенная видимость на дальних расстояниях\n\n"
            "Параметры: r.Grass.Enable=0, foliage.CullAll=1"
        )
        self.remove_grass_cb.setStyleSheet("""
            QCheckBox {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                border: 2px solid rgba(76, 175, 80, 0.8);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """)
        self.remove_grass_cb.stateChanged.connect(self.on_grass_option_changed)
        grass_layout.addWidget(self.remove_grass_cb)
        
        self.grass_distance_cb = QCheckBox("Оставить траву на расстояние (метры)")
        self.grass_distance_cb.setChecked(False)
        self.grass_distance_cb.setStyleSheet(self.remove_grass_cb.styleSheet())
        self.grass_distance_cb.setToolTip(
            "Оставляет траву видимой только вблизи (например, 10 метров).\n\n"
            "Эффект:\n"
            "• Трава видна только в радиусе выбранного расстояния\n"
            "• Враги лучше видны на дальних дистанциях\n"
            "• Хороший баланс между производительностью и реализмом\n\n"
            "Рекомендуется: 10-15 метров для оптимального баланса"
        )
        self.grass_distance_cb.stateChanged.connect(self.on_grass_option_changed)
        grass_layout.addWidget(self.grass_distance_cb)
        
        distance_layout = QHBoxLayout()
        distance_layout.setSpacing(10)
        dist_label = QLabel("Расстояние (метры):")
        dist_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 12px;")
        distance_layout.addWidget(dist_label)
        self.grass_distance_spin = QSpinBox()
        self.grass_distance_spin.setRange(5, 50)
        self.grass_distance_spin.setValue(10)
        self.grass_distance_spin.setSuffix(" м")
        self.grass_distance_spin.setEnabled(False)
        self.grass_distance_spin.setToolTip(
            "Расстояние, на котором трава будет видна (в метрах).\n\n"
            "Примеры:\n"
            "• 5 метров - очень близко, почти не видно\n"
            "• 10 метров - оптимально для баланса\n"
            "• 15-20 метров - больше травы, но меньше FPS\n\n"
            "Рекомендуется: 10 метров для оптимального баланса"
        )
        self.grass_distance_spin.setStyleSheet("""
            QSpinBox {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(15px);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 8px 12px;
                color: white;
                font-size: 13px;
            }
            QSpinBox:hover {
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QSpinBox:disabled {
                background: rgba(100, 100, 100, 0.2);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        distance_layout.addWidget(self.grass_distance_spin)
        grass_layout.addLayout(distance_layout)
        
        info_label = QLabel("Выберите: полное удаление ИЛИ оставить на определенное расстояние (например, 10 м)")
        info_label.setWordWrap(True)  # Перенос текста
        info_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        grass_layout.addWidget(info_label)
        
        grass_group.setLayout(grass_layout)
        layout.addWidget(grass_group)
        
        # Ландшафт
        landscape_group = QGroupBox("⛰️ Ландшафт")
        landscape_group.setStyleSheet(grass_group.styleSheet())
        landscape_layout = QVBoxLayout()
        
        self.potato_landscape_cb = QCheckBox("Картофельный ландшафт (низкая детализация)")
        self.potato_landscape_cb.setChecked(True)
        self.potato_landscape_cb.setStyleSheet(self.remove_grass_cb.styleSheet())
        self.potato_landscape_cb.setToolTip(
            "МАКСИМАЛЬНО снижает детализацию ландшафта для максимального FPS.\n\n"
            "Эффект:\n"
            "• Минимальная дальность прорисовки (r.ViewDistanceScale=0.01)\n"
            "• Максимальный LOD bias для ландшафта (LODBias=15)\n"
            "• Картофельный вид ландшафта, но максимальный FPS\n"
            "• Игроки остаются четкими (настройка не влияет)\n\n"
            "Результат: +30-50% FPS на слабых системах"
        )
        landscape_layout.addWidget(self.potato_landscape_cb)
        
        landscape_info = QLabel("МАКСИМАЛЬНОЕ снижение детализации ландшафта")
        landscape_info.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; padding-top: 5px;")
        landscape_layout.addWidget(landscape_info)
        
        landscape_params = QLabel("Параметры: r.ViewDistanceScale=0.01, LODBias=15")
        landscape_params.setStyleSheet("color: rgba(100, 181, 246, 0.9); font-size: 10px; padding-left: 15px;")
        landscape_layout.addWidget(landscape_params)
        
        ultra_potato_label = QLabel("🔥 УЛЬТРА-КАРТОФЕЛЬНЫЙ режим включен!")
        ultra_potato_label.setStyleSheet("""
            color: rgba(255, 107, 107, 1);
            font-size: 12px;
            font-weight: bold;
            padding: 8px;
            background: rgba(211, 47, 47, 0.2);
            border-radius: 8px;
            border: 1px solid rgba(255, 107, 107, 0.3);
        """)
        landscape_layout.addWidget(ultra_potato_label)
        
        landscape_group.setLayout(landscape_layout)
        layout.addWidget(landscape_group)
        
        # Игроки
        players_group = QGroupBox("⚡ Детализация игроков")
        players_group.setStyleSheet(grass_group.styleSheet())
        players_layout = QVBoxLayout()
        
        self.clear_players_cb = QCheckBox("Четкие игроки (высокая детализация моделей)")
        self.clear_players_cb.setChecked(True)
        self.clear_players_cb.setStyleSheet(self.remove_grass_cb.styleSheet())
        self.clear_players_cb.setToolTip(
            "Сохраняет максимальную детализацию моделей игроков.\n\n"
            "Эффект:\n"
            "• CharacterQuality = 4 (максимум)\n"
            "• r.SkeletalMeshLODBias = 0 (максимальная детализация)\n"
            "• Враги всегда четкие и детализированные\n"
            "• Отключены эффекты, мешающие видимости (Bloom, LensFlare, AO)\n"
            "• Улучшенный контраст для лучшей видимости\n\n"
            "Критично для соревновательной игры!"
        )
        players_layout.addWidget(self.clear_players_cb)
        
        players_info = QLabel("Сохраняет высокую детализацию моделей игроков для лучшей видимости")
        players_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        players_layout.addWidget(players_info)
        
        players_group.setLayout(players_layout)
        layout.addWidget(players_group)
        
        # Дополнительные настройки графики
        advanced_group = QGroupBox("⚙️ Дополнительно")
        advanced_group.setStyleSheet(grass_group.styleSheet())
        advanced_layout = QVBoxLayout()
        
        self.low_shadows_cb = QCheckBox("Низкие тени")
        self.low_shadows_cb.setChecked(True)
        self.low_shadows_cb.setStyleSheet(self.remove_grass_cb.styleSheet())
        self.low_shadows_cb.setToolTip(
            "Снижает качество теней для увеличения FPS.\n\n"
            "Эффект:\n"
            "• r.ShadowQuality = 0 (минимальное качество)\n"
            "• r.Shadow.MaxResolution = 64\n"
            "• r.Shadow.DistanceScale = 0.1\n\n"
            "Результат: +10-15% FPS"
        )
        advanced_layout.addWidget(self.low_shadows_cb)
        
        self.low_effects_cb = QCheckBox("Низкие эффекты")
        self.low_effects_cb.setChecked(True)
        self.low_effects_cb.setStyleSheet(self.remove_grass_cb.styleSheet())
        self.low_effects_cb.setToolTip(
            "Снижает качество эффектов (частицы, взрывы и т.д.).\n\n"
            "Эффект:\n"
            "• r.LightFunctionQuality = 0\n"
            "• r.EmitterSpawnRateScale = 0.1\n"
            "• Отключены лишние эффекты постобработки\n\n"
            "Результат: +5-10% FPS в бою"
        )
        advanced_layout.addWidget(self.low_effects_cb)
        
        self.disable_antialiasing_cb = QCheckBox("Отключить сглаживание")
        self.disable_antialiasing_cb.setChecked(True)
        self.disable_antialiasing_cb.setStyleSheet(self.remove_grass_cb.styleSheet())
        self.disable_antialiasing_cb.setToolTip(
            "Полностью отключает сглаживание (Anti-Aliasing).\n\n"
            "Эффект:\n"
            "• r.DefaultFeature.AntiAliasing = 0\n"
            "• r.PostProcessAAQuality = 0\n"
            "• r.FXAA = 0, r.TemporalAA = 0\n\n"
            "Результат: +15-25% FPS, но могут быть заметны \"зубцы\" на краях"
        )
        advanced_layout.addWidget(self.disable_antialiasing_cb)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Uncapped FPS и Rendering
        uncapped_group = QGroupBox("🚀 Uncapped FPS и Rendering")
        uncapped_group.setStyleSheet(grass_group.styleSheet())
        uncapped_layout = QVBoxLayout()
        
        self.uncapped_fps_cb = QCheckBox("Uncapped FPS и Rendering (без ограничений)")
        self.uncapped_fps_cb.setChecked(True)
        self.uncapped_fps_cb.setStyleSheet(self.remove_grass_cb.styleSheet())
        self.uncapped_fps_cb.setToolTip(
            "Полностью снимает все ограничения FPS и рендеринга.\n\n"
            "Эффект:\n"
            "• FrameRateLimit = 0 (без ограничений)\n"
            "• VSync отключен\n"
            "• Динамическое разрешение отключено\n"
            "• Все лимиты FPS сняты\n\n"
            "Результат: Максимальная производительность, FPS зависит только от железа"
        )
        uncapped_layout.addWidget(self.uncapped_fps_cb)
        
        uncapped_info = QLabel("Полностью снимает ограничения FPS и рендеринга для максимальной производительности")
        uncapped_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        uncapped_layout.addWidget(uncapped_info)
        
        uncapped_details = QLabel("• FrameRateLimit = 0\n• VSync отключен\n• Динамическое разрешение отключено\n• Все лимиты FPS сняты")
        uncapped_details.setStyleSheet("color: rgba(100, 181, 246, 0.9); font-size: 10px; padding-left: 15px; padding-top: 5px;")
        uncapped_layout.addWidget(uncapped_details)
        
        uncapped_group.setLayout(uncapped_layout)
        layout.addWidget(uncapped_group)
        
        layout.addStretch()
        
        # Устанавливаем виджет в ScrollArea
        scroll.setWidget(widget)
        return scroll
    
    def on_grass_option_changed(self):
        """Обработка изменения опций травы"""
        if self.remove_grass_cb.isChecked():
            self.grass_distance_cb.setChecked(False)
            self.grass_distance_spin.setEnabled(False)
        elif self.grass_distance_cb.isChecked():
            self.remove_grass_cb.setChecked(False)
            self.grass_distance_spin.setEnabled(True)
    
    def create_audio_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        widget.setMinimumWidth(600)
        
        audio_group = QGroupBox("🔊 Настройки звука")
        audio_group.setStyleSheet("""
            QGroupBox {
                background: rgba(255, 255, 255, 0.06);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 20px;
                margin-top: 10px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background: transparent;
            }
        """)
        audio_layout = QVBoxLayout()
        
        checkbox_style = """
            QCheckBox {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                border: 2px solid rgba(76, 175, 80, 0.8);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """
        
        self.optimize_audio_cb = QCheckBox("Улучшить качество звука")
        self.optimize_audio_cb.setChecked(True)
        self.optimize_audio_cb.setStyleSheet(checkbox_style)
        self.optimize_audio_cb.setToolTip(
            "МАКСИМАЛЬНО улучшает звук для лучшей слышимости шагов и выстрелов.\n\n"
            "Эффект:\n"
            "• MaxChannels = 128 (максимум каналов)\n"
            "• SFXVolumeMultiplier = 3.0 (увеличенная громкость эффектов)\n"
            "• FootstepVolume = 3.0 (максимальная громкость шагов)\n"
            "• GunshotVolume = 3.0 (максимальная громкость выстрелов)\n"
            "• HRTF включен для точной локализации звука\n\n"
            "Результат: Слышимость шагов и выстрелов увеличена в 3 раза!"
        )
        audio_layout.addWidget(self.optimize_audio_cb)
        
        audio_info = QLabel("Оптимизация настроек звука для лучшего качества и позиционирования")
        audio_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        audio_layout.addWidget(audio_info)
        
        audio_details = QLabel("• Увеличение количества каналов до 64\n• Высокое качество (48kHz)\n• Улучшенное позиционирование звука (HRTF)\n• Больше потоков звука")
        audio_details.setStyleSheet("color: rgba(100, 181, 246, 0.9); font-size: 10px; padding-left: 15px; padding-top: 5px;")
        audio_layout.addWidget(audio_details)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def create_input_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        widget.setMinimumWidth(600)
        
        input_group = QGroupBox("⌨️ Настройки инпута")
        input_group.setStyleSheet("""
            QGroupBox {
                background: rgba(255, 255, 255, 0.06);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 20px;
                margin-top: 10px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background: transparent;
            }
        """)
        input_layout = QVBoxLayout()
        
        checkbox_style = """
            QCheckBox {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                border: 2px solid rgba(76, 175, 80, 0.8);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """
        
        self.optimize_input_cb = QCheckBox("Оптимизировать инпута")
        self.optimize_input_cb.setChecked(True)
        self.optimize_input_cb.setStyleSheet(checkbox_style)
        self.optimize_input_cb.setToolTip(
            "Оптимизирует инпут для нулевой задержки.\n\n"
            "Эффект:\n"
            "• bUseMouseSmoothing = False (отключение сглаживания мыши)\n"
            "• bUseRawInput = True (использование raw input)\n"
            "• bUseHighPrecisionMouseInput = True (высокая точность)\n"
            "• bUseMouseAcceleration = False (отключение ускорения)\n"
            "• FrameRateLimit = 0 (uncapped FPS)\n\n"
            "Результат: Мгновенная реакция мыши, минимальная задержка"
        )
        input_layout.addWidget(self.optimize_input_cb)
        
        input_info = QLabel("Оптимизирует задержку ввода и чувствительность мыши")
        input_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        input_layout.addWidget(input_info)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def create_performance_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        widget.setMinimumWidth(600)
        
        perf_group = QGroupBox("⚡ Оптимизация производительности")
        perf_group.setStyleSheet("""
            QGroupBox {
                background: rgba(255, 255, 255, 0.06);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 20px;
                margin-top: 10px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background: transparent;
            }
        """)
        perf_layout = QVBoxLayout()
        
        checkbox_style = """
            QCheckBox {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                border: 2px solid rgba(76, 175, 80, 0.8);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """
        
        self.optimize_perf_cb = QCheckBox("Оптимизировать производительность")
        self.optimize_perf_cb.setChecked(True)
        self.optimize_perf_cb.setStyleSheet(checkbox_style)
        self.optimize_perf_cb.setToolTip(
            "Дополнительные оптимизации производительности.\n\n"
            "Эффект:\n"
            "• Минимальные настройки теней и частиц\n"
            "• Оптимизация физики и звука\n"
            "• Многопоточный рендеринг\n"
            "• Оптимизация текстур и потоков\n\n"
            "Результат: Дополнительные +5-10% FPS"
        )
        perf_layout.addWidget(self.optimize_perf_cb)
        
        perf_info = QLabel("Агрессивные оптимизации + установка высокого приоритета процесса в Windows")
        perf_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        perf_layout.addWidget(perf_info)
        
        priority_info = QLabel("🔧 Приоритет процесса будет установлен на HIGH автоматически")
        priority_info.setStyleSheet("""
            color: rgba(255, 107, 107, 1);
            font-size: 12px;
            font-weight: bold;
            padding: 8px;
            background: rgba(211, 47, 47, 0.2);
            border-radius: 8px;
            border: 1px solid rgba(255, 107, 107, 0.3);
        """)
        perf_layout.addWidget(priority_info)
        
        nvidia_info = QLabel("💡 PUBG запускается автоматически с примененными оптимизациями")
        nvidia_info.setStyleSheet("color: rgba(100, 181, 246, 0.9); font-size: 11px; padding-top: 5px;")
        perf_layout.addWidget(nvidia_info)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def create_driver_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        widget.setMinimumWidth(600)
        
        group_style = """
            QGroupBox {
                background: rgba(255, 255, 255, 0.06);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 20px;
                margin-top: 10px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background: transparent;
            }
        """
        checkbox_style = """
            QCheckBox {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                border: 2px solid rgba(76, 175, 80, 0.8);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """
        
        # Оптимизация таймера
        timer_group = QGroupBox("⏱️ Таймер Windows")
        timer_group.setStyleSheet(group_style)
        timer_layout = QVBoxLayout()
        
        self.timer_resolution_cb = QCheckBox("Оптимизировать разрешение таймера (снижение задержки)")
        self.timer_resolution_cb.setChecked(True)
        self.timer_resolution_cb.setStyleSheet(checkbox_style)
        self.timer_resolution_cb.setToolTip(
            "Оптимизирует разрешение таймера Windows для снижения задержки.\n\n"
            "Эффект:\n"
            "• Устанавливает высокое разрешение таймера (0.5ms)\n"
            "• Снижает задержку ввода\n"
            "• Улучшает плавность игры\n\n"
            "⚠️ Требует прав администратора"
        )
        timer_layout.addWidget(self.timer_resolution_cb)
        
        timer_info = QLabel("Увеличивает точность таймера Windows для плавной игры (требует админа)")
        timer_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        timer_layout.addWidget(timer_info)
        
        timer_group.setLayout(timer_layout)
        layout.addWidget(timer_group)
        
        # CPU Affinity
        cpu_group = QGroupBox("💻 CPU Affinity")
        cpu_group.setStyleSheet(group_style)
        cpu_layout = QVBoxLayout()
        
        self.cpu_affinity_cb = QCheckBox("Установить CPU Affinity")
        self.cpu_affinity_cb.setChecked(True)
        self.cpu_affinity_cb.setStyleSheet(checkbox_style)
        self.cpu_affinity_cb.setToolTip(
            "Привязывает процесс PUBG к определенным ядрам CPU.\n\n"
            "Эффект:\n"
            "• Стабильная производительность\n"
            "• Избежание переключений между ядрами\n"
            "• Оптимизация для многопоточности\n\n"
            "Рекомендуется: 'Все ядра' для максимальной производительности"
        )
        cpu_layout.addWidget(self.cpu_affinity_cb)
        
        cpu_cores_layout = QHBoxLayout()
        cores_label = QLabel("Ядра CPU:")
        cores_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 12px;")
        cpu_cores_layout.addWidget(cores_label)
        self.cpu_cores_combo = QComboBox()
        self.cpu_cores_combo.addItems(["Все ядра", "2 ядра", "4 ядра", "6 ядер", "8 ядер"])
        self.cpu_cores_combo.setToolTip(
            "Выберите количество ядер CPU для привязки процесса PUBG.\n\n"
            "Опции:\n"
            "• Все ядра - максимальная производительность (рекомендуется)\n"
            "• 2-8 ядер - ограничение для стабильности на старых CPU\n\n"
            "Рекомендуется: 'Все ядра' если у вас 4+ ядерный процессор"
        )
        self.cpu_cores_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(15px);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 8px 12px;
                color: white;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 8px;
            }
        """)
        cpu_cores_layout.addWidget(self.cpu_cores_combo)
        cpu_layout.addLayout(cpu_cores_layout)
        
        cpu_info = QLabel("Привязка процесса к определенным ядрам CPU для стабильности")
        cpu_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        cpu_layout.addWidget(cpu_info)
        
        cpu_group.setLayout(cpu_layout)
        layout.addWidget(cpu_group)
        
        # Fullscreen Optimizations
        fs_group = QGroupBox("🖥️ Fullscreen Optimizations")
        fs_group.setStyleSheet(group_style)
        fs_layout = QVBoxLayout()
        
        self.disable_fs_optimizations_cb = QCheckBox("Отключить Fullscreen Optimizations")
        self.disable_fs_optimizations_cb.setChecked(True)
        self.disable_fs_optimizations_cb.setToolTip(
            "Отключает оптимизации полноэкранного режима Windows.\n\n"
            "Эффект:\n"
            "• Снижает задержку ввода в полноэкранном режиме\n"
            "• Улучшает производительность\n"
            "• Убирает дополнительные обработки Windows\n\n"
            "⚠️ Требует прав администратора"
        )
        self.disable_fs_optimizations_cb.setStyleSheet(checkbox_style)
        fs_layout.addWidget(self.disable_fs_optimizations_cb)
        
        fs_info = QLabel("Отключает оптимизации Windows для полноэкранного режима (меньше задержка)")
        fs_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        fs_layout.addWidget(fs_info)
        
        fs_group.setLayout(fs_layout)
        layout.addWidget(fs_group)
        
        # Game Mode
        game_mode_group = QGroupBox("🎮 Игровой режим Windows")
        game_mode_group.setStyleSheet(group_style)
        game_mode_layout = QVBoxLayout()
        
        self.enable_game_mode_cb = QCheckBox("Включить игровой режим")
        self.enable_game_mode_cb.setChecked(True)
        self.enable_game_mode_cb.setStyleSheet(checkbox_style)
        self.enable_game_mode_cb.setToolTip(
            "Включает игровой режим Windows для оптимизации.\n\n"
            "Эффект:\n"
            "• Приоритет ресурсов для игры\n"
            "• Отключение фоновых процессов\n"
            "• Улучшенная производительность\n\n"
            "Результат: +5-10% FPS"
        )
        game_mode_layout.addWidget(self.enable_game_mode_cb)
        
        self.disable_game_bar_cb = QCheckBox("Отключить Game Bar")
        self.disable_game_bar_cb.setChecked(True)
        self.disable_game_bar_cb.setStyleSheet(checkbox_style)
        self.disable_game_bar_cb.setToolTip(
            "Отключает Windows Game Bar.\n\n"
            "Эффект:\n"
            "• Освобождает ресурсы\n"
            "• Убирает фоновые процессы\n"
            "• Немного улучшает FPS\n\n"
            "Результат: Небольшое улучшение производительности"
        )
        game_mode_layout.addWidget(self.disable_game_bar_cb)
        
        game_mode_info = QLabel("Оптимизирует Windows для игр")
        game_mode_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        game_mode_layout.addWidget(game_mode_info)
        
        game_mode_group.setLayout(game_mode_layout)
        layout.addWidget(game_mode_group)
        
        # План питания
        power_group = QGroupBox("⚡ План питания")
        power_group.setStyleSheet(group_style)
        power_layout = QVBoxLayout()
        
        self.optimize_power_plan_cb = QCheckBox("Оптимизировать план питания (High Performance)")
        self.optimize_power_plan_cb.setChecked(True)
        self.optimize_power_plan_cb.setStyleSheet(checkbox_style)
        self.optimize_power_plan_cb.setToolTip(
            "Устанавливает план питания на High Performance.\n\n"
            "Эффект:\n"
            "• Максимальная производительность CPU\n"
            "• Отключение энергосбережения\n"
            "• Стабильные частоты процессора\n\n"
            "Результат: Стабильный FPS без просадок"
        )
        power_layout.addWidget(self.optimize_power_plan_cb)
        
        power_info = QLabel("Устанавливает режим высокой производительности (требует админа)")
        power_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        power_layout.addWidget(power_info)
        
        power_group.setLayout(power_layout)
        layout.addWidget(power_group)
        
        # Сеть
        network_group = QGroupBox("🌐 Сеть")
        network_group.setStyleSheet(group_style)
        network_layout = QVBoxLayout()
        
        self.optimize_network_cb = QCheckBox("Оптимизировать сетевые настройки")
        self.optimize_network_cb.setChecked(True)
        self.optimize_network_cb.setStyleSheet(checkbox_style)
        self.optimize_network_cb.setToolTip(
            "Оптимизирует сетевые настройки TCP для снижения задержки.\n\n"
            "Эффект:\n"
            "• Оптимизация TCP настроек\n"
            "• Отключение Auto-Tuning\n"
            "• Снижение сетевой задержки\n\n"
            "Результат: Чуть более стабильный пинг"
        )
        network_layout.addWidget(self.optimize_network_cb)
        
        network_info = QLabel("Оптимизация TCP для снижения задержки (требует админа)")
        network_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        network_layout.addWidget(network_info)
        
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)
        
        # Память
        memory_group = QGroupBox("🧠 Память")
        memory_group.setStyleSheet(group_style)
        memory_layout = QVBoxLayout()
        
        self.memory_optimization_cb = QCheckBox("Оптимизация памяти")
        self.memory_optimization_cb.setChecked(True)
        self.memory_optimization_cb.setStyleSheet(checkbox_style)
        self.memory_optimization_cb.setToolTip(
            "Оптимизирует использование памяти процессом PUBG.\n\n"
            "Эффект:\n"
            "• Улучшенное управление памятью\n"
            "• Снижение утечек памяти\n"
            "• Оптимизация подсистемы памяти Windows\n\n"
            "Результат: Более стабильная работа игры"
        )
        memory_layout.addWidget(self.memory_optimization_cb)
        
        memory_info = QLabel("Оптимизация использования памяти процесса")
        memory_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; padding-top: 5px;")
        memory_layout.addWidget(memory_info)
        
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)
        
        admin_warning = QLabel("⚠️ Некоторые оптимизации требуют прав администратора")
        admin_warning.setStyleSheet("""
            color: rgba(255, 152, 0, 1);
            font-size: 12px;
            font-weight: bold;
            padding: 10px;
            background: rgba(255, 152, 0, 0.2);
            border-radius: 10px;
            border: 1px solid rgba(255, 152, 0, 0.4);
        """)
        layout.addWidget(admin_warning)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        settings = self.settings_manager.load_settings()
        
        # Графика
        if 'graphics' in settings:
            self.remove_grass_cb.setChecked(settings['graphics'].get('remove_grass', True))
            grass_dist = settings['graphics'].get('grass_distance', 0)
            if grass_dist > 0:
                self.grass_distance_cb.setChecked(True)
                self.grass_distance_spin.setValue(grass_dist)
                self.remove_grass_cb.setChecked(False)
            else:
                self.grass_distance_cb.setChecked(False)
            self.potato_landscape_cb.setChecked(settings['graphics'].get('potato_landscape', True))
            self.clear_players_cb.setChecked(settings['graphics'].get('clear_players', True))
            self.low_shadows_cb.setChecked(settings['graphics'].get('low_shadows', True))
            self.low_effects_cb.setChecked(settings['graphics'].get('low_effects', True))
            self.disable_antialiasing_cb.setChecked(settings['graphics'].get('disable_antialiasing', True))
            self.uncapped_fps_cb.setChecked(settings['graphics'].get('uncapped_fps', True))
        
        # Звук
        if 'audio' in settings:
            self.optimize_audio_cb.setChecked(settings['audio'].get('optimize_audio', True))
        
        # Инпута
        if 'input' in settings:
            self.optimize_input_cb.setChecked(settings['input'].get('optimize_input', True))
        
        # Производительность
        if 'performance' in settings:
            self.optimize_perf_cb.setChecked(settings['performance'].get('optimize_performance', True))
        
        # Драйверы
        if 'driver_optimization' in settings:
            driver = settings['driver_optimization']
            self.timer_resolution_cb.setChecked(driver.get('timer_resolution', True))
            self.cpu_affinity_cb.setChecked(driver.get('cpu_affinity', True))
            cpu_cores = driver.get('cpu_cores', 'all')
            if cpu_cores == 'all':
                self.cpu_cores_combo.setCurrentIndex(0)
            else:
                cores_map = {'2': 1, '4': 2, '6': 3, '8': 4}
                self.cpu_cores_combo.setCurrentIndex(cores_map.get(str(cpu_cores), 0))
            self.disable_fs_optimizations_cb.setChecked(driver.get('disable_fullscreen_optimizations', True))
            self.enable_game_mode_cb.setChecked(driver.get('enable_game_mode', True))
            self.disable_game_bar_cb.setChecked(driver.get('disable_game_bar', True))
            self.optimize_power_plan_cb.setChecked(driver.get('optimize_power_plan', True))
            self.optimize_network_cb.setChecked(driver.get('optimize_network', True))
            self.memory_optimization_cb.setChecked(driver.get('memory_optimization', True))
    
    def save_settings(self):
        """Сохраняет текущие настройки"""
        settings = {
            'graphics': {
                'remove_grass': self.remove_grass_cb.isChecked(),
                'grass_distance': self.grass_distance_spin.value() if self.grass_distance_cb.isChecked() else 0,
                'potato_landscape': self.potato_landscape_cb.isChecked(),
                'clear_players': self.clear_players_cb.isChecked(),
                'low_shadows': self.low_shadows_cb.isChecked(),
                'low_effects': self.low_effects_cb.isChecked(),
                'disable_antialiasing': self.disable_antialiasing_cb.isChecked(),
                'uncapped_fps': self.uncapped_fps_cb.isChecked()
            },
            'audio': {
                'optimize_audio': self.optimize_audio_cb.isChecked()
            },
            'input': {
                'optimize_input': self.optimize_input_cb.isChecked()
            },
            'performance': {
                'optimize_performance': self.optimize_perf_cb.isChecked()
            },
            'driver_optimization': {
                'timer_resolution': self.timer_resolution_cb.isChecked(),
                'cpu_affinity': self.cpu_affinity_cb.isChecked(),
                'cpu_cores': ['all', '2', '4', '6', '8'][self.cpu_cores_combo.currentIndex()],
                'disable_fullscreen_optimizations': self.disable_fs_optimizations_cb.isChecked(),
                'enable_game_mode': self.enable_game_mode_cb.isChecked(),
                'disable_game_bar': self.disable_game_bar_cb.isChecked(),
                'optimize_power_plan': self.optimize_power_plan_cb.isChecked(),
                'optimize_network': self.optimize_network_cb.isChecked(),
                'memory_optimization': self.memory_optimization_cb.isChecked()
            }
        }
        if self.config_manager:
            settings['last_config_path'] = str(self.config_manager.config_path)
        self.settings_manager.save_settings(settings)
    
    def select_pubg_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку установки PUBG (например: C:\\Program Files (x86)\\Steam\\steamapps\\common\\PUBG)",
            "C:\\Program Files (x86)\\Steam\\steamapps\\common"
        )
        
        # Всегда используем стандартный путь к конфигурации Windows
        default_path = os.path.join(
            os.path.expanduser("~"),
            "AppData", "Local", "TslGame", "Saved", "Config", "WindowsNoEditor"
        )
        
        # Пытаемся найти конфигурационные файлы в указанной папке
        config_paths = [
            os.path.join(folder, "TslGame", "Saved", "Config", "WindowsNoEditor"),
            os.path.join(folder, "Engine", "Config"),
        ]
        
        found_path = None
        if os.path.exists(default_path):
            found_path = default_path
        else:
            # Пробуем указанную папку
            for path in config_paths:
                if os.path.exists(path):
                    found_path = path
                    break
        
        # Используем найденный путь или стандартный
        if found_path:
            self.config_manager = PUBGConfigManager(found_path)
            self.path_label.setText(f"✓ Конфигурация найдена: {found_path}")
            self.path_label.setStyleSheet("padding: 8px; background: #d4edda; border-radius: 4px; color: #155724;")
        else:
            # Используем стандартный путь (создадим при необходимости)
            self.config_manager = PUBGConfigManager(default_path)
            self.path_label.setText(f"✓ Будет использовано: {default_path}")
            self.path_label.setStyleSheet("padding: 8px; background: #fff3cd; border-radius: 4px; color: #856404;")
        
        self.optimize_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        self.status_label.setText("✓ Конфигурация готова! Нажмите 'Оптимизировать' для максимального FPS!")
    
    def start_optimization(self):
        if not self.config_manager:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку с PUBG!")
            return
        
        # Сохраняем настройки перед оптимизацией
        self.save_settings()
        
        cpu_cores_map = {'Все ядра': 'all', '2 ядра': '2', '4 ядра': '4', '6 ядер': '6', '8 ядер': '8'}
        cpu_cores = cpu_cores_map.get(self.cpu_cores_combo.currentText(), 'all')
        
        # Определяем, что делать с травой
        grass_distance = 0
        remove_grass = True  # По умолчанию полное удаление
        if self.grass_distance_cb.isChecked() and not self.remove_grass_cb.isChecked():
            grass_distance = self.grass_distance_spin.value()
            remove_grass = False  # Если выбрано расстояние, не удаляем полностью
        elif self.remove_grass_cb.isChecked():
            remove_grass = True
            grass_distance = 0
        
        optimizations = {
            'graphics': True,
            'remove_grass': remove_grass,
            'grass_distance': grass_distance,
            'potato_landscape': self.potato_landscape_cb.isChecked(),
            'clear_players': self.clear_players_cb.isChecked(),
            'low_shadows': self.low_shadows_cb.isChecked(),
            'low_effects': self.low_effects_cb.isChecked(),
            'disable_antialiasing': self.disable_antialiasing_cb.isChecked(),
            'uncapped_fps': self.uncapped_fps_cb.isChecked(),
            'audio': {
                'optimize_audio': self.optimize_audio_cb.isChecked()
            },
            'input': self.optimize_input_cb.isChecked(),
            'performance': self.optimize_perf_cb.isChecked(),
            'driver_optimization': {
                'timer_resolution': self.timer_resolution_cb.isChecked(),
                'cpu_affinity': self.cpu_affinity_cb.isChecked(),
                'cpu_cores': cpu_cores,
                'disable_fullscreen_optimizations': self.disable_fs_optimizations_cb.isChecked(),
                'enable_game_mode': self.enable_game_mode_cb.isChecked(),
                'disable_game_bar': self.disable_game_bar_cb.isChecked(),
                'optimize_power_plan': self.optimize_power_plan_cb.isChecked(),
                'optimize_network': self.optimize_network_cb.isChecked(),
                'memory_optimization': self.memory_optimization_cb.isChecked()
            }
        }
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.optimize_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.status_label.setText("Оптимизация в процессе...")
        
        self.optimization_thread = OptimizationThread(self.config_manager, optimizations, self.driver_optimizer)
        self.optimization_thread.progress.connect(self.progress_bar.setValue)
        self.optimization_thread.finished.connect(self.on_optimization_finished)
        self.optimization_thread.start()
    
    def on_optimization_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.optimize_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Успех", message)
            self.status_label.setText("✓ Оптимизация завершена успешно!")
        else:
            QMessageBox.critical(self, "Ошибка", message)
            self.status_label.setText("✗ Ошибка при оптимизации")
    
    def restore_backup(self):
        if not self.config_manager:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку с PUBG!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите восстановить резервные копии?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.config_manager.restore_backup()
                QMessageBox.information(self, "Успех", "Резервные копии восстановлены!")
                self.status_label.setText("✓ Конфигурация восстановлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось восстановить: {str(e)}")
                self.status_label.setText("✗ Ошибка восстановления")
    
    def eventFilter(self, obj, event):
        """Обработчик событий для масштабирования текста при изменении размера окна"""
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Resize and obj == self:
            self.update_font_scaling()
        return super().eventFilter(obj, event)
    
    def get_font_scale(self):
        """Вычисляет коэффициент масштабирования шрифта на основе размера окна"""
        current_width = self.width()
        current_height = self.height()
        
        # Используем более точную формулу на основе ширины (важнее для текста)
        scale_x = current_width / self.base_width
        scale_y = current_height / self.base_height
        # Приоритет ширине, так как текст обычно обрезается по ширине
        scale = scale_x * 0.7 + scale_y * 0.3
        
        # Ограничиваем масштаб для предотвращения слишком маленьких/больших шрифтов
        scale = max(0.7, min(1.4, scale))
        
        return scale
    
    def update_font_scaling(self):
        """Обновляет размеры шрифтов всех элементов интерфейса"""
        scale = self.get_font_scale()
        current_width = self.width()
        current_height = self.height()
        
        # Обновляем отступы layout для адаптации
        if hasattr(self, 'centralWidget'):
            main_layout = self.centralWidget().layout()
            if main_layout:
                # Адаптивные отступы
                margin = max(15, int(30 * (current_width / self.base_width)))
                main_layout.setContentsMargins(margin, margin, margin, margin)
        
        # Масштабируем баннер
        if hasattr(self, 'banner_label'):
            # Поддержка PyInstaller (EXE файл)
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(".")
            
            banner_path = base_path / "banner.png"
            if not banner_path.exists():
                banner_path = base_path / "banner.jpg"
            
            if banner_path.exists():
                pixmap = QPixmap(str(banner_path))
                # Масштабируем баннер в зависимости от размера окна
                max_width = int(min(current_width - 60, 860))
                if pixmap.width() > max_width:
                    pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)
                self.banner_label.setPixmap(pixmap)
                self.banner_label.setScaledContents(False)  # Отключаем авто-масштабирование
        
        # Масштабируем кнопки
        if hasattr(self, 'optimize_btn'):
            btn_base_size = 16 if current_width > 900 else 14 if current_width > 700 else 13
            btn_font_size = int(btn_base_size * scale)
            self.optimize_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(76, 175, 80, 0.8), stop: 1 rgba(56, 142, 60, 0.8));
                    backdrop-filter: blur(20px);
                    border-radius: 18px;
                    padding: 18px 30px;
                    color: white;
                    font-size: {btn_font_size}px;
                    font-weight: bold;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    min-width: 150px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(86, 195, 90, 0.9), stop: 1 rgba(66, 162, 70, 0.9));
                    border: 1px solid rgba(255, 255, 255, 0.4);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(66, 155, 70, 0.9), stop: 1 rgba(46, 122, 50, 0.9));
                }}
                QPushButton:disabled {{
                    background: rgba(100, 100, 100, 0.3);
                    color: rgba(255, 255, 255, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }}
            """)
        
        if hasattr(self, 'restore_btn'):
            btn_base_size = 16 if current_width > 900 else 14 if current_width > 700 else 13
            btn_font_size = int(btn_base_size * scale)
            self.restore_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(255, 152, 0, 0.8), stop: 1 rgba(230, 137, 0, 0.8));
                    backdrop-filter: blur(20px);
                    border-radius: 18px;
                    padding: 18px 30px;
                    color: white;
                    font-size: {btn_font_size}px;
                    font-weight: bold;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    min-width: 150px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(265, 172, 10, 0.9), stop: 1 rgba(240, 157, 10, 0.9));
                    border: 1px solid rgba(255, 255, 255, 0.4);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(235, 142, 0, 0.9), stop: 1 rgba(210, 127, 0, 0.9));
                }}
                QPushButton:disabled {{
                    background: rgba(100, 100, 100, 0.3);
                    color: rgba(255, 255, 255, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }}
            """)
        
        # Обновляем размер path_label с переносом текста
        if hasattr(self, 'path_label'):
            path_font_size = int(12 * scale) if current_width > 900 else int(11 * scale) if current_width > 700 else int(10 * scale)
            self.path_label.setWordWrap(True)  # Включаем перенос для длинных путей
            self.path_label.setStyleSheet(f"""
                QLabel {{
                    background: rgba(255, 255, 255, 0.08);
                    backdrop-filter: blur(20px);
                    border-radius: 12px;
                    padding: 12px 18px;
                    color: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    font-size: {path_font_size}px;
                    min-height: 40px;
                }}
            """)
        
        # Масштабируем вкладки
        if hasattr(self, 'tabs_widget'):
            tab_font_size = int(12 * scale) if current_width > 900 else int(11 * scale) if current_width > 700 else int(10 * scale)
            self.tabs_widget.setStyleSheet(f"""
                QTabWidget::pane {{
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(25px);
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    padding: 10px;
                }}
                QTabBar::tab {{
                    background: rgba(255, 255, 255, 0.08);
                    backdrop-filter: blur(15px);
                    border-radius: 12px;
                    padding: 10px 15px;
                    margin-right: 6px;
                    color: rgba(255, 255, 255, 0.7);
                    font-weight: bold;
                    font-size: {tab_font_size}px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    min-width: 80px;
                }}
                QTabBar::tab:selected {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(76, 175, 80, 0.4), stop: 1 rgba(56, 142, 60, 0.4));
                    backdrop-filter: blur(20px);
                    color: white;
                    border: 1px solid rgba(76, 175, 80, 0.5);
                }}
                QTabBar::tab:hover:!selected {{
                    background: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
            """)
        
        # Масштабируем все информационные метки через рекурсивный обход
        self._scale_widget_fonts(self.centralWidget(), scale)
    
    def _scale_widget_fonts(self, widget, scale):
        """Рекурсивно масштабирует шрифты всех виджетов"""
        if widget is None:
            return
        
        try:
            current_width = self.width()
            
            # Масштабируем стили виджета если это QLabel
            if isinstance(widget, QLabel) and hasattr(widget, 'styleSheet'):
                # Включаем перенос текста для длинных меток
                widget.setWordWrap(True)
                
                stylesheet = widget.styleSheet()
                if stylesheet and 'font-size' in stylesheet:
                    import re
                    def scale_font(match):
                        size = float(match.group(1))
                        # Адаптивный размер на основе ширины окна
                        if current_width < 700:
                            size = size * 0.9
                        elif current_width > 1200:
                            size = size * 1.1
                        new_size = int(size * scale)
                        return f"font-size: {new_size}px"
                    
                    stylesheet = re.sub(r'font-size:\s*(\d+(?:\.\d+)?)px', scale_font, stylesheet)
                    widget.setStyleSheet(stylesheet)
            
            # Рекурсивно обрабатываем дочерние виджеты
            if hasattr(widget, 'children'):
                for child in widget.children():
                    if isinstance(child, QWidget):
                        self._scale_widget_fonts(child, scale)
            
            # Также обрабатываем элементы в layout
            if hasattr(widget, 'layout') and widget.layout():
                self._scale_layout_fonts(widget.layout(), scale)
        except Exception:
            pass  # Игнорируем ошибки при масштабировании
    
    def _scale_layout_fonts(self, layout, scale):
        """Рекурсивно масштабирует шрифты виджетов в layout"""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item:
                widget_item = item.widget()
                if widget_item:
                    self._scale_widget_fonts(widget_item, scale)
                elif item.layout():
                    self._scale_layout_fonts(item.layout(), scale)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Создаем и показываем окно (оно покажет дисклеймер при инициализации)
    window = PUBGOptimizerApp()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

