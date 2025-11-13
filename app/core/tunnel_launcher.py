import subprocess
import re
import os
import threading

def update_env_var(key: str, value: str, env_path=".env"):
    lines, found = [], False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[INFO] {key} обновлён в {env_path}")

def start_tuna():
    # Возвращение к команде tuna
    proc = subprocess.Popen(
        ["tuna", "http", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in proc.stdout: # type: ignore
        print(line, end="")
        # Шаблон для tuna
        match = re.search(r"Forwarding\s+(https://[^\s]+)\s+->", line)
        if match:
            public_url = match.group(1)
            os.environ["WEB_APP_URL"] = public_url
            update_env_var("WEB_APP_URL", public_url)
            print(f"\n[INFO] Установлен WEB_APP_URL={public_url}\n")
            # Не используем break, чтобы позволить процессу tuna продолжать вывод
            # и оставаться живым.
            
    # Процесс остается запущенным в потоке (threading.Thread)
    proc.wait() 

def run_tunnel():
    threading.Thread(target=start_tuna, daemon=True).start()