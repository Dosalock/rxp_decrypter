"""RXP Guide Tool - Enter your BattleTag to generate your guide file."""
import base64
import json
import os
import re
import sys
import zlib
import urllib.request
from tkinter import Tk, Label, Entry, Button, messagebox, StringVar, Frame, W, E
from tkinter.filedialog import askdirectory
from tkinter import OptionMenu

# === CONFIG (set by BuildTool at build time) ===
EMBEDDED_PACK = "Forever Leveling Guide - Both Factions"
EMBEDDED_LOCALE_PREFIX = "_"
EMBEDDED_TRAILING = ""
EMBEDDED_DATA_B64 = "<base64-encoded zlib-compressed guide text>"
EMBEDDED_DATA_DE_B64 = "<base64-encoded zlib-compressed german guide text, or empty>"
GUIDE_COUNT = 1
ORIGINAL_TAG = "rafiejessi#2561"


def rc4(data, key):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i & 0xF]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


def derive_key(base_str):
    raw = base_str.encode("utf-8").lower()[-16:].rjust(16, b"\x00")
    buf = list(raw)
    for i in range(16):
        buf[(-i) & 0xF] = (buf[(15 - i) & 0xF] ^ buf[(13 - i) & 0xF] ^
                           buf[(12 - i) & 0xF] ^ buf[(10 - i) & 0xF])
    return bytes(buf)


def get_cache_path(locale="en"):
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.getcwd()
    fname = ".rxp_cache_en.dat" if locale == "en" else (".rxp_cache_" + locale + ".dat")
    return os.path.join(base, fname)


