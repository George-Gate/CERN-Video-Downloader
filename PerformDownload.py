import urllib.request
import os

'''if set smallFileMode to True, the program will use simpleDownload method, which may be faster for many small files but do not support break point resume.''' 
smallFileMode=False


def showProgress(blockNum, blockSize, totalSize):
    '''Called by urllib.request.urlretrieve
return the progress of downloading'''
    # display download progress
    if blockNum*blockSize>=totalSize : 
        print ('\rDownload Finished!(%.2f'%round(blockNum*blockSize/2**20,2)
                ,'/','%.2f MB)'%round(totalSize/2**20,2))
    else:
        if totalSize!=-1 :
            print ('\r','%.2f'%round(blockNum*blockSize/2**20,2),
                   '/','%.2f'%round(totalSize/2**20,2),
                   'MB    ','%.2f'%round(blockNum*blockSize/totalSize*100,2),'%',end='')
        else:
            print ('\r','%.2f'%round(blockNum*blockSize/2**20,2),
                    'MB Downloaded.',end='')
# end {showProgress}

def recordToFile(record,msg):
    '''Record msg to file, using binary mode'''
    if len(msg.encode())>50:
        while len(msg.encode())>47:
            msg=msg[0:-int((len(msg.encode())-47)/2)-1]
        msg=msg+'...'
    written=record.write( '{: <50}'.format(msg).encode() )
    record.seek(-written,1)
# end {recordToFile}

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

def download(url, filename):
    ''' Download url to filename, support break point resume. '''
    import errno
    import socket
    import time
    import configparser
    
    # get url info
    urlHandler = urllib.request.urlopen( url,timeout=10 )
    headers = urlHandler.info()
    size = int(headers.get('Content-Length'))
    lastmodified=headers.get('Last-Modified')
    
    # access download info file
    infoname=filename+'.lock'
    info=configparser.ConfigParser()
    if os.path.exists(infoname):
        info.read(infoname)
        try:
            if (info.get('FileInfo','size')!=str(size) or
                    info.get('FileInfo','url')!=str(url)  or
                    info.get('FileInfo','lastmodified')!=str(lastmodified)):
                info.remove_section('FileInfo')
                print('File changed, restart download.')
        except:
            info.remove_section('FileInfo')
            print('.lock file damaged, restart download.')
    # end if
    
    # decide whether to resume or restart
    if not info.has_section('FileInfo'):
        info.add_section('FileInfo')
        info.set('FileInfo','size',str(size))
        info.set('FileInfo','url',str(url))
        info.set('FileInfo','lastmodified',str(lastmodified))
        with open(infoname,'w') as f:
            info.write(f)
        # delete existing file
        open(filename,'wb').close()
    
    # rebuild start point
    try:
        downloaded = os.path.getsize(filename )
    except OSError:
        downloaded = 0
    startpoint = downloaded
    
    # start download
    connectionError=True
    resetCounter=0
    while connectionError and resetCounter<10:
        connectionError=False
        try:
            if startpoint < size:
                oneTimeSize = 65535 #64KB/time
                
                urlHandler = urllib.request.Request(url)
                urlHandler.add_header("Range", "bytes=%d-%d" % (startpoint, size))
                urlHandler = urllib.request.urlopen(urlHandler,timeout=10)
                
                data = urlHandler.read( oneTimeSize )
                with open( filename, 'ab+' ) as filehandle:
                    while data:
                        filehandle.write( data )
                        downloaded += len( data )
                        showProgress(1, downloaded, size)
                        data = urlHandler.read( oneTimeSize )
            # end if
        except urllib.error.HTTPError as errinfo:
            # HTTP Error
            if errinfo.code==errno.ECONNRESET:
                # Connection reset by peer, connect again
                connectionError=True
                resetCounter+=1
            else:
                raise
        except urllib.error.URLError as errinfo:
            # URL Error
            if (isinstance(errinfo.reason,socket.gaierror) and
                  errinfo.reason.errno==-2):
                # Name or service not known, usually caused by internet break or wrong server address
                connectionError=True
                resetCounter+=1
                time.sleep(10)
            else:
                raise
        except socket.timeout:
            # request timeout
            connectionError=True
            resetCounter+=1
        # end try
    # end while
          
    # if resetCounter>10 and there is a connectionError then raise it
    if connectionError:
        raise Exception('Connection Error')
          
    # check if download finished successfully
    try:
        downloaded = os.path.getsize(filename )
    except OSError:
        downloaded = 0
    
    if downloaded==size:
        # remove info file
        os.remove(infoname) 
        return 'Success'
    elif downloaded>size:
        os.remove(infoname)
        return 'The size of file downloaded is bigger than that on server.'
    else:
        return ('Download Not Finished! The size of file downloaded is smaller than that on server.'
                 ' If this error continues, please try delete the file downloaded.')
#end {def download}
                    
def simpleDownload(url, filename):
    '''Simple download method, do not suppot break point resume, but may be faster for small files'''
    urllib.request.urlretrieve(url, filename, showProgress)
    return 'Success'
# end {def simpleDownload}


#-----------------------------------------------------------------------------------------------------------------
# main procedure start from here

# get current working directory
                                #currentPath=os.path.dirname(performDownload)
                                #os.chdir(str(currentPath))
currentPath=os.getcwd()

# read download info from 'downloadList.csv'
with open('downloadList.csv') as f:
    downloadlist=f.readlines()
    
onError=False   # error flag

# open 'downloadList.csv' for status maintenance
with open('downloadList.csv','rb+') as record:
    for item in downloadlist:
        if item=='\n': continue
        # parse item
        status, localname, url = item[:-1].split(';')
        status = status.strip(' ').upper()
        # check status for downloading
        if status in {'QUEUED','PAUSED',''}:
            # record status
            recordToFile(record,'Downloading')
            
            # start download
            print ('Begin to download',url)
            print ('Save to:',localname)
            checkDir(currentPath+localname[1:])  # check if parent dir exists
            try:
                if smallFileMode:
                    result=simpleDownload(url,
                                          currentPath+localname[1:])
                else:
                    result=download(url,
                                    currentPath+localname[1:])
                # if download not success, raise exception
                if result!='Success':
                    raise Exception(result)

            except urllib.error.HTTPError as errinfo:
                # 404 Not Found
                print ('\r'+str(errinfo))
                recordToFile(record,str(errinfo))
            except KeyboardInterrupt as errinfo:
                # Ctrl+C Interrupt
                print ('\rDownload Abort!'+20*' ')
                if smallFileMode:
                    # reset status to 'Queued' since smallFileMode don't support break point resume
                    recordToFile(record,'Queued')
                else:
                    # set status to 'Paused'
                    recordToFile(record,'Paused')
                onError=True
                break
            except Exception as errinfo:
                # Other exceptions
                print ('\rUnexpected Error!('+str(errinfo)+')')
                recordToFile(record,str(errinfo))
            except:
                # Unexpected exceptions
                print ('\rUnexpected Error!'+20*' ')
                recordToFile(record,'Unexpected Error')
            else:
                # Download success, write 'Downloaded' to file
                recordToFile(record,'Downloaded')
            
            print ()   # output new line for good layout
        # if status is 'Unexpected Error', 'Downloaded' or 'Downloading' etc. then skip
        elif status in {'UNEXPECTED ERROR','DOWNLOADED','DOWNLOADING'}:
            pass
        else:
            print ('Unexpected status:',status,'(Download skipped).')
        # end {if status...}
        
        record.seek(len(item.encode())+1,1)  # seek to next item
    # end {for item}

# end {with open ... as record}

if not onError:
    print ('Download List Finished!')


