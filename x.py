import os
import sys
import json
import fire
import subprocess

def getfilename(path, filenames):
    items = os.listdir(path)
    for item in items:
        filename = os.path.join(path, item)
        if os.path.isfile(filename):
            filenames.append(filename)
        elif os.path.isdir(filename):
            getfilename(filename, filenames)

def rename(path, srcSuffix, dstSuffix):
    filenames = []
    getfilename(path, filenames)

    for filename in filenames:
        if filename.endswith(srcSuffix):
            dstfilename = filename[:-len(srcSuffix)]
            dstfilename = dstfilename + dstSuffix
            print('rename: %s -> %s' % (filename, dstfilename))
            os.rename(filename, dstfilename)

def repair(path, srcSuffix):
    filenames = []
    getfilename(path, filenames)

    srcSuffix = srcSuffix.strip('.')
    for filename in filenames:
        if os.path.basename(filename).startswith('.'): continue
        status, output = subprocess.getstatusoutput('file %s' % filename.replace(' ', '\ ').replace('(', '\(').replace(')', '\)'))
        if status != 0:
            raise Exception("fail to exec: cmd: %s, (%s, %s)" % ('file %s' % filename, status, output))

        output = output.split(':', 1)[1]
        if srcSuffix.lower() in output.lower():
            srcfilename = filename[2:] if filename.startswith('.') else filename
            basename = srcfilename.split('.', 1)[0]
            dstfilename = './' + basename + '.' + srcSuffix
            print('rename: %s -> %s' % (filename, dstfilename))
            os.rename(filename, dstfilename)

class X:
    def __str__(self):
        return ''

    @staticmethod
    def x_shadow(path, conf):
        with open(conf, 'r') as f: buf = f.read()
        jm = json.loads(buf)

        for src, dst in jm.items():
            rename(path, src, dst)

    @staticmethod
    def x_restore(path, conf):
        with open(conf, 'r') as f: buf = f.read()
        jm = json.loads(buf)

        for src, dst in jm.items():
            rename(path, dst, src)

    @staticmethod
    def x_repair(path, conf):
        with open(conf, 'r') as f: buf = f.read()
        jm = json.loads(buf)

        for src, dst in jm.items():
            repair(path, src)

if __name__ == '__main__':
    fire.Fire(X)
