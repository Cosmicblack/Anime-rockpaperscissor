import tkinter as tk
from tkinter import ttk
import random
import os
import platform
import subprocess
import wave
import math
import tempfile
import threading
import urllib.request
import urllib.parse

# ==========================================
# 1. LOCALIZATION (Language Support)
# ==========================================
CURRENT_LANG = "English"

TRANSLATIONS = {
    "English": {
        "title": "ANIME ARENA v22.0", "choose_fighter": "CHOOSE YOUR FIGHTER:", "match_type": "SELECT MATCH TYPE:",
        "enter_arena": "ENTER ARENA", "best_3": "Best of 3 Match", "best_5": "Best of 5 Match",
        "time_rush": "30-Second Rush", "infinite": "Infinite Survival", "awaiting": "AWAITING COMMAND...",
        "restart": "RESTART MATCH", "main_menu": "MAIN MENU", "victory": "VICTORY FOR", "defeat": "DEFEATED BY BOSS DIO!",
        "stalemate": "STALEMATE", "clash": "CLASH! Both threw", "critical": "CRITICAL!", "damage": "DAMAGE!",
        "beats": "beats", "language": "LANGUAGE:"
    },
    "日本語 (Japanese)": {
        "title": "アニメアリーナ v22.0", "choose_fighter": "ファイターを選択:", "match_type": "マッチタイプを選択:",
        "enter_arena": "アリーナに入る", "best_3": "3本勝負", "best_5": "5本勝負", "time_rush": "30秒ラッシュ",
        "infinite": "無限サバイバル", "awaiting": "コマンド待機中...", "restart": "再スタート", "main_menu": "メインメニュー",
        "victory": "の勝利!", "defeat": "ボス・ディオに敗北!", "stalemate": "引き分け", "clash": "激突! 両者:",
        "critical": "クリティカル!", "damage": "ダメージ!", "beats": "が勝つ", "language": "言語:"
    }
}

def t(key): return TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["English"]).get(key, key)

# ==========================================
# 2. AUDIO ENGINE (NETWORK, MANUAL, 8-BIT)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# NEW DIRECTORY: Guarantees a fresh start with no old broken files
VOICE_DIR = os.path.join(BASE_DIR, "anime_voices_v22") 
TEMP_DIR = tempfile.gettempdir()
SOUND_FILES = {}
system_os = platform.system()
current_bgm_process = None
is_muted = False

if system_os == "Windows":
    import winsound
    import ctypes

if not os.path.exists(VOICE_DIR):
    os.makedirs(VOICE_DIR)

def is_valid_audio(filepath):
    try:
        if not os.path.exists(filepath): return False
        if os.path.getsize(filepath) < 500: return False # Protects short valid MP3s
        with open(filepath, 'rb') as f:
            header = f.read(500).lower()
            if b'<html' in header or b'cloudflare' in header or b'just a moment' in header: return False
        return True
    except: return False

def generate_retro_voice(filename, file_path):
    """Generates an 8-bit procedural sound effect based on the character if ALL MP3 downloads fail."""
    notes = [(400, 0.1), (600, 0.2)]
    wave_type = 'square'
    
    if "gojo" in filename: notes, wave_type = [(400, 0.1), (800, 0.1), (1200, 0.4)], 'sine'
    elif "naruto" in filename: notes, wave_type = [(200, 0.05), (300, 0.05), (200, 0.05), (300, 0.05), (400, 0.2)], 'saw'
    elif "sasuke" in filename: notes, wave_type = [(800, 0.05), (1000, 0.05), (1200, 0.2)], 'square'
    elif "goku" in filename: notes, wave_type = [(100, 0.1), (200, 0.1), (400, 0.1), (800, 0.4)], 'sine'
    elif "luffy" in filename: notes, wave_type = [(300, 0.1), (500, 0.1), (200, 0.2)], 'square'
    elif "zoro" in filename: notes, wave_type = [(600, 0.1), (400, 0.2)], 'saw'
    elif "jotaro" in filename: notes, wave_type = [(150, 0.05), (200, 0.05)] * 4 + [(100, 0.3)], 'square'
    elif "dio" in filename: notes, wave_type = [(100, 0.2), (50, 0.5)], 'saw'
    
    if "ult" in filename: notes = [(f * 1.5, d * 1.5) for f, d in notes]
    _make_sfx(file_path, notes, wave_type)

def play_local_voice(filename):
    """Core player that plays any local file natively."""
    if is_muted: return
    file_path = os.path.join(VOICE_DIR, filename)
    if not os.path.exists(file_path): return
    
    def _play():
        try:
            if system_os == "Windows":
                mci_path = file_path.replace("\\", "/")
                alias = f"v_{random.randint(100, 99999)}"
                ctypes.windll.winmm.mciSendStringW(f'open "{mci_path}" alias {alias}', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
            elif system_os == "Darwin": subprocess.run(["afplay", file_path])
            elif system_os == "Linux": subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path])
        except: pass
    threading.Thread(target=_play, daemon=True).start()

