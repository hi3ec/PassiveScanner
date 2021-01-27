#! /usr/bin/env python
import subprocess
import sys
import re
import netifaces
import socket
import time
from datetime import date
from IPy import IP
from networking.ethernet import Ethernet
from networking.ipv4 import IPv4
from networking.icmp import ICMP
from networking.tcp import TCP
from networking.udp import UDP
from networking.pcap import Pcap
from pymongo import MongoClient
from threading import Event
from concurrent.futures import ThreadPoolExecutor
import struct

def main():
    db = selectdatabase()
    inf = ethinterface()
    event = Event()
    while True:
        event.clear()
        with ThreadPoolExecutor(max_workers=2) as executor:           
            executor.submit(passive_scan, event, db, inf)
            executor.submit(mac_vendor_db, db)
            #executor.submit(change_html, event, webcol)
            time.sleep(10)
            event.set()
   
def selectdatabase():
    database_list = ['Mongodb', 'PostgreSQL']
    for index in range(len(database_list)):
        print (index, ':', database_list[index])
    db = int(input('enter database number '))
    database = database_list[db]
    print('database selected is:', database)

    if database == 'Mongodb':
        client = MongoClient('mongodb://localhost:27017/')
        scannerdb = client['scanner']
        return scannerdb

    elif database == 'PostgreSQL':
        print('hi')
    
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

def mac_vendor_db(db):
    #save mac vendor to database
    print('start update mac vendor database')
    maccol = db["mac_vendor"]
    macfile = 'mac-vendor.txt'
    file1 = open(macfile, 'r').readlines()
    for line in file1:
        maccol.update_one({'mac3B':line.strip()[:6]},{'$set': {'mac_vendor':line.strip()[7:]}})  
    print('Update mac vendor database finished')

def passive_scan(event, db, inf):
    #db.drop_collection("passive_scanner")
    passivecol = db["passive_scanner"]
    start = time.time()
    pcap = Pcap(f'pcap/{start}.pcap')
    conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    exception_ip = ['0.0.0.0', '127.0.0.1', ]
    exception_ttl = ['1','0']
    os_type = ['windows','linux']

    while not event.is_set():
        raw_data, addr = conn.recvfrom(65535)
        if addr[0] == inf:
            pcap.write(raw_data)
            eth = Ethernet(raw_data)
            #IPV4
            if eth.proto == 8:
                ipv4 = IPv4(eth.data)
                src_type = IP(ipv4.src).iptype()
                des_type = IP(ipv4.target).iptype()

                # ICMP
                if ipv4.proto == 1:
                    icmp = ICMP(ipv4.data)
                    icmp_head = (icmp.type, icmp.code, icmp.checksum)
                
                # TCP
                elif ipv4.proto == 6:
                    tcp = TCP(ipv4.data)
                    tcp_head = (tcp.src_port, tcp.dest_port, tcp.sequence, tcp.acknowledgment, tcp.flag_urg, tcp.flag_ack, tcp.flag_psh, tcp.flag_rst, tcp.flag_syn, tcp.flag_fin)

                # UDP
                elif ipv4.proto == 17:
                    udp = UDP(ipv4.data)
                    udp_head = (udp.src_port, udp.dest_port, udp.size)

                # Other IPv4
                else:
                    #print(ipv4.data)
                    pass

                # OS Detection
                if ipv4.ttl in range(60,65):
                    OS = os_type[1]
                elif ipv4.ttl in range(120,129):
                    OS = os_type[0]
                else:
                    OS = ipv4.ttl

                # 
                if src_type == 'PRIVATE':
                    if ipv4.src not in exception_ip and str(ipv4.ttl) not in exception_ttl:
                        day = str(date.today())
                        tsec = time.time()
                        mac = eth.src_mac
                        mac_strip = mac.replace(":", "").replace("-", "").replace(".","").upper().strip()[:6]
                        index = {"IP Address": ipv4.src,'MAC Address': eth.src_mac,'MAC Vendor': mac_strip, 'OS': OS, "day":day}
                        data = { "Time": tsec}
                        passivecol.update_one(index, 
                        {
                            '$push': { "Data" : data },
                            '$min': { "First": data.get('Time')},
                            '$max': { "Last": data.get('Time')},
                            },
                            upsert=True)
            else:
                #print(eth.data)
                pass                
    pcap.close()

def ParsPcap():
    pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()