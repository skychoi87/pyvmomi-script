#!/usr/bin/env python

from pyVmomi import vim
from pyVim.connect import SmartConnectNoSSL, Disconnect
from tools import cli

import atexit
import sys
import json
import string


def main():

    args = cli.get_args()

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
    perfManager = content.perfManager

    counterInfo = {}
    for c in perfManager.perfCounter:
        prefix = c.groupInfo.key
        fullName = c.groupInfo.key + "." + c.nameInfo.key + "." + c.rollupType
        counterInfo[fullName] = c.key


    dict_to_str = json.dumps(counterInfo)
    dict_to_str = dict_to_str.replace(',', '\n')

    sys.stdout = open('counterInfo.txt','w')
    print(dict_to_str)



#container = content.rootFolder
#viewType = [vim.VirtualMachine]
#recursive = True

#containerView = content.viewManager.CreateContainerView(container, viewType, recursive)
#children = containerView.view

#for child in children:
    # Get all available metric IDs for this VM
#    counterIDs = [m.counterId for m in
#                  perfManager.QueryAvailablePerfMetric(entity=child)]

    # Using the IDs form a list of MetricId
    # objects for building the Query Spec
#    metricIDs = [vim.PerformanceManager.MetricId(counterId=c,instance="*")
#                 for c in counterIDs]

    # Build the specification to be used
    # for querying the performance manager
#    spec = vim.PerformanceManager.QuerySpec(maxSample=1,
#                                            entity=child,
#                                            metricId=metricIDs)
    # Query the performance manager
    # based on the metrics created above
#    result = perfManager.QueryStats(querySpec=[spec])

#    print(result, child.summary.config.name)



# Start program
if __name__ == "__main__":
   main()

