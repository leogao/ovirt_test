#!/usr/bin/python
#!/usr/bin/env python
#
# Copyright 2013 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#
# author: Wei Gao
# history: created on Dec 27, 2013
# 

import sys
import time
from ovirtsdk.api import API
from ovirtsdk.xml import params

class ovirt_test( object ):
    """An instance represents ovirt test.
    """
    def __init__ ( self, test_dict = {} ):
        '''Constructor for ovirt_test.
        self.ovirt_dict = {}
        self.ovirt_dict['URL'] = url
        self.ovirt_dict['VERSION'] = params.Version(major='3', minor='0')
        self.ovirt_dict['CA_FILE'] = "/etc/pki/ovirt-engine/ca.pem"
        self.ovirt_dict['USERINFO'] = {}
        self.ovirt_dict['USERINFO']['NAME'] = 'admin@internal'
        self.ovirt_dict['USERINFO']['PASSWORD'] = 'admin' 

        self.ovirt_dict['DATACENTERS'] = [(name,type,cluster,storage,network),(name,...), ...] 
        network = [(name,type),(name, ...), ...]
        storage = [(name,type,addr,path),(name, ...), ...]
        cluster = [(name,type,hosts,vms,volumes),(name, ...), ...]
        hosts   = [(name,address),(name, ...), ...]
        volumes = [(name,type),(name, ...), ...]
        vms     = [(name,type,ostype,display,nics,disks),(name, ...), ...]
        nics    = [(name,type,network),(name, ...), ...]
        disks   = [(name,type,size,storage),(name, ...), ...] '''

        global iCLUSTERS
        global iSTORAGES
        global iHOSTS
        iCLUSTERS = 2
        iSTORAGES = 3
        iHOSTS = 2

        self.ovirt_dict = {}
        self.ovirt_dict['URL'] = test_dict['URL']
        self.ovirt_dict['VERSION'] = test_dict['VERSION']
        self.ovirt_dict['CA_FILE'] = test_dict['CA_FILE']
        self.ovirt_dict['USERINFOS'] = []
        self.ovirt_dict['USERINFOS'].append(test_dict['USERINFOS'][0])
        self.ovirt_dict['CONNECTION'] = False
        self.ovirt_dict['DATACENTERS'] = []
        self.ovirt_dict['CLUSTERS'] = []
        self.ovirt_dict['HOSTS'] = []
        self.ovirt_dict['STORAGES'] = []
        self.ovirt_dict['VMS'] = []
        self.ovirt_dict['NICS'] = []
        self.ovirt_dict['DISKS'] = []

    def connect_engine( self ): 
        '''Connect ovirt-engine, default connect local ovirt-engine
        api = API(url="https://128.224.165.209:443/api", \
                username="admin@internal", \
                password="123456", \
                ca_file="/etc/pki/ovirt-engine/ca.pem")
        '''
        try:
            self.api = API(url=self.ovirt_dict['URL'],
                       username=self.ovirt_dict['USERINFOS'][0][0],
                       password=self.ovirt_dict['USERINFOS'][0][1],
                       ca_file=self.ovirt_dict['CA_FILE'])
            print 'Connect ovirt-engine successfully'
            self.ovirt_dict['CONNECTION'] = True
        except Exception as e:
            print 'Connect ovirt-engine failed:\n%s' % (str(e))
            self.ovirt_dict['CONNECTION'] = False
            return False

    def disconnect( self ): 
        '''Disconnect ovirt-engine'''
        try:
            if self.api.disconnect() == None:
                print 'Disconnect ovirt-engine successfully'
                self.ovirt_dict['CONNECTION'] = False
        except Exception as e:
            print 'Disconnect ovirt-engine failed:\n%s' % (str(e))
            self.ovirt_dict['CONNECTION'] = 1
            return False

    def check_item( self, group , item_name, Other = 'None' ): 
        '''Check the item(item_name) exist in group'''
        try:
            index = 0
            length = len(group)
            for index in range(0,length):
                if group[index][0] == item_name:
                    if Other != 'None' and group[index][1] == Other:
                        return index
                    return index
            if index + 1 >= length:
                return None
        except Exception as e:
            print 'Check %s failed:\n%s' % (item_name,str(e))
            return None

    def add_user( self, UserInfo = ('admin@internal','admin') ): 
        '''add a new user'''
        try:
            self.ovirt_dict['USERINFOS'].append(UserInfo)
        except Exception as e:
            print 'Add new user failed:\n%s' % (str(e))
            return False

    def change_user( self, UserInfo = ('admin@internal','admin') ): 
        '''change username and password'''
        try:
            length = len(self.ovirt_dict['USERINFOS'])
            for i in range(0,length):
                if self.ovirt_dict['USERINFOS'][i][0] == UserInfo[0]:
                    tempUser = self.ovirt_dict['USERINFOS'][i]
                    self.ovirt_dict['USERINFOS'].remove(tempUser)
                    self.ovirt_dict['USERINFOS'].insert(i,UserInfo)
                    Found = 1
                    break
                else:
                    Found = 0
            if Found == 0:
                print 'Change user information failed'
                return False
        except Exception as e:
            print 'Change user information failed:\n%s' % (str(e))
            return False

    def printInstanceInfo( self ): 
        ''''change username and password'''
        print self.ovirt_dict

    def print_summary(self, summary):
        lenth = len(summary)
        print ' \n' + '#'*10 + ' ' + summary + ' ' + '#'*(40-lenth) + ' \n'
    
