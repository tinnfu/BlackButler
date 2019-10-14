import os

class FsMsg:
    def __init__(self, filepath, op_type):
        self.filepath = filepath
        self.op_type = op_type

PathJoin = lambda base, *path: os.path.join(base, *[p if p[0] != '/' else p[1:] for p in path])

def GetAllFilepath(path):
    fnames = os.listdir(path)
    filepaths = []
    for f in fnames:
        if os.path.isdir(PathJoin(path, f)):
            filepaths += GetAllFilepath(PathJoin(path, f))
        else:
            filepaths.append(PathJoin(path, f))

    return filepaths