def play_voice(filename, web_urls):
    if is_muted: return
    file_path = os.path.join(VOICE_DIR, filename)
    if isinstance(web_urls, str): web_urls = [web_urls]

    def _audio_thread():
        # Clean corrupted files from previous failed attempts
        if os.path.exists(file_path) and not is_valid_audio(file_path):
            try: os.remove(file_path)
            except: pass

        # If user manually added the file, skip downloading
        if not os.path.exists(file_path):
            downloaded = False
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            for web_url in web_urls:
                if downloaded: break
                try:
                    if system_os == "Windows": subprocess.run(["curl", "-s", "-L", "-A", user_agent, web_url, "-o", file_path], creationflags=subprocess.CREATE_NO_WINDOW, timeout=4)
                    else: subprocess.run(["curl", "-s", "-L", "-A", user_agent, web_url, "-o", file_path], timeout=4)
                    if is_valid_audio(file_path): downloaded = True; break
                except: pass

                encoded_url = urllib.parse.quote(web_url)
                mirrors = [f"https://api.codetabs.com/v1/proxy?quest={encoded_url}", f"https://api.allorigins.win/raw?url={encoded_url}"]
                for mirror in mirrors:
                    try:
                        req = urllib.request.Request(mirror, headers={'User-Agent': user_agent, 'Referer': 'https://www.myinstants.com/'})
                        with urllib.request.urlopen(req, timeout=4) as response:
                            data = response.read()
                            if len(data) > 500 and b'<html' not in data[:100].lower():
                                with open(file_path, 'wb') as f: f.write(data)
                                downloaded = True; break
                    except: continue

            # LAST RESORT: Retro sound & Terminal Manual Download Instructions
            if not downloaded or not is_valid_audio(file_path):
                print(f"\n[NETWORK BLOCKED] Cloudflare prevented automatic download of {filename}")
                print(f"--> Playing 8-Bit Retro Sound Fallback.")
                print(f"--> FIX IT: Download this link manually: {web_urls[0]}")
                print(f"--> Save it as '{filename}' inside the '{VOICE_DIR}' folder.\n")
                generate_retro_voice(filename, file_path)

        play_local_voice(filename) # Hand off to universal local player

    threading.Thread(target=_audio_thread, daemon=True).start()

# ==========================================
# 3. PROCEDURAL SOUND EFFECTS & BGM
# ==========================================
def _make_sfx(filename, notes, wave_type='square'):
    sr = 8000
    with wave.open(filename, 'w') as f:
        f.setnchannels(1); f.setsampwidth(1); f.setframerate(sr)
        data = bytearray()
        for freq, duration in notes:
            for i in range(int(sr * duration)):
                t_val = i / sr
                if freq == 0: val = 127
                elif wave_type == 'sine': val = int(127 + 127 * math.sin(2 * math.pi * freq * t_val))
                elif wave_type == 'square': val = 255 if math.sin(2 * math.pi * freq * t_val) > 0 else 0
                elif wave_type == 'saw': val = int(((freq * t_val) % 1) * 255)
                data.append(max(0, min(255, val)))
        f.writeframesraw(data)

def _make_bgm(filename):
    sr, beat = 8000, 60.0 / 125
    data = bytearray()
    notes = [110, 110, 0, 110, 220, 110, 0, 110]
    for i in range(int(sr * beat * 16)):
        t_val = i / sr; bt = t_val % beat
        kick = math.sin(2 * math.pi * (150 * max(0, 1 - (bt * 5)) + 40) * bt) * max(0, 1 - (bt * 5))
        freq = notes[int(t_val / (beat / 4)) % len(notes)]
        synth = (((freq * t_val) % 1.0 - 0.5) * 2.0) if freq > 0 else 0
        data.append(max(0, min(255, int(((kick * 0.7) + (synth * 0.4) + 1.0) * 127))))
    with wave.open(filename, 'w') as f:
        f.setnchannels(1); f.setsampwidth(1); f.setframerate(sr); f.writeframesraw(data)

def generate_sounds():
    global SOUND_FILES
    SOUND_FILES = {'click': os.path.join(TEMP_DIR, 'rps_click.wav'), 'hit': os.path.join(TEMP_DIR, 'rps_hit.wav'),
                   'win': os.path.join(TEMP_DIR, 'rps_win.wav'), 'lose': os.path.join(TEMP_DIR, 'rps_lose.wav'), 'bgm': os.path.join(TEMP_DIR, 'rps_bgm.wav')}
    _make_sfx(SOUND_FILES['click'], [(1200, 0.02), (0, 0.01)], 'square')
    _make_sfx(SOUND_FILES['hit'], [(100, 0.1), (50, 0.1)], 'saw')
    _make_sfx(SOUND_FILES['win'], [(440, 0.1), (659, 0.1), (880, 0.2)], 'sine')
    _make_sfx(SOUND_FILES['lose'], [(270, 0.1), (200, 0.2)], 'saw')
    _make_bgm(SOUND_FILES['bgm'])
generate_sounds()

def play_sfx(name):
    if is_muted: return
    try:
        if system_os == "Windows": winsound.PlaySound(SOUND_FILES.get(name,''), winsound.SND_ASYNC | winsound.SND_FILENAME)
        else: subprocess.Popen(["afplay" if system_os == "Darwin" else "aplay", SOUND_FILES.get(name,'')])
    except: pass

def start_bgm():
    global current_bgm_process
    if is_muted: return
    try:
        if system_os == "Windows": winsound.PlaySound(SOUND_FILES['bgm'], winsound.SND_ASYNC | winsound.SND_LOOP | winsound.SND_FILENAME)
        else: current_bgm_process = subprocess.Popen(["afplay" if system_os == "Darwin" else "aplay", SOUND_FILES['bgm']])
    except: pass

def stop_bgm():
    global current_bgm_process
    try:
        if system_os == "Windows": winsound.PlaySound(None, winsound.SND_ASYNC)
        elif current_bgm_process: current_bgm_process.terminate(); current_bgm_process = None
    except: pass

def toggle_mute():
    global is_muted; is_muted = not is_muted
    if is_muted: stop_bgm(); mute_btn.config(text="🔇", fg=COLORS["error"])
    else: start_bgm(); mute_btn.config(text="🔊", fg=COLORS["primary"]); play_sfx('click')

# ==========================================
# 4. UI WIDGETS
# ==========================================
COLORS = {"bg": "#0D0D12", "surface": "#1A1A24", "primary": "#00FFCC", "secondary": "#FF007F", "error": "#FF3366", "text": "#FFFFFF", "ult": "#FFD700"}

