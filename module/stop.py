import os

from module import *

STOP_ADD = 'stop_add'
STOP_REMOVE = 'stop_remove'

class Stop:
    def __init__(self, rootpath):
        self._rootpath = PathJoin(rootpath, 'stop')

    @property
    def rootpath(self):
        return self._rootpath

    def set_monitor(self, monitor):
        self._monitor = monitor

    def probefile(self):
        fnames = GetAllFilepath(self._rootpath)
        for f in fnames:
            self.process(FsMsg(self.get_op_path(f), STOP_ADD))

    def add(self, filepath):
        self._monitor.process_stop(filepath)

    def remove(self, filepath):
        self._monitor.process_start(filepath)

    def process(self, msg):
        _method_map = {
            STOP_ADD: self.add,
            STOP_REMOVE: self.remove,
        }

        filepath = msg.filepath
        op_type = msg.op_type
        _method_map[op_type](filepath)

    # return: /period/seconds/1/x.sh
    def get_op_path(self, filepath):
        if filepath.startswith(self._rootpath):
            return filepath[len(self._rootpath):]
        return filepath

    def on_moved(self, event):
        src_path = event.src_path
        dest_path = event.dest_path
        if src_path.startswith(self._rootpath):
            self.process(FsMsg(self.get_op_path(src_path), STOP_REMOVE))
            if dest_path.startswith(self._rootpath):
                self.process(FsMsg(self.get_op_path(dest_path), STOP_ADD))
        elif dest_path.startswith(self._rootpath):
                self.process(FsMsg(self.get_op_path(dest_path), STOP_ADD))
    
    def on_created(self, event):
        self.process(FsMsg(self.get_op_path(event.src_path), STOP_ADD))

    def on_deleted(self, event):
        self.process(FsMsg(self.get_op_path(event.src_path), STOP_REMOVE))

    def on_modified(self, event):
        pass
