import os
import json

def main():
    pid = os.fork()
    if pid == 0:
        print 'fork ok, exit'
    elif pid > 0:
        print 'I am child, ok'
    elif pid < 0:
        print 'fork fail, exit'

if __name__ == '__main__':
    main()
