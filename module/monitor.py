from watchdog.observers import Observer
from watchdog.events import *
import time
from collections import OrderedDict

from module import PathJoin

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        FileSystemEventHandler.__init__(self)
        self._monitor = monitor
        self._monitor.probefile()

    def on_moved(self, event):
        if event.is_directory:
            return
        print('on_moved: %s -> %s' % (event.src_path, event.dest_path))
        self._monitor.process_moved(event)

    def on_created(self, event):
        if event.is_directory:
            return
        print('on_created: %s' % (event.src_path))
        self._monitor.process_created(event)

    def on_deleted(self, event):
        if event.is_directory:
            return
        print('on_deleted: %s' % (event.src_path))
        self._monitor.process_deleted(event)

    def on_modified(self, event):
        if event.is_directory:
            return
        print('on_modified: %s' % (event.src_path))
        self._monitor.process_modified(event)

class FsMonitor:
    def __init__(self, rootpath):
        self._handler = OrderedDict()
        self._rootpath = rootpath

    @property
    def handler(self):
        return str(self._handler)

    def probefile(self):
        for basedir in self._handler:
            self._handler[basedir].probefile()

    def register(self, handler):
        basedir = handler.rootpath
        assert basedir not in self._handler
        self._handler[basedir] = handler
        self._handler[basedir].set_monitor(self)

    def unregister(self, handler):
        basedir = handler.rootpath + '/'
        assert basedir in self._handler
        del self._handler[basedir]

    def process_moved(self, event):
        src_path = event.src_path
        dest_path = event.dest_path
        for basedir in self._handler:
            if src_path.startswith(basedir) or dest_path.startswith(basedir):
                self._handler[basedir].on_moved(event)
                return

    def process_created(self, event):
        for basedir in self._handler:
            if event.src_path.startswith(basedir):
                self._handler[basedir].on_created(event)
                return

    def process_deleted(self, event):
        for basedir in self._handler:
            if event.src_path.startswith(basedir):
                self._handler[basedir].on_deleted(event)
                return

    def process_modified(self, event):
        for basedir in self._handler:
            if event.src_path.startswith(basedir):
                self._handler[basedir].on_modified(event)
                return

    def process_stop(self, filepath):
        path = PathJoin(self._rootpath, filepath)
        for basedir in self._handler:
            if path.startswith(basedir):
                self._handler[basedir].on_stop(path)
                return

    def process_start(self, filepath):
        path = PathJoin(self._rootpath, filepath)
        for basedir in self._handler:
            if path.startswith(basedir):
                self._handler[basedir].on_start(path)
                return
