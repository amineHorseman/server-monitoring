#!/usr/bin/env python

import socket
import threading
import sh
import json
import time
import os

############################################
#         CONFIGURATION VARIABLES          #
############################################
PORT = 11350 # listening port
SERVICES_TO_MONITOR = ['apache2', 'cron', 'mysql', 'fail2ban']  # list of the services to check
AUTH_CODE = "password"  # set a password to reject other persons from checking your running services (it's not a perfect security, but it's better than nothing xD)
############################################

WAITING_TIME_BEFORE_RECHECKING_SERVICES = 10

class ServerMonitoring:

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("",PORT))
        self.main()

    def main(self):
        while True:
            #print "listening..."
            self.server_socket.listen(10)
            #print "waiting for a client..."
            (client_socket, (ip, port)) = self.server_socket.accept()
            newthread = MonitoringThread(ip, port, client_socket)
            #print "starting new thread"
            newthread.start()


class MonitoringThread(threading.Thread):

    def __init__(self, ip, port, service_socket):
        self.file_directory = os.path.dirname(os.path.realpath(__file__))
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.service_socket = service_socket
        self.down_services = []

    def check_authentification(self, code):
        if code == AUTH_CODE:
            return True
        else: 
            return False

    def check_services(self):
        checked_services = dict()
        for service_name in SERVICES_TO_MONITOR:
            try:
                status = sh.service(service_name, "status")
                if "is not running" in status or "stop" in status:
                    checked_services[service_name] = 0 # down
                elif "running" in status: 
                    checked_services[service_name] = 1 # up 
                else:
                    checked_services[service_name] = -1 #unknown
            except:
                checked_services[service_name] = -1
        return checked_services

    def restart_services(self, services):
        trying_to_restart_service = False
        try:
            for service_name in services:
                if services[service_name] == 0:
                    trying_to_restart_service = True 
                    sh.service(service_name, "start")
        except:
            pass

        if trying_to_restart_service:
            time.sleep(WAITING_TIME_BEFORE_RECHECKING_SERVICES)

    def hosted_websites(self):
        websites = []
        file = open(self.file_directory + '/hosted-websites.txt', 'r')
        for line in file:
            websites.append(line)
        return websites

    def run(self): 
        #print "[Th] waiting for authentification code"
        auth_code = self.service_socket.recv(2048)
        if self.check_authentification(auth_code):
            #print "[Th] sending wesites list"
            websites = json.dumps(self.hosted_websites())
            self.service_socket.send(websites)
            
            #print "[Th] checking services"
            services_log = ""
            services_t1 = self.check_services()
            self.restart_services(services_t1)
            services_t2 = self.check_services()
            for service_name in services_t1:
                if services_t1[service_name] != services_t2[service_name] \
                        and services_t1[service_name] == 0:
                    services_log += service_name + " >> Was Down, Restarted\n"
                elif services_t1[service_name] == 0:
                    services_log += service_name + " >> Down\n"
                elif services_t2[service_name] == 1:
                    services_log += service_name + " >> OK\n"
                elif services_t2[service_name] == -1:
                    services_log += service_name + " >> ??\n"
                
            #print "[Th]sending services status"
            self.service_socket.send(services_log)

        #print "[Th]Finishing thread"
        self.service_socket.close()

ServerMonitoring()
