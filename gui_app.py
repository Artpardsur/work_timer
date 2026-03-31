"""
Work Timer - Профессиональное приложение с графическим интерфейсом
Последовательная логика: работа -> перерыв -> работа -> перерыв...
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
import datetime as dt
import os


class WorkTimerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Work Timer - Забота о здоровье")
        self.root.geometry("550x700")
        self.root.resizable(False, False)
        
        # Устанавливаем иконку (если есть)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Настройки таймера (в секундах)
        self.work_interval = 30 * 60
        self.blink_interval = 10 * 60
        self.break_duration = 5 * 60
        
        # Состояние
        self.running = False
        self.paused = False
        self.current_phase = "idle"  # idle, work, break
        
        # Статистика
        self.breaks_taken = 0
        self.blink_reminders = 0
        self.pauses_count = 0
        self.start_time = None
        self.total_pause_seconds = 0
        self.pause_start = None
        
        # Для таймера
        self.timer_thread = None
        self.remaining_time = 0
        self.last_blink_time = None
        
        self.setup_ui()
        self.update_time_display()
        self.update_stats_periodically()
        
    def setup_ui(self):
        """Создаёт интерфейс"""
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
            text="Нажмите Старт",
            font=("Segoe UI", 14),
            bg=self.bg_color,
            fg="#34495e"
        )
        self.countdown_label.pack(pady=10)
        
        # Кнопки
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
            command=self.toggle_pause,
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
        self.update_stats_display()
        
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
        
        row = 0
        tk.Label(settings_frame, text="Перерывы каждые:", bg=self.bg_color).grid(row=row, column=0, sticky="w", pady=5)
        self.work_var = tk.StringVar(value="30")
        work_entry = tk.Entry(settings_frame, textvariable=self.work_var, width=8)
        work_entry.grid(row=row, column=1, padx=5)
        tk.Label(settings_frame, text="минут", bg=self.bg_color).grid(row=row, column=2, sticky="w")
        
        row += 1
        tk.Label(settings_frame, text="Моргать каждые:", bg=self.bg_color).grid(row=row, column=0, sticky="w", pady=5)
        self.blink_var = tk.StringVar(value="10")
        blink_entry = tk.Entry(settings_frame, textvariable=self.blink_var, width=8)
        blink_entry.grid(row=row, column=1, padx=5)
        tk.Label(settings_frame, text="минут", bg=self.bg_color).grid(row=row, column=2, sticky="w")
        
        row += 1
        tk.Label(settings_frame, text="Длительность перерыва:", bg=self.bg_color).grid(row=row, column=0, sticky="w", pady=5)
        self.break_var = tk.StringVar(value="5")
        break_entry = tk.Entry(settings_frame, textvariable=self.break_var, width=8)
        break_entry.grid(row=row, column=1, padx=5)
        tk.Label(settings_frame, text="минут", bg=self.bg_color).grid(row=row, column=2, sticky="w")
        
        row += 1
        save_btn = tk.Button(
            settings_frame,
            text="Сохранить",
            font=("Segoe UI", 9),
            bg="#3498db",
            fg="white",
            command=self.save_settings
        )
        save_btn.grid(row=row, column=1, pady=10)
    
    def start_timer(self):
        """Запускает таймер"""
        if self.running:
            return
        
        self.running = True
        self.paused = False
        self.current_phase = "work"
        self.remaining_time = self.work_interval
        self.start_time = dt.datetime.now()
        self.total_pause_seconds = 0
        self.last_blink_time = self.remaining_time
        
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="⏸️ Пауза", bg="#f39c12")
        self.stop_btn.config(state="normal")
        
        self.update_status()
        
        # Запускаем основной таймер
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
    
    def stop_timer(self):
        """Полная остановка таймера"""
        self.running = False
        self.paused = False
        self.current_phase = "idle"
        self.remaining_time = 0
        
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="⏸️ Пауза", bg="#f39c12")
        self.stop_btn.config(state="disabled")
        
        self.update_status()
        self.update_stats_display()
        self.countdown_label.config(text="Нажмите Старт")
    
    def toggle_pause(self):
        """Переключает паузу"""
        if not self.running:
            return
        
        if self.paused:
            # Возобновляем
            self.paused = False
            if self.pause_start:
                pause_seconds = (dt.datetime.now() - self.pause_start).total_seconds()
                self.total_pause_seconds += pause_seconds
            self.pause_btn.config(text="⏸️ Пауза", bg="#f39c12")
            self.update_status()
            # Возобновляем таймер
            self._timer_loop()
        else:
            # Ставим на паузу
            self.paused = True
            self.pause_start = dt.datetime.now()
            self.pauses_count += 1
            self.pause_btn.config(text="▶️ Возобновить", bg="#3498db")
            self.update_status()
    
    def _timer_loop(self):
        """Основной цикл таймера (последовательный)"""
        while self.running and not self.paused:
            if self.current_phase == "work":
                self._run_work_phase()
            elif self.current_phase == "break":
                self._run_break_phase()
    
    def _run_work_phase(self):
        """Выполняет рабочий период с напоминаниями о моргании"""
        self.remaining_time = self.work_interval
        
        # Сбрасываем настройки моргания для нового цикла
        blink_interval_seconds = self.blink_interval
        next_blink_time = self.work_interval - blink_interval_seconds
        last_blink_reminder = None
        
        # Для случая, если интервал моргания больше времени работы
        if next_blink_time < 0:
            next_blink_time = self.work_interval // 2  # напоминание в середине
        
        print(f"Новый рабочий цикл: {self.work_interval} сек, моргание каждые {blink_interval_seconds} сек")
        
        while self.running and not self.paused and self.current_phase == "work" and self.remaining_time > 0:
            # Обновляем отображение
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.root.after(0, lambda m=minutes, s=seconds: self.countdown_label.config(text=f"Работа: {m:02d}:{s:02d}"))
            
            # Напоминание о моргании
            if self.remaining_time <= next_blink_time and next_blink_time > 0:
                if last_blink_reminder != next_blink_time:
                    last_blink_reminder = next_blink_time
                    print(f"Моргание! осталось {self.remaining_time} сек")
                    self.root.after(0, self._remind_blink)
                    # Устанавливаем следующее напоминание
                    next_blink_time -= blink_interval_seconds
                    # Не уходим в отрицательные значения
                    if next_blink_time < 0:
                        next_blink_time = 0
            
            time.sleep(1)
            self.remaining_time -= 1
            
            # Если на паузе — выходим из цикла
            if self.paused:
                return
        
        # Рабочий период закончился
        if self.running and not self.paused and self.current_phase == "work":
            print("Рабочий период закончен")
            self.root.after(0, self._take_break)
    
    def _run_break_phase(self):
        """Выполняет период отдыха"""
        self.remaining_time = self.break_duration
        
        while self.running and not self.paused and self.current_phase == "break" and self.remaining_time > 0:
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.root.after(0, lambda m=minutes, s=seconds: self.countdown_label.config(text=f"Отдых: {m:02d}:{s:02d}"))
            time.sleep(1)
            self.remaining_time -= 1
            
            if self.paused:
                return
        
        if self.running and not self.paused and self.current_phase == "break":
            self.root.after(0, self._end_break)
    
    def _take_break(self):
        """Начать перерыв"""
        self.current_phase = "break"
        self.breaks_taken += 1
        self.update_stats_display()
        self.update_status()
        
        self._notify("🧘 ПЕРЕРЫВ!", f"Встаньте и разомнитесь! {self.break_duration // 60} минут отдыха.")
        
        # Запускаем цикл отдыха
        self._run_break_phase()

    def _end_break(self):
        """Закончить перерыв и вернуться к работе"""
        self.current_phase = "work"
        self.update_status()
        
        self._notify("✅ ПЕРЕРЫВ ЗАКОНЧЕН!", "Возвращайтесь к работе!")
        
        # Сбрасываем время для моргания в новом рабочем цикле
        self.last_blink_time = None
        self.next_blink_time = None
        
        # Запускаем следующий рабочий цикл
        self._run_work_phase()
    
    def _remind_blink(self):
        """Напомнить моргнуть"""
        # Проверяем, что мы всё ещё в рабочей фазе и таймер работает
        if not self.running or self.paused or self.current_phase != "work":
            return
        
        self.blink_reminders += 1
        self.update_stats_display()
        self._notify("👁️ НАПОМИНАНИЕ!", "Не забывайте моргать! Это помогает глазам.")
    
    def _notify(self, title, message):
        """Показывает уведомление со звуком (в основном потоке)"""
        
        # Звук (не блокирует)
        sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
        
        if "ПЕРЕРЫВ" in title and "ЗАКОНЧЕН" not in title:
            sound_file = os.path.join(sounds_dir, "break_start.wav")
        elif "ЗАКОНЧЕН" in title:
            sound_file = os.path.join(sounds_dir, "break_end.wav")
        elif "МОРГАНИЕ" in title:
            sound_file = os.path.join(sounds_dir, "blink.wav")
        else:
            sound_file = None
        
        if sound_file and os.path.exists(sound_file):
            try:
                import winsound
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except:
                pass
        else:
            print('\a')
        
        # Уведомление — запускаем в основном потоке через after
        self.root.after(0, lambda: self._show_messagebox(title, message))

    def _show_messagebox(self, title, message):
        """Показывает messagebox в основном потоке"""
        try:
            messagebox.showinfo(title, message)
        except Exception as e:
            print(f"Ошибка при показе уведомления: {e}")
    
    def update_status(self):
        """Обновляет статус"""
        if not self.running:
            status = "⏹️ Остановлен"
            color = "#7f8c8d"
        elif self.paused:
            status = "⏸️ На паузе"
            color = "#f39c12"
        elif self.current_phase == "break":
            status = "🧘 На перерыве"
            color = "#e74c3c"
        else:
            status = "▶️ Работает"
            color = "#27ae60"
        
        self.status_label.config(text=status, fg=color)
    
    def update_time_display(self):
        """Обновляет отображение времени (для обратной совместимости)"""
        self.root.after(1000, self.update_time_display)
    
    def update_stats_display(self):
        """Обновляет отображение статистики"""
        if self.running and not self.paused and self.start_time:
            work_seconds = (dt.datetime.now() - self.start_time).total_seconds() - self.total_pause_seconds
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
    
    def update_stats_periodically(self):
        """Периодическое обновление статистики"""
        self.update_stats_display()
        self.root.after(1000, self.update_stats_periodically)
    
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