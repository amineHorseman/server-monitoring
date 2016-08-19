#!/usr/bin/env python
# coding: utf-8 

import socket
import time
import json
import urllib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from subprocess import Popen, PIPE

############################################
#         CONFIGURATION VARIABLES          #
############################################
PORT = 11350 # listening port of the service_provider script
DESTINATION_MAIL_ADDRESS = "admin@mail.com"  # your mail address
MAIL_ADDRESS = "alerts@yourserver.com"  # the adress that will be displayed in your mailbox
REMOTE_SERVER_IP = "127.0.0.1"  # the IP adress of your server ("127.0.0.1" if your client script is located in the server itself)
AUTH_CODE = "password" # the same password defined in the service_provider script (a simple security check)
############################################

class ServerChecker:

    def __init__(self):
        self.file_directory = os.path.dirname(os.path.realpath(__file__))
        self.start_time = time.time()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.main()

    def check_websites(self, websites):
        websites_log = ''
        for url in websites:
            if url[-1] == "\n":
                url = url[:-1]
            try: 
                http_code = urllib.urlopen("http://" + url).getcode()
                if (http_code == 200):
                    websites_log += url + " >> OK\n"
                else:
                    websites_log += url + " >> " + str(http_code) + "\n"
            except Exception as e:
                websites_log += url + " >> Not reachable\n"
                #print e
        return websites_log

    def save_status(self, log):
        f = open(self.file_directory + "/last_status.log", 'w')
        f.write(log)
        f.close()

    def status_changed(self, log):
        try:
            f = open(self.file_directory + "/last_status.log", 'r')
            last_log = f.read()
            f.close()
        except:
            last_log = ''

        if log != last_log:
            return True
        else:
            return False
    
    def sendmail(self, log):
        execution_time = "{:5.4f}".format(time.time() - self.start_time)
        mail_content = "<html><body><h3>DATE {} {}</h3><p><br />{}<br /><br />Total execution time: {}</body></html>".format(time.strftime("%x"), 
            time.strftime("%X"), log.replace("\n", "<br />"), execution_time)
        html = MIMEText(mail_content, "html")
        msg = MIMEMultipart("alternative")
        msg["From"] = MAIL_ADDRESS
        msg["To"] = DESTINATION_MAIL_ADDRESS
        msg["Subject"] = "[KoulElBanane] Server status alert"
        msg.attach(html)

        p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
        p.communicate(msg.as_string())
        
        datetime = round(time.time())
        f = open(self.file_directory + "/last_mail_time.log", 'w')
        json.dump(datetime, f)
        f.close()

        #print "sending mail..."
        #print mail_content

    def no_mail_sent_since_yesterday(self):
        datetime = round(time.time())
        try:
            f = open(self.file_directory + "/last_mail_time.log", 'r')
            last_datetime = json.load(f)
            f.close()
        except:
            last_datetime = 0
        
        if datetime - last_datetime > 3600 * 24:
            return True
        else:
            return False

    def main(self):
        
        try:
            #print "connecting to server"
            self.socket.connect((REMOTE_SERVER_IP, PORT))

            #print "sending authentification code"
            self.socket.send(AUTH_CODE)

            if socket is not None:
                #print "waiting for websites list"
                websites = self.socket.recv(2048)
                #print "checking websites"
                websites_log = self.check_websites(json.loads(websites))
                #print "waiting for services status"
                services_log = self.socket.recv(2048)

                log = "***Webstites***\n{}\n\n***SERVICES***\n{}\n".format(
                    websites_log, services_log)
                if self.status_changed(log):
                    #print "status changed"
                    self.save_status(log)
                    self.sendmail(log)
                
                if self.no_mail_sent_since_yesterday():
                    self.sendmail(log)
            
            else:
                #print "connection aborted"
                pass

            self.socket.close()

        except socket.timeout:
            self.sendmail("Cannot establish a connection with the server")
	    

ServerChecker()