class data_center( ovirt_test ):
    """An instance for data-center inherit ovirt_test.
    """
    def __init__ ( self, test_dict ):
        '''Constructor for data-center.'''
        super(data_center, self).__init__(test_dict)

    def __keepdc__( self, DC_Name ):
        '''clean data center for append new one or delete it'''
        index = self.check_item(self.ovirt_dict['DATACENTERS'], DC_Name)
        if index != None:
            Center = self.ovirt_dict['DATACENTERS'][index]
            self.ovirt_dict['DATACENTERS'].remove(Center)

    def new_data_center( self, DC_Name, DC_Type ):
        ''''create data center (NFS/LOCAL/iSCSi/POSIXFS/GLUSTERFS)'''
        try:
            '''[(name,type,cluster,storage,network),()]'''
            dccenter = (DC_Name,DC_Type,[],[],[])
            if self.api.datacenters.get(DC_Name) != None:
                print 'Data Center (%s) already exist' % DC_Name
                return True
            if self.api.datacenters.add(params.DataCenter(name=DC_Name, 
                                       storage_type=DC_Type, 
                                       version=self.ovirt_dict['VERSION'])):
                print 'Data Center (%s) was created successfully' % DC_Name
        except Exception as e:
            print 'Failed to create Data Center (%s):\n%s' % (DC_Name,str(e))
            return False

        self.__keepdc__(DC_Name)
        self.ovirt_dict['DATACENTERS'].append(dccenter)

    def delete_data_center( self, DC_Name ):
        ''''delete data center (NFS/LOCAL/iSCSi/POSIXFS/GLUSTERFS)'''
        try:
            if self.api.datacenters.get(DC_Name):
                if self.api.datacenters.get(DC_Name).update():
                    print 'Data Center (%s) was update successfully' % DC_Name
                if self.api.datacenters.get(DC_Name).delete(params.Action(force=1)) == '':
                    print 'Data Center (%s) was delete successfully' % DC_Name
        except Exception as e:
            print 'Failed to Delete Data Center (%s):\n%s' % (DC_Name,str(e))
            return False

        self.__keepdc__(DC_Name)