class ModernDropdown(tk.Frame):
    def __init__(self, parent, options, default_val, width=300, command=None):
        super().__init__(parent, bg=COLORS["surface"], width=width, height=40, cursor="hand2")
        self.pack_propagate(False); self.options = options; self.current_val = default_val; self.command = command; self.is_open = False; self.menu_win = None
        self.display_lbl = tk.Label(self, text=f"{self.current_val}  ▼", font=("Segoe UI", 12, "bold"), bg=COLORS["surface"], fg=COLORS["text"])
        self.display_lbl.pack(expand=True, fill=tk.BOTH)
        for w in (self, self.display_lbl):
            w.bind("<Button-1>", self.toggle)
            w.bind("<Enter>", lambda e: self.config(bg="#2A2A3A") or self.display_lbl.config(bg="#2A2A3A", fg=COLORS["primary"]))
            w.bind("<Leave>", lambda e: self.config(bg=COLORS["surface"]) or self.display_lbl.config(bg=COLORS["surface"], fg=COLORS["text"]))
    def toggle(self, event=None):
        play_sfx('click')
        if self.is_open and (not self.menu_win or not self.menu_win.winfo_exists()): self.is_open = False
        if self.is_open: return self.close()
        self.is_open = True; self.menu_win = tk.Toplevel(self); self.menu_win.wm_overrideredirect(True); self.menu_win.attributes('-topmost', True); self.menu_win.config(bg=COLORS["primary"])
        opts = self.options[:10]
        self.menu_win.geometry(f"{self.winfo_width()}x{len(opts)*40}+{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height()}")
        for opt in opts:
            btn = tk.Label(self.menu_win, text=opt, font=("Segoe UI", 12), bg=COLORS["surface"], fg=COLORS["text"], pady=8, cursor="hand2")
            btn.pack(fill=tk.X, pady=(0, 1))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["primary"], fg="#000"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["surface"], fg=COLORS["text"]))
            btn.bind("<Button-1>", lambda e, o=opt: self.select(o))
    def close(self): self.is_open = False; (self.menu_win.destroy() if self.menu_win and self.menu_win.winfo_exists() else None)
    def select(self, val): play_sfx('click'); self.current_val = val; self.display_lbl.config(text=f"{val}  ▼"); self.close(); (self.command(val) if self.command else None)
    def get(self): return self.current_val

class ModernRoundButton(tk.Canvas):
    def __init__(self, parent, size, text, emoji, bg_color, command):
        super().__init__(parent, width=size, height=size, bg=COLORS["bg"], highlightthickness=0)
        self.command = command; self.bg_color = bg_color; self.disabled = False
        self.oval = self.create_oval(5, 5, size-5, size-5, fill=bg_color, outline="")
        self.emoji_text = self.create_text(size/2, size/2 - 10, text=emoji, font=("Segoe UI Emoji", int(size/3.5)))
        self.label_text = self.create_text(size/2, size/2 + 20, text=text, font=("Helvetica", 9, "bold"), fill=COLORS["text"])
        for item in (self.oval, self.emoji_text, self.label_text):
            self.tag_bind(item, "<Enter>", lambda e: self.itemconfig(self.oval, fill="#FFFFFF") if not self.disabled else None)
            self.tag_bind(item, "<Leave>", lambda e: self.itemconfig(self.oval, fill=self.bg_color) if not self.disabled else None)
            self.tag_bind(item, "<Button-1>", lambda e: self.command() if not self.disabled else None)
    def set_state(self, state): self.disabled = (state == tk.DISABLED); self.itemconfig(self.oval, fill="#333333" if self.disabled else self.bg_color)

