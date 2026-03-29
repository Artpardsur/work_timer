"""
Консольный интерфейс для Work Timer
"""

import time
import sys
import os
from src.timer import WorkTimer


def clear_screen():
    """Очистить экран"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Печатает заголовок"""
    clear_screen()
    print("=" * 50)
    print("   🧘 WORK TIMER - Забота о здоровье программиста")
    print("=" * 50)
    print()


def print_menu():
    """Печатает меню"""
    print("\n📋 Меню:")
    print("  1. ▶️  Запустить таймер")
    print("  2. ⏸️  Поставить на паузу")
    print("  3. ▶️  Возобновить")
    print("  4. ⏹️  Остановить")
    print("  5. 📊  Показать статистику")
    print("  6. ⚙️  Настройки")
    print("  7. 🚪  Выход")
    print()


def show_stats(timer):
    """Показать статистику"""
    print_header()
    print("📊 СТАТИСТИКА")
    print("-" * 50)
    
    stats = timer.get_stats()
    
    print(f"  ⏱️  Время работы: {stats['work_time']}")
    print(f"  🔄 Сделано перерывов: {stats['breaks_taken']}")
    print(f"  👁️  Напоминаний о моргании: {stats['blink_reminders']}")
    print(f"  ⏸️  Пауз: {stats['pauses_count']}")
    print()
    
    input("Нажмите Enter, чтобы продолжить...")


def show_settings(timer):
    """Показать настройки"""
    print_header()
    print("⚙️ НАСТРОЙКИ")
    print("-" * 50)
    
    # Показываем в минутах с одним знаком после запятой
    work_min = timer.work_interval / 60
    blink_min = timer.blink_interval / 60
    break_min = timer.break_duration / 60
    
    print(f"  1. Интервал между перерывами: {work_min:.1f} минут")
    print(f"  2. Интервал между морганиями: {blink_min:.1f} минут")
    print(f"  3. Длительность перерыва: {break_min:.1f} минут")
    print()
    print("  💡 Для теста можно ввести дробные числа (например, 0.5 = 30 секунд)")
    print()
    print("  0. Назад")
    print()
    
    choice = input("Выберите настройку для изменения (0-3): ")
    
    if choice == "1":
        try:
            new_val = float(input("Новый интервал (минут, можно дробный): "))
            if new_val <= 0:
                print("❌ Интервал должен быть больше 0!")
            else:
                timer.work_interval = new_val * 60
                print(f"✅ Интервал изменён на {new_val:.1f} минут ({timer.work_interval:.0f} секунд)")
        except ValueError:
            print("❌ Ошибка: нужно ввести число (например, 0.5 или 30)")
    
    elif choice == "2":
        try:
            new_val = float(input("Новый интервал моргания (минут, можно дробный): "))
            if new_val <= 0:
                print("❌ Интервал должен быть больше 0!")
            else:
                timer.blink_interval = new_val * 60
                print(f"✅ Интервал моргания изменён на {new_val:.1f} минут ({timer.blink_interval:.0f} секунд)")
        except ValueError:
            print("❌ Ошибка: нужно ввести число (например, 0.5 или 10)")
    
    elif choice == "3":
        try:
            new_val = float(input("Новая длительность перерыва (минут, можно дробный): "))
            if new_val <= 0:
                print("❌ Длительность должна быть больше 0!")
            else:
                timer.break_duration = new_val * 60
                print(f"✅ Длительность перерыва изменена на {new_val:.1f} минут ({timer.break_duration:.0f} секунд)")
        except ValueError:
            print("❌ Ошибка: нужно ввести число (например, 0.5 или 5)")
    
    elif choice == "0":
        return
    
    else:
        print("❌ Неверный выбор!")
    
    time.sleep(2)


def main():
    """Главная функция"""
    print_header()
    print("Добро пожаловать в Work Timer!")
    print()
    print("Программа будет напоминать вам:")
    print("  🧘 - Вставать и разминаться каждые 30 минут")
    print("  👁️ - Моргать каждые 10 минут")
    print()
    print("Программа работает в фоне. Вы можете свернуть это окно.")
    print()
    input("Нажмите Enter, чтобы начать...")
    
    # Создаём таймер
    timer = WorkTimer()
    
    # Запускаем
    timer.start()
    
    try:
        while True:
            print_header()
            print(f"Статус: {timer.get_status()}")
            print()
            print_menu()
            
            choice = input("Ваш выбор (1-7): ")
            
            if choice == "1":
                timer.start()
                print("✅ Таймер запущен!")
                time.sleep(1)
                
            elif choice == "2":
                timer.pause()
                print("⏸️ Таймер на паузе")
                time.sleep(1)
                
            elif choice == "3":
                timer.resume()
                print("▶️ Таймер возобновлён")
                time.sleep(1)
                
            elif choice == "4":
                timer.stop()
                print("⏹️ Таймер остановлен")
                time.sleep(1)
                
            elif choice == "5":
                show_stats(timer)
                
            elif choice == "6":
                show_settings(timer)
                
            elif choice == "7":
                print("\n🛑 Остановка таймера...")
                timer.stop()
                print("👋 До свидания! Будьте здоровы!")
                break
                
            else:
                print("❌ Неверный выбор!")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
        timer.stop()


if __name__ == "__main__":
    main()