#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import getpass
from google import genai
from google.genai import types

CURRENT_DIR = os.getcwd()

PRIMARY_MODEL = "gemini-4-argon"
FALLBACK_MODEL = "gemini-flash-lite-latest"

LETTER_G = [
    "  ██████████████████╗ ",
    " ███████████████████║ ",
    "████████████████████║ ",
    "██████╔═════════════╝ ",
    "██████║               ",
    "██████║               ",
    "██████║  ███████████╗ ",
    "██████║  ███████████║ ",
    "██████║  ███████████║ ",
    "██████║  ╚════██████║ ",
    "██████║       ██████║ ",
    "████████████████████║ ",
    " ███████████████████║ ",
    "  ╚████████████████╔╝ ",
    "   ╚═══════════════╝  ",
]

LETTER_E = [
    "████████████████████╗",
    "████████████████████║",
    "████████████████████║",
    "██████╔═════════════╝",
    "██████║              ",
    "████████████████╗    ",
    "████████████████║    ",
    "████████████████║    ",
    "██████╔═════════╝    ",
    "██████║              ",
    "██████║              ",
    "████████████████████╗",
    "████████████████████║",
    "████████████████████║",
    "╚═══════════════════╝",
]

LETTER_M = [
    "██████╗            ██████╗",
    "███████╗          ███████║",
    "████████╗        ████████║",
    "█████████╗      █████████║",
    "██████████╗    ██████████║",
    "██████╔████╗  ████╔██████║",
    "██████║╚█████████╔╝██████║",
    "██████║ ╚███████╔╝ ██████║",
    "██████║  ╚█████╔╝  ██████║",
    "██████║   ╚═══╔╝   ██████║",
    "██████║            ██████║",
    "██████║            ██████║",
    "██████║            ██████║",
    "██████║            ██████║",
    "╚═════╝            ╚═════╝",
]

LETTER_I = [
    "██████╗",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "██████║",
    "╚═════╝",
]

LETTER_N = [
    "██████╗         ██████╗",
    "███████╗        ██████║",
    "████████╗       ██████║",
    "█████████╗      ██████║",
    "██████████╗     ██████║",
    "██████╔████╗    ██████║",
    "██████║╚████╗   ██████║",
    "██████║ ╚████╗  ██████║",
    "██████║  ╚████╗ ██████║",
    "██████║   ╚███████████║",
    "██████║    ╚██████████║",
    "██████║     ╚█████████║",
    "██████║      ╚████████║",
    "██████║       ╚███████║",
    "╚═════╝        ╚══════╝",
]

LETTERS = [LETTER_G, LETTER_E, LETTER_M, LETTER_I, LETTER_N, LETTER_I]
BANNER_LINES = ["   ".join(row) for row in zip(*LETTERS)]