# ==========================================
# 5. ROSTER & ULTIMATES
# ==========================================
ROSTER = {
    "Gojo (Jujutsu Kaisen)": {"color": "#BB86FC", "idle": "( ⌐■_■)🤞", "attack": "( ಠ_ಠ)🫴🔴", "hit": "( ≖_≖)", "win": "( ˘▽˘) ♾️", "file": "gojo.mp3", "url": ["https://www.myinstants.com/media/sounds/hollow-purple.mp3", "https://www.myinstants.com/media/sounds/gojo-hollow-purple.mp3"], "ult_name": "DOMAIN EXPANSION", "ult_file": "gojo_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/muryokusho-domain-expansion-1.mp3", "https://www.myinstants.com/media/sounds/domain-expansion_3.mp3"]},
    "Yuji (Jujutsu Kaisen)": {"color": "#FF3333", "idle": "( Ò_Ó)🥊", "attack": "( ╬ Ò_Ó)💨", "hit": "( >﹏<)", "win": "( ≧ᗜ≦) 👊", "file": "yuji.mp3", "url": ["https://www.myinstants.com/media/sounds/yuji-itadori-shout.mp3", "https://www.myinstants.com/media/sounds/itadori-yuji-shout.mp3"], "ult_name": "DOMAIN EXPANSION", "ult_file": "yuji_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/black-flash_h4C30X2.mp3", "https://www.myinstants.com/media/sounds/kokusen_1.mp3"]},
    "Megumi (Jujutsu Kaisen)": {"color": "#4A90E2", "idle": "( ⇀_↼)🐺", "attack": "( ಠ_ಠ)🦅", "hit": "( ×_×)", "win": "( ˘_˘) 🐸", "file": "megumi.mp3", "url": ["https://www.myinstants.com/en/instant/megumi-42206/", "https://www.myinstants.com/en/instant/megumi-42206/"], "ult_name": "DOMAIN EXPANSION", "ult_file": "megumi_ult.mp3", "ult_url": ["https://www.myinstants.com/en/instant/domain-expansion-48982/", "https://www.myinstants.com/en/instant/domain-expansion-48982/"]},
    "Naruto (Naruto)": {"color": "#FF9800", "idle": "( ⇀‸↼)🍥", "attack": "(ง Ò_Ó)ง💨", "hit": "(×﹏×)", "win": "( ≧ᗜ≦) 🦊", "file": "naruto.mp3", "url": ["https://www.myinstants.com/media/sounds/naruto-rasengan-sound-effect.mp3", "https://www.myinstants.com/media/sounds/rasengan_2.mp3"], "ult_name": "RASEN SHURIKEN", "ult_file": "naruto_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/naruto-rasenshuriken.mp3", "https://www.myinstants.com/media/sounds/rasenshuriken.mp3"]},
    "Sasuke (Naruto)": {"color": "#673AB7", "idle": "( ⇀_↼)🗡️", "attack": "( ಠ_ಠ)⚡", "hit": "( >_<)", "win": "( ≖_≖) 🦅", "file": "sasuke.mp3", "url": ["https://www.myinstants.com/media/sounds/sasuke-chidori.mp3", "https://www.myinstants.com/media/sounds/chidori_1.mp3"], "ult_name": "SUSANOO", "ult_file": "sasuke_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/sasuke-amaterasu.mp3", "https://www.myinstants.com/media/sounds/amaterasu.mp3"]},
    "Goku (Dragon Ball)": {"color": "#FFC107", "idle": "( ˘▽˘)🐉", "attack": "( ╬ Ò_Ó)🔥", "hit": "( >﹏<)", "win": "( ≧ᗜ≦) 💥", "file": "goku.mp3", "url": ["https://www.myinstants.com/media/sounds/kamehameha.mp3", "https://www.myinstants.com/media/sounds/goku-kamehameha.mp3"], "ult_name": "SUPER SAIYAN", "ult_file": "goku_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/goku-super-saiyan-theme.mp3", "https://www.myinstants.com/media/sounds/goku-screaming.mp3"]},
    "Luffy (One Piece)": {"color": "#FF5252", "idle": "( ˘▽˘)🍖", "attack": "( ╬ Ò_Ó)🥊", "hit": "( >﹏<)", "win": "( ≧ᗜ≦) 🏴‍☠️", "file": "luffy.mp3", "url": ["https://www.myinstants.com/media/sounds/gomu-gomu-no-pistol.mp3", "https://www.myinstants.com/media/sounds/luffy-pistol.mp3"], "ult_name": "GEAR FIFTH", "ult_file": "luffy_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/luffy-gear-5-drums-of-liberation.mp3", "https://www.myinstants.com/media/sounds/gear-5.mp3"]},
    "Zoro (One Piece)": {"color": "#4CAF50", "idle": "( ⇀_↼)⚔️", "attack": "( ╬ Ò_Ó)🗡️", "hit": "( ×_×)", "win": "( ˘▽˘) 🍶", "file": "zoro.mp3", "url": ["https://www.myinstants.com/media/sounds/zoro-santoryu-secret-technique.mp3", "https://www.myinstants.com/media/sounds/zoro-santoryu.mp3"], "ult_name": "ASURA", "ult_file": "zoro_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/zoro-ashura_1.mp3", "https://www.myinstants.com/media/sounds/zoro-ashura.mp3"]},
    "Jotaro (JoJo)": {"color": "#3F51B5", "idle": "( ⌐■_■)🧢", "attack": "( ಠ_ಠ)👊", "hit": "( ✖_✖)", "win": "( ≖_≖) 🚬", "file": "jotaro.mp3", "url": ["https://www.myinstants.com/media/sounds/jotaro-ora-ora-ora.mp3", "https://www.myinstants.com/media/sounds/ora-ora.mp3"], "ult_name": "STAR PLATINUM", "ult_file": "jotaro_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/star-platinum-za-warudo_1.mp3", "https://www.myinstants.com/media/sounds/star-platinum-za-warudo.mp3"]},
    "Tanjiro (Demon Slayer)": {"color": "#009688", "idle": "( ˘_˘)🌊", "attack": "( Ò_Ó)🗡️", "hit": "( >﹏<)", "win": "( ≧ᗜ≦) ☀️", "file": "tanjiro.mp3", "url": ["https://www.myinstants.com/media/sounds/water-breathing-first-form.mp3", "https://www.myinstants.com/media/sounds/water-breathing.mp3"], "ult_name": "HINOKAMI KAGURA", "ult_file": "tanjiro_ult.mp3", "ult_url": ["https://www.myinstants.com/media/sounds/hinokami-kagura-dance.mp3", "https://www.myinstants.com/media/sounds/hinokami-kagura.mp3"]}
}
ANIME_HERO = ROSTER["Gojo (Jujutsu Kaisen)"]
ANIME_BOSS = {"idle": "( ◣_◢)", "attack": "( ಠ益ಠ)", "hit": "(✖╭╮✖)", "win": "( ≖ ͜ʖ≖)", "color": "#FF3366", "file": "boss_dio.mp3", "url": ["https://www.myinstants.com/media/sounds/za-warudo-toki-yo-tomare.mp3", "https://www.myinstants.com/media/sounds/dio-za-warudo.mp3"]}
SIGNS = {'Rock': '🪨', 'Paper': '📄', 'Scissors': '✂️', 'Lizard': '🦎', 'Spock': '🖖', 'Fist': '✊', 'Ult': '🌟'}

# --- GAME STATE ---
p_score, e_score, ult_charge = 0, 0, 0
game_mode, max_steps, time_left = "steps", 3, 30
user_history = {'Rock': 0, 'Paper': 0, 'Scissors': 0, 'Lizard': 0, 'Spock': 0}
battle_state, game_active = "idle", True
anim_seq_id, idle_loop_id, timer_id = 0, None, None
frame, p_x, p_y, e_x, e_y = 0, 130, 110, 470, 110

