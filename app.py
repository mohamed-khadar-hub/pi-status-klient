import threading
import time
import socket

import psutil
import requests
from flask import Flask, render_template

# ── Innstillinger ───────────────────────────────────────────────
TEACHER_URL = "http://10.2.0.58:5000/data"   # ← IP-adressen du får av læreren. Husk port 5000 og /data til slutt, og http:// foran!
NAME = "Mohamed"                          # ← ditt eget navn
SEND_INTERVAL = 30                             # Antall sekunder mellom hver sending. Denne kan godt stå på 30.
# ──────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

def get_local_ip(): # ny kode for å hente ut riktig IP fra Pien.
    try:
        # Komplisert forklaring: Oppretter kobling mot en ekstern adresse. Ingen data sendes – vi bruker det bare for å se hvilken IP-adresse OSet velger, og finner dermed vår lokale IP.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"

def get_status():
    """Henter systeminfo fra denne Pi-en og pakker det i en dict."""
    # Prøv å finne IP-adressen. Hvis det feiler, bruk teksten "unknown".
    try:
        ip = get_local_ip()
    except Exception:
        ip = "unknown"

    # Hvor lenge maskinen har vært på, regnet om til timer og minutter.
    uptime_seconds = time.time() - psutil.boot_time()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    return {
        "name":     NAME,
        "hostname": socket.gethostname(),
        "ip":       ip,
        "cpu":      psutil.cpu_percent(interval=1)*100,   # CPU-bruk i prosent
        "ram":      psutil.virtual_memory().percent*100,  # RAM-bruk i prosent
        "disk":     psutil.disk_usage("/").percent*100,   # Diskbruk i prosent
        "uptime":   f"{hours}h {minutes}m",
    }

@app.route("/")
def index():
    # Viser statussiden til eleven i nettleseren.
    return render_template("status.html", s=get_status())


def send_loop():
    # Kjører hele tiden i bakgrunnen og sender status til lærer-serveren.
    while True:
        try:
            requests.post(TEACHER_URL, json=get_status(), timeout=5)
        except Exception:
            # Får vi ikke kontakt (server nede, feil IP, e.l.) hopper vi bare over
            # og prøver igjen ved neste runde.
            pass
        time.sleep(SEND_INTERVAL)


# daemon=True gjør at tråden stopper automatisk når hovedprogrammet avsluttes.
threading.Thread(target=send_loop, daemon=True).start()

if __name__ == "__main__":
    # Port 8080: åpne http://<din-ip>:8080 for å se din egen side.
    app.run(host="0.0.0.0", port=8080)