def get_latest_sha():
    api_url = "https://api.github.com/repos/Inariaa/rxp_decrypter/commits/main"
    req = urllib.request.Request(api_url, headers={'User-Agent': 'RXP-Guide-Tool/1.0', 'Accept': 'application/vnd.github.v3+json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        info = json.loads(resp.read().decode('utf-8'))
    return info["sha"]


def download_update(locale="en", silent=False):
    try:
        sha = get_latest_sha()
        fname = "guide.txt" if locale == "en" else ("guide_" + locale + ".txt")
        url = "https://raw.githubusercontent.com/Inariaa/rxp_decrypter/" + sha + "/" + fname
        req = urllib.request.Request(url, headers={'User-Agent': 'RXP-Guide-Tool/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode('utf-8')
        if '|' not in data or ':' not in data:
            return False, "Invalid response from server"
        cache = get_cache_path(locale)
        old_data = None
        if os.path.isfile(cache):
            with open(cache, 'r', encoding='utf-8') as f:
                old_data = f.read().strip()
        new_data = data.strip()
        if old_data == new_data:
            return True, "Already up to date"
        with open(cache, 'w', encoding='utf-8') as f:
            f.write(new_data)
        return True, "Updated successfully"
    except Exception as err:
        if silent:
            return False, str(err)
        return False, f"Update failed: {err}"


def get_plain_text(locale="en"):
    # Try cache first (downloaded from GitHub)
    cache = get_cache_path(locale)
    if os.path.isfile(cache):
        try:
            with open(cache, 'r', encoding='utf-8') as f:
                data = f.read().strip()
            m = re.match(r"^(\d+)\|(\d+):(.+?)(%.*)$", data)
            if m:
                b64_payload = m.group(3)
                cipher_bytes = base64.b64decode(b64_payload)
                old_key = derive_key(ORIGINAL_TAG)
                comp2 = rc4(cipher_bytes, old_key)
                text = zlib.decompress(comp2).decode("utf-8")
                return text
        except Exception:
            pass
    # Fallback to embedded
    if locale == "en" and EMBEDDED_DATA_B64:
        return zlib.decompress(base64.b64decode(EMBEDDED_DATA_B64)).decode("utf-8")
    elif locale == "de" and EMBEDDED_DATA_DE_B64:
        return zlib.decompress(base64.b64decode(EMBEDDED_DATA_DE_B64)).decode("utf-8")
    # For non-English with no cache, try downloading now
    ok, msg = download_update(locale, silent=True)
    if ok:
        cache = get_cache_path(locale)
        if os.path.isfile(cache):
            with open(cache, 'r', encoding='utf-8') as f:
                data = f.read().strip()
            m = re.match(r"^(\d+)\|(\d+):(.+?)(%.*)$", data)
            if m:
                b64_payload = m.group(3)
                cipher_bytes = base64.b64decode(b64_payload)
                old_key = derive_key(ORIGINAL_TAG)
                comp2 = rc4(cipher_bytes, old_key)
                text = zlib.decompress(comp2).decode("utf-8")
                return text
    raise Exception(f"No guide data available for locale '{locale}'. Check your internet connection.")


def copy_to_clipboard():
    new_tag = tag_var.get().strip()
    if not new_tag:
        messagebox.showerror("Error", "Please enter your BattleTag first.")
        return
    if not re.match(r"^[^#]+#\d+$", new_tag):
        messagebox.showerror("Invalid Format", "BattleTag must be in the format: Name#1234")
        return

    locale = lang_var.get()
    try:
        text = get_plain_text(locale)
    except Exception as err:
        messagebox.showerror("Error", str(err))
        return
    key_new = derive_key(new_tag)
    comp2 = zlib.compress(text.encode("utf-8"), 6)
    cipher = rc4(comp2, key_new)
    b64_out = base64.b64encode(cipher).decode()
    check_val = int.from_bytes(comp2[-4:], "big")

    content = f"{GUIDE_COUNT}|{check_val}:{b64_out}%"
    if EMBEDDED_TRAILING:
        content += EMBEDDED_TRAILING

    root.clipboard_clear()
    root.clipboard_append(content)
    save_tag_to_history(new_tag)
    status_var.set("Copied to clipboard!")
    messagebox.showinfo("Copied", "Guide data copied to clipboard. Paste it into RXPGuides.")


def get_history_file():
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.join(docs, ".rxp_guide_tags.txt")


def load_tag_history():
    try:
        with open(get_history_file(), "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except (FileNotFoundError, IOError):
        return []


def save_tag_to_history(tag):
    history = load_tag_history()
    if tag in history:
        history.remove(tag)
    history.insert(0, tag)
    history = history[:10]
    try:
        with open(get_history_file(), "w", encoding="utf-8") as f:
            for i, t in enumerate(history):
                if i > 0:
                    f.write(chr(10))
                f.write(t)
    except IOError:
        pass


def load_last_tag():
    h = load_tag_history()
    return h[0] if h else ""


def show_tag_menu(event=None):
    history = load_tag_history()
    if not history:
        return
    from tkinter import Toplevel, Listbox, END
    win = Toplevel(root)
    win.title("Recent Tags")
    win.resizable(False, False)
    lb = Listbox(win, width=30, height=min(len(history), 10))
    for tag in history:
        lb.insert(END, tag)
    def on_select(e):
        sel = lb.curselection()
        if sel:
            tag_var.set(history[sel[0]])
            win.destroy()
    lb.bind("<Double-Button-1>", on_select)
    lb.pack(padx=5, pady=5)
    Button(win, text="Close", command=win.destroy).pack(pady=3)


# --- Dark Theme Colors (Catppuccin Mocha) ---
BG = "#1e1e2e"
FG = "#cdd6f4"
ACCENT = "#89b4fa"
ACCENT_HOVER = "#74a0f5"
SURFACE = "#313244"
TEXT_ENTRY_BG = "#45475a"
STATUS_FG = "#a6adc8"

root = Tk()
root.title("RXP Decryption Tool")
root.resizable(False, False)
root.configure(bg=BG)

# Set taskbar/window icon
import sys as _sys
def _get_icon_path():
    if getattr(_sys, 'frozen', False):
        base = _sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "icon.ico")
try:
    root.iconbitmap(default=_get_icon_path())
except Exception:
    pass

frame = Frame(root, bg=BG)
frame.pack(padx=20, pady=15)

Label(frame, text="Your BattleTag:", bg=BG, fg=FG, font=("Segoe UI", 10)).grid(row=0, column=0, sticky=W, padx=(0, 8), pady=6)
tag_var = StringVar(value=load_last_tag())
entry_widget = Entry(frame, textvariable=tag_var, width=32, bg=TEXT_ENTRY_BG, fg=FG,
                     insertbackground=ACCENT, relief="flat", font=("Segoe UI", 10),
                     highlightthickness=1, highlightbackground=SURFACE, highlightcolor=ACCENT)
entry_widget.grid(row=0, column=1, sticky=E, padx=(0, 6), pady=6)
Button(frame, text="History", command=show_tag_menu, width=8, bg=SURFACE, fg=FG,
       activebackground="#45475a", activeforeground=FG, relief="flat",
       font=("Segoe UI", 9), cursor="hand2").grid(row=0, column=2, padx=(0, 0), pady=6)

Label(frame, text="Language:", bg=BG, fg=FG, font=("Segoe UI", 10)).grid(row=4, column=0, sticky=W, padx=(0, 8), pady=6)
lang_var = StringVar(value="en")
LANGUAGES = [("English", "en"), ("German", "de")]
lang_menu = OptionMenu(frame, lang_var, "en", "de")
lang_menu.grid(row=4, column=1, sticky=W, padx=(0, 6), pady=6)

Button(frame, text="Copy Guide to Clipboard", command=copy_to_clipboard,
       bg=ACCENT, fg="#1e1e2e", font=("Segoe UI", 11, "bold"),
       activebackground=ACCENT_HOVER, activeforeground="#1e1e2e",
       relief="flat", cursor="hand2", padx=16, pady=4).grid(row=5, column=0, columnspan=3, padx=5, pady=(10, 6))

status_var = StringVar(value="Enter your BattleTag and click Copy")
Label(frame, textvariable=status_var, bg=BG, fg=STATUS_FG, font=("Segoe UI", 9)).grid(row=6, column=0, columnspan=3, padx=5, pady=4)
Button(frame, text="Check for Updates", command=lambda: check_updates_btn(), width=20,
       bg=SURFACE, fg=FG, activebackground="#45475a", activeforeground=FG,
       relief="flat", font=("Segoe UI", 9), cursor="hand2").grid(row=7, column=0, columnspan=3, padx=5, pady=6)

Label(frame, text="v1.0 | made by slcker", bg=BG, fg="#6c7086", font=("Segoe UI", 8)).grid(row=8, column=0, columnspan=3, sticky=E, padx=8, pady=(2, 4))


def check_updates_btn():
    locale = lang_var.get()
    status_var.set("Checking for updates...")
    root.update()
    ok, msg = download_update(locale, False)
    if ok:
        status_var.set(msg)
    else:
        status_var.set("Update failed: " + msg)


# Auto-update on startup (silent) - English only
download_update("en", silent=True)

root.mainloop()
