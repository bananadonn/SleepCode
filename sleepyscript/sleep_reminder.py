import json
import os
import sys
import time
import tkinter as tk
import urllib.request
import webbrowser
from datetime import datetime, timezone

import psutil

INTERVAL_MINUTES = 10  # how often to nag
NAG_START_HOUR = 23    # start nagging at 11pm
BLOCK_START_HOUR = 0   # hard block from midnight...
BLOCK_END_HOUR = 6     # ...until 6am, unless the daily leetcode is solved

LEETCODE_USERNAME = "reithdonald04"  # your leetcode username (profile must be public)
KILL_EVERY_SECONDS = 5
CHECK_LEETCODE_EVERY_SECONDS = 60

# process names (lowercase) that get killed during the block
BLOCKED_APPS = {
    "discord.exe",
    "steam.exe",
    "epicgameslauncher.exe",
    "riotclientservices.exe",
    "battle.net.exe",
}
# anything running from these folders counts as a game
BLOCKED_DIRS = [
    "\\steamapps\\common\\",
    "\\epic games\\",
    "\\riot games\\",
    "\\xboxgames\\",
]
# steam stuff that isn't a game
ALLOWED_APPS = {"wallpaper32.exe", "wallpaper64.exe"}

DAILY_QUERY = """query {
  activeDailyCodingChallengeQuestion { date link question { title titleSlug } }
}"""
RECENT_AC_QUERY = """query($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) { titleSlug timestamp }
}"""


def play_sound():
    if sys.platform == "win32":
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    elif sys.platform == "darwin":
        os.system("afplay /System/Library/Sounds/Glass.aiff &")
    else:
        os.system("paplay /usr/share/sounds/freedesktop/stereo/bell.oga &")


def seconds_to_next_hour():
    now = datetime.now()
    return 3600 - (now.minute * 60 + now.second)


def in_block_hours():
    return BLOCK_START_HOUR <= datetime.now().hour < BLOCK_END_HOUR


def leetcode_query(query, variables=None):
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)["data"]


def check_daily():
    """Return (daily question info, whether it's been solved since it went live)."""
    daily = leetcode_query(DAILY_QUERY)["activeDailyCodingChallengeQuestion"]
    # the daily resets at midnight UTC, so only count solves after that
    went_live = datetime.strptime(daily["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    subs = leetcode_query(RECENT_AC_QUERY, {"username": LEETCODE_USERNAME, "limit": 20})
    solved = any(
        s["titleSlug"] == daily["question"]["titleSlug"]
        and int(s["timestamp"]) >= went_live.timestamp()
        for s in subs["recentAcSubmissionList"]
    )
    return daily, solved


def kill_blocked():
    for p in psutil.process_iter(["name", "exe"]):
        name = (p.info["name"] or "").lower()
        exe = (p.info["exe"] or "").lower()
        if name in ALLOWED_APPS:
            continue
        if name in BLOCKED_APPS or any(d in exe for d in BLOCKED_DIRS):
            try:
                p.kill()
            except psutil.Error:
                pass


def nag():
    global count
    hour = datetime.now().hour
    if in_block_hours():
        start_block()
        return
    if hour < NAG_START_HOUR:  # outside the bedtime window, so quit
        root.destroy()
        return

    count += 1
    now = datetime.now().strftime("%I:%M %p").lstrip("0")
    msg = f"It's {now}. Go to sleep 😴"
    if count > 1:
        msg += f"\n(reminder #{count})"
    label.config(text=msg)

    play_sound()
    root.deiconify()  # bring the window back if it was dismissed
    root.lift()
    # wake up on the hour too, so the block starts right at midnight
    delay = min(INTERVAL_MINUTES * 60, seconds_to_next_hour() + 1)
    root.after(delay * 1000, nag)  # schedule the next one


def start_block():
    global last_check
    last_check = 0
    root.protocol("WM_DELETE_WINDOW", lambda: None)  # X does nothing during the block
    ok_button.pack_forget()
    open_button.pack(side="left", padx=10)
    check_button.pack(side="left", padx=10)
    buttons.pack(pady=(0, 20))
    play_sound()
    root.deiconify()
    root.lift()
    block_tick()


def block_tick():
    global daily, last_check
    if not in_block_hours():  # morning, block's over
        root.destroy()
        return

    kill_blocked()
    if root.state() != "normal":  # minimized, so put it back
        root.deiconify()
    if time.monotonic() - last_check >= CHECK_LEETCODE_EVERY_SECONDS:
        check_now()
    root.after(KILL_EVERY_SECONDS * 1000, block_tick)


def check_now():
    global daily, last_check
    last_check = time.monotonic()
    try:
        daily, solved = check_daily()
    except Exception as e:
        label.config(text=f"Sleep block is on.\nCouldn't reach LeetCode ({e}).\nStill blocked.")
        return

    if solved:
        label.config(text="Daily solved. Unlocked 🎉\nNow actually go to sleep.")
        root.after(5000, root.destroy)
        return
    label.config(
        text="Sleep block is on 🔒\nDiscord and games are blocked until you solve:\n"
        f"{daily['question']['title']}"
    )


def open_problem():
    link = daily["link"] if daily else "/problemset/"
    webbrowser.open("https://leetcode.com" + link)


root = tk.Tk()
root.title("Bedtime")
root.attributes("-topmost", True)
# X acts like "Okay, okay" so closing the nag doesn't kill the midnight block
root.protocol("WM_DELETE_WINDOW", root.withdraw)
label = tk.Label(root, font=("Helvetica", 20), padx=40, pady=30)
label.pack()
ok_button = tk.Button(root, text="Okay, okay", command=root.withdraw)
ok_button.pack(pady=(0, 20))
buttons = tk.Frame(root)
open_button = tk.Button(buttons, text="Open problem", command=open_problem)
check_button = tk.Button(buttons, text="I solved it", command=check_now)

count = 0
daily = None
last_check = 0
if not LEETCODE_USERNAME:
    sys.exit("Set LEETCODE_USERNAME at the top of the script first.")
nag()
root.mainloop()
