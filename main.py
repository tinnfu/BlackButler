import os
import time

from watchdog.observers import Observer
from watchdog.events import *

from module.monitor import *
from module.period import *
from module.stop import *

abspath = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    period_runner = Period(abspath)
    stop_runner = Stop(abspath)
    monitor = FsMonitor(abspath)
    monitor.register(stop_runner) # must register stop_runner at first
    monitor.register(period_runner)

    observer = Observer()
    observer.schedule(FileEventHandler(monitor), abspath, True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
