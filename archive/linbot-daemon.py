#!/usr/bin/env python

import sys, time, os
from daemon import daemon
import logging
import json
import motion

class MyDaemon(daemon):
    def run(self):
        global g_exit
        self.logger.info("Starting linbot daemon.")
        self.logger.debug("Debugging on")
        
        while True:
            ########################################################################
            # Main
            ########################################################################

            warnings.filterwarnings("ignore")
            conf = json.load(open("conf.json"))
            self.logger.info("Reading configuration")
            client = None

            # check to see if the Dropbox should be used
            if conf["use_dropbox"]:
                # connect to dropbox and start the session authorization process
                flow = DropboxOAuth2FlowNoRedirect(conf["dropbox_key"], conf["dropbox_secret"])
                print "[INFO] Authorize this application: {}".format(flow.start())
                authCode = raw_input("Enter auth code here: ").strip()

                # finish the authorization and grab the Dropbox client
                (accessToken, userID) = flow.finish(authCode)
                client = DropboxClient(accessToken)
                print "[SUCCESS] dropbox account linked"

            # initialize the camera and grab a reference to the raw camera capture
            camera = PiCamera()
            camera.resolution = tuple(conf["resolution"])
            camera.framerate = conf["fps"]
            rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

            # allow the camera to warmup, then initialize the average frame, last
            # uploaded timestamp, and frame motion counter
            print "[INFO] warming up..."
            time.sleep(conf["camera_warmup_time"])

            avg = None
            lastUploaded = datetime.datetime.now()
            motionCounter = 0

            # capture frames from the camera
            for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                # grab the raw NumPy array representing the image
                frame = f.array
                # make a motion detection
                motion.handleFrame(frame)
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
            ########################################################################
            
            # Non blocking loop to intercept Stop
            while(g_exit != 1):
                time.sleep(10)
            t_com.join()
            self.logger.info("Closing linbot daemon.")

if __name__ == "__main__":
    g_exit = 0
    daemon = MyDaemon('/tmp/daemon-example.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            g_exit = 1
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