def update_character_state(state, p_sign, e_sign):
    arena.itemconfig(player_sprite, text=f"{ANIME_HERO[state]}\n{p_sign}")
    arena.itemconfig(enemy_sprite, text=f"{ANIME_BOSS[state]}\n{e_sign}")

def start_idle():
    global idle_loop_id
    if idle_loop_id: game_window.after_cancel(idle_loop_id); idle_loop_id = None
    render_idle()

def render_idle():
    global frame, idle_loop_id
    if battle_state != "idle": return
    frame += 1
    bob = math.sin(frame * 0.1) * 6
    pulse = math.sin(frame * 0.05) * 10
    arena.coords(player_sprite, p_x, p_y + bob); arena.coords(enemy_sprite, e_x, e_y + bob)
    arena.coords(player_aura, p_x - 70 - pulse, p_y - 70 - pulse, p_x + 70 + pulse, p_y + 70 + pulse)
    arena.coords(enemy_aura, e_x - 70 - pulse, e_y - 70 - pulse, e_x + 70 + pulse, e_y + 70 + pulse)
    idle_loop_id = game_window.after(20, render_idle)

def charge_ult(amount):
    global ult_charge
    if ult_charge >= 100 or not game_active: return
    ult_charge = min(100, ult_charge + amount)
    arena.coords(ult_bar_fill, 20, 235, 20 + (ult_charge * 2.6), 245)
    if ult_charge >= 100: ult_btn.config(state=tk.NORMAL, bg=COLORS["ult"], fg="#000", text=f"🔥 {ANIME_HERO['ult_name']} 🔥"); play_sfx('win')

def trigger_ultimate():
    global ult_charge, p_score
    if ult_charge < 100 or not game_active or battle_state != "idle": return
    ult_charge = 0; arena.coords(ult_bar_fill, 20, 235, 20, 245)
    ult_btn.config(state=tk.DISABLED, bg=COLORS["surface"], fg="#555", text="ULTIMATE CHARGING...")
    play_voice(ANIME_HERO["ult_file"], ANIME_HERO["ult_url"])
    arena.itemconfig(bg_rect, fill="#000"); arena.itemconfig(player_aura, outline=COLORS["ult"], width=5)
    p_score += 1 
    log_text.config(text=f"💥 {ANIME_HERO['ult_name'].upper()}! UNBLOCKABLE ATTACK! 💥", fg=COLORS["ult"])
    animate_throw("Ult", random.choice(list(SIGNS.keys())[:-2]), "player", True)

def animate_throw(p_choice, e_choice, winner, is_ultimate=False):
    global battle_state, anim_seq_id; battle_state = "animating"; anim_seq_id += 1; my_seq = anim_seq_id  
    for btn in action_buttons.values(): btn.set_state(tk.DISABLED)
    ult_btn.config(state=tk.DISABLED)
    if not is_ultimate: play_voice(ANIME_HERO["file"] if winner in ["player", "draw"] else ANIME_BOSS["file"], ANIME_HERO["url"] if winner in ["player", "draw"] else ANIME_BOSS["url"])
    update_character_state("attack", SIGNS["Fist"], SIGNS["Fist"])
    def pump(count):
        if anim_seq_id != my_seq: return 
        if count > 0: arena.move(player_sprite, 0, -15); arena.move(player_aura, 0, -15); arena.move(enemy_sprite, 0, -15); arena.move(enemy_aura, 0, -15); play_sfx('click'); game_window.after(80, lambda: drop(count))
        else: clash()
    def drop(count):
        if anim_seq_id != my_seq: return 
        arena.move(player_sprite, 0, 15); arena.move(player_aura, 0, 15); arena.move(enemy_sprite, 0, 15); arena.move(enemy_aura, 0, 15); game_window.after(100, lambda: pump(count - 1))
    def clash():
        if anim_seq_id != my_seq: return 
        update_character_state("attack", SIGNS[p_choice], SIGNS[e_choice])
        arena.coords(player_sprite, p_x + 120, p_y); arena.coords(player_aura, p_x+50, p_y-70, p_x+190, p_y+70); arena.coords(enemy_sprite, e_x - 120, e_y); arena.coords(enemy_aura, e_x-190, e_y-70, e_x-50, e_y+70); play_sfx('hit')
        if winner == "player": arena.itemconfig(enemy_sprite, text=f"{ANIME_BOSS['hit']}\n{SIGNS[e_choice]}"); arena.itemconfig(player_sprite, text=f"{ANIME_HERO['win']}\n{SIGNS[p_choice]}"); shake(enemy_sprite, 12 if is_ultimate else 8, my_seq); shake(enemy_aura, 12 if is_ultimate else 8, my_seq)
        elif winner == "enemy": arena.itemconfig(player_sprite, text=f"{ANIME_HERO['hit']}\n{SIGNS[p_choice]}"); arena.itemconfig(enemy_sprite, text=f"{ANIME_BOSS['win']}\n{SIGNS[e_choice]}"); shake(player_sprite, 8, my_seq); shake(player_aura, 8, my_seq)
        else: shake(player_sprite, 4, my_seq); shake(enemy_sprite, 4, my_seq)
        game_window.after(900, reset_pos)
    def reset_pos():
        global battle_state
        if anim_seq_id != my_seq: return
        arena.itemconfig(bg_rect, fill=COLORS["bg"]); arena.itemconfig(player_aura, outline=ANIME_HERO["color"], width=2); arena.coords(player_sprite, p_x, p_y); arena.coords(enemy_sprite, e_x, e_y)
        battle_state = "idle"; update_character_state("idle", SIGNS['Fist'], SIGNS['Fist']); update_scores(); check_game_over()
        if game_active:
            for btn in action_buttons.values(): btn.set_state(tk.NORMAL)
            if ult_charge >= 100: ult_btn.config(state=tk.NORMAL)
        start_idle() 
    pump(2)

