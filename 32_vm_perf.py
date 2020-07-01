#!/usr/bin/env python

from __future__ import print_function
from pyVmomi import vim
from pyVmomi import vmodl
from pyVim.connect import SmartConnectNoSSL, Disconnect
from threading import Thread

import atexit
import argparse
import getpass
import sys
import math
import time, datetime


def get_args():
    parser = argparse.ArgumentParser(
        description='Process args for retrieving all the Virtual Machines')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='Remote host to connect to')

    parser.add_argument('-o', '--port',
                        required=False,
                        action='store',
                        help="port to use, default 443", default=443)

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-d', '--uuid',
                        required=False,
                        action='store',
                        help='Instance UUID (not BIOS id) of a VM to find.')

    parser.add_argument('-i', '--ip',
                        required=False,
                        action='store',
                        help='IP address of the VM to search for')

    parser.add_argument('-n', '--name',
                        required=False,
                        action='store',
                        help='Name of the VM to search for')

    args = parser.parse_args()

    password = None
    if args.password is None:
        password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.host, args.user))

    args = parser.parse_args()

    if password:
        args.password = password

    return args


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder,
                                                        vimtype,
                                                        True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break
    return obj


def convertSize(sizeBytes):
    floor = math.floor
    log = math.log
    name = ("B", "KB", "MB", "GB", "TB", "PB")
    base = int(log(sizeBytes, 1024))
    power = pow(1024,base)
    size = round(sizeBytes/power,2)
    return "{}{}".format(round(size, 2),name[base])


class perfdata():
    def perfcounters(self):
        perfcounter=['cpu.usage.average','mem.usage.average','net.usage.average']
        return perfcounter

    def run(self, content, vm, counter_name):
        try:
            perf_dict = {}
            perfManager = content.perfManager
            perfList = content.perfManager.perfCounter
            for counter in perfList:
                counter_full = "{}.{}.{}".format(counter.groupInfo.key,counter.nameInfo.key,counter.rollupType)
                perf_dict[counter_full] = counter.key

            counterId = perf_dict[counter_name]
            metricId = vim.PerformanceManager.MetricId(counterId=counterId, instance="")

            #'''
            startTime = datetime.datetime.now() - datetime.timedelta(hours=1)
            #startTime = datetime.datetime.now() - datetime.timedelta(days=7)
            endTime = datetime.datetime.now()
            #'''

            '''
            startTime = datetime.datetime(2020, 6, 23)
            endTime = datetime.datetime(2020, 6, 24)
            '''

            query = vim.PerformanceManager.QuerySpec(entity=vm,
                                                        metricId=[metricId],
                                                        startTime=startTime,
                                                        endTime=endTime,
                                                        maxSample=10)

            stats = perfManager.QueryPerf(querySpec=[query])
            count=0
            output=[]
            for val in stats[0].value[0].value:
                perfinfo={}
                if counter_name == 'net.usage.average':
                    val=float(val)
                else:
                    val=float(val/100)
                perfinfo['timestamp']=stats[0].sampleInfo[count].timestamp + datetime.timedelta(hours=9)
                perfinfo['hostname']=vm.summary.config.name
                perfinfo['value']=val
                output.append(perfinfo)
                count+=1
            for out in output:
                print("Hostname: {}  Resoruce: {} TimeStame: {} Usage: {}".format(out['hostname'],
                                                                                  counter_name,
                                                                                  out['timestamp'],
                                                                                  out['value']) )

        except vmodl.MethodFault as e:
            print("Caught vmodl fault : " + e.msg)
            return -1
        except Exception as e:
            print("Caught exception : " + str(e))
            return -1
        return 0



def main():
    args = get_args()
    try:
        si = SmartConnectNoSSL(host=args.host,
                               user=args.user,
                               pwd=args.password,
                               port=int(args.port))
        atexit.register(Disconnect, si)

    except IOError as e:
        pass

    if not si:
        raise SystemExit("Unable to connect to host with supplied info.")

    content = si.RetrieveContent()
    search_index = content.searchIndex

    vm = None
    if args.uuid:
        vm = search_index.FindByUuid(None, args.uuid, True, True)
    elif args.ip:
        vm = search_index.FindByIp(None, args.ip, True)
    else:
        vm = get_obj(content, [vim.VirtualMachine], args.name)
   
    if not vm:
        print(u"Could not find a virtual machine to examine.")
        exit(1)

    perf=perfdata()
    counters=perf.perfcounters()
    for counter in counters:
        p = Thread(target=perf.run, args=(content,vm,counter,))
        p.start()

        
if __name__ == "__main__":
    main()
