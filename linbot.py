#!/usr/bin/env python

from dropbox.client import DropboxOAuth2FlowNoRedirect
from dropbox.client import DropboxClient
from picamera.array import PiRGBArray
from picamera import PiCamera
from motiondetection import detection
from motiondetection import logger
import warnings
import datetime
import imutils
import json
import time
import cv2
import errno
import os

def safe_read(fd, size=1024):
   ''' reads data from a pipe and returns `None` on EAGAIN '''
   try:
      return os.read(fd, size)
   except OSError, exc:
      if exc.errno == errno.EAGAIN:
         return None
      raise

def handleCommand(cmd):
    global mode
    
    if(len(cmd) is not 0):
        cmd = cmd.rstrip()
        log.write("CMD", cmd)
        if(cmd == "exit"):
            raise KeyboardInterrupt
        elif(cmd == "motion"):
            mode = cmd
        elif(cmd == "idle"):
            mode = cmd
        elif(cmd == "snapshot"):
            mode = cmd
        else:
            mode = cmd

def main(conf):
    global new_pipe
    global mode
    client = None
    obj = detection.motionObject()

    # check to see if the Dropbox should be used
    if conf["use_dropbox"]:
        # connect to dropbox and start the session authorization process
        flow = DropboxOAuth2FlowNoRedirect(conf["dropbox_key"], conf["dropbox_secret"])
        log.write("INFO", "Authorize this application: {}".format(flow.start()))
        authCode = raw_input("Enter auth code here: ").strip()

        # finish the authorization and grab the Dropbox client
        (accessToken, userID) = flow.finish(authCode)
        client = DropboxClient(accessToken)
        log.write("INFO", "dropbox account linked")

    # initialize the camera and grab a reference to the raw camera capture
    camera = PiCamera()
    camera.resolution = tuple(conf["resolution"])
    camera.framerate = conf["fps"]
    rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

    # allow the camera to warmup, then initialize the average frame, last
    # uploaded timestamp, and frame motion counter
    log.write("INFO", "warming up...")
    time.sleep(conf["camera_warmup_time"])
    try:
        # capture frames from the camera
        for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            cmd = safe_read(new_pipe, 1024)
            handleCommand(cmd)
            # grab the raw NumPy array representing the image
            frame = f.array

            if(mode == "motion"):
                # make a motion detection
                obj = detection.handleMotionFrame(frame, rawCapture, conf, log)
                if((obj is not None) and (obj.area != 0)):
                    # print also if not confirmed
                    log.write("INFO", "Area: {}, x: {}".format(obj.area, obj.x))
            if(mode == "face"):
                # make a face detection
                obj = detection.handleFaceFrame(frame, rawCapture, conf, log)
                if((obj is not None) and (obj.area != 0)):
                    # print also if not confirmed
                    log.write("INFO", "Area: {}, x: {}".format(obj.area, obj.x))
            elif(mode == "idle"):
                pass
            elif(mode == "snapshot"):
                cv2.imwrite("../linbotNET/web/snapshot.jpg", frame)
                mode = "idle"
            else:
                pass

            # check to see if the frames should be displayed to screen
            if conf["show_video"]:
                # display the security feed
                cv2.imshow("Security Feed", frame)
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the loop
                if key == ord("q"):
                    break
            # clear the stream in preparation for the next frame
            rawCapture.truncate(0)
    except KeyboardInterrupt:
        rawCapture.truncate(0)
        log.write("INFO", "Exit.")
        return
    ########################################################################
            
if __name__ == "__main__":
    conf = json.load(open("conf.json"))
    pipe_path = conf["fifo_name"]
    mode = conf["default_mode"]
    log = logger.log(conf["debug"], conf["log_to_file"])
    
    # Open a fifo pipe for communication
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    try:
        new_pipe = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
        log.write("INFO", "Pipe opened")
    except:
        raise
    
    # Run main program
    main(conf)