class cluster( data_center ):
    """An instance for cluster inherit data_center.
    """
    def __init__ ( self, test_dict ):
        '''Constructor for cluster.'''
        super(cluster, self).__init__(test_dict)

    def __keepc__( self, CL_Name, DC_Name ):
        '''clean cluster for append new cluster or delete data-center '''
        idc = self.check_item(self.ovirt_dict['DATACENTERS'], DC_Name)
        if idc != None:
            Clusters = self.ovirt_dict['DATACENTERS'][idc][iCLUSTERS]
            index = self.check_item(Clusters, CL_Name)
            if index != None:
                Clusters.remove(Clusters[index])
        return Clusters

    def new_cluster( self, CL_Name, CPU_Type, DC_Name ):
        '''create cluster according to host's CPU.
        CPU_TYPE = 'Intel Nehalem Family'
        CPU_TYPE = 'Intel Conroe Family'
        CPU_TYPE = 'Intel Penryn Family'
        CPU_TYPE = 'Intel Westmere Family'
        CPU_TYPE = 'Intel SandyBridge Family'
        CPU_TYPE = 'Intel Haswell' '''

        try:
            ''' 
            cluster = [(name,type,hosts,vms,volumes),(name, ...), ...]
            data_center = [(name,type,cluster,storage,network),(name,...), ...] '''
            ccluster = (CL_Name,CPU_Type,[],[],[])
            if self.api.clusters.get(CL_Name) != None:
                print 'Cluster (%s) already exist' % CL_Name
                return True
            if self.api.clusters.add(params.Cluster(name=CL_Name, 
                                   cpu=params.CPU(id=CPU_Type), 
                                   data_center=self.api.datacenters.get(DC_Name), 
                                   version=self.ovirt_dict['VERSION'])):
                print 'Cluster (%s) was created successfully' % CL_Name
        except Exception as e:
            print 'Failed to create Cluster (%s):\n%s' % (CL_Name, str(e))
            return False

        Clusters = self.__keepc__(CL_Name,DC_Name)
        Clusters.append(ccluster)


    def delete_cluster( self, CL_Name, CPU_Type, DC_Name ):
        '''delete cluster according to host's CPU.'''
        try:
            if self.api.clusters.get(CL_Name):
                if self.api.clusters.get(CL_Name).update():
                    print 'Cluster (%s) was updated successfully' % CL_Name
                if self.api.clusters.get(CL_Name).delete() == '':
                    print 'Cluster (%s) was deleted successfully' % CL_Name
        except Exception as e:
            print 'Failed to delete Cluster (%s):\n%s' % (CL_Name, str(e))
            return False

        self.__keepc__(CL_Name,DC_Name)

    def get_data_center( self, CL_Name):
        '''get data_center name via cluster name.'''
        try:
            length = len(self.api.datacenters.list())
            for i in range(0,length):
                if self.api.clusters.get(CL_Name).get_data_center().id == self.api.datacenters.list()[i].id:
                    dc_name = self.api.datacenters.list()[i].name
                    print 'Got dc_name via cluster (%s) successfully' % CL_Name
                    return dc_name
            if i + 1 >= length:
                print 'Got dc_name via cluster (%s) failed' % CL_Name
                return None
        except Exception as e:
            print 'Failed to got dc_name via cluster (%s):\n%s' % (CL_Name, str(e))
            return None

