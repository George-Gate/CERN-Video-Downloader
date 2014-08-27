'''
Created on 2011-11-10
Modified on 2014-08-08 by George-Gate

@author: PaulWang
@improver: George-Gate

Description:
'''

'''It is a multi-thread downloading tool

    It was developed follow axel.
        Author: volans
        E-mail: volansw [at] gmail.com
'''

import sys
import os
import time
import urllib.request
from threading import Thread
import signal

#===============================================================================
# def download(url, output, threadNum=6, proxies=local_proxies)
# output:输出文件的全路径，不带路径帽默认在本文件夹中生成
# threadNum:开几个线程
# proxies:代理地址
#===============================================================================

local_proxies = {'http': 'http://131.139.58.200:8080'}#代理地址

class AxelPython(Thread, urllib.request.FancyURLopener):
    '''Multi-thread downloading class.

        run() is a vitural method of Thread.
    '''
    def __init__(self, threadname, url, filename, ranges=0, proxies={}):
        Thread.__init__(self, name=threadname)
        urllib.request.FancyURLopener.__init__(self, proxies)
        self.name = threadname
        self.url = url
        self.filename = filename
        self.ranges = ranges
        self.downloaded = 0
        self.downloadSpeed = 0 
        self.stopFlag = False
        self.returnMsg = ''

    def set_stopFlag(self):
        self.stopFlag=True

    def download(self):
        '''perform download'''
        self.oneTimeSize = 65535 # 64 KB/time for initial value
        #blockLimit = 2**20     # Maximum value for self.oneTimeSize
        
        self.addheader("Range", "bytes=%d-%d" % (self.startpoint, self.ranges[1]))

        self.urlhandle = self.open( self.url )

        with open( self.filename, 'ab+' ) as filehandle:
            data=1
            while data:
                self.timeStamp=time.perf_counter()
                data = self.urlhandle.read( self.oneTimeSize )
                filehandle.write( data )
                self.downloaded += len( data )
                
                diffTime = time.perf_counter()-self.timeStamp
                #print(diffTime,self.oneTimeSize/2**10,'KB',round(self.downloadSpeed/(2**10)),'KB/s')
                
                self.downloadSpeed = len( data ) / diffTime
                '''
                # adjust oneTimeSize
                if diffTime < 0.1:
                    self.oneTimeSize += round(min(blockLimit/200,self.oneTimeSize*0.01/diffTime))
                elif diffTime > 1:
                    self.oneTimeSize = round(self.oneTimeSize*0.01/diffTime)
                    
                if self.oneTimeSize > blockLimit:
                    self.oneTimeSize = blockLimit
                '''
                if self.stopFlag:
                    self.returnMsg='Download Interrupted.'
                    return
                    
    # end {def download}

    def run(self):
        '''vertual function in Thread'''
        while not self.stopFlag:
            try:
                self.downloaded = os.path.getsize( self.filename )
            except OSError:
                #print 'never downloaded'
                self.downloaded = 0

            # rebuild start point
            self.startpoint = self.ranges[0] + self.downloaded

            # This part is completed
            if self.startpoint >= self.ranges[1]:
                #print ('Part %s has been downloaded over.' % self.filename)
                self.stopFlag = True
                self.returnMsg =  'Download Finished.'
            else:
                self.download()
        # end while
        return self.returnMsg
    # end {def run}
    
# end {class AxelPython}

def GetUrlFileSize(url, proxies={}):
    urlHandler = urllib.request.urlopen( url )
    headers = urlHandler.info()

    length = int(headers.get('Content-Length'))
    #print('Content-Length is %.2f MB' % (length/2**20),'(%d)' % length)
    return length

def SpliteBlocks(totalSize, blockNum):
    blockSize = int(totalSize/blockNum)
    ranges = []
    for i in range(0, blockNum-1):
        ranges.append((i*blockSize, i*blockSize +blockSize - 1))
    ranges.append(( blockSize*(blockNum-1), totalSize -1 ))

    return ranges
    
def islive(tasks):
    for task in tasks:
        if task.isAlive():
            return True
    return False

def checkDir(filename):
    '''To check whether the parent of filename exists. If not, create it.
filename should be a string'''
    from pathlib import Path
    p=Path(filename)
    try:
        if not p.parent.exists():
            p.parent.mkdir(parents=True)
    except:
        print ('Error occurred when creating Directory:',str(p.parent))
# end {checkDir}

def download(url, output, threadNum=6, proxies=local_proxies):
    ''' paxel
    '''
    size = GetUrlFileSize( url, proxies )
    ranges = SpliteBlocks( size, threadNum )
    
    threadname = [ "thread_%d" % i for i in range(0, threadNum) ]
    filename = [ output+".part%d" % i for i in range(0, threadNum) ]

    #create output files
    checkDir(output)
    try:
        open(output,'wb').close()
    except:
         return 'File Occupied.'

    try:
        # start download in threads
        print('Start to download with %d threads.'%threadNum)
        tasks = []
        for i in range(0,threadNum):
            task = AxelPython( threadname[i], url, filename[i], ranges[i] )
            task.setDaemon( True )
            task.start()
            tasks.append( task )

        # display download progress
        while islive(tasks):
            downloaded = sum( [task.downloaded for task in tasks] )
            print ('\r','%.2f'%round(downloaded/2**20,2),
                       '/','%.2f'%round(size/2**20,2),
                       'MB    ','%.2f'%round(downloaded/size*100,2),'%',end='')
            print ('     %.0f KB/s              '%round(sum( [task.downloadSpeed for task in tasks] )/(2**10),0),end='')
            time.sleep( 0.1 )
    except KeyboardInterrupt:
        for task in tasks:
            task.set_stopFlag()
        print('\nWaitting for threads to stop...')
        while islive(tasks):
            time.sleep(0.1)
        return 'KeyboardInterrupt'
    # end try
    
    # link files
    print ('\rLinking...'+20*' ',end='')
    with open( output, 'wb+' ) as filehandle:
        for i in filename:
            f = open( i, 'rb' )
            filehandle.write( f.read() )
            f.close()
            try:
                os.remove(i)
            except:
                pass
    
    print ('\rDownload Finished!'+20*' ')

    return 'Success'
# end {def download}


url = "https://mediastream.cern.ch/MediaArchive/Video/Public/WebLectures/2014/317007/317007_desktop_camera_1080p_4000.mp4"
output = os.getcwd()+'/13/desktop_camera_1080p.mp4'

if __name__ == '__main__':
    print(download( url, output, proxies={} ))

