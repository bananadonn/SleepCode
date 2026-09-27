# SleepCode

A bedtime enforcer for Windows that makes you earn your late-night Discord and gaming time.

Each night it works in two phases:

1. **Wind-down reminders.** From an hour you choose until midnight, a window pops up every few minutes telling you to go to sleep. You can dismiss it, but it keeps coming back.
2. **Hard block.** From midnight until a morning hour you choose, the apps you list (Discord and game launchers by default) are force-closed every few seconds. The only way to lift the block early is to solve that day's [LeetCode daily problem](https://leetcode.com/problemset/).

Outside those hours the script does nothing and exits.

## Getting started

**Requirements:** Windows, Python 3 ([python.org](https://www.python.org/downloads/)), and a LeetCode account with a public profile.

```powershell
git clone https://github.com/bananadonn/SleepCode.git
cd SleepCode
pip install psutil
```

Open `sleep_reminder.py` and set your LeetCode username near the top:

```python
LEETCODE_USERNAME = "your-leetcode-username"
```

Then read through the settings below and adjust them to fit your schedule before you run it.

## Making it yours

Every setting lives at the top of `sleep_reminder.py`. None of the defaults are special: pick whatever matches your routine.

### Your schedule

Hours use the 24-hour clock (`23` = 11pm, `1` = 1am).

- **`NAG_START_HOUR`**: when reminders begin. They run from this hour until midnight. Set it to when you *should* start winding down.
- **`INTERVAL_MINUTES`**: how often the reminder pops back up. Shorter is more annoying, which is the point.
- **`BLOCK_END_HOUR`**: when the block lifts on its own if you never solve the problem. Set it to roughly when you wake up.
- **`BLOCK_START_HOUR`**: when the block begins. Leave this at `0` (midnight). The reminders hand off to the block at midnight, so other values leave a gap.

### What gets blocked

- **`BLOCKED_APPS`**: process names to shut down during the block, written in lowercase (e.g. `"discord.exe"`). To find a program's process name, open Task Manager → **Details** while it's running and look at the **Name** column.
- **`BLOCKED_DIRS`**: folders whose programs count as games. Anything launched from inside them is shut down. This catches games that keep running after their launcher closes. Add your own install folders here if your games live somewhere unusual.
- **`ALLOWED_APPS`**: exceptions to both lists. Use this for non-game tools that happen to live in a game folder (e.g. Wallpaper Engine in Steam's folder).

Want to block something other than games, like a browser? Add its process name to `BLOCKED_APPS`. Just keep a way to reach LeetCode, or you'll be locked out of the only way to unlock.

### How strict it is

- **`KILL_EVERY_SECONDS`**: how often blocked apps are checked for and closed.
- **`CHECK_LEETCODE_EVERY_SECONDS`**: how often it checks whether you've solved the daily. The **I solved it** button checks immediately, so this only matters if you don't click it.

> **Heads up:** LeetCode's daily problem changes at midnight UTC, which is the evening in the Americas. The block checks the daily that's live *at the time*, so a problem you solved earlier in the day may not count.

## Trying it out

Since it only runs at night, test it by temporarily changing the hours so the current time falls inside a phase, then run `python sleep_reminder.py`:

- **To see the block:** set `BLOCK_END_HOUR = 24`, then open one of your blocked apps. It should close within a few seconds.
- **To see the reminders:** set `NAG_START_HOUR` to the current hour and `INTERVAL_MINUTES` to something tiny like `0.25` (15 seconds).

Change the values back when you're done. If you leave `BLOCK_END_HOUR` at `24`, you'll be blocked all day.

## Running it every night automatically

Windows' equivalent of a cron job is **Task Scheduler**. Run this in PowerShell from the `SleepCode` folder, first setting `$startTime` to a few minutes before your `NAG_START_HOUR`:

```powershell
$startTime = "10:55PM"   # a few minutes before NAG_START_HOUR

$dir = (Get-Location).Path
$py  = (python -c "import sys; print(sys.executable)") -replace 'python\.exe$', 'pythonw.exe'

$action   = New-ScheduledTaskAction -Execute $py -Argument "`"$dir\sleep_reminder.py`"" -WorkingDirectory $dir
$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At $startTime),
    (New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME")
)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "SleepCode" -Action $action -Trigger $triggers -Settings $settings
```

What this sets up:

- The script starts every night at `$startTime`, **and** every time you log in, so restarting your PC doesn't escape the block. Outside your hours it just exits, so the login trigger is harmless during the day.
- If your PC is asleep at the scheduled time, it runs as soon as the PC wakes up.
- It runs with `pythonw`, so there's no console window you can close to kill it.

The task runs the script from the cloned folder, so you can keep tweaking settings. Changes apply the next time it starts. If you later change `NAG_START_HOUR`, re-run the block above with a new `$startTime` and add `-Force` to the last line to replace the old task.

To check it's set up and see when it runs next:

```powershell
Get-ScheduledTaskInfo -TaskName "SleepCode" | Select-Object LastRunTime, LastTaskResult, NextRunTime
```

## Turning it off

| To… | Run |
|---|---|
| Stop tonight's reminder or block | `Stop-ScheduledTask -TaskName "SleepCode"` |
| Pause it until you turn it back on | `Disable-ScheduledTask -TaskName "SleepCode"` |
| Turn it back on | `Enable-ScheduledTask -TaskName "SleepCode"` |
| Remove it completely | `Unregister-ScheduledTask -TaskName "SleepCode" -Confirm:$false` |

If you started the script by hand instead of through Task Scheduler, stop it with:

```powershell
Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
    Where-Object CommandLine -like "*sleep_reminder*" |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```