class host( cluster ):
    """An instance for host class inherit cluster.
    """
    def __init__ ( self, test_dict ):
        '''Constructor for host.'''
        super(host, self).__init__(test_dict)
        self.ovirt_dict['HOSTS'] = test_dict['HOSTS']

    def __waith__( self, HS_Name, State ):
        '''Wait VM status.state'''
        loop_c = 0
        while self.api.hosts.get(HS_Name).status.state != State:
            time.sleep(1)
            loop_c += 1
            if loop_c > 600 : 
                print "Host reach %s status failed" % (State)
                break
        if loop_c < 600 : 
            print "Host reach %s status OK" % (State)

    def __keeph__( self, HS_Name, CL_Name ):
        dc_name = self.get_data_center(CL_Name)
        if dc_name == None:
            return False
        idc     = self.check_item(self.ovirt_dict['DATACENTERS'],dc_name)
        if idc != None:
            Clusters = self.ovirt_dict['DATACENTERS'][idc][iCLUSTERS]
            icl = self.check_item(Clusters, CL_Name)
            if icl != None:
                Hosts = Clusters[icl][iHOSTS]
                ihs = self.check_item(Hosts, HS_Name)
                if ihs != None:
                    tmpHost = Hosts[ihs]
                    Hosts.remove(tmpHost)
                return Hosts
            return None
        return None

    def new_host( self, HS_Name, Address, CL_Name, RPassword = 'root' ):
        '''install host: 
        Address      = 'hostname.my.domain.com'
        RPassword    = 'root_password' '''
        try:
            ''' 
            hosts   = [(name,address),(name, ...), ...]
            cluster = [(name,type,hosts,vms,volumes),(name, ...), ...]
            data_center = [(name,type,cluster,storage,network),(name,...), ...] '''
            hhost = (HS_Name,Address)
            if self.api.hosts.get(HS_Name) != None:
                print 'Host(%s) already exist' % HS_Name
                return True
            if self.api.hosts.add(params.Host(name=HS_Name, 
                                 address=Address, 
                                 cluster=self.api.clusters.get(CL_Name),
                                 root_password=RPassword)):
                    print 'Host was installed successfully'
                    print 'Waiting for host to reach the Up status'
                    self.__waith__(HS_Name,'up')
        except Exception as e:
            print 'Failed to install Host (%s):\n%s' % (HS_Name, str(e))
            return False

        Hosts = self.__keeph__(HS_Name,CL_Name)
        Hosts.append(hhost)


    def delete_host( self, HS_Name, Address, CL_Name, RPassword = 'root' ):
        '''delete host'''
        try:
            if self.api.hosts.get(HS_Name):
                print 'Get host object ok'
                if self.api.hosts.get(HS_Name).update():
                    print 'Update the host ok'
                    if self.api.hosts.get(HS_Name).deactivate():
                        self.__waith__(HS_Name,'maintenance')
                        print 'Deactivate the host ok'
                        if self.api.hosts.get(HS_Name).delete() == '':
                            print 'Delete the host and waiting for it finished'
                            loop_c = 0
                            while self.api.hosts.get(HS_Name) != None:
                                time.sleep(1)
                                loop_c += 1
                                if loop_c > 600 : 
                                    print "Host delete failed"
                                    break
                            if loop_c < 600 : 
                                print "Host is deleted"
        except Exception as e:
            print 'Failed to delete Host (%s):\n%s' % (HS_Name, str(e))
            return False

        self.__keeph__(HS_Name,CL_Name)

