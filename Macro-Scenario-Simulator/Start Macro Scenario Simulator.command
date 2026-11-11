#!/bin/zsh
ROOT="${0:A:h}"
LOG="$HOME/Library/Logs/Macro Scenario Simulator.log"
mkdir -p "$HOME/Library/Logs"
# Finder does not inherit the user's terminal PATH.
for PY in /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "$PY" ]] && "$PY" -c 'import sys, tkinter; assert sys.version_info >= (3, 10)' >>"$LOG" 2>&1; then
    cd "$ROOT" || exit 1
    "$PY" "$ROOT/app.py" >>"$LOG" 2>&1
    CODE=$?
    if [[ $CODE -ne 0 ]]; then
      /usr/bin/osascript -e 'display alert "Macro Scenario Simulator could not start" message "See Library/Logs/Macro Scenario Simulator.log in your home folder for details." as critical'
    fi
    exit $CODE
  fi
done
/usr/bin/osascript -e 'display alert "Python with Tk is needed" message "Install Python 3.10 or newer from python.org using its macOS installer, then reopen Macro Scenario Simulator. No extra packages are required."'
exit 1
