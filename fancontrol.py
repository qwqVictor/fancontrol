#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-
# 2022 Victor Huang <i@qwq.ren>
# Licensed under Unlicense.
# Description: Little Python script to control fan speed of Dell PowerEdge server

import sys
import subprocess
import time
import re
import platform
import signal
import os

VERSION="1.0.0beta2"
COPYRIGHT_YEAR=2022
AUTHOR="Victor Huang <i@qwq.ren>"

UNAME_SYSTEM=platform.system()

IPMITOOL_BIN=""
CHECK_INTERVAL=-1
if UNAME_SYSTEM == "VMkernel":
    IPMITOOL_BIN="/opt/ipmitool/bin/ipmitool"
    CHECK_INTERVAL=3
else:
    IPMITOOL_BIN="/usr/bin/ipmitool"
    CHECK_INTERVAL=0.5

PIDFILE="/var/run/fancontrol.pid"

IPMITOOL_EXTRA_ARGS=[]
CMDTYPE="raw"
BASE_FAN = ["0x30", "0x30", "0x02", "0xff"]
BASE_AUTO=["0x30", "0x30", "0x01"]
FANSPEED=[6]

IPMITOOL_EXECBASE = [IPMITOOL_BIN] + IPMITOOL_EXTRA_ARGS + [CMDTYPE]

MATCH_TEMP=re.compile('(\d+(\.\d+)?)')

def get_log_time():
    return "[" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "] "

# special hack to prevent ESXi background killing.
# use SIGUSR1 to safely kill this program
if UNAME_SYSTEM == "VMkernel":
    def signal_handler(signal_id, frame):
        print(get_log_time() + "%s received." % (str(signal.Signals(signal_id))),file=sys.stderr)
        if signal_id == signal.SIGUSR1:
            os.remove(PIDFILE)
            sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler) 
    signal.signal(signal.SIGUSR1, signal_handler)

# get current temperature for cpu 0
def get_package_temp():
    if UNAME_SYSTEM == "VMkernel":
        try:
            result = subprocess.run([IPMITOOL_BIN, *IPMITOOL_EXTRA_ARGS, "sensor", "reading", "Temp"], capture_output=True)
            return float(MATCH_TEMP.search(result.stdout.decode()).group())
        except:
            return None
    else:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return float(f.read()) / 1000

# get cpu thermal level
# Levels please see 'help'
def get_thermal_level(temp):
    if temp <= 66:   
        return 0
    else:
        return 1

# make it control the fans automatically
def set_fan_auto(auto: bool):
    subprocess.run(IPMITOOL_EXECBASE + BASE_AUTO + [hex(auto)], capture_output=True)
    return auto

def set_fan_percentage(percentage: int):
    if percentage > 100 or percentage < 0:
        return None
    else:
        set_fan_auto(False)
        subprocess.run(IPMITOOL_EXECBASE + BASE_FAN + [hex(percentage)], capture_output=True)
        return percentage

def do_fan_control():
    temp = None
    thermal_level = None
    try:
        temp = get_package_temp()
        thermal_level = get_thermal_level(temp)
    except Exception as e:
        set_fan_auto(True)
        print(get_log_time() + str(e), file=sys.stderr)
    try:
        percentage = FANSPEED[thermal_level]
        auto = False
    except:
        percentage = None
        auto = True
    if auto:
        set_fan_auto(True)
    else:
        set_fan_percentage(percentage)
    return (temp, thermal_level)

def main(argv):
    print("Fancontrol for Dell PowerEdge ver %s" % VERSION)
    print("%d (c) %s\n" % (COPYRIGHT_YEAR, AUTHOR))

    try:
        if (not argv[1].startswith("--") and argv[1].find("h") != -1) or argv[1] == "--help":
            print(r"""
Levels:
- 0: 6% fan speed, for temperature range [0, 66°C], low temp
- 1: let it control
    """)
        else:
            print("ERROR! Unknown option.")
    except:
        print(get_log_time() + "Script started, working hard to control the fans.")
        recent_thermal_level = do_fan_control()[1]
        while True:
            status = do_fan_control()
            if status:
                if recent_thermal_level != status[1]:
                    if (status[0] is not None) and (status[1] is not None):
                        print(get_log_time() + "Thermal level changed from %d to %d. Now CPU is %d°C." % (recent_thermal_level, status[1], status[0]))
                        recent_thermal_level = status[1]
                    else:
                        print(get_log_time() + "Get temperature failed. Triggered auto.")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main(sys.argv)
