#!/usr/bin/env python

"""
vSphere Python SDK program for demonstrating vSphere perfManager API based on
Rbvmomi sample https://gist.github.com/toobulkeh/6124975
"""

"""
https://github.com/dograga/ESXPerfData/blob/master/vmperfcollection_threaded.py
"""

import argparse
import atexit
import getpass
#import string, re
import time, datetime

from threading import Thread
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim


def get_args():
    """
    This sample uses different arguments than the standard sample. We also
    need the vihost to work with.
    """
    parser = argparse.ArgumentParser(
        description='Process args for retrieving all the Virtual Machines')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='Remote host to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-x', '--vihost',
                        required=True,
                        action='store',
                        help='Name of ESXi host as seen in vCenter Server')

    parser.add_argument('-S', '--sdate',
                        required=False,
                        action='store',
                        help='Start Date, Time Set 00:00:00')

    parser.add_argument('-E', '--edate',
                        required=False,
                        action='store',
                        help='End Date, Time Set 00:00:00')

    args = parser.parse_args()
    if not args.password:
        args. password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.host, args.user))

    return args


class perfdata():
    def perfcounters(self):
        perfcounter=['cpu.usage.average','mem.usage.average','net.usage.average']
        return perfcounter

    def run(self, content, host, counter_name):
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

            query = vim.PerformanceManager.QuerySpec(entity=host,
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
                perfinfo['hostname']=host.summary.config.name
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
        service_instance = connect.SmartConnectNoSSL(host=args.host,
                                                user=args.user,
                                                pwd=args.password,
                                                port=int(args.port))
    except:
        print("Could not connect to the specified host using specified "
              "username and password")
        return -1

    atexit.register(connect.Disconnect, service_instance)
    content = service_instance.RetrieveContent()

    search_index = content.searchIndex
    host = search_index.FindByDnsName(dnsName=args.vihost, vmSearch=False)

    perf=perfdata()
    counters=perf.perfcounters()
    for counter in counters:
        p = Thread(target=perf.run,args=(content,host,counter,))
        p.start()
        
# Start program
if __name__ == "__main__":
    main()
