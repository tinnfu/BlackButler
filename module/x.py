import threading
import subprocess
import os
import sys

from module import *

X_ADD = 'x_add'
X_STOP = 'x_stop'
X_START = 'x_start'

class X:
    def __init__(self, rootpath):
        self._blacklist = set()
        self._rootpath = PathJoin(rootpath, 'x')

    def set_monitor(self, monitor):
        self._monitor = monitor

    @property
    def rootpath(self):
        return self._rootpath
    
    def probefile(self):
        if not os.path.exists(self._rootpath):
            os.mkdir(self._rootpath)

        fnames = GetAllFilepath(self._rootpath)
        for f in fnames:
            self.process(FsMsg(self.get_op_path(f), X_ADD))

    @staticmethod
    def getfilename(path, filenames):
        items = os.listdir(path)
        for item in items:
            filename = PathJoin(path, item)
            if os.path.isfile(filename):
                filenames.append(filename)
            elif os.path.isdir(filename):
                getfilename(filename, filenames)


    def add(self, filepath):
        for bl in self._blacklist:
            if filepath.startswith(bl):
                return

        if filepath.endswith('.x'): return

        srcfilepath = PathJoin(self._rootpath, filepath)
        dstfilepath = srcfilepath + '.x' 
        os.rename(srcfilepath, dstfilepath)

    def stop(self, filepath):
        self._blacklist.add(filepath)

        filenames = []
        X.getfilename(PathJoin(self._rootpath, filepath), filenames)
        for srcfilepath in filenames:
            if not srcfilepath.endswith('.x'): continue
            dstfilepath = srcfilepath
            while dstfilepath.endswith('.x'):
                dstfilepath = dstfilepath[:-2] 
            assert dstfilepath != ''
            os.rename(srcfilepath, dstfilepath)

    def start(self, filepath):
        self._blacklist.remove(filepath)

        filenames = []
        X.getfilename(PathJoin(self._rootpath, filepath), filenames)
        for srcfilepath in filenames:
            if srcfilepath.endswith('.x'): continue
            dstfilepath = srcfilepath + '.x'
            os.rename(srcfilepath, dstfilepath)

    def process(self, msg):
        _method_map = {
            X_ADD: self.add,
            X_STOP: self.stop,
            X_START: self.start,
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
            if dest_path.startswith(self._rootpath):
                self.process(FsMsg(self.get_op_path(dest_path), X_ADD))
        elif dest_path.startswith(self._rootpath):
                self.process(FsMsg(self.get_op_path(dest_path), X_ADD))
    
    def on_created(self, event):
        self.process(FsMsg(self.get_op_path(event.src_path), X_ADD))

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        pass

    def on_stop(self, filepath):
        self.process(FsMsg(self.get_op_path(filepath), X_STOP))

    def on_start(self, filepath):
        self.process(FsMsg(self.get_op_path(filepath), X_START))
