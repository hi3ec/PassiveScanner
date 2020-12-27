#! /usr/bin/env python

import subprocess
import sys
import re
import netifaces
import socket
import time
from IPy import IP
from networking.ethernet import Ethernet
from networking.ipv4 import IPv4
from networking.pcap import Pcap
from pymongo import MongoClient




def main():
    client = MongoClient('mongodb://localhost:27017/')
    scannerdb = client['scanner']
    passivecol = scannerdb["passive_scanner"]

    #ethinterface()
    passive_scan(passivecol)

def ethinterface():
    """
    Uses the python library netifaces to enumerate a list of the interfaces
    on the system.
    Presents a list of interfaces and prompt the use to select one.
    """
    iflist = netifaces.interfaces()
    print('Interfaces found')

    for index in range(len(iflist)):
        print (index, ':', iflist[index])

    interface = input('enter interface # ')
    interface = int(interface)
    interface = iflist[interface]
    print('interface selected is:', interface)
    return interface

def passive_scan(passivecol):
   
    pcap = Pcap('capture.pcap')
    conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    
    exception_ip = ['0.0.0.0', '127.0.0.1', ]
    exception_ttl = ['1']

    while True:
        try:
            raw_data , addr= conn.recvfrom(65535)
            pcap.write(raw_data)
            eth = Ethernet(raw_data)

            ipv4 = IPv4(eth.data) 
            ip_address = IP(ipv4.src)
            ip_type = ip_address.iptype()
            if ip_type == 'PRIVATE':
                if ipv4.src not in exception_ip:
                    if str(ipv4.ttl) not in exception_ttl:
                        if eth.proto == 8:
                            key = {"mac_address":eth.src_mac, "ip_address": ipv4.src}
                            data = { "mac_address": eth.src_mac, "ip_address": ipv4.src, "os": "windows" }
                            passivecol.update_one(key, {'$set': data},upsert=True)

                            #print('update database for mac address: ' + eth.src_mac)
                           
        except KeyboardInterrupt:
            passivecol.update_one(key,{'$set': data}, upsert=True)
            time.sleep(5)
            break
    pcap.close()

if __name__ == '__main__':
    main()
