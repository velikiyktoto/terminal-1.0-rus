import pygame
import sys
import random
import time
import os
import math


pygame.init()
pygame.mixer.init()


WIDTH, HEIGHT = 900, 650
BORDER_WIDTH = 3
BUTTON_SIZE = 20
BUTTON_SPACING = 10


content_surface = pygame.Surface((WIDTH - BORDER_WIDTH * 2, HEIGHT - BORDER_WIDTH * 2 - 30))


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("1982 TERMINAL OS v1.2")


try:
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
except:
    pass  



def get_monospace_font(size):
    """Создает моноширинный шрифт"""
    try:
        
        font_names = [
            'consolas', 'couriernew', 'courier', 'monospace',
            'liberation mono', 'dejavu sans mono', 'roboto mono'
        ]

        for font_name in font_names:
            try:
                font = pygame.font.SysFont(font_name, size)
                
                test_surface = font.render("Test", True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    return font
            except:
                continue

        
        font = pygame.font.Font(None, size)
        return font

    except Exception as e:
        print(f"Ошибка загрузки шрифта: {e}")
        
        return pygame.font.Font(None, size)



font_small = get_monospace_font(14)
font_medium = get_monospace_font(18)
font_large = get_monospace_font(22)
font_title = get_monospace_font(28)
font_tiny = get_monospace_font(10)


if font_small.size("Test")[0] == 0:
    font_small = pygame.font.Font(None, 14)
if font_medium.size("Test")[0] == 0:
    font_medium = pygame.font.Font(None, 18)
if font_large.size("Test")[0] == 0:
    font_large = pygame.font.Font(None, 22)
if font_title.size("Test")[0] == 0:
    font_title = pygame.font.Font(None, 28)
if font_tiny.size("Test")[0] == 0:
    font_tiny = pygame.font.Font(None, 10)


BLACK = (0, 0, 0)
DARK_GREEN = (0, 16, 0)
TERMINAL_GREEN = (0, 255, 0)
BRIGHT_GREEN = (128, 255, 128)
DARK_GRAY = (20, 20, 20)
GRAY = (50, 50, 50)
LIGHT_GRAY = (150, 150, 150)
WHITE = (200, 200, 200)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
BLUE = (0, 120, 255)
CYAN = (0, 200, 200)
PURPLE = (180, 0, 255)
ORANGE = (255, 165, 0)



class ConsoleState:
    BOOT = 0
    MENU = 1
    GAME = 2
    TERMINAL = 3
    FILE_VIEW = 4
    TERMINFO = 5
    SETTINGS = 6
    CREDITS = 7



class RetroButton:
    def __init__(self, x, y, width, height, color, hover_color, text="", action=None, icon=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.action = action
        self.icon = icon
        self.hovered = False
        self.pressed = False

    def draw(self, surface):
        
        color = self.hover_color if self.hovered else self.color
        if self.pressed:
            pygame.draw.rect(surface, DARK_GRAY, self.rect)
            pygame.draw.rect(surface, color, self.rect.inflate(-4, -4))
        else:
            pygame.draw.rect(surface, color, self.rect)

        
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 2)

        
        if self.text:
            text_surf = font_small.render(self.text, True, BLACK)
            if text_surf.get_width() > 0:  # Проверяем, что текст отрендерился
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)

        
        if self.action == "exit":
            pygame.draw.line(surface, BLACK,
                             (self.rect.x + 5, self.rect.y + 5),
                             (self.rect.x + self.rect.width - 5, self.rect.y + self.rect.height - 5), 2)
            pygame.draw.line(surface, BLACK,
                             (self.rect.x + self.rect.width - 5, self.rect.y + 5),
                             (self.rect.x + 5, self.rect.y + self.rect.height - 5), 2)
        elif self.action == "minimize":
            pygame.draw.line(surface, BLACK,
                             (self.rect.x + 5, self.rect.y + self.rect.height - 5),
                             (self.rect.x + self.rect.width - 5, self.rect.y + self.rect.height - 5), 2)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.pressed = True
                if self.action:
                    return self.action
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False
        return None



class TextEffect:
    def __init__(self, min_alpha=100, max_alpha=255, speed=5):
        self.alpha = max_alpha
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.speed = speed
        self.fade_dir = -speed

    def update(self):
        self.alpha += self.fade_dir
        if self.alpha <= self.min_alpha or self.alpha >= self.max_alpha:
            self.fade_dir *= -1

    def get_alpha(self):
        return max(self.min_alpha, min(self.max_alpha, self.alpha))



