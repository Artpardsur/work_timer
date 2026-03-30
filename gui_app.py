"""
Work Timer - Профессиональное приложение с графическим интерфейсом
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import sys
import os


class WorkTimerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Work Timer - Забота о здоровье")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # Устанавливаем иконку (если есть)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Настройки таймера
        self.work_interval = 30 * 60  # 30 минут в секундах
        self.blink_interval = 10 * 60  # 10 минут
        self.break_duration = 5 * 60   # 5 минут
        
        # Состояние
        self.running = False
        self.paused = False
        self.on_break = False
        
        # Статистика
        self.breaks_taken = 0
        self.blink_reminders = 0
        self.pauses_count = 0
        self.start_time = None
        self.total_pause_seconds = 0
        self.pause_start = None
        
        # Создаём интерфейс
        self.setup_ui()
        
        # Запускаем обновление времени
        self.update_time_display()
        
    def setup_ui(self):
        """Создаёт интерфейс"""
        # Основной цвет
        self.bg_color = "#f0f0f0"
        self.root.configure(bg=self.bg_color)
        
        # Заголовок
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🧘 WORK TIMER",
            font=("Segoe UI", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)
        
        subtitle = tk.Label(
            title_frame,
            text="Забота о здоровье программиста",
            font=("Segoe UI", 10),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        subtitle.pack()
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Статус
        self.status_label = tk.Label(
            main_frame,
            text="⏹️ Остановлен",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_color,
            fg="#7f8c8d"
        )
        self.status_label.pack(pady=10)
        
        # Таймер обратного отсчёта
        self.countdown_label = tk.Label(
            main_frame,
            text="До следующего напоминания:\n--:--",
            font=("Segoe UI", 14),
            bg=self.bg_color,
            fg="#34495e"
        )
        self.countdown_label.pack(pady=10)
        
        # Кнопки управления
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        self.start_btn = tk.Button(
            button_frame,
            text="▶️ Старт",
            font=("Segoe UI", 12),
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=10,
            command=self.start_timer
        )
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.pause_btn = tk.Button(
            button_frame,
            text="⏸️ Пауза",
            font=("Segoe UI", 12),
            bg="#f39c12",
            fg="white",
            padx=20,
            pady=10,
            command=self.pause_timer,
            state="disabled"
        )
        self.pause_btn.grid(row=0, column=1, padx=5)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹️ Стоп",
            font=("Segoe UI", 12),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=10,
            command=self.stop_timer,
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        # Статистика
        stats_frame = tk.LabelFrame(
            main_frame,
            text="📊 Статистика",
            font=("Segoe UI", 12, "bold"),
            bg=self.bg_color,
            fg="#2c3e50",
            padx=15,
            pady=10
        )
        stats_frame.pack(fill="x", pady=10)
        
        self.stats_text = tk.Text(
            stats_frame,
            height=6,
            font=("Consolas", 10),
            bg=self.bg_color,
            fg="#2c3e50",
            borderwidth=0
        )
        self.stats_text.pack(fill="x")
        self.stats_text.insert("1.0", "⏱️ Время работы: 0ч 0м\n🔄 Перерывов: 0\n👁️ Морганий: 0\n⏸️ Пауз: 0")
        self.stats_text.config(state="disabled")
        
        # Настройки
        settings_frame = tk.LabelFrame(
            main_frame,
            text="⚙️ Настройки",
            font=("Segoe UI", 12, "bold"),
            bg=self.bg_color,
            fg="#2c3e50",
            padx=15,
            pady=10
        )
        settings_frame.pack(fill="x", pady=10)
        
        # Интервалы
        row = 0
        tk.Label(settings_frame, text="Перерывы каждые:", bg=self.bg_color).grid(row=row, column=0, sticky="w", pady=2)
        self.work_var = tk.StringVar(value="30")
        work_entry = tk.Entry(settings_frame, textvariable=self.work_var, width=8)
        work_entry.grid(row=row, column=1, padx=5)
        tk.Label(settings_frame, text="минут", bg=self.bg_color).grid(row=row, column=2, sticky="w")
        
        row += 1
        tk.Label(settings_frame, text="Моргать каждые:", bg=self.bg_color).grid(row=row, column=0, sticky="w", pady=2)
        self.blink_var = tk.StringVar(value="10")
        blink_entry = tk.Entry(settings_frame, textvariable=self.blink_var, width=8)
        blink_entry.grid(row=row, column=1, padx=5)
        tk.Label(settings_frame, text="минут", bg=self.bg_color).grid(row=row, column=2, sticky="w")
        
        row += 1
        tk.Label(settings_frame, text="Длительность перерыва:", bg=self.bg_color).grid(row=row, column=0, sticky="w", pady=2)
        self.break_var = tk.StringVar(value="5")
        break_entry = tk.Entry(settings_frame, textvariable=self.break_var, width=8)
        break_entry.grid(row=row, column=1, padx=5)
        tk.Label(settings_frame, text="минут", bg=self.bg_color).grid(row=row, column=2, sticky="w")
        
        save_btn = tk.Button(
            settings_frame,
            text="Сохранить",
            font=("Segoe UI", 9),
            bg="#3498db",
            fg="white",
            command=self.save_settings
        )
        save_btn.grid(row=3, column=1, pady=10)
        
    def start_timer(self):
        """Запускает таймер"""
        if self.running:
            return
        
        self.running = True
        self.paused = False
        self.start_time = datetime.now()
        self.total_pause_seconds = 0
        
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        
        # Запускаем фоновые потоки
        self.work_thread = threading.Thread(target=self._work_loop, daemon=True)
        self.blink_thread = threading.Thread(target=self._blink_loop, daemon=True)
        self.work_thread.start()
        self.blink_thread.start()
        
        self.update_status()
    
    def pause_timer(self):
        """Ставит на паузу"""
        if not self.running or self.paused:
            return
        
        self.paused = True
        self.pause_start = datetime.now()
        self.pauses_count += 1
        self.update_stats()
        self.update_status()
        
        self.pause_btn.config(state="disabled")
        self.start_btn.config(state="normal")
    
    def resume_timer(self):
        """Возобновляет работу"""
        if not self.running or not self.paused:
            return
        
        self.paused = False
        if self.pause_start:
            self.total_pause_seconds += (datetime.now() - self.pause_start).total_seconds()
        
        self.pause_btn.config(state="normal")
        self.start_btn.config(state="disabled")
        self.update_status()
    
    def stop_timer(self):
        """Останавливает таймер"""
        self.running = False
        self.paused = False
        self.on_break = False
        
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        
        self.update_status()
    
    def _work_loop(self):
        """Цикл напоминаний о перерывах"""
        last_break = datetime.now()
        
        while self.running:
            if not self.paused and not self.on_break:
                elapsed = (datetime.now() - last_break).total_seconds()
                if elapsed >= self.work_interval:
                    self._take_break()
                    last_break = datetime.now()
            time.sleep(1)
    
    def _blink_loop(self):
        """Цикл напоминаний о моргании"""
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
        self.breaks_taken += 1
        self.update_stats()
        
        self._notify("🧘 ПЕРЕРЫВ!", f"Встаньте и разомнитесь! {self.break_duration // 60} минут отдыха.")
        
        start_break = time.time()
        while self.on_break and (time.time() - start_break) < self.break_duration:
            time.sleep(0.5)
            if not self.running or self.paused:
                break
        
        self.on_break = False
        
        if self.running and not self.paused:
            self._notify("✅ ПЕРЕРЫВ ЗАКОНЧЕН!", "Возвращайтесь к работе!")
    
    def _remind_blink(self):
        """Напомнить моргнуть"""
        self.blink_reminders += 1
        self.update_stats()
        self._notify("👁️ НАПОМИНАНИЕ!", "Не забывайте моргать! Это помогает глазам.")
    
    def _notify(self, title, message):
        """Показывает уведомление"""
        # Всплывающее окно
        messagebox.showinfo(title, message)
        
        # Звук
        print('\a')
    
    def update_status(self):
        """Обновляет статус в интерфейсе"""
        if not self.running:
            status = "⏹️ Остановлен"
            color = "#7f8c8d"
        elif self.paused:
            status = "⏸️ На паузе"
            color = "#f39c12"
        elif self.on_break:
            status = "🧘 На перерыве"
            color = "#e74c3c"
        else:
            status = "▶️ Работает"
            color = "#27ae60"
        
        self.status_label.config(text=status, fg=color)
        self.root.after(0, lambda: self.status_label.update())
    
    def update_time_display(self):
        """Обновляет отображение времени"""
        if self.running and not self.paused and not self.on_break and self.start_time:
            # Считаем время до следующего напоминания
            elapsed = (datetime.now() - self.start_time).total_seconds() - self.total_pause_seconds
            remaining = self.work_interval - (elapsed % self.work_interval)
            
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            self.countdown_label.config(text=f"До следующего напоминания:\n{minutes:02d}:{seconds:02d}")
        
        self.root.after(1000, self.update_time_display)
    
    def update_stats(self):
        """Обновляет статистику"""
        if self.running and not self.paused and self.start_time:
            work_seconds = (datetime.now() - self.start_time).total_seconds() - self.total_pause_seconds
        else:
            work_seconds = 0
        
        hours = int(work_seconds // 3600)
        minutes = int((work_seconds % 3600) // 60)
        
        stats_text = f"⏱️ Время работы: {hours}ч {minutes}м\n"
        stats_text += f"🔄 Перерывов: {self.breaks_taken}\n"
        stats_text += f"👁️ Морганий: {self.blink_reminders}\n"
        stats_text += f"⏸️ Пауз: {self.pauses_count}"
        
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
        self.stats_text.config(state="disabled")
    
    def save_settings(self):
        """Сохраняет настройки"""
        try:
            self.work_interval = int(self.work_var.get()) * 60
            self.blink_interval = int(self.blink_var.get()) * 60
            self.break_duration = int(self.break_var.get()) * 60
            messagebox.showinfo("Успех", "Настройки сохранены!")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целые числа!")
    
    def run(self):
        """Запускает приложение"""
        self.root.mainloop()


if __name__ == "__main__":
    app = WorkTimerApp()
    app.run()