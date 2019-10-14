import threading
import subprocess
import os
import re

from module import *

PERIOD_ADD = 'period_add'
PERIOD_REMOVE = 'period_remove'
PERIOD_UPDATE = 'period_update'
PERIOD_STOP = 'period_stop'
PERIOD_START = 'period_start'

class PeriodTimer(threading.Timer):
    def __init__(self, interval, function, args = None, kwargs = None):
        threading.Timer.__init__(self, interval, function, args, kwargs)

    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)

def TimerTask(taskfilepath):
    exitcode, output = subprocess.getstatusoutput(taskfilepath)
    if exitcode != 0 and exitcode != 127:
        raise Exception('fail to exec: %s, (%s, %s)' % (taskfilepath, exitcode, output))
    print(output)

class Period:
    def __init__(self, rootpath):
        self._records = {}
        self._blacklist = set()
        self._rootpath = PathJoin(rootpath, 'period')

    def set_monitor(self, monitor):
        self._monitor = monitor

    @property
    def records(self):
        return self._records

    @property
    def rootpath(self):
        return self._rootpath
    
    def probefile(self):
        fnames = GetAllFilepath(self._rootpath)
        for f in fnames:
            self.process(FsMsg(self.get_op_path(f), PERIOD_ADD))
    
    def add(self, filepath):
        assert filepath not in self._records

        def get_period_seconds(filepath):
            ret = re.search('/seconds/(\d+)/', filepath)
            if ret: return int(ret.group(1))
            ret = re.search('/minutes/(\d+)/', filepath)
            if ret: return int(ret.group(1)) * 60
            ret = re.search('/hours/(\d+)/', filepath)
            if ret: return int(ret.group(1)) * 60 * 60
            ret = re.search('/days/(\d+)/', filepath)
            if ret: return int(ret.group(1)) * 60 * 60 * 24
            raise Exception('invalid filepath: %s' % filepath)

        interval = get_period_seconds(filepath)
        self._records[filepath] = PeriodTimer(interval, TimerTask, args = [PathJoin(self._rootpath, filepath),])
        if filepath in self._blacklist:
            return

        self._records[filepath].start()
    
    def remove(self, filepath):
        if filepath not in self._records:
            return

        self._records[filepath].cancel()
        del self._records[filepath]

    def update(self, filepath):
        self.remove(filepath)
        self.add(filepath)
    
    def stop(self, filepath):
        self._blacklist.add(filepath)
        self.remove(filepath)
    
    def start(self, filepath):
        self._blacklist.remove(filepath)
        self.add(filepath)

    def process(self, msg):
        _method_map = {
            PERIOD_ADD: self.add,
            PERIOD_REMOVE: self.remove,
            PERIOD_UPDATE: self.update,
            PERIOD_STOP: self.stop,
            PERIOD_START: self.start,
        }

        filepath = msg.filepath
        op_type = msg.op_type
        _method_map[op_type](filepath)

    # return: /seconds/1/x.sh
    def get_op_path(self, filepath):
        if filepath.startswith(self._rootpath):
            return filepath[len(self._rootpath):]
        return filepath

    def on_moved(self, event):
        src_path = event.src_path
        dest_path = event.dest_path
        if src_path.startswith(self._rootpath):
            self.process(FsMsg(self.get_op_path(src_path), PERIOD_REMOVE))
            if dest_path.startswith(self._rootpath):
                self.process(FsMsg(self.get_op_path(dest_path), PERIOD_ADD))
        elif dest_path.startswith(self._rootpath):
                self.process(FsMsg(self.get_op_path(dest_path), PERIOD_ADD))
    
    def on_created(self, event):
        self.process(FsMsg(self.get_op_path(event.src_path), PERIOD_ADD))

    def on_deleted(self, event):
        self.process(FsMsg(self.get_op_path(event.src_path), PERIOD_REMOVE))

    def on_modified(self, event):
        self.process(FsMsg(self.get_op_path(event.src_path), PERIOD_UPDATE))

    def on_stop(self, filepath):
        self.process(FsMsg(self.get_op_path(filepath), PERIOD_STOP))

    def on_start(self, filepath):
        self.process(FsMsg(self.get_op_path(filepath), PERIOD_START))
