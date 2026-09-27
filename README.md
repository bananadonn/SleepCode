# SleepCode

A bedtime enforcer for Windows.

- **11pm – midnight:** pops up a "Go to sleep " reminder with a beep every 10 minutes. Dismissing it just hides it until the next one.
- **Midnight – 6am:** hard block. Discord, game launchers and games are force-closed every 5 seconds. The block lifts as soon as you solve the [LeetCode daily](https://leetcode.com/problemset/). The window can't be closed and comes back if minimized.
- **Any other time:** the script exits immediately.

## Setup

1. Install Python 3 from [python.org](https://www.python.org/downloads/) (tkinter is included).
2. Install the one dependency:
   ```powershell
   pip install psutil
   ```
3. Open `sleep_reminder.py` and set your LeetCode username (your profile must be public):
   ```python
   LEETCODE_USERNAME = "your-username"
   ```
4. Run it once to check it starts:
   ```powershell
   python sleep_reminder.py
   ```
   It exits right away outside 11pm–6am. See [Testing](#testing) to see it in action during the day.

## Configuration

All settings are at the top of `sleep_reminder.py`.

| Setting | Default | What it does |
|---|---|---|
| `NAG_START_HOUR` | `23` | Hour (24h) the reminders start. They run until midnight. |
| `INTERVAL_MINUTES` | `10` | Minutes between reminders. |
| `BLOCK_START_HOUR` | `0` | Hour the block starts. Keep this at `0` (midnight). |
| `BLOCK_END_HOUR` | `6` | Hour the block ends if you haven't solved the daily. |
| `BLOCKED_APPS` | Discord, Steam, Epic, Riot, Battle.net | Process names to kill (lowercase, e.g. `"discord.exe"`). |
| `BLOCKED_DIRS` | Steam/Epic/Riot/Xbox game folders | Anything running from these folders gets killed. |
| `ALLOWED_APPS` | Wallpaper Engine | Exceptions to the two lists above. |

To find the name of a program you want to block, open Task Manager, go to **Details**, and use the name in the **Name** column.

> The daily LeetCode problem changes at midnight **UTC** (8pm Eastern). The block checks the *current* daily, so solving the previous day's problem earlier in the evening doesn't count.

## Run it automatically (Task Scheduler)

This is Windows' version of a cron job. Run the following in PowerShell from the `sleepyscript` folder. It creates a task that starts the script at 10:55pm every night **and** every time you log in, so a restart doesn't get you out of the block. It uses `pythonw.exe`, so there's no console window to close.

```powershell
$dir = (Get-Location).Path
$py  = (python -c "import sys; print(sys.executable)") -replace 'python\.exe$', 'pythonw.exe'

$action   = New-ScheduledTaskAction -Execute $py -Argument "`"$dir\sleep_reminder.py`"" -WorkingDirectory $dir
$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At "10:55PM"),
    (New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME")
)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "Sleep Reminder" -Action $action -Trigger $triggers -Settings $settings
```

If you change `NAG_START_HOUR`, change `"10:55PM"` to a few minutes before the new hour. The task runs the script file where it is, so edits to the settings take effect the next time it starts.

Check it's registered and see when it runs next:

```powershell
Get-ScheduledTaskInfo -TaskName "Sleep Reminder" | Select-Object LastRunTime, LastTaskResult, NextRunTime
```

## Stopping it

| Goal | Command |
|---|---|
| Stop the currently running reminder/block | `Stop-ScheduledTask -TaskName "Sleep Reminder"` |
| Pause it (won't run until re-enabled) | `Disable-ScheduledTask -TaskName "Sleep Reminder"` |
| Turn it back on | `Enable-ScheduledTask -TaskName "Sleep Reminder"` |
| Remove it completely | `Unregister-ScheduledTask -TaskName "Sleep Reminder" -Confirm:$false` |

If you started it by hand rather than through the task, kill it directly:

```powershell
Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
    Where-Object CommandLine -like "*sleep_reminder*" |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

## Testing

To see it working during the day, temporarily edit the settings, run `python sleep_reminder.py`, and then **put the values back**:

- **Block:** set `BLOCK_END_HOUR = 24`. Open Discord and it should close within 5 seconds.
- **Reminders:** set `NAG_START_HOUR` to the current hour and `INTERVAL_MINUTES = 0.25` (15 seconds).

If `BLOCK_END_HOUR` is left at `24`, the scheduled task will block your apps all day.
