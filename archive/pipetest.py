#!/usr/bin/env python

#mkfifo pipe

import errno
import os
import time

def safe_read(fd, size=1024):
   ''' reads data from a pipe and returns `None` on EAGAIN '''
   try:
      return os.read(fd, size)
   except OSError, exc:
      if exc.errno == errno.EAGAIN:
         return None
      raise
      
print "Start"
pipe_path = "fifo"
new_pipe = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK) # pipe_path points to a FIFO
print "Pipe opened"

try:
    while(1):
        cmd = safe_read(new_pipe, 1024)
        if(len(cmd) is not 0):
            print cmd,
        time.sleep(0.1)
except KeyboardInterrupt:
    print "[INFO] Exit."
    
