#!/usr/bin/env python

import os
import argparse
import atexit
import getpass
import time, datetime
import plotly
import plotly.graph_objs as go

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim
from threading import Thread
from statistics import mean

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
#        perfcounter=['cpu.usage.average']
        return perfcounter

    def run(self, content, host, counter_name):
        try:

#### Set Values
            perf_dict = {}
            perfManager = content.perfManager
            perfList = content.perfManager.perfCounter
            for counter in perfList:
                counter_full = "{}.{}.{}".format(counter.groupInfo.key,counter.nameInfo.key,counter.rollupType)
                perf_dict[counter_full] = counter.key

            counterId = perf_dict[counter_name]
            metricId = vim.PerformanceManager.MetricId(counterId=counterId, instance="")

            '''
            startTime = datetime.datetime.now() - datetime.timedelta(hours=1)
            #startTime = datetime.datetime.now() - datetime.timedelta(days=7)
            endTime = datetime.datetime.now()
            '''
           
            #''' 
            startTime = datetime.datetime(2020, 6, 24)
            endTime = datetime.datetime(2020, 6, 25)
            #'''

#### Get Perf Data
####
            query = vim.PerformanceManager.QuerySpec(entity=host,
							metricId=[metricId],
							startTime=startTime,
							endTime=endTime,
							maxSample=10)
            stats = perfManager.QueryPerf(querySpec=[query])

            count=0
            x_output=[]
            y_output=[]
            for val in stats[0].value[0].value:
                x_timestamp={}
                y_usage={}
                if counter_name == 'net.usage.average':
                    val=float(val)
                else:
                    val=float(val/100)
                x_timestamp['timestamp']=stats[0].sampleInfo[count].timestamp + datetime.timedelta(hours=9)
                y_usage['value']=val
                x_output.append(x_timestamp)
                y_output.append(y_usage)
                count+=1

            slice_xout=[]
            slice_yout=[]
            for xout in x_output:
                slice_xout.append(xout['timestamp'])

            for yout in y_output:
                slice_yout.append(yout['value'])

            y_min = round(min(slice_yout), 2)
            y_max = round(max(slice_yout), 2)
            y_avg = round(mean(slice_yout), 2)

            '''
            print(x_output)
            print(y_output)
            print(slice_xout)
            print(slice_yout)
            '''

#### Create Graph
####
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=slice_xout,
                                     y=slice_yout,
                                     name=counter_name,
                                     mode='lines') )

            fig.update_layout(title={'text' : counter_name,
                                     'x':0.5,
                                     'yanchor' : 'bottom',
                                     'xanchor' : 'center'},
                              yaxis_title='Usage (%)')
            if counter_name == 'net.usage.average':
                fig.update_layout(yaxis_title='Usage (Kbps)')

            if y_min > 10:
                fig['layout']['yaxis'].update(range=[y_min-(y_min/10),y_max+(y_max/20)], autorange=False)
            else:
                fig['layout']['yaxis'].update(range=[0,y_max+(y_max/4)], autorange=False)

            #fig.write_html('/var/www/html/'+ counter_name +'.html', auto_open=True)
            #'''
            if not os.path.exists("graph_images"):
                os.mkdir("graph_images")
            # https://plotly.com/python/static-image-export/
            # https://github.com/plotly/orca
            fig.write_image('graph_images/'+ counter_name +'.jpeg', width=600, height=600)
            #fig.write_image('graph_images/'+ counter_name +'.png')
            #'''

#### exception control
####
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
