#!/usr/bin/env python

from pyVmomi import vim
from tools import cli
from pyVim.connect import SmartConnectNoSSL, Disconnect
import atexit
import sys
import math

def main():

    args = cli.get_args()

    # Connect to the host without SSL signing
    try:
        si = SmartConnectNoSSL(
            host=args.host,
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

    # create a list of vim.VirtualMachine objects so
    # that we can query them for statistics
    container = content.rootFolder
    viewType = [vim.Datastore]
    recursive = True

    containerView = content.viewManager.CreateContainerView(container,
                                                            viewType,
                                                            recursive)
    children = containerView.view

    # Loop through all the VMs
    for datastore in children:
        print("")
        print("---------- DATASTORE : ",datastore.info.name, "------------")
        print("Name : ", datastore.info.name)
        print("Type : ", datastore.summary.type)
        print("Url  : ", datastore.info.url)
        print("Total Space : ", convertSize(datastore.summary.capacity))
        print("Free Space  : ", convertSize(datastore.summary.freeSpace))
        
def convertSize(sizeBytes):
    floor = math.floor
    log = math.log
    name = ("B", "KB", "MB", "GB", "TB", "PB")
    base = int(floor(log(sizeBytes, 1024)))
#    base = int(log(sizeBytes, 1024))
    power = pow(1024,base)
    size = round(sizeBytes/power,2)
    return "{}{}".format(round(size, 2),name[base])

if __name__ == "__main__":
    main()