class NoiseEffect:
    def __init__(self, width, height, density=0.02):
        self.width = width
        self.height = height
        self.density = density
        self.noise_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.generate_noise()

    def generate_noise(self):
        self.noise_surface.fill((0, 0, 0, 0))
        for _ in range(int(self.width * self.height * self.density)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            intensity = random.randint(5, 25)
            color = random.choice([(0, 255, 0, intensity), (128, 255, 128, intensity // 2)])
            pygame.draw.rect(self.noise_surface, color, (x, y, 1, 1))

    def draw(self, surface):
        surface.blit(self.noise_surface, (0, 0))



class ScanlineEffect:
    def __init__(self, width, height, spacing=4, speed=1):
        self.width = width
        self.height = height
        self.spacing = spacing
        self.offset = 0
        self.speed = speed

    def update(self):
        self.offset = (self.offset + self.speed) % self.spacing

    def draw(self, surface):
        for y in range(self.offset, self.height, self.spacing):
            alpha = 30 + math.sin(time.time() * 2) * 15
            pygame.draw.line(surface, (0, 0, 0, int(alpha)), (0, y), (self.width, y))



class Terminal:
    def __init__(self, font, prompt_color, text_color):
        self.font = font
        self.prompt_color = prompt_color
        self.text_color = text_color
        self.prompt = "C:\\1982>"
        self.input_text = ""
        self.output_lines = []
        self.command_history = []
        self.history_index = -1
        self.cursor_visible = True
        self.cursor_timer = 0
        self.max_lines = 25

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def add_output(self, text, color=None):
        if color is None:
            color = self.text_color

        
        max_width = content_surface.get_width() - 40

        # Простая проверка работы шрифта
        if self.font.size("A")[0] == 0:
            # Если шрифт не работает, используем простой перенос
            words = text.split()
            lines = []
            current_line = ""

            for word in words:
                if len(current_line) + len(word) + 1 < 60:  # Эмпирическое значение
                    current_line += word + " "
                else:
                    lines.append(current_line)
                    current_line = word + " "

            if current_line:
                lines.append(current_line)
        else:
            # Нормальный перенос текста
            words = text.split()
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + word + " "
                if self.font.size(test_line)[0] < max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word + " "

            if current_line:
                lines.append(current_line)

        for line in lines:
            self.output_lines.append((line, color))

        
        if len(self.output_lines) > self.max_lines:
            self.output_lines = self.output_lines[-self.max_lines:]

    def process_command(self, command):
        if command.strip():
            self.command_history.append(command)
            self.history_index = len(self.command_history)

        self.add_output(f"{self.prompt}{self.input_text}", self.prompt_color)

        cmd = command.strip().lower()

        if cmd == "help":
            self.add_output("ДОСТУПНЫЕ КОМАНДЫ:", YELLOW)
            self.add_output("HELP - показать эту справку")
            self.add_output("RUN DIAGNOSTICS - проверить системные файлы")
            self.add_output("RUN SNAKE - запустить игру Змейка")
            self.add_output("LOAD HISTORY.TXT - загрузить исторический файл")
            self.add_output("TERMINFO - информация о терминале")
            self.add_output("SETTINGS - настройки системы")
            self.add_output("CREDITS - информация о разработчиках")
            self.add_output("CLEAR - очистить экран")
            self.add_output("EXIT - выйти из терминала")

        elif cmd == "run diagnostics":
            self.simulate_diagnostics()

        elif cmd == "run snake":
            self.add_output("ЗАГРУЗКА SNAKE.EXE...", YELLOW)
            return "run_snake"

        elif cmd == "load history.txt":
            self.add_output("ЗАГРУЗКА ФАЙЛА HISTORY.TXT...", CYAN)
            return "load_file"

        elif cmd == "terminfo":
            self.add_output("ЗАГРУЗКА ИНФОРМАЦИИ О ТЕРМИНАЛЕ...", PURPLE)
            return "terminfo"

        elif cmd == "settings":
            self.add_output("ОТКРЫТИЕ НАСТРОЕК СИСТЕМЫ...", BLUE)
            return "settings"

        elif cmd == "credits":
            self.add_output("ЗАГРУЗКА ИНФОРМАЦИИ О РАЗРАБОТЧИКАХ...", ORANGE)
            return "credits"

        elif cmd == "clear":
            self.output_lines = []
            self.add_output("ЭКРАН ОЧИЩЕН.", TERMINAL_GREEN)

        elif cmd == "exit":
            return "exit_terminal"

        elif cmd == "matrix":
            self.add_output("ПОПЫТКА ДОСТУПА К MATRIX... ОТКАЗАНО.", RED)

        elif cmd == "hack":
            self.simulate_hacking()

        else:
            self.add_output(f"НЕИЗВЕСТНАЯ КОМАНДА: {command}", RED)
            self.add_output("ВВЕДИТЕ HELP ДЛЯ СПИСКА КОМАНД.")

        return None

    def simulate_diagnostics(self):
        self.add_output("ЗАПУСК ДИАГНОСТИКИ СИСТЕМЫ...")
        self.add_output("ПРОВЕРКА СИСТЕМНЫХ ФАЙЛОВ:")

        files = [
            ("SNAKE.EXE", 0.9),
            ("SYSTEM.DLL", 0.95),
            ("HISTORY.TXT", 0.8)
        ]

        for file, status in files:
            time.sleep(0.1)
            if status > 0.7:
                self.add_output(f"  {file}......[RUNNING]", TERMINAL_GREEN)
            elif status > 0.4:
                self.add_output(f"  {file}......[WARNING]", YELLOW)
            else:
                self.add_output(f"  {file}......[FAILED]", RED)

        self.add_output("ДИАГНОСТИКА ЗАВЕРШЕНА. СИСТЕМА В НОРМЕ.")

    def simulate_hacking(self):
        self.add_output("ИНИЦИАЛИЗАЦИЯ ПРОТОКОЛА ВЗЛОМА...", PURPLE)
        for i in range(5):
            time.sleep(0.1)
            code = "".join(random.choices("0123456789ABCDEF", k=8))
            self.add_output(f"ПОПЫТКА {i + 1}: {code}", CYAN)
        self.add_output("ВЗЛОМ НЕ УДАЛСЯ. СИСТЕМА ЗАЩИЩЕНА.", RED)

    def draw(self, surface):
        
        y_pos = 20
        for line, color in self.output_lines:
            text_surface = self.font.render(line, True, color)
            if text_surface.get_width() > 0:  # Проверяем, что текст отрендерился
                surface.blit(text_surface, (20, y_pos))
                y_pos += self.font.get_height() + 3


        prompt_text = self.font.render(self.prompt, True, self.prompt_color)
        if prompt_text.get_width() > 0:
            surface.blit(prompt_text, (20, y_pos))

        input_text = self.font.render(self.input_text, True, self.text_color)
        if input_text.get_width() > 0:
            surface.blit(input_text, (20 + prompt_text.get_width(), y_pos))


        if self.cursor_visible:
            cursor_x = 20 + prompt_text.get_width() + input_text.get_width()
            pygame.draw.rect(surface, self.text_color, (cursor_x, y_pos + 2, 8, self.font.get_height() - 4))



def generate_random_text(length):
    """Генерирует случайный текст из букв, цифр и символов"""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_[]{}<>()/*-+=!@#$%^&"
    prefixes = ["INIT:", "LOAD:", "MEM:", "SYS:", "CPU:", "DEV:", "IO:", "KERNEL:", "BIOS:", "RAM:"]
    result = random.choice(prefixes) + " "


    for _ in range(length - len(result)):
        result += random.choice(chars)

    return result



def draw_boot_screen(progress, noise, scanline):
    content_surface.fill(BLACK)


    title = font_title.render("1982 TERMINAL OS v1.2", True, TERMINAL_GREEN)
    if title.get_width() > 0:
        content_surface.blit(title, (
        content_surface.get_width() // 2 - title.get_width() // 2, content_surface.get_height() // 4))


    bar_width = content_surface.get_width() // 2
    pygame.draw.rect(content_surface, DARK_GRAY,
                     (content_surface.get_width() // 4, content_surface.get_height() // 2, bar_width, 20))
    pygame.draw.rect(content_surface, TERMINAL_GREEN, (
    content_surface.get_width() // 4, content_surface.get_height() // 2, int(bar_width * progress), 20))
    pygame.draw.rect(content_surface, DARK_GRAY,
                     (content_surface.get_width() // 4, content_surface.get_height() // 2, bar_width, 20), 2)


    lines_to_show = min(10, int(progress * 15))
    for i in range(lines_to_show):
        line_text = generate_random_text(40)
        line_color = BRIGHT_GREEN if random.random() > 0.3 else TERMINAL_GREEN


        if random.random() > 0.8:
            line_color = YELLOW

        line = font_small.render(line_text, True, line_color)
        if line.get_width() > 0:
            content_surface.blit(line, (content_surface.get_width() // 4, content_surface.get_height() // 3 + i * 20))


    if progress > 0.2:
        msg = font_small.render("INIT: Загрузка базовой системы ввода-вывода...", True, CYAN)
        if msg.get_width() > 0:
            content_surface.blit(msg, (content_surface.get_width() // 4, content_surface.get_height() // 3 + 200))

    if progress > 0.4:
        msg = font_small.render("MEM: Проверка оперативной памяти...", True, CYAN)
        if msg.get_width() > 0:
            content_surface.blit(msg, (content_surface.get_width() // 4, content_surface.get_height() // 3 + 220))

    if progress > 0.6:
        msg = font_small.render("SYS: Инициализация системных служб...", True, CYAN)
        if msg.get_width() > 0:
            content_surface.blit(msg, (content_surface.get_width() // 4, content_surface.get_height() // 3 + 240))

    if progress > 0.8:
        msg = font_small.render("IO: Настройка периферийных устройств...", True, CYAN)
        if msg.get_width() > 0:
            content_surface.blit(msg, (content_surface.get_width() // 4, content_surface.get_height() // 3 + 260))


    percent_text = font_medium.render(f"{int(progress * 100)}%", True, TERMINAL_GREEN)
    if percent_text.get_width() > 0:
        content_surface.blit(percent_text, (
        content_surface.get_width() // 2 - percent_text.get_width() // 2, content_surface.get_height() // 2 + 30))


    if progress > 0.9:
        ready_text = font_medium.render("СИСТЕМА ГОТОВА К РАБОТЕ", True, BRIGHT_GREEN)
        if ready_text.get_width() > 0:
            content_surface.blit(ready_text, (
            content_surface.get_width() // 2 - ready_text.get_width() // 2, content_surface.get_height() // 2 + 60))


    noise.draw(content_surface)
    scanline.draw(content_surface)



def show_file_content():
    return [
        "ФАЙЛ: HISTORY.TXT",
        "ДАТА СОЗДАНИЯ: 06.02.1982",
        "АВТОР: СИСТЕМНЫЙ АРХИВ",
        "",
        "ИСТОРИЧЕСКИЕ СОБЫТИЯ 1979-1982:",
        "",
        "1979 ГОД:",
        "10.02.1979 - РЕВОЛЮЦИЯ В ИРАНЕ",
        "04.11.1979 - ЗАХВАТ ЗАЛОЖНИКОВ В ТЕГЕРАНЕ",
        "27.12.1979 - ВВОД СОВЕТСКИХ ВОЙСК В АФГАНИСТАН",
        "",
        "1980 ГОД:",
        "22.05.1980 - PAC-MAN",
        "04.11.1980 - ПОБЕДА РЕЙГАНА",
        "",
        "1981 ГОД:",
        "12.08.1981 - ПЕРВЫЙ IBM PC",
        "",
        "1982 ГОД:",
        "06.02.1982 - COMMODORE 64",
        "02.03.1982 - ZORK II",
        "",
        "ФАЙЛ ЗАВЕРШЕН."
    ]



def show_terminfo():
    return [
        "1982 TERMINFO",
        "",
        "ТЕХНИЧЕСКИЕ ДАННЫЕ:",
        "МОДЕЛЬ: VT-220",
        "РАЗРЕШЕНИЕ: 80×24",
        "ЦВЕТА: Монохромный зеленый",
        "ПАМЯТЬ: 8 КБ ОЗУ",
        "",
        "СИСТЕМНЫЕ КОМАНДЫ:",
        "HELP - справка",
        "CLEAR - очистка экрана",
        "",
        "СТАТУС СИСТЕМЫ:",
        "СИСТЕМА: [ONLINE]",
        "ПАМЯТЬ: [84% СВОБОДНО]",
        "",
        "КОНЕЦ ДОКУМЕНТА"
    ]



def show_settings():
    return [
        "НАСТРОЙКИ СИСТЕМЫ",
        "",
        "ВНЕШНИЙ ВИД:",
        "[X] ЭФФЕКТ СКАНИРУЮЩЕЙ ЛИНИИ",
        "[X] ЭФФЕКТ ШУМА",
        "[X] МЕРЦАНИЕ КУРСОРА",
        "",
        "СИСТЕМНЫЕ:",
        "СКОРОСТЬ ЗАГРУЗКИ: [СРЕДНЯЯ]",
        "",
        "ИСПОЛЬЗУЙТЕ СТРЕЛКИ ДЛЯ ВЫБОРА"
    ]



def show_credits():
    return [
        "РАЗРАБОТЧИКИ",
        "",
        "1982 TERMINAL OS v1.2",
        "РЕТРО-СИМУЛЯТОР ТЕРМИНАЛА",
        "",
        "АВТОРЫ:",
        "ВЕДУЩИЙ ПРОГРАММИСТ",
        "ДИЗАЙНЕР ИНТЕРФЕЙСА",
        "",
        "ТЕХНОЛОГИИ:",
        "PYGAME GRAPHICS ENGINE",
        "PYTHON 3.9+",
        "",
        "© 1982 RETRO SYSTEMS",
        "",
        "НАЖМИТЕ ESC ДЛЯ ВОЗВРАТА"
    ]



def draw_file_content(content, noise, scanline):
    content_surface.fill(BLACK)


    title = font_title.render("HISTORY.TXT", True, CYAN)
    if title.get_width() > 0:
        content_surface.blit(title, (content_surface.get_width() // 2 - title.get_width() // 2, 20))


    y_pos = 60
    for line in content:
        text_surface = font_medium.render(line, True, BRIGHT_GREEN)
        if text_surface.get_width() > 0:
            content_surface.blit(text_surface, (40, y_pos))
            y_pos += font_medium.get_height() + 5


        if y_pos > content_surface.get_height() - 50:
            break


    hint = font_small.render("Нажмите ESC для возврата в меню", True, TERMINAL_GREEN)
    if hint.get_width() > 0:
        content_surface.blit(hint, (
        content_surface.get_width() // 2 - hint.get_width() // 2, content_surface.get_height() - 30))


    noise.draw(content_surface)
    scanline.draw(content_surface)



def draw_terminfo(content, noise, scanline):
    content_surface.fill(BLACK)


    title = font_title.render("1982 TERMINFO", True, PURPLE)
    if title.get_width() > 0:
        content_surface.blit(title, (content_surface.get_width() // 2 - title.get_width() // 2, 20))


    y_pos = 60
    for line in content:
        text_surface = font_medium.render(line, True, BRIGHT_GREEN)
        if text_surface.get_width() > 0:
            content_surface.blit(text_surface, (40, y_pos))
            y_pos += font_medium.get_height() + 5

        if y_pos > content_surface.get_height() - 50:
            break


    hint = font_small.render("Нажмите ESC для возврата в меню", True, TERMINAL_GREEN)
    if hint.get_width() > 0:
        content_surface.blit(hint, (
        content_surface.get_width() // 2 - hint.get_width() // 2, content_surface.get_height() - 30))


    noise.draw(content_surface)
    scanline.draw(content_surface)



def draw_settings(content, noise, scanline):
    content_surface.fill(BLACK)


    title = font_title.render("НАСТРОЙКИ СИСТЕМЫ", True, BLUE)
    if title.get_width() > 0:
        content_surface.blit(title, (content_surface.get_width() // 2 - title.get_width() // 2, 20))


    y_pos = 60
    for line in content:
        text_surface = font_medium.render(line, True, BRIGHT_GREEN)
        if text_surface.get_width() > 0:
            content_surface.blit(text_surface, (40, y_pos))
            y_pos += font_medium.get_height() + 5

        if y_pos > content_surface.get_height() - 50:
            break


    hint = font_small.render("Нажмите ESC для возврата в меню", True, TERMINAL_GREEN)
    if hint.get_width() > 0:
        content_surface.blit(hint, (
        content_surface.get_width() // 2 - hint.get_width() // 2, content_surface.get_height() - 30))


    noise.draw(content_surface)
    scanline.draw(content_surface)



def draw_credits(content, noise, scanline):
    content_surface.fill(BLACK)


    y_pos = 40
    for line in content:
        text_surface = font_medium.render(line, True, BRIGHT_GREEN)
        if text_surface.get_width() > 0:
            content_surface.blit(text_surface,
                                 (content_surface.get_width() // 2 - text_surface.get_width() // 2, y_pos))
            y_pos += font_medium.get_height() + 5

        if y_pos > content_surface.get_height() - 30:
            break


    hint = font_small.render("Нажмите ESC для возврата в меню", True, TERMINAL_GREEN)
    if hint.get_width() > 0:
        content_surface.blit(hint, (
        content_surface.get_width() // 2 - hint.get_width() // 2, content_surface.get_height() - 20))


    noise.draw(content_surface)
    scanline.draw(content_surface)



def draw_main_menu(selected_item, noise, scanline):
    content_surface.fill(BLACK)


    title = font_title.render("1982 TERMINAL", True, TERMINAL_GREEN)
    if title.get_width() > 0:
        content_surface.blit(title, (content_surface.get_width() // 2 - title.get_width() // 2, 80))


    menu_items = [
        "1. ЗМЕЙКА",
        "2. ТЕРМИНАЛ",
        "3. HISTORY.TXT",
        "4. TERMINFO",
        "5. НАСТРОЙКИ",
        "6. РАЗРАБОТЧИКИ",
        "7. ВЫХОД"
    ]

    for i, item in enumerate(menu_items):
        if i == selected_item:
            text = font_medium.render("> " + item + " <", True, BRIGHT_GREEN)
        else:
            text = font_medium.render("  " + item, True, TERMINAL_GREEN)

        if text.get_width() > 0:
            content_surface.blit(text, (content_surface.get_width() // 2 - text.get_width() // 2, 150 + i * 25))


    hint = font_small.render("ИСПОЛЬЗУЙТЕ СТРЕЛКИ И ENTER ДЛЯ ВЫБОРА", True, TERMINAL_GREEN)
    if hint.get_width() > 0:
        content_surface.blit(hint, (
        content_surface.get_width() // 2 - hint.get_width() // 2, content_surface.get_height() - 50))


    noise.draw(content_surface)
    scanline.draw(content_surface)



def draw_terminal(terminal, noise, scanline):
    content_surface.fill(BLACK)
    terminal.draw(content_surface)
    noise.draw(content_surface)
    scanline.draw(content_surface)



def draw_window_frame():

    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, HEIGHT))


    pygame.draw.rect(screen, DARK_GRAY,
                     (BORDER_WIDTH, BORDER_WIDTH, WIDTH - BORDER_WIDTH * 2, HEIGHT - BORDER_WIDTH * 2))


    title_bar = pygame.Rect(BORDER_WIDTH, BORDER_WIDTH, WIDTH - BORDER_WIDTH * 2, 30)
    pygame.draw.rect(screen, GRAY, title_bar)


    title_text = font_small.render("1982 TERMINAL OS v1.2", True, WHITE)
    if title_text.get_width() > 0:
        screen.blit(title_text,
                    (title_bar.centerx - title_text.get_width() // 2, title_bar.centery - title_text.get_height() // 2))


    close_button.draw(screen)
    file_button.draw(screen)
    terminfo_button.draw(screen)
    settings_button.draw(screen)


    screen.blit(content_surface, (BORDER_WIDTH, BORDER_WIDTH + 30))



def snake_game():
    grid_size = 20
    grid_width = content_surface.get_width() // grid_size
    grid_height = (content_surface.get_height() - 40) // grid_size

    snake = [(grid_width // 2, grid_height // 2)]
    direction = (1, 0)
    food = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
    score = 0
    game_over = False

    clock = pygame.time.Clock()
    last_update_time = time.time()
    update_interval = 0.1


    noise = NoiseEffect(content_surface.get_width(), content_surface.get_height(), 0.01)
    scanline = ScanlineEffect(content_surface.get_width(), content_surface.get_height(), 3)

    running = True
    while running:
        current_time = time.time()


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP and direction != (0, 1):
                    direction = (0, -1)
                elif event.key == pygame.K_DOWN and direction != (0, -1):
                    direction = (0, 1)
                elif event.key == pygame.K_LEFT and direction != (1, 0):
                    direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and direction != (-1, 0):
                    direction = (1, 0)
                elif event.key == pygame.K_r and game_over:

                    snake = [(grid_width // 2, grid_height // 2)]
                    direction = (1, 0)
                    food = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
                    score = 0
                    game_over = False


            close_button.handle_event(event)
            file_button.handle_event(event)
            terminfo_button.handle_event(event)
            settings_button.handle_event(event)

        if not game_over:

            if current_time - last_update_time > update_interval:
                last_update_time = current_time


                head_x, head_y = snake[0]
                new_head = (head_x + direction[0], head_y + direction[1])


                if (new_head[0] < 0 or new_head[0] >= grid_width or
                        new_head[1] < 0 or new_head[1] >= grid_height or
                        new_head in snake):
                    game_over = True
                    continue

                snake.insert(0, new_head)


                if new_head == food:
                    score += 1
                    food = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
                    while food in snake:
                        food = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))

                    update_interval = max(0.05, update_interval * 0.95)
                else:
                    snake.pop()


        content_surface.fill(BLACK)


        pygame.draw.rect(content_surface, TERMINAL_GREEN, (0, 0, grid_width * grid_size, grid_height * grid_size), 1)


        for segment in snake:
            pygame.draw.rect(content_surface, TERMINAL_GREEN,
                             (segment[0] * grid_size, segment[1] * grid_size,
                              grid_size - 1, grid_size - 1))


        pygame.draw.rect(content_surface, BRIGHT_GREEN,
                         (food[0] * grid_size, food[1] * grid_size,
                          grid_size - 1, grid_size - 1))


        score_text = font_medium.render(f"СЧЕТ: {score}", True, TERMINAL_GREEN)
        if score_text.get_width() > 0:
            content_surface.blit(score_text, (10, content_surface.get_height() - 30))


        if game_over:
            game_over_text = font_large.render("GAME OVER", True, RED)
            restart_text = font_medium.render("Нажмите R для рестарта", True, YELLOW)
            if game_over_text.get_width() > 0 and restart_text.get_width() > 0:
                content_surface.blit(game_over_text, (
                content_surface.get_width() // 2 - game_over_text.get_width() // 2,
                content_surface.get_height() // 2 - 30))
                content_surface.blit(restart_text, (content_surface.get_width() // 2 - restart_text.get_width() // 2,
                                                    content_surface.get_height() // 2 + 10))


        noise.draw(content_surface)
        scanline.draw(content_surface)


        draw_window_frame()

        pygame.display.flip()
        clock.tick(60)



close_button = RetroButton(
    WIDTH - BORDER_WIDTH - BUTTON_SIZE - BUTTON_SPACING,
    BORDER_WIDTH + (30 - BUTTON_SIZE) // 2,
    BUTTON_SIZE, BUTTON_SIZE, RED, (255, 100, 100), "exit"
)

file_button = RetroButton(
    WIDTH - BORDER_WIDTH - BUTTON_SIZE * 2 - BUTTON_SPACING * 2,
    BORDER_WIDTH + (30 - BUTTON_SIZE) // 2,
    BUTTON_SIZE, BUTTON_SIZE, CYAN, (100, 255, 255), "H", "load_file"
)

terminfo_button = RetroButton(
    WIDTH - BORDER_WIDTH - BUTTON_SIZE * 3 - BUTTON_SPACING * 3,
    BORDER_WIDTH + (30 - BUTTON_SIZE) // 2,
    BUTTON_SIZE, BUTTON_SIZE, PURPLE, (200, 100, 255), "T", "terminfo"
)

settings_button = RetroButton(
    WIDTH - BORDER_WIDTH - BUTTON_SIZE * 4 - BUTTON_SPACING * 4,
    BORDER_WIDTH + (30 - BUTTON_SIZE) // 2,
    BUTTON_SIZE, BUTTON_SIZE, BLUE, (100, 100, 255), "S", "settings"
)


def main():
    state = ConsoleState.BOOT
    boot_progress = 0
    boot_speed = 0.3
    selected_menu_item = 0


    noise = NoiseEffect(content_surface.get_width(), content_surface.get_height())
    scanline = ScanlineEffect(content_surface.get_width(), content_surface.get_height())
    terminal = Terminal(font_small, TERMINAL_GREEN, BRIGHT_GREEN)


    terminal.add_output("1982 TERMINAL OS v1.2")
    terminal.add_output("СИСТЕМА ЗАГРУЖЕНА УСПЕШНО")
    terminal.add_output("ВВЕДИТЕ HELP ДЛЯ СПИСКА КОМАНД")


    file_content = show_file_content()
    terminfo_content = show_terminfo()
    settings_content = show_settings()
    credits_content = show_credits()

    clock = pygame.time.Clock()
    last_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time


        mouse_pos = pygame.mouse.get_pos()


        close_button.check_hover(mouse_pos)
        file_button.check_hover(mouse_pos)
        terminfo_button.check_hover(mouse_pos)
        settings_button.check_hover(mouse_pos)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()


            button_action = None
            for button in [close_button, file_button, terminfo_button, settings_button]:
                action = button.handle_event(event)
                if action:
                    button_action = action
                    break

            if button_action == "exit":
                pygame.quit()
                sys.exit()
            elif button_action == "load_file":
                state = ConsoleState.FILE_VIEW
            elif button_action == "terminfo":
                state = ConsoleState.TERMINFO
            elif button_action == "settings":
                state = ConsoleState.SETTINGS

            if state == ConsoleState.MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_menu_item = (selected_menu_item - 1) % 7
                    elif event.key == pygame.K_DOWN:
                        selected_menu_item = (selected_menu_item + 1) % 7
                    elif event.key == pygame.K_RETURN:
                        if selected_menu_item == 0:
                            snake_game()
                        elif selected_menu_item == 1:
                            state = ConsoleState.TERMINAL
                        elif selected_menu_item == 2:
                            state = ConsoleState.FILE_VIEW
                        elif selected_menu_item == 3:
                            state = ConsoleState.TERMINFO
                        elif selected_menu_item == 4:
                            state = ConsoleState.SETTINGS
                        elif selected_menu_item == 5:
                            state = ConsoleState.CREDITS
                        elif selected_menu_item == 6:
                            pygame.quit()
                            sys.exit()

            elif state == ConsoleState.TERMINAL:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = ConsoleState.MENU
                    elif event.key == pygame.K_RETURN:
                        result = terminal.process_command(terminal.input_text)
                        if result == "run_snake":
                            terminal.input_text = ""
                            snake_game()
                        elif result == "load_file":
                            terminal.input_text = ""
                            state = ConsoleState.FILE_VIEW
                        elif result == "terminfo":
                            terminal.input_text = ""
                            state = ConsoleState.TERMINFO
                        elif result == "settings":
                            terminal.input_text = ""
                            state = ConsoleState.SETTINGS
                        elif result == "credits":
                            terminal.input_text = ""
                            state = ConsoleState.CREDITS
                        elif result == "exit_terminal":
                            state = ConsoleState.MENU
                        terminal.input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        terminal.input_text = terminal.input_text[:-1]
                    else:

                        if event.unicode.isprintable() and len(terminal.input_text) < 50:
                            terminal.input_text += event.unicode

            elif state in [ConsoleState.FILE_VIEW, ConsoleState.TERMINFO, ConsoleState.SETTINGS, ConsoleState.CREDITS]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = ConsoleState.MENU

        noise.generate_noise()
        scanline.update()
        if state == ConsoleState.TERMINAL:
            terminal.update(dt)

        if state == ConsoleState.BOOT:
            boot_progress += boot_speed * dt
            if boot_progress >= 1.0:
                state = ConsoleState.MENU
                boot_progress = 1.0

        if state == ConsoleState.BOOT:
            draw_boot_screen(boot_progress, noise, scanline)
        elif state == ConsoleState.MENU:
            draw_main_menu(selected_menu_item, noise, scanline)
        elif state == ConsoleState.TERMINAL:
            draw_terminal(terminal, noise, scanline)
        elif state == ConsoleState.FILE_VIEW:
            draw_file_content(file_content, noise, scanline)
        elif state == ConsoleState.TERMINFO:
            draw_terminfo(terminfo_content, noise, scanline)
        elif state == ConsoleState.SETTINGS:
            draw_settings(settings_content, noise, scanline)
        elif state == ConsoleState.CREDITS:
            draw_credits(credits_content, noise, scanline)

        draw_window_frame()

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()