class domain_storage( host ):
    """An instance for storage domain inherit host to got data-center info.
    """
    def __init__ ( self, test_dict ):
        '''Constructor for host.'''
        super(host, self).__init__(test_dict)

    def __waitd__( self, D_Name, State, DC_Name = None ):
        '''Wait Storage Domain status.state'''
        loop_c = 0
        if DC_Name == None:
            domain = self.api.storagedomains.get(D_Name)
        else:
            domain = self.api.datacenters.get(DC_Name).storagedomains.get(D_Name)
        while domain.status.state != State:
            time.sleep(1)
            loop_c += 1
            if loop_c > 600 : 
                print "Domain(%s) reach %s status failed" % (D_Name,State)
                break
        if loop_c < 600 : 
            print "Domain(%s) reach %s status OK" % (D_Name,State)

    def __keepd__( self, DC_Name, D_Name ):
        '''clean cluster for append new cluster or delete data-center '''
        idc = self.check_item(self.ovirt_dict['DATACENTERS'], DC_Name)
        if idc != None:
            Storages = self.ovirt_dict['DATACENTERS'][idc][iSTORAGES]
            index = self.check_item(Storages, D_Name)
            if index != None:
                Storages.remove(Storages[index])
        return Storages

    def get_up_host( self, DC_Name ):
        ''' Get the up host in data-center via DC_Name '''
        clusters = self.api.clusters.list()
        clength = len(clusters)
        for i in range(0, clength):
            hosts    = self.api.hosts.list()
            hlength  = len(hosts)
            for j in range(0, hlength):
                if clusters[i].id == hosts[j].get_cluster().id and hosts[j].status.state == 'up':
                    if clusters[i].get_data_center().id == self.api.datacenters.get(DC_Name).id:
                        hs_name = hosts[j].name
                        return hs_name
        if i + 1 >= clength:
            print 'Failed to get up host in datacenter(%s)' % (DC_Name)
            return None

    def new_storage_domain( self, D_Name, D_Type, EX_Address, EX_Path, DC_Name ):
        '''create storage domain: 
           STORAGE_ADDRESS = 'storage_server.my.domain.com'
           TARGET_NAME = 'target_name'
           LUN_GUID = 'lun_guid' 
           HS_Name just attached iscsi disk'''

        LUN_GUID = 'lun_guid'
        TARGET_NAME = 'target_name'
        Format = 'v2'
        try:
            ''' 
            storage = [(name,type,addr,path),(name, ...), ...]
            data_center = [(name,type,cluster,storages,network),(name,...), ...] '''
            storageDomain = (D_Name,D_Type,EX_Address,EX_Path)
            if self.api.storagedomains.get(D_Name) != None:
                print 'Storage Domain(%s) already exist' % D_Name
                return True
            st_type = self.api.datacenters.get(DC_Name).get_storage_type()
            hs_name = self.get_up_host(DC_Name)
            if hs_name == None:
                return False
            if st_type == 'iscsi':
                Params_storage = params.Storage(type_=st_type, 
                    volume_group=params.VolumeGroup(logical_unit=[params.LogicalUnit(id=LUN_GUID,
                    address=ST_Address,
                    port=3260,
                    target=TARGET_NAME)]))
                sdParams = params.StorageDomain(name=D_Name,
                                        data_center=self.api.datacenters.get(DC_Name),
                                        storage_format='v2',
                                        type_=D_Type,
                                        host=self.api.hosts.get(hs_name),
                                        storage = Params_storage)
            else: 
                Params_storage = params.Storage(type_=st_type, 
                                                address=EX_Address, 
                                                path=EX_Path)
                sdParams = params.StorageDomain(name=D_Name,
                                 data_center=self.api.datacenters.get(DC_Name),
                                 type_=D_Type,
                                 host=self.api.hosts.get(hs_name),
                                 storage = Params_storage)

            if self.api.storagedomains.add(sdParams):
               print '%s Storage Domain was created successfully'  % (D_Type)
        except Exception as e:
            print 'Failed to create %s Storage Domain\n%s' % (D_Type, str(e))
            return False

        try:
            if self.api.datacenters.get(name=DC_Name).storagedomains.add(self.api.storagedomains.get(D_Name)):
                print '%s Storage Domain was attached successfully' % (D_Type)
        except Exception as e:
            print 'Failed to attach %s Domain:\n%s' % (D_Type, str(e))
            return False

        if st_type != 'iscsi':
            try:
                if self.api.datacenters.get(DC_Name).storagedomains.get(D_Name).status.state != 'active':
                    self.__waitd__(D_Name, 'maintenance', DC_Name)
                    if self.api.datacenters.get(DC_Name).storagedomains.get(D_Name).activate():
                        self.__waitd__(D_Name, 'active', DC_Name)
                print '%s Domain was activated successfully' % (D_Type)
            except Exception as e:
                print 'Failed to add %s domain\n%s' % (D_Type, str(e))
                return False

        Storages = self.__keepd__(DC_Name, D_Name)
        Storages.append(storageDomain)

    def delete_storage_domain( self, DC_Name, D_Name ):
        '''delete storage domain: 
           LUN_GUID = 'lun_guid' '''
        try:
            st_type = self.api.datacenters.get(DC_Name).get_storage_type()
            hs_name = self.get_up_host(DC_Name)
            if st_type != 'iscsi':
                if self.api.datacenters.get(DC_Name).storagedomains.get(D_Name).deactivate():
                    print '%s Domain was deactivated successfully' % (D_Name)
                self.__waitd__(D_Name, 'maintenance', DC_Name)
                if self.api.datacenters.get(DC_Name).storagedomains.get(D_Name).delete() == '':
                    print '%s Domain was dettached successfully' % (D_Name)
                    self.__waitd__(D_Name, 'unattached')
                    storage_domain = params.StorageDomain(host=self.api.hosts.get(hs_name))
                    if self.api.storagedomains.get(D_Name).delete(storage_domain) == '':
                        print 'Delete %s successfully' % (D_Name)
        except Exception as e:
            print 'Failed to delete %s domain\n%s' % (D_Name, str(e))
            return False

        self.__keepd__(DC_Name, D_Name)

    def judge_master_domain( self, D_Name ):
        '''judge master storage domain '''
        try:
            if self.api.storagedomains.get(D_Name).get_master() == False:
                print '%s Domain is NOT a master domain' % (D_Name)
                return False
            return True
        except Exception as e:
            print 'Failed get %s domain(master):\n%s' % (D_Name, str(e))
            return False