def shake(sprite, shakes_left, my_seq, orig_coords=None):
    if anim_seq_id != my_seq: return
    if orig_coords is None: orig_coords = arena.coords(sprite); (None if orig_coords else ...)
    if not orig_coords: return
    if shakes_left > 0:
        offset = random.randint(-15, 15)
        if len(orig_coords) == 2: arena.coords(sprite, orig_coords[0] + offset, orig_coords[1])
        elif len(orig_coords) == 4: arena.coords(sprite, orig_coords[0] + offset, orig_coords[1], orig_coords[2] + offset, orig_coords[3])
        game_window.after(20, lambda: shake(sprite, shakes_left - 1, my_seq, orig_coords))
    else: arena.coords(sprite, *orig_coords)

def play(p_choice):
    global p_score, e_score
    if not game_active or battle_state != "idle": return 
    user_history[p_choice] += 1
    choices = list(SIGNS.keys())[:-2] 
    if sum(user_history.values()) < 3: e_choice = random.choice(choices)
    else: e_choice = random.choice({'Rock': ['Paper', 'Spock'], 'Paper': ['Scissors', 'Lizard'], 'Scissors': ['Rock', 'Spock'], 'Lizard': ['Rock', 'Scissors'], 'Spock': ['Paper', 'Lizard']}[max(user_history, key=user_history.get)]) if random.random() < 0.7 else random.choice(choices)
    win_conds = {'Rock': ['Scissors', 'Lizard'], 'Paper': ['Rock', 'Spock'], 'Scissors': ['Paper', 'Lizard'], 'Lizard': ['Spock', 'Paper'], 'Spock': ['Scissors', 'Rock']}
    if p_choice == e_choice: winner = "draw"; log_text.config(text=f"{t('clash')} {p_choice}.", fg=COLORS["text"]); charge_ult(15)
    elif e_choice in win_conds[p_choice]: winner = "player"; p_score += 1; log_text.config(text=f"{t('critical')} {p_choice} {t('beats')} {e_choice}.", fg=ANIME_HERO["color"]); charge_ult(35)
    else: winner = "enemy"; e_score += 1; log_text.config(text=f"{t('damage')} {e_choice} {t('beats')} {p_choice}.", fg=COLORS["error"]); charge_ult(10)
    animate_throw(p_choice, e_choice, winner)

def update_scores(): p_score_lbl.config(text=f"{p_score}"); e_score_lbl.config(text=f"{e_score}")
def check_game_over():
    if game_mode == "steps" and game_active:
        if p_score >= max_steps: end_match("player")
        elif e_score >= max_steps: end_match("enemy")
def countdown():
    global time_left, timer_id
    if game_mode == "time" and game_active:
        if time_left > 0: time_left -= 1; timer_label.config(text=f"00:{time_left:02d}"); timer_id = game_window.after(1000, countdown)
        else:
            timer_label.config(text="TIME UP", fg=COLORS["error"])
            if p_score > e_score: end_match("player")
            elif e_score > p_score: end_match("enemy")
            else: end_match("draw")

def end_match(winner):
    global game_active, timer_id; game_active = False
    for btn in action_buttons.values(): btn.set_state(tk.DISABLED)
    ult_btn.config(state=tk.DISABLED)
    if timer_id: game_window.after_cancel(timer_id); timer_id = None
    if winner == "player":
        # FINAL FIX: Custom Voice File Logic for Gojo
        if "Gojo" in char_dropdown.get(): play_local_voice("gojo_win.mp3") 
        else: play_sfx('win')
        
        log_text.config(text=f"{char_dropdown.get().split(' ')[0].upper()} {t('victory')}" if CURRENT_LANG == "日本語 (Japanese)" else f"{t('victory')} {char_dropdown.get().split(' ')[0].upper()}!", fg=ANIME_HERO["color"])
        update_character_state("win", SIGNS["Fist"], SIGNS["Fist"])
    elif winner == "enemy": play_sfx('lose'); log_text.config(text=t('defeat'), fg=COLORS["error"]); update_character_state("hit", SIGNS["Fist"], SIGNS["Fist"])
    else: log_text.config(text=t('stalemate'), fg=COLORS["text"])

def restart_game():
    global p_score, e_score, time_left, game_active, ult_charge, battle_state, timer_id, anim_seq_id
    play_sfx('click'); anim_seq_id += 1 
    if timer_id: game_window.after_cancel(timer_id); timer_id = None
    p_score, e_score, ult_charge, game_active = 0, 0, 0, True
    arena.coords(player_sprite, p_x, p_y); arena.coords(enemy_sprite, e_x, e_y); arena.itemconfig(bg_rect, fill=COLORS["bg"]); arena.itemconfig(player_aura, outline=ANIME_HERO["color"], width=2); arena.coords(ult_bar_fill, 20, 235, 20, 245)
    update_scores(); ult_btn.config(state=tk.DISABLED, bg=COLORS["surface"], fg="#555", text="ULTIMATE CHARGING..."); battle_state = "idle"; log_text.config(text=t('awaiting'), fg=COLORS["primary"]); update_character_state("idle", SIGNS["Fist"], SIGNS["Fist"])
    for btn in action_buttons.values(): btn.set_state(tk.NORMAL)
    start_idle() 
    if game_mode == "time": time_left = 30; timer_label.config(text=f"00:{time_left:02d}", fg=COLORS["primary"]); countdown()

