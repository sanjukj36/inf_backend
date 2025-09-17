# # main.py
# import subprocess

# files_to_run = [
#     "source_code/api/Api_Alert.py",
#     "source_code/api/Band_storage.py",
#     "source_code/api/db.py",
#     "source_code/api/util/data_striming.py",
#     "source_code/api/util/data_striming_edit.py",
#     "source_code/api/util/filewire.py",
#     "source_code/api/historic_alarm.py",
#     "source_code/api/mqtt.py",
#     "source_code/api/Ping_satatus.py",
# ]

# # Run each file one by one
# for file in files_to_run:
#     print(f"🚀 Running {file} ...")
#     subprocess.Popen(["python", file])

# main.py
import subprocess
import signal
import sys

files_to_run = [
    "source_code/api/Api_Alert.py",
    "source_code/api/Band_storage.py",
    "source_code/api/db.py",
    "source_code/api/util/data_striming.py",
    "source_code/api/util/data_striming_edit.py",
    "source_code/api/util/filewire.py",
    "source_code/api/historic_alarm.py",
    "source_code/api/mqtt.py",
    "source_code/api/Ping_satatus.py",
]

# Keep references to processes
processes = []

try:
    # Start processes
    for file in files_to_run:
        print(f"🚀 Running {file} ...")
        p = subprocess.Popen(["python", file])
        processes.append(p)

    # Wait for processes
    for p in processes:
        p.wait()

except KeyboardInterrupt:
    print("\n🛑 Ctrl+C detected! Stopping all processes...")
    for p in processes:
        try:
            p.terminate()  # ask nicely
        except Exception:
            pass
    for p in processes:
        try:
            p.kill()  # force kill if still alive
        except Exception:
            pass
    sys.exit(0)
