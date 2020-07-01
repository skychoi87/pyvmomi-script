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
    viewType = [vim.HostSystem]
    recursive = True

    containerView = content.viewManager.CreateContainerView(container,
                                                            viewType,
                                                            recursive)
    children = containerView.view
    #print(children)

    # Loop through all the VMs
    for host in children:
        print("")
        print("----------",host.summary.config.name, "------------")
        print("Host Name : ", host.summary.config.name)
        print("Host Product : ", host.summary.config.product.fullName)
        print("Cpu Model : ", host.summary.hardware.cpuModel)
#        print("Cpu Cores : ", host.summary.hardware.numCpuCores)
#        print("Cpu Packages : ", host.summary.hardware.numCpuPkgs)
        print("Cpu Threads : ", host.summary.hardware.numCpuThreads)
        print("CPU Clock :", round(((host.hardware.cpuInfo.hz/1e+9)*host.hardware.cpuInfo.numCpuCores),0),"GHz")
        print("Memory : ", convertMemory(host.hardware.memorySize))
        print("System Model : ", host.summary.hardware.model)
        print("uuid (BIOS identification) : ", host.summary.hardware.uuid)
        print("vendor : ", host.summary.hardware.vendor)
        
def convertMemory(sizeBytes):
    floor = math.floor
    log = math.log
    name = ("B", "KB", "MB", "GB", "TB", "PB")
    base = int(floor(log(sizeBytes, 1024)))
    power = pow(1024,base)
    size = round(sizeBytes/power,2)
    return "{}{}".format(floor(size),name[base])

if __name__ == "__main__":
    main()

