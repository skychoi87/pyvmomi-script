#!/usr/bin/env python

from __future__ import print_function
from pyVmomi import vim
from pyVim.connect import SmartConnectNoSSL, Disconnect

import atexit
import argparse
import getpass
import sys
import math

def get_args():
    parser = argparse.ArgumentParser()

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


def main():

    args = get_args()

    # Connect to the host without SSL signing
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

#    perfManager = content.perfManager

#    container = content.rootFolder
#    viewType = [vim.HostSystem]
#    recursive = True
#    containerView = content.viewManager.CreateContainerView(container,
#                                                            viewType,
#                                                            recursive)
#    children = containerView.view

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


    print(u"Found Virtual Machine")
    print(u"=====================")
    details = {'name': vm.summary.config.name,
               'instance UUID': vm.summary.config.instanceUuid,
               'bios UUID': vm.summary.config.uuid,
               'path to VM': vm.summary.config.vmPathName,
               'guest OS id': vm.summary.config.guestId,
               'guest OS name': vm.summary.config.guestFullName,
               'host name': vm.runtime.host.name,
               'last booted timestamp': vm.runtime.bootTime}

    for name, value in details.items():
        print(u"  {0:{width}{base}}: {1}".format(name, value, width=25, base='s'))


#    print("Host Name : ", host.summary.config.name)
#    print("Host Product : ", host.summary.config.product.fullName)
#    print("Cpu Model : ", host.summary.hardware.cpuModel)
#    print("Cpu Threads : ", host.summary.hardware.numCpuThreads)
#    print("CPU Clock :", round(((host.hardware.cpuInfo.hz/1e+9)*host.hardware.cpuInfo.numCpuCores),0),"GHz")
#    print("Memory : ", convertMemory(host.hardware.memorySize))
#    print("System Model : ", host.summary.hardware.model)
#    print("uuid (BIOS identification) : ", host.summary.hardware.uuid)
#    print("vendor : ", host.summary.hardware.vendor)

        
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