def return_to_main_menu():
    global p_score, e_score, game_active, ult_charge, battle_state, timer_id, anim_seq_id
    play_sfx('click'); lang_dropdown.close(); char_dropdown.close(); anim_seq_id += 1 
    if timer_id: game_window.after_cancel(timer_id); timer_id = None
    if idle_loop_id: game_window.after_cancel(idle_loop_id)
    stop_bgm(); battle_state = "idle"; p_score, e_score, ult_charge, game_active = 0, 0, 0, False
    update_scores(); log_text.config(text=t('awaiting'), fg=COLORS["primary"])
    for btn in action_buttons.values(): btn.set_state(tk.NORMAL)
    game_window.withdraw(); setup_window.deiconify()

# ==========================================
# 7. UI SETUP & APP LAUNCHER
# ==========================================
def update_ui_language(selected_lang):
    global CURRENT_LANG; CURRENT_LANG = selected_lang
    title_lbl.config(text=t("title")); fighter_lbl.config(text=t("choose_fighter")); match_lbl.config(text=t("match_type"))
    enter_btn.config(text=t("enter_arena")); lang_lbl.config(text=t("language"))
    mode_3_btn.config(text=t("best_3")); mode_5_btn.config(text=t("best_5")); mode_time_btn.config(text=t("time_rush")); mode_inf_btn.config(text=t("infinite"))
    log_text.config(text=t("awaiting")); restart_btn.config(text=t("restart")); menu_btn.config(text=t("main_menu"))

def launch():
    global game_mode, max_steps, ANIME_HERO, game_active, ult_charge, battle_state, anim_seq_id, p_score, e_score
    play_sfx('click'); lang_dropdown.close(); char_dropdown.close()
    chosen_char = char_dropdown.get(); ANIME_HERO = ROSTER.get(chosen_char, ROSTER["Gojo (Jujutsu Kaisen)"])
    p_name_lbl.config(text=chosen_char.split(" ")[0].upper(), fg=ANIME_HERO["color"]); arena.itemconfig(player_aura, outline=ANIME_HERO["color"])
    mode_val = mode_var.get()
    if mode_val == "time": game_mode = "time"; timer_label.pack(pady=5); countdown()
    elif mode_val == "endless": game_mode = "endless"; timer_label.pack_forget()
    else: game_mode = "steps"; max_steps = int(mode_val); timer_label.pack_forget()
    game_active = True; battle_state = "idle"; anim_seq_id += 1; p_score, e_score, ult_charge = 0, 0, 0; update_scores()
    arena.coords(ult_bar_fill, 20, 235, 20, 245); ult_btn.config(state=tk.DISABLED, bg=COLORS["surface"], fg="#555", text="ULTIMATE CHARGING...")
    setup_window.withdraw(); game_window.deiconify(); update_character_state("idle", SIGNS["Fist"], SIGNS["Fist"])
    start_idle(); start_bgm()

def on_close(): 
    stop_bgm()
    try: 
        if game_window.winfo_exists(): game_window.destroy()
        if setup_window.winfo_exists(): setup_window.destroy()
    except: pass

setup_window = tk.Tk(); setup_window.title("Anime Auto-Fetch v22.0"); setup_window.geometry("450x650"); setup_window.config(bg=COLORS["bg"]); setup_window.protocol("WM_DELETE_WINDOW", on_close)
title_lbl = tk.Label(setup_window, text=t("title"), font=("Segoe UI Black", 26, "italic"), bg=COLORS["bg"], fg=COLORS["primary"]); title_lbl.pack(pady=(30, 20))
lang_lbl = tk.Label(setup_window, text=t("language"), font=("Segoe UI", 10, "bold"), bg=COLORS["bg"], fg="#888"); lang_lbl.pack(pady=(0, 5))
lang_dropdown = ModernDropdown(setup_window, list(TRANSLATIONS.keys()), "English", width=320, command=update_ui_language); lang_dropdown.pack(pady=(0, 15))
fighter_lbl = tk.Label(setup_window, text=t("choose_fighter"), font=("Segoe UI", 10, "bold"), bg=COLORS["bg"], fg=COLORS["secondary"]); fighter_lbl.pack(pady=5)
char_dropdown = ModernDropdown(setup_window, list(ROSTER.keys()), "Gojo (Jujutsu Kaisen)", width=320); char_dropdown.pack(pady=15)
match_lbl = tk.Label(setup_window, text=t("match_type"), font=("Segoe UI", 10, "bold"), bg=COLORS["bg"], fg=COLORS["secondary"]); match_lbl.pack(pady=(20,10))
mode_var = tk.StringVar(value="3")
mode_3_btn = tk.Radiobutton(setup_window, text=t("best_3"), variable=mode_var, value="3", font=("Segoe UI", 11), bg=COLORS["bg"], fg=COLORS["text"], selectcolor=COLORS["surface"], activebackground=COLORS["bg"], activeforeground=COLORS["primary"]); mode_3_btn.pack(anchor="w", padx=130, pady=4)
mode_5_btn = tk.Radiobutton(setup_window, text=t("best_5"), variable=mode_var, value="5", font=("Segoe UI", 11), bg=COLORS["bg"], fg=COLORS["text"], selectcolor=COLORS["surface"], activebackground=COLORS["bg"], activeforeground=COLORS["primary"]); mode_5_btn.pack(anchor="w", padx=130, pady=4)
mode_time_btn = tk.Radiobutton(setup_window, text=t("time_rush"), variable=mode_var, value="time", font=("Segoe UI", 11), bg=COLORS["bg"], fg=COLORS["text"], selectcolor=COLORS["surface"], activebackground=COLORS["bg"], activeforeground=COLORS["primary"]); mode_time_btn.pack(anchor="w", padx=130, pady=4)
mode_inf_btn = tk.Radiobutton(setup_window, text=t("infinite"), variable=mode_var, value="endless", font=("Segoe UI", 11), bg=COLORS["bg"], fg=COLORS["text"], selectcolor=COLORS["surface"], activebackground=COLORS["bg"], activeforeground=COLORS["primary"]); mode_inf_btn.pack(anchor="w", padx=130, pady=4)
enter_btn = tk.Button(setup_window, text=t("enter_arena"), font=("Segoe UI", 14, "bold"), bg=COLORS["primary"], fg="#000", command=launch, width=22, pady=10, relief="flat", cursor="hand2"); enter_btn.pack(pady=35)

