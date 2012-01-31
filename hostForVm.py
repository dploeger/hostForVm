# hostForVm.py

# Retrieve information from a vCenter, on which host a vm currently resides
# or what vms a host currently services

from suds.client import Client
import argparse
import logging
import sys

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(
        description = 'Find which host hosts a ' +
            'specific VM or which VMs are serviced by' +
            'a specific host.'
    )
    parser.add_argument(
        '--server', 
        metavar = 'server', 
        type = str, 
        nargs = 1,
        help = 'The vCenter-Server',
        required = True
    )
    parser.add_argument(
        '--username', 
        metavar = 'username', 
        type = str, 
        nargs = 1,
        help = 'Username for vCenter-Server', 
        required = True
    )
    parser.add_argument(
        '--password', 
        metavar = 'password', 
        type = str, 
        nargs = 1,
        help = 'Password for vCenter-Server', 
        required = True
    )
    parser.add_argument(
        '--mode', 
        type = str, 
        choices = 'vh', 
        nargs = 1,
        help = "Info mode: v = retrieve a host for a VM, " +
            "h = retrieve all VMs for a host",
        required = True
    )
    parser.add_argument(
        '--name', 
        type = str, 
        nargs = 1,
        help = "DNS-name of VM (as seen by VMware Tools) or host",
        required = True
    )

    args = parser.parse_args()
    
    url = "https://%s/sdk/vimService.wsdl" % (args.server[0])
    location = "https://%s/sdk/vimService" % (args.server[0])
    
    client = Client(url, location=location)
    
    serviceInstance = client.factory.create('ns0:ManagedObjectReference')
    serviceInstance._type = "ServiceInstance"
    serviceInstance.value = "ServiceInstance"
    
    serviceContent = client.service.RetrieveServiceContent(
        serviceInstance
    )
    
    client.service.Login(
        serviceContent.sessionManager, 
        args.username[0],
        args.password[0]
    )
    
    if (args.mode[0] == "v"):
    
        searchResult = client.service.FindByDnsName(
            serviceContent.searchIndex,
            dnsName = args.name[0],
            vmSearch = True
        )
        
        if (not searchResult):
            print "VM Not found"
            sys.exit(1)
        
        propertySpec = client.factory.create("ns0:PropertySpec")
        propertySpec.pathSet.append("runtime.host")
        propertySpec.all = False
        propertySpec.type = "VirtualMachine"
        
        objectSpec = client.factory.create("ns0:ObjectSpec")
        objectSpec.obj = searchResult
        
        propertyFilterSpec = client.factory.create("ns0:PropertyFilterSpec")
        propertyFilterSpec.propSet.append(propertySpec)
        propertyFilterSpec.objectSet.append(objectSpec)
        
        host = client.service.RetrievePropertiesEx(
            serviceContent.propertyCollector,
            [propertyFilterSpec]
        )
        
        if (not host):
            print "No Runtime (perhaps VM turned off)"
            sys.exit(2)
            
        hostFound = host.objects[0][1][0].val
        
        propertySpec.type = "HostSystem"
        propertySpec.pathSet.pop()
        propertySpec.pathSet.append("name")
        
        objectSpec.obj = hostFound
        
        hostName = client.service.RetrievePropertiesEx(
            serviceContent.propertyCollector,
            [propertyFilterSpec]
        )
        
        print hostName.objects[0][1][0].val
        
        sys.exit(0)
        
    if (args.mode[0] == "h"):
        
        searchResult = client.service.FindByDnsName(
            serviceContent.searchIndex,
            dnsName = args.name[0],
            vmSearch = False
        )
        
        if (not searchResult):
            print "Host Not found"
            sys.exit(1)
            
                
        propertySpec = client.factory.create("ns0:PropertySpec")
        propertySpec.pathSet.append("vm")
        propertySpec.all = False
        propertySpec.type = "HostSystem"
        
        objectSpec = client.factory.create("ns0:ObjectSpec")
        objectSpec.obj = searchResult
        
        propertyFilterSpec = client.factory.create("ns0:PropertyFilterSpec")
        propertyFilterSpec.propSet.append(propertySpec)
        propertyFilterSpec.objectSet.append(objectSpec)
        
        vms = client.service.RetrievePropertiesEx(
            serviceContent.propertyCollector,
            [propertyFilterSpec]
        )
        
        for vmRef in vms.objects[0][1][0].val[0]:
            
            propertySpec.type = "VirtualMachine"
            propertySpec.pathSet.pop()
            propertySpec.pathSet.append("name")
            
            objectSpec.obj = vmRef
            
            vmInfo = client.service.RetrievePropertiesEx(
                serviceContent.propertyCollector,
                [propertyFilterSpec]
            )
            
            print vmInfo.objects[0][1][0].val