"""
Логика работы таймера
"""

import time
import threading
from datetime import datetime
from typing import Optional


class WorkTimer:
    """Класс для управления таймерами напоминаний"""
    
    def __init__(self, work_interval=30, blink_interval=10, break_duration=5):
        """
        Инициализация таймера
        
        Args:
            work_interval: минут до перерыва (по умолч. 30)
            blink_interval: минут до напоминания о моргании (по умолч. 10)
            break_duration: минут длительность перерыва (по умолч. 5)
        """
        self.work_interval = work_interval * 60  # переводим в секунды
        self.blink_interval = blink_interval * 60
        self.break_duration = break_duration * 60
        
        # Состояние
        self.running = False
        self.paused = False
        self.on_break = False
        
        # Потоки
        self.work_thread = None
        self.blink_thread = None
        
        # Статистика
        self.stats = {
            'breaks_taken': 0,
            'blink_reminders': 0,
            'pauses_count': 0,
            'total_work_seconds': 0
        }
        
        # Время
        self.start_time = None
        self.pause_start = None
        self.total_pause_seconds = 0
    
    def start(self):
        """Запустить таймер"""
        if self.running and not self.paused:
            return
        
        if not self.running:
            self.running = True
            self.start_time = datetime.now()
            self.total_pause_seconds = 0
            
            # Запускаем потоки
            self.work_thread = threading.Thread(target=self._work_loop, daemon=True)
            self.blink_thread = threading.Thread(target=self._blink_loop, daemon=True)
            self.work_thread.start()
            self.blink_thread.start()
        
        elif self.paused:
            self.paused = False
            if self.pause_start:
                self.total_pause_seconds += (datetime.now() - self.pause_start).total_seconds()
    
    def pause(self):
        """Поставить на паузу"""
        if self.running and not self.paused:
            self.paused = True
            self.pause_start = datetime.now()
            self.stats['pauses_count'] += 1
    
    def resume(self):
        """Возобновить работу"""
        if self.running and self.paused:
            self.start()
    
    def stop(self):
        """Остановить таймер"""
        self.running = False
        self.paused = False
        self.on_break = False
        
        # Обновляем статистику
        if self.start_time:
            total_seconds = (datetime.now() - self.start_time).total_seconds()
            self.stats['total_work_seconds'] = int(total_seconds - self.total_pause_seconds)
    
    def _work_loop(self):
        """Основной цикл для напоминаний о перерывах"""
        last_break = datetime.now()
        
        while self.running:
            if not self.paused and not self.on_break:
                elapsed = (datetime.now() - last_break).total_seconds()
                
                if elapsed >= self.work_interval:
                    self._take_break()
                    last_break = datetime.now()
            
            time.sleep(1)
    
    def _blink_loop(self):
        """Цикл для напоминаний о моргании"""
        last_blink = datetime.now()
        
        while self.running:
            if not self.paused and not self.on_break:
                elapsed = (datetime.now() - last_blink).total_seconds()
                
                if elapsed >= self.blink_interval:
                    self._remind_blink()
                    last_blink = datetime.now()
            
            time.sleep(1)
    
    def _take_break(self):
        """Сделать перерыв"""
        self.on_break = True
        self.stats['breaks_taken'] += 1
        
        # Уведомление о начале перерыва
        self._notify(
            "🧘 ПЕРЕРЫВ!",
            f"Встаньте и разомнитесь! {self.break_duration // 60} минут отдыха."
        )
        
        # Ждём окончания перерыва
        time.sleep(self.break_duration)
        
        self.on_break = False
        self._notify("✅ ПЕРЕРЫВ ЗАКОНЧЕН!", "Возвращайтесь к работе!")
    
    def _remind_blink(self):
        """Напомнить моргнуть"""
        self.stats['blink_reminders'] += 1
        self._notify("👁️ НАПОМИНАНИЕ!", "Не забывайте моргать! Это помогает глазам.")
    
    def _notify(self, title, message):
        """Показать уведомление"""
        print(f"\n{'='*50}")
        print(f"🔔 {title}")
        print(f"   {message}")
        print(f"{'='*50}")
        
        # Звуковой сигнал (простейший)
        print('\a')  # системный звук
    
    def get_status(self):
        """Получить статус таймера"""
        if not self.running:
            return "⏹️ Остановлен"
        elif self.paused:
            return "⏸️ На паузе"
        elif self.on_break:
            return "🧘 На перерыве"
        else:
            return "▶️ Работает"
    
    def get_stats(self):
        """Получить статистику"""
        stats_copy = self.stats.copy()
        
        # Форматируем время работы
        hours = stats_copy['total_work_seconds'] // 3600
        minutes = (stats_copy['total_work_seconds'] % 3600) // 60
        stats_copy['work_time'] = f"{hours}ч {minutes}м"
        
        return stats_copy