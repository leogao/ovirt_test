''' vdsm_storage.py:  Module to do vdsm storage domain testing.
    Author: Wei.Gao Email: wei.gao@windriver.com 
    Date : Tue Jul 16 16:37:57 CST 2013

    vdsmStorage ( connection ):
      [ connection is a valid adress or directory ->
          return a new vdsmStorage instance with 
          a serials UUID ]
    .hostID [ the host id ]
    .scsikey [ the scsikey ]
    .masterVersion [the masterVersion ]
    .session [ the session connect to vdsmd ]
    .spUUID  [ the storagePool uuid ]
    .sdUUID  [ the storageDomain uuid ]
    .imgUUID [ the image uuid ]
    .volUUID [ the volume uuid ]
    .connection [ the connection directory ]
    .__connect__(self ):
      [ create a session connect to vdsmd
          return the session ]
    .__vdsOK__(self, op ):
      [ op is a operation ->
          return the operation ]
    .__waitTask__(self, taskid):
      [ taskid marking a task which is running ->
          return the task's running status. ]
    .connectServer(self, fsType, name):
      [ fsType is the domain file system type 
        name is the domain server's name  ->
          return the task's status ]
    .createDomain(self, fsType, name):
      [ fsType is the domain file system type 
        name is the domain server's name  ->
          return the task's status ]
    .createPool(self, fsType, name):
      [ fsType is the domain file system type 
        name is the domain server's name  ->
          return the task's status ]
    .connectPool( self ):
      [ return the task's status ]
    .spmStart( self ):
      [ return the task's status ]
    .createVolume(self, name):
      [ name is the domain server's name  ->
          return the task's status ]
    .printInstanceInfo( self ):
      [ return the vdsmStorage instance informations ]
'''

import os
import sys
import uuid
import time

sys.path.append('/usr/share/vdsm')

from vdsm import vdscli
from storage.sd import NFS_DOMAIN, LOCALFS_DOMAIN, POSIXFS_DOMAIN, DATA_DOMAIN, ISO_DOMAIN, BACKUP_DOMAIN
from storage.volume import COW_FORMAT, SPARSE_VOL, LEAF_VOL, BLANK_UUID

class vdsmStorage:
    """An instance represents a vdsmStorage.
    """
    def __init__ ( self, connection ):
        """Constructor for vdsmStorage.
        """
        #if not os.path.exists(connection):
        if connection == "":
            print "Connection of vdsmStorage Invalid."
            sys.exit(1)
        else:
            self.hostID = 1 
            self.scsikey = "scsikey"
            self.masterVersion = 1 
            self.session = self.__connect__()
            self.spUUID = str(uuid.uuid4())
            self.sdUUID = str(uuid.uuid4())
            self.imgUUID = str(uuid.uuid4())
            self.volUUID = str(uuid.uuid4())
            self.connection = connection

    def __connect__( self ): 
        ''''Connect VDSM, default connect local VDSM'''
        return vdscli.connect() 

    def __vdsOK__( self, op ): 
        '''Judge the operation success or NOT.'''
        print op
        if op['status']['code']: 
            raise Exception(str(op)) 
            return -1            
        return op

    def __waitTask__( self, taskid ): 
        '''Many VDSM tasks are async operated, so each request should be a task, 
           so defined the function to check the task operation success or NOT
        '''
        while self.__vdsOK__(self.session.getTaskStatus(taskid))['taskStatus']['taskState'] != 'finished': 
            time.sleep(3) 
        return self.__vdsOK__(self.session.clearTask(taskid)) 

    def connectServer( self, fsType, name ):
        '''Connect a VDSM StorageServer'''
        if fsType == 'LOCALFS':
            return self.__vdsOK__(self.session.connectStorageServer(LOCALFS_DOMAIN,
                name, [dict(id=1, connection=self.connection)])) 
        elif fsType == 'NFS':
            return self.__vdsOK__(self.session.connectStorageServer(NFS_DOMAIN,
                name, [dict(id=1, connection=self.connection)])) 
        elif fsType == 'POSIXFS':
            return self.__vdsOK__(self.session.connectStorageServer(POSIXFS_DOMAIN,
                name, [dict(id=1, connection=self.connection)])) 
        else:
            print 'Invalid fsType'
            return -1

    def createDomain( self, fsType, name ):
        '''Create Storage Domain sdUUID'''
        if fsType == 'LOCALFS':
            return self.__vdsOK__(self.session.createStorageDomain(LOCALFS_DOMAIN, self.sdUUID, 
                name, self.connection, DATA_DOMAIN, 0)) 
        elif fsType == 'NFS':
            return self.__vdsOK__(self.session.createStorageDomain(NFS_DOMAIN, self.sdUUID, 
                name, self.connection, DATA_DOMAIN, 0)) 
        elif fsType == 'POSIXFS':
            return self.__vdsOK__(self.session.createStorageDomain(POSIXFS_DOMAIN, self.sdUUID, 
                name, self.connection, DATA_DOMAIN, 0)) 
        else:
            print 'Invalid fsType'
            return -1

    def createPool( self, fsType, name ):
        '''Using sdUUID as master domain create Storage Pool'''
        if fsType == 'LOCALFS':
            return self.__vdsOK__(self.session.createStoragePool(LOCALFS_DOMAIN, self.spUUID, 
	        name, self.sdUUID, [self.sdUUID], self.masterVersion)) 
        elif fsType == 'NFS':
            return self.__vdsOK__(self.session.createStoragePool(NFS_DOMAIN, self.spUUID, 
	        name, self.sdUUID, [self.sdUUID], self.masterVersion)) 
        elif fsType == 'POSIXFS':
            return self.__vdsOK__(self.session.createStoragePool(POSIXFS_DOMAIN, self.spUUID, 
	        name, self.sdUUID, [self.sdUUID], self.masterVersion)) 
        else:
            print 'Invalid fsType'
            return -1


    def connectPool( self ):
        '''Connect Storage Pool'''
        return self.__vdsOK__(self.session.connectStoragePool(self.spUUID, self.hostID, 
            self.scsikey, self.sdUUID, self.masterVersion)) 

    def spmStart( self ):
        '''Startup SPM which on Storage Pool, this Node as SPM'''
        tid = self.__vdsOK__(self.session.spmStart(self.spUUID, -1, -1, -1, 0))['uuid'] 
        return self.__waitTask__(tid) 

    def createVolume( self, name ):
        '''Create Volume, size is 10GB, the volume is on the created Storage Domain 
           OK, we can create VM using the volume UUID.
        '''
        sizeGiB = 10 
        sectors_per_GB = 2097152 
        size = sizeGiB * sectors_per_GB 
        tid = self.__vdsOK__(self.session.createVolume(self.sdUUID, self.spUUID, self.imgUUID, size, 
                       COW_FORMAT, SPARSE_VOL, LEAF_VOL, 
                       self.volUUID, name, 
                       BLANK_UUID, BLANK_UUID))['uuid'] 
        return self.__waitTask__(tid) 

    def printInstanceInfo( self ):
        '''Return vdsmStorage's spUUID'''
        print "spUUID = %s" % (self.spUUID)
        print "sdUUID = %s" % (self.sdUUID)
        print "imgUUID = %s" % (self.imgUUID)
        print "volUUID = %s" % (self.volUUID)
        print "hostID = %s" % (self.hostID)
        print "scsikey = %s" % (self.scsikey)

def print_summary(summary):
    lenth = len(summary)
    print ' \n' + '#'*10 + summary + '#'*(40-lenth) + ' \n'

def main():
    '''Storage domain test:  A test driver for local storage domain via the vdsmStorage module.'''

    failCount = 0
    fsType = sys.argv[1]
    coPath = sys.argv[2]
    conName = 'connect_server_%s' % fsType
    creName = 'create_domain_%s' % fsType
    pooName = 'create_pool_%s' % fsType
    volName = 'create_pool_%s' % fsType

    print_summary('New a vdsmStorage instance')
    instan = vdsmStorage(coPath)

    instan.printInstanceInfo()

    print_summary('Connect Storage Server')
    if instan.connectServer(fsType, conName) == -1:
        failCount += 1
        print 'Connect Storage Server failed \n'

    print_summary('Create Storage Domain')
    if instan.createDomain(fsType, creName) == -1:
        failCount += 1
        print 'Create Storage Domain failed \n'

    print_summary('Create Storage Pool')
    if instan.createPool(fsType, pooName) == -1:
        failCount += 1
        print 'Create Storage Pool failed \n'

    print_summary('Connect Storage Pool')
    if instan.connectPool() == -1:
        failCount += 1
        print 'Connect Storage Pool failed \n'

    print_summary('spm Start')
    if instan.spmStart() == -1:
        failCount += 1
        print 'spm Start failed \n'

    print_summary('Create Volume')
    if instan.createVolume(volName) == -1:
        failCount += 1
        print 'Create Volume failed \n'

    sys.exit(failCount)

if __name__ == "__main__":
    main()