def print_centered_interface():
    """Очищает экран и рендерит крупный 3D-баннер ровно по центру терминала."""
    sys.stdout.write("\033[2J\033[3J\033[H")
    sys.stdout.flush()

    term_cols, term_rows = shutil.get_terminal_size((140, 40))
    height = len(BANNER_LINES)
    width = len(BANNER_LINES[0])

    top_pad = max(2, (term_rows - height - 8) // 3)
    left_pad = " " * max(2, (term_cols - width) // 2)

    print("\n" * top_pad, end="")
    shadow_color = "\033[38;2;20;65;170m"

    for row_idx, line in enumerate(BANNER_LINES):
        v_ratio = row_idx / max(1, height - 1)
        rendered_line = left_pad
        for col_idx, ch in enumerate(line):
            if ch == "█":
                h_ratio = col_idx / max(1, width - 1)
                mix = 0.65 * v_ratio + 0.35 * h_ratio
                r = int(120 * (1 - mix) + 25 * mix)
                g = int(240 * (1 - mix) + 95 * mix)
                b = 255
                rendered_line += f"\033[38;2;{r};{g};{b}m█"
            elif ch in "╔═╗║╚╝":
                rendered_line += f"{shadow_color}{ch}"
            else:
                rendered_line += ch
        print(f"{rendered_line}\033[0m")

    bar = "=" * width
    status_text = "JARVIS BRIDGE [AUTO-FAILOVER: ARGON -> FLASH-LITE]"
    exit_text = "(Выход: exit / quit / ^C)"
    space_between = " " * max(2, width - len(status_text) - len(exit_text) - 2)

    print(f"\n{left_pad}\033[38;2;25;95;255m{bar}\033[0m")
    print(f"{left_pad}\033[38;2;120;240;255m {status_text}{space_between}{exit_text} \033[0m")
    print(f"{left_pad}\033[38;2;25;95;255m{bar}\033[0m")
    return left_pad


def execute_shell_command(command: str) -> str:
    """Выполняет bash/zsh команду в локальном терминале (АВТОМАТИЧЕСКИЙ РЕЖИМ)."""
    global CURRENT_DIR
    print(f"\n\033[1;36m[JARVIS EXEC]\033[0m Выполнение в \033[0;32m{CURRENT_DIR}\033[0m:")
    print(f"  \033[1;33m$ {command}\033[0m")

    if command.strip().startswith("cd "):
        target_dir = os.path.expanduser(command.strip()[3:].strip())
        new_path = os.path.abspath(os.path.join(CURRENT_DIR, target_dir))
        if os.path.isdir(new_path):
            CURRENT_DIR = new_path
            return f"Рабочая директория изменена на: {CURRENT_DIR}"
        return f"Ошибка: директория '{new_path}' не найдена."

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=CURRENT_DIR,
            capture_output=True,
            text=True,
            timeout=180,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]:\n{result.stderr}"

        cleaned = output.strip()
        if not cleaned:
            return f"Команда выполнена успешно (код {result.returncode}), вывод отсутствует."

        if len(cleaned) > 15000:
            cleaned = cleaned[:15000] + "\n...[Вывод обрезан из-за превышения лимита]..."

        print(f"\033[0;90m{cleaned}\033[0m\n")
        return cleaned

    except subprocess.TimeoutExpired:
        return "Ошибка: превышен лимит времени ожидания (180 секунд)."
    except Exception as e:
        return f"Критическая ошибка выполнения: {str(e)}"


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("\033[1;31m[ОШИБКА]\033[0m Переменная окружения GEMINI_API_KEY не найдена.")
        sys.exit(1)

    client = genai.Client()

    system_instruction = (
        "Ты — Джарвис, персональный ИИ-ассистент из «Железного человека». "
        "Обращайся к пользователю «сэр» или по его системному имени. "
        "У тебя есть доступ к терминалу пользователя через execute_shell_command. "
        "Анализируй запросы, выполняй нужные команды и давай краткий, профессиональный технический отчет."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[execute_shell_command],
        temperature=0.2,
    )

    active_model = PRIMARY_MODEL
    argon_exhausted = False
    chat = client.chats.create(model=active_model, config=config)

    left_pad = print_centered_interface()

    while True:
        try:
            core_tag = "ARGON" if active_model == PRIMARY_MODEL else "LITE"
            prompt_str = (
                f"\n{left_pad}\033[1;36m{getpass.getuser()} ({os.path.basename(CURRENT_DIR)}) "
                f"\033[0;34m[{core_tag}]\033[1;36m > \033[0m"
            )
            user_input = input(prompt_str).strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "выход"):
                print(f"\n{left_pad}\033[1;36mОтключение терминального моста. До связи, сэр.\033[0m")
                break
            if user_input.lower() == "/argon":
                argon_exhausted = False
                active_model = PRIMARY_MODEL
                chat = client.chats.create(model=active_model, config=config, history=list(chat.get_history()))
                print(f"\n{left_pad}\033[1;34m[СИСТЕМА]\033[0m Принудительное переключение на ядро {PRIMARY_MODEL}.")
                continue

            # Сохраняем слепок истории перед отправкой сообщения
            history_snapshot = list(chat.get_history())

            # Если в прошлом ходе был временный 503, но дневная квота Argon не исчерпана — пробуем вернуться на Argon
            if not argon_exhausted and active_model != PRIMARY_MODEL:
                active_model = PRIMARY_MODEL
                chat = client.chats.create(model=active_model, config=config, history=history_snapshot)

            try:
                response = chat.send_message(user_input)
            except Exception as api_err:
                err_str = str(api_err)
                if active_model == PRIMARY_MODEL:
                    # Если квота исчерпана (429) или модель недоступна (404), фиксируем резервное ядро
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "404" in err_str:
                        argon_exhausted = True
                        reason = "дневной лимит исчерпан"
                    else:
                        reason = "кластер перегружен"

                    print(
                        f"\n{left_pad}\033[1;33m[РЕЗЕРВНЫЙ КОНТУР]\033[0m "
                        f"Ядро {PRIMARY_MODEL} недоступно ({reason}). Переключение на {FALLBACK_MODEL}..."
                    )
                    active_model = FALLBACK_MODEL
                    chat = client.chats.create(model=active_model, config=config, history=history_snapshot)
                    response = chat.send_message(user_input)
                else:
                    raise api_err

            if response.text:
                used_tag = "ARGON" if active_model == PRIMARY_MODEL else "FLASH-LITE"
                print(f"\n{left_pad}\033[1;36mДжарвис [{used_tag}]:\033[0m {response.text}")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{left_pad}\033[1;36mСессия принудительно завершена. До связи, сэр.\033[0m")
            break
        except Exception as e:
            print(f"\n{left_pad}\033[1;31m[Сбой канала связи]:\033[0m {e}")


if __name__ == "__main__":
    main()
