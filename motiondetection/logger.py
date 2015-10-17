#!/usr/bin/env python

class log:
    def __init__(self, debug, log_to_file):
        self.debug = debug
        self.log_to_file = log_to_file
        
    def writelog(self, message):
        if(self.log_to_file == "ON"):
            pass
        else:
            print message
        
    def write(self, level, message):
        if((self.debug == "ON") or (level == "ERROR")):
            self.writelog("["+level+"] "+message)