class virtualMachine( domain_storage ):
    """An instance for vm inherit ovirt_test.
    """
    def __init__ ( self, test_dict ):
        '''Constructor for virtualMachine.'''
        super(virtualMachine, self).__init__(test_dict)
        self.ovirt_dict['VMS'] = test_dict['VMS']

    def __waitv__( self, VmName, State ):
        '''Wait VM status.state'''
        loop_c = 0
        while self.api.vms.get(VmName).status.state != State:
            time.sleep(1)
            loop_c += 1
            if loop_c > 600 : 
                print "VM reach %s status failed" % (State)
                break
        if loop_c < 600 : 
            print "VM reach %s status OK" % (State)

    def new_vm( self, VmName, VmType, CL_Name, OsType = 'windriver_linux', DisplayType = 'spice' ):
        '''create a vm: 
           VmName = 'VM1' '''

        MB = 1024*1024
        GB = 1024*MB
        try:
            t_os = self.api.templates.get('Blank').get_os()
            t_display = self.api.templates.get('Blank').get_display()
            t_os.set_type(OsType)
            t_display.set_type(DisplayType)

            self.api.vms.add(params.VM(name=VmName, memory=256*MB, 
                             cluster=self.api.clusters.get(CL_Name), 
                             template=self.api.templates.get('Blank'),
                             os=t_os, display=t_display,type_=VmType))
            print 'VM %s created' % (VmName)
            print 'Waiting for VM to reach Down status'
            self.__waitv__(VmName,'down')
        except Exception as e:
            print 'Failed to create VM(%s) \n%s' % (VmName, str(e))
            return False

        if self.check_item('VMS', VmName) == False:
            self.ovirt_dict['VMS'].append((VmName, VmType, OsType, DisplayType, CL_Name))

    def do_add_nic( self, VmName, NicName='eth0', NetName = 'ovirtmgmt'):
        '''add a nic on vm '''
        try:
            self.api.vms.get(VmName).nics.add(params.NIC(name=NicName, 
                                              network=params.Network(name=NetName), 
                                              interface='virtio'))
            loop_c = 0
            while self.api.vms.get(VmName).nics.get(NicName).get_active() != True:
                loop_c += 1
                print "VM's Nic reach up status in loop_c : %d" % loop_c
                if loop_c > 600 : 
                    print "VM's Nic reach up status failed"
                    break
                time.sleep(1)
            if loop_c < 600 : 
                print "VM's Nic reach up status OK"
            print 'NIC added to VM'
        except Exception as e:
            print 'Failed to add nic for VM(%s)%s' % (VmName, str(e))
            return False

        if self.check_item('NICS', NicName, VmName) == False:
            self.ovirt_dict['NICS'].append((NicName,VmName,NetName))

    def do_del_nic( self, VmName, NicName='eth0'):
        '''delete a nic on vm '''
        try:
            if self.api.vms.get(VmName).nics.get(NicName).delete() == '':
                print 'NIC delete ok'
                time.sleep(1)
        except Exception as e:
            print 'Failed to delete nic for VM(%s)%s' % (VmName, str(e))
            return False

        if self.check_item('NICS', NicName, VmName) == True:
            self.ovirt_dict['NICS'].remove((NicName,VmName,NetName))

    def do_add_disk( self, VdName, D_Name, VmName ):
        '''add a nic on vm '''
        MB = 1024*1024
        GB = 1024*MB
        try:
            Params_Domains=params.StorageDomains(storage_domain=[self.api.storagedomains.get(D_Name)])
            self.api.vms.get(VmName).disks.add(params.Disk(storage_domains=Params_Domains,
                                               name=VdName,
                                               size=8*GB,
                                               # type_='system', - disk type is deprecated
                                               status=None,
                                               interface='virtio',
                                               format='raw',
                                               sparse=True,
                                               bootable=True))
            print 'Disk added to VM'
            loop_c = 0
            while self.api.vms.get(VmName).disks.get(VdName).get_active() != True:
                loop_c += 1
                print "VM's vDisk reach up status in loop_c : %d" % loop_c
                if loop_c > 600 : 
                    print "VM's vDisk reach up status failed"
                    break
                time.sleep(1)
            if loop_c < 600 : 
                print "VM's vDisk reach up status OK"
        except Exception as e:
            print 'Failed to add vDisk for VM(%s)%s' % (VmName, str(e))
            return False

        if self.check_item('DISKS', VdName, VmName) == False:
            self.ovirt_dict['DISKS'].append((VdName,VmName,D_Name))

    def do_del_disk( self, VmName, VdName = 'vdisk' ):
        '''delete a disk'''
        try:
            if self.api.vms.get(VmName).disks.get(VdName).delete() == '':
                print 'Vdsik delete ok'
                time.sleep(5)
        except Exception as e:
            print 'Failed to delete disk for VM(%s)%s' % (VmName, str(e))
            return False

        if self.check_item('DISKS', VdName, VmName) == True:
            self.ovirt_dict['DISKS'].remove((VdName,VmName,D_Name))

    def do_start( self, VmName):
        '''do start vm action via api'''
        try:
            if self.api.vms.get(VmName).status.state != 'up':
                print 'Starting VM'
                if self.api.vms.get(VmName).start():
                    print 'Waiting for VM to reach Up status'
                    self.__waitv__(VmName,'up')
                else:
                    print 'VM already up'
        except Exception as e:
            print 'Failed to Start VM(%s):\n%s' % (VmName, str(e))
            return False

    def do_stop( self, VmName):
        '''do stop vm action via api'''
        try:
            if self.api.vms.get(VmName).status.state == 'up':
                print 'Stop VM'
                if self.api.vms.get(VmName).stop():
                    print 'Waiting for VM to reach Down status'
                    self.__waitv__(VmName,'down')
                else:
                    print 'VM already down'
        except Exception as e:
            print 'Failed to Stop VM(%s):\n%s' % (VmName, str(e))
            return False

    def do_migrate( self, VmName):
        '''do migrate vm action via api'''
        try:
            if self.api.vms.get(VmName).status.state == 'up':
                print 'Migrate VM'
                if self.api.vms.get(VmName).migrate():
                    print 'Waiting for VM migrate to another node'
                    self.__waitv__(VmName,'up')
                else:
                    print 'VM already migrated'
        except Exception as e:
            print 'Failed to Migrate VM(%s):\n%s' % (VmName, str(e))
            return False

    def do_delete( self, VmName):
        '''do migrate vm action via api'''
        try:
            if self.api.vms.get(VmName).status.state != 'down':
                if self.api.vms.get(VmName).stop():
                    print 'Waiting for VM to reach Down status'
                    self.__waitv__(VmName,'down')
                print 'Delete VM'
                if self.api.vms.get(VmName).delete() == '':
                    time.sleep(3)
        except Exception as e:
            print 'Failed to Delete VM(%s):\n%s' % (VmName, str(e))
            return False

        print "Delete VM %s OK" % (VmName)
        if self.check_item('VMS', VmName) == True:
            self.ovirt_dict['VMS'].remove((VmName, VmType, OsType, DisplayType, CL_Name))
