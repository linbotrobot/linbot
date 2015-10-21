from pyimagesearch.tempimage import TempImage
from dropbox.client import DropboxOAuth2FlowNoRedirect
from dropbox.client import DropboxClient
from picamera.array import PiRGBArray
from picamera import PiCamera
import warnings
import datetime
import imutils
import time
import cv2

avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0
lastTimelapse = datetime.datetime.now()

class motionObject:
    x=0; y=0; w=0; h=0; area=0; confirmed=False
    
    def reset(self):
        self.x=0; self.y=0; self.w=0; self.h=0; self.area=0; self.confirmed=False

def handleTimelaps(frame, rawCapture, conf, log):
    global lastTimelapse
    
    timestamp = datetime.datetime.now()
    elapsed = timestamp - lastTimelapse
    #print elapsed
    if( elapsed.seconds > conf["timelapse"]):
        ts = timestamp.strftime("%Y%m%d%H%M%S")
        path = "{timestamp}.jpg".format(timestamp=ts)
        if(conf["images_to_usb"] == "ON"):
            path = conf["usb_path"]+"/"+path
        cv2.imwrite(path, frame)
        log.write("INFO", "Take a timelapse picture")
        lastTimelapse = timestamp

def handleFaceFrame(frame, rawCapture, conf, log):
    global avg
    global lastUploaded
    global motionCounter

    obj = motionObject()
    timestamp = datetime.datetime.now()
    image = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier("face.xml")
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=1,
        minSize=(20, 20),
        flags = cv2.cv.CV_HAAR_SCALE_IMAGE
        )
    if(len(faces)>0):
        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(gray, (x, y), (x+w, y+h), (0, 255, 0), 2)
            obj.x = x; obj.y = y; obj.w = w; obj.h = h; obj.area = w*h; obj.confirmed=True
        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        path = "{timestamp}.jpg".format(timestamp=ts)
        if(conf["images_to_usb"] == "ON"):
            path = conf["usb_path"]+"/"+path
        cv2.imwrite(path, frame)
        log.write("INFO", "Found {0} faces!".format(len(faces)))
        #print '\a'
    return obj

def handleMotionFrame(frame, rawCapture, conf, log):
    global avg
    global lastUploaded
    global motionCounter
    
    obj = motionObject()
    timestamp = datetime.datetime.now()
    text = "Unoccupied"
    
    # resize the frame, convert it to grayscale, and blur it
#    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # if the average frame is None, initialize it
    if avg is None:
        log.write("INFO", "starting background model...")
        avg = gray.copy().astype("float")
        rawCapture.truncate(0)
        return obj

    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    # threshold the delta image, dilate the thresholded image to fill
    # in holes, then find contours on thresholded image
    thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # loop over the contours
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < conf["min_area"]:
            continue

        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        if(obj.area <= w*h):
            obj.x = x; obj.y = y; obj.w = w; obj.h = h; obj.area = w*h
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Occupied"

    # draw the text and timestamp on the frame
    #ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    ts = timestamp.strftime("%Y%m%d%H%M%S")
    cv2.putText(frame, "Room Status: {}".format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    # check to see if the room is occupied
    if text == "Occupied":
        # check to see if enough time has passed between uploads
        if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
            # increment the motion counter
            motionCounter += 1

            # check to see if the number of frames with consistent motion is
            # high enough
            if motionCounter >= conf["min_motion_frames"]:
                # write the image to temporary file
                t = TempImage()
                cv2.imwrite(t.path, frame)
                print "[UPLOAD] {}".format(ts)
                obj.confirmed=True
                # check to see if dropbox sohuld be used
                if conf["use_dropbox"]:
                    # upload the image to Dropbox and cleanup the tempory image
                    path = "{base_path}/{timestamp}.jpg".format(base_path=conf["dropbox_base_path"], timestamp=ts)
                    #path = "{timestamp}.jpg".format(timestamp=ts)
                    cv2.imwrite(path, frame)
                    client.put_file(path, open(t.path, "rb"))
                else:
                    path = "{timestamp}.jpg".format(timestamp=ts)
                    if(conf["images_to_usb"] == "ON"):
                        path = conf["usb_path"]+"/"+"{timestamp}.jpg".format(timestamp=ts)
                        #path = conf["usb_path"]+"/"+path
                    print path
                    cv2.imwrite(path, frame)
                t.cleanup()

                # update the last uploaded timestamp and reset the motion counter
                lastUploaded = timestamp
                motionCounter = 0

    # otherwise, the room is not occupied
    else:
        motionCounter = 0
    return obj
