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


def convertSize(sizeBytes):
    floor = math.floor
    log = math.log
    name = ("B", "KB", "MB", "GB", "TB", "PB")
    base = int(log(sizeBytes, 1024))
    power = pow(1024,base)
    size = round(sizeBytes/power,2)
    return "{}{}".format(round(size, 2),name[base])

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
               'CPU (core)': vm.summary.config.numCpu,
               'MEM (MB)': vm.summary.config.memorySizeMB,
               'host name': vm.runtime.host.name,
               'last booted timestamp': vm.runtime.bootTime}

    for name, value in details.items():
        print(u"  {0:{width}{base}}: {1}".format(name, value, width=25, base='s'))


    print(u"  Devices:")
    print(u"  --------")
    for device in vm.config.hardware.device:
        # diving into each device, we pull out a few interesting bits
        dev_details = {'key': device.key,
                       'summary': device.deviceInfo.summary,
                       'device type': type(device).__name__,
                       'backing type': type(device.backing).__name__}

        print(u"  label: {0}".format(device.deviceInfo.label))
        print(u"  ------------------")
        for name, value in dev_details.items():
            print(u"    {0:{width}{base}}: {1}".format(name, value,
                                                       width=15, base='s'))

        if device.backing is None:
            continue

        # the following is a bit of a hack, but it lets us build a summary
        # without making many assumptions about the backing type, if the
        # backing type has a file name we *know* it's sitting on a datastore
        # and will have to have all of the following attributes.
        if hasattr(device.backing, 'fileName'):
                datastore = device.backing.datastore

                if datastore and 'vmdk' in device.backing.fileName:
                    print(u"    datastore")
                    print(u"        name: {0}".format(datastore.name))
                    # there may be multiple hosts, the host property
                    # is a host mount info type not a host system type
                    # but we can navigate to the host system from there
                    for host_mount in datastore.host:
                        host_system = host_mount.key
                        print(u"        host: {0}".format(host_system.name))
                    print(u"        summary")
                    summary = {'capacity': convertSize(datastore.summary.capacity),
                               'freeSpace': convertSize(datastore.summary.freeSpace),
                               'file system': datastore.summary.type,
                               'url': datastore.summary.url}
                    for key, val in summary.items():
                        print(u"            {0}: {1}".format(key, val))

                print(u"    fileName: {0}".format(device.backing.fileName))
                print(u"    device ID: {0}".format(device.backing.backingObjectId))

        print(u"  ------------------")

    print(u"=====================")

        
if __name__ == "__main__":
    main()