game_window = tk.Toplevel(setup_window); game_window.title("Anime RPS Auto-Fetch v22.0"); game_window.geometry("650x750"); game_window.config(bg=COLORS["bg"]); game_window.protocol("WM_DELETE_WINDOW", on_close); game_window.withdraw()
header = tk.Frame(game_window, bg=COLORS["bg"]); header.pack(fill=tk.X, padx=20, pady=5)
mute_btn = tk.Button(header, text="🔊", font=("Segoe UI Emoji", 14), bg=COLORS["bg"], fg=COLORS["primary"], command=toggle_mute, cursor="hand2", relief="flat", activebackground=COLORS["bg"]); mute_btn.pack(side=tk.RIGHT)
timer_label = tk.Label(game_window, text="00:30", font=("Consolas", 24, "bold"), bg=COLORS["bg"], fg=COLORS["primary"])
score_frame = tk.Frame(game_window, bg=COLORS["surface"], pady=15); score_frame.pack(pady=10, fill=tk.X, padx=40)
p_name_lbl = tk.Label(score_frame, text="HERO", font=("Segoe UI", 14, "bold"), bg=COLORS["surface"], fg=COLORS["primary"]); p_name_lbl.pack(side=tk.LEFT, padx=20)
p_score_lbl = tk.Label(score_frame, text="0", font=("Segoe UI Black", 28), bg=COLORS["surface"], fg=COLORS["text"]); p_score_lbl.pack(side=tk.LEFT)
tk.Label(score_frame, text="VS", font=("Segoe UI", 14, "italic"), bg=COLORS["surface"], fg=COLORS["text"]).pack(side=tk.LEFT, expand=True)
e_score_lbl = tk.Label(score_frame, text="0", font=("Segoe UI Black", 28), bg=COLORS["surface"], fg=COLORS["text"]); e_score_lbl.pack(side=tk.RIGHT)
tk.Label(score_frame, text="DIO BOSS", font=("Segoe UI", 14, "bold"), bg=COLORS["surface"], fg=COLORS["error"]).pack(side=tk.RIGHT, padx=20)
arena = tk.Canvas(game_window, width=600, height=270, bg=COLORS["bg"], highlightthickness=0); arena.pack(pady=5)
bg_rect = arena.create_rectangle(0, 0, 600, 270, fill=COLORS["bg"], outline=""); arena.create_line(50, 200, 550, 200, fill=COLORS["surface"], width=2)
player_aura = arena.create_oval(p_x-70, p_y-70, p_x+70, p_y+70, outline=COLORS["primary"], width=2)
enemy_aura = arena.create_oval(e_x-70, e_y-70, e_x+70, e_y+70, outline=COLORS["error"], width=2)
player_sprite = arena.create_text(p_x, p_y, text="", font=("Segoe UI Emoji", 30, "bold"), fill=COLORS["text"], justify="center")
enemy_sprite = arena.create_text(e_x, e_y, text="", font=("Segoe UI Emoji", 30, "bold"), fill=COLORS["error"], justify="center")
arena.create_text(30, 220, text="ULTIMATE", font=("Segoe UI", 9, "bold"), fill=COLORS["text"], anchor="w")
arena.create_rectangle(20, 235, 280, 245, fill=COLORS["surface"], outline=COLORS["text"])
ult_bar_fill = arena.create_rectangle(20, 235, 20, 245, fill=COLORS["ult"], outline="")
log_text = tk.Label(game_window, text=t("awaiting"), font=("Segoe UI", 12, "bold"), bg=COLORS["bg"], fg=COLORS["primary"], pady=10); log_text.pack()
btn_frame = tk.Frame(game_window, bg=COLORS["bg"]); btn_frame.pack(pady=5); action_buttons = {}
for i, (text, action, emoji, color) in enumerate([("ROCK", 'Rock', '🪨', "#FF5252"), ("PAPER", 'Paper', '📄', "#448AFF"), ("SCISSOR", 'Scissors', '✂️', "#FFC107"), ("LIZARD", 'Lizard', '🦎', "#69F0AE"), ("SPOCK", 'Spock', '🖖', "#E040FB")]):
    btn = ModernRoundButton(btn_frame, size=90, text=text, emoji=emoji, bg_color=COLORS["surface"], command=lambda act=action: play(act)); btn.grid(row=0, column=i, padx=8); action_buttons[action] = btn
ult_btn = tk.Button(game_window, text="ULTIMATE CHARGING...", font=("Segoe UI Black", 14, "italic"), bg=COLORS["surface"], fg="#555", state=tk.DISABLED, relief="flat", cursor="hand2", pady=8, command=trigger_ultimate); ult_btn.pack(fill=tk.X, padx=40, pady=10)
controls_frame = tk.Frame(game_window, bg=COLORS["bg"]); controls_frame.pack(pady=10)
restart_btn = tk.Button(controls_frame, text=t("restart"), font=("Segoe UI", 10, "bold"), bg=COLORS["surface"], fg=COLORS["text"], command=restart_game, width=16, relief="flat", cursor="hand2", pady=6); restart_btn.pack(side=tk.LEFT, padx=10)
menu_btn = tk.Button(controls_frame, text=t("main_menu"), font=("Segoe UI", 10, "bold"), bg=COLORS["error"], fg=COLORS["text"], command=return_to_main_menu, width=16, relief="flat", cursor="hand2", pady=6); menu_btn.pack(side=tk.LEFT, padx=10)

setup_window.mainloop()