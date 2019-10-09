from watchdog.observers import Observer
from watchdog.events import *
import time
from collections import OrderedDict
import threading
import subprocess

class GlobalRecords:
    def __init__(self):
        self._records = OrderedDict()

    def add(self, key, value):
        if key not in self._records:
            self._records[key] = set()
        self._records[key].add(value)

    def remove(self, key, value):
        if key in self._records:
            self._records[key].remove(value)

    @property
    def records(self):
        return self._records

globalRecords = GlobalRecords()

class GlobalBlacklist:
    def __init__(self):
        self._blacklist = set()

    def add(self, target):
        print('add blacklist: %s' % target)
        self._blacklist.add(target)
        for k in globalRecords.records:
            if k.endswith(target):
                for t in globalRecords.records[k]:
                    t.suspend()

    def remove(self, target):
        if target not in self._blacklist:
            return

        print('remove blacklist: %s' % target)
        self._blacklist.remove(target)
        for k in globalRecords.records:
            if k.endswith(target):
                for t in globalRecords.records[k]:
                    t.resume()

    @property
    def blacklist(self):
        return self._blacklist

globalBlacklist = GlobalBlacklist()

class PeriodTimer(threading.Timer):
    def __init__(self, interval, function, args = None, kwargs = None):
        threading.Timer.__init__(self, interval, function, args, kwargs)
        self.hangup = False

    def run(self):
        while not self.finished.is_set():
            if not self.hangup:
                self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)

    def suspend(self):
        self.hangup = True

    def resume(self):
        self.hangup = False

def TimerTask(s, taskPath):
    exitcode, output = subprocess.getstatusoutput(taskPath)
    if exitcode != 0 and exitcode != 127:
        raise Exception('fail to exec: %s, (%s, %s)' % (taskPath, exitcode, output))
    print(output)

PERIOD_TYPE_SECONDS = 'seconds'
PERIOD_TYPE_MINUTES = 'minutes'
PERIOD_TYPE_HOURS = 'hours'
PERIOD_TYPE_DAYS = 'days'

class StopEventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns = None, ignore_patterns = None, ignore_directories = False, case_sensitive = False,
            abspath = None):
        PatternMatchingEventHandler.__init__(self, patterns, ignore_patterns, ignore_directories, case_sensitive)

        self._abspath = abspath

    def on_moved(self, event):
        if event.is_directory:
            return

        if event.src_path.startswith(self._abspath):
            self.on_deleted(event)
        if event.dest_path.startswith(self._abspath):
            ev = FileSystemEvent(event.dest_path)
            self.on_deleted(ev)
            self.on_created(ev)

    def on_created(self, event):
        if event.is_directory:
            return

        path = event.src_path
        globalBlacklist.add(path[len(self._abspath):])

    def on_deleted(self, event):
        if event.is_directory:
            return

        path = event.src_path
        globalBlacklist.remove(path[len(self._abspath):])

class PeriodEventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns = None, ignore_patterns = None, ignore_directories = False, case_sensitive = False,
            period_type = PERIOD_TYPE_SECONDS, get_period_seconds = lambda path: int(re.search('/seconds/(\d+)/', path).group(1)),
            abspath = None):
        PatternMatchingEventHandler.__init__(self, patterns, ignore_patterns, ignore_directories, case_sensitive)

        self._period_type = period_type
        self._get_period_seconds = get_period_seconds
        self._abspath = abspath

        self._seconds_period_tasks = OrderedDict()
        self._minutes_period_tasks = OrderedDict()
        self._hours_period_tasks = OrderedDict()
        self._days_period_tasks = OrderedDict()

    def on_moved(self, event):
        if event.is_directory:
            return

        print('on_moved: %s -> %s' % (event.src_path, event.dest_path))
        if event.src_path.startswith(self._abspath):
            self.on_deleted(event)
        if event.dest_path.startswith(self._abspath):
            ev = FileSystemEvent(event.dest_path)
            self.on_deleted(ev)
            self.on_created(ev)

    def on_modified(self, event):
        if event.is_directory:
            return

        self.on_deleted(event)
        self.on_created(event)

    def on_created(self, event):
        if event.is_directory:
            return

        print('on_created: %s' % event.src_path)

        path = event.src_path
        if path[path.find('period'):] in globalBlacklist.blacklist:
            return

        def seconds_timer(s, path):
            self._seconds_period_tasks[path] = PeriodTimer(s, TimerTask, args = [s, path])
            globalRecords.add(path, self._seconds_period_tasks[path])
            self._seconds_period_tasks[path].start()
        def minutes_timer(s, path):
            self._minutes_period_tasks[path] = PeriodTimer(s, TimerTask, args = [s, path])
            globalRecords.add(path, self._minutes_period_tasks[path])
            self._minutes_period_tasks[path].start()
        def hours_timer(s, path):
            self._hours_period_tasks[path] = PeriodTimer(s, TimerTask, args = [s, path])
            globalRecords.add(path, self._hours_period_tasks[path])
            self._hours_period_tasks[path].start()
        def days_timer(s, path):
            self._days_period_tasks[path] = PeriodTimer(s, TimerTask, args = [s, path])
            globalRecords.add(path, self._days_period_tasks[path])
            self._days_period_tasks[path].start()

        path = event.src_path
        _method_map = {
            PERIOD_TYPE_SECONDS: seconds_timer,
            PERIOD_TYPE_MINUTES: minutes_timer,
            PERIOD_TYPE_HOURS: hours_timer,
            PERIOD_TYPE_DAYS: days_timer,
        }
        _method_map[self._period_type](self._get_period_seconds(path), path)

    def on_deleted(self, event):
        if event.is_directory:
            return

        print('on_deleted: %s' % event.src_path)
        path = event.src_path
        if path[path.find('period'):] in globalBlacklist.blacklist:
            return

        def seconds_timer(path):
            if path not in self._seconds_period_tasks:
                return
            self._seconds_period_tasks[path].cancel()
            globalRecords.remove(path, self._seconds_period_tasks[path])
            del self._seconds_period_tasks[path]
        def minutes_timer(path):
            if path not in self._minutes_period_tasks:
                return
            self._minutes_period_tasks[path].cancel()
            globalRecords.remove(path, self._minutes_period_tasks[path])
            del self._minutes_period_tasks[path]
        def hours_timer(path):
            if path not in self._hours_period_tasks:
                return
            self._hours_period_tasks[path].cancel()
            globalRecords.remove(path, self._hours_period_tasks[path])
            del self._hours_period_tasks[path]
        def days_timer(path):
            if path not in self._days_period_tasks:
                return
            self._days_period_tasks[path].cancel()
            globalRecords.remove(path, self._days_period_tasks[path])
            del self._days_period_tasks[path]

        path = event.src_path
        _method_map = {
            PERIOD_TYPE_SECONDS: seconds_timer,
            PERIOD_TYPE_MINUTES: minutes_timer,
            PERIOD_TYPE_HOURS: hours_timer,
            PERIOD_TYPE_DAYS: days_timer,
        }
        _method_map[self._period_type](path)

if __name__ == "__main__":
    abspath = os.path.dirname(os.path.realpath(__file__))

    periodSecondsEventHandler = PeriodEventHandler(patterns = [os.path.join(abspath, 'period/seconds/*')],
            abspath = os.path.join(abspath, 'period/seconds/'))
    periodMinutesEventHandler = PeriodEventHandler(patterns = [os.path.join(abspath, 'period/minutes/*')],
            abspath = os.path.join(abspath, 'period/minutes/'),
            period_type = PERIOD_TYPE_MINUTES,
            get_period_seconds = lambda path: int(re.search('/minutes/(\d+)/', path).group(1)) * 60)
    periodHoursEventHandler = PeriodEventHandler(patterns = [os.path.join(abspath, 'period/hours/*')],
            abspath = os.path.join(abspath, 'period/hours/'),
            period_type = PERIOD_TYPE_HOURS,
            get_period_seconds = lambda path: int(re.search('/hours/(\d+)/', path).group(1)) * 60*60)
    periodDaysEventHandler = PeriodEventHandler(patterns = [os.path.join(abspath, 'period/days/*')],
            abspath = os.path.join(abspath, 'period/days/'),
            period_type = PERIOD_TYPE_DAYS,
            get_period_seconds = lambda path: int(re.search('/days/(\d+)/', path).group(1)) * 60*60*24)

    opStopEventHandler = StopEventHandler(patterns = [os.path.join(abspath, 'op/stop/*')],
            abspath = os.path.join(abspath, 'op/stop/'))
    #opUpgradeEventHandler = UpgradeEventHandler(patterns = [os.path.join(abspath, 'op/upgrade/*')], abspath = abspath)

    observer = Observer()
    observer.schedule(periodSecondsEventHandler, abspath, True)
    observer.schedule(periodMinutesEventHandler, abspath, True)
    observer.schedule(periodHoursEventHandler, abspath, True)
    observer.schedule(periodDaysEventHandler, abspath, True)
    observer.schedule(opStopEventHandler, abspath, True)
    #observer.schedule(opUpgradeEventHandler, abspath, True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
