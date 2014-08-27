import urllib.request
import os
import configparser

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
    # get url info
    urlHandler = urllib.request.urlopen( url )
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
    if startpoint < size:
        oneTimeSize = 65535 #64KB/time
        
        urlHandler = urllib.request.Request(url)
        urlHandler.add_header("Range", "bytes=%d-%d" % (startpoint, size))
        urlHandler = urllib.request.urlopen(urlHandler)

        data = urlHandler.read( oneTimeSize )
        with open( filename, 'ab+' ) as filehandle:
            while data:
                filehandle.write( data )
                downloaded += len( data )
                showProgress(1, downloaded, size)
                data = urlHandler.read( oneTimeSize )
    # end if      
    
    # remove info file
    os.remove(infoname) 
    
    return 'Success'
#end {def download}                    
                    
def simpleDownload(url, filename):
    '''Simple download method, do not suppot break point resume, but may be faster for small files'''
    urllib.request.urlretrieve(url, filename, showProgress)
    
# end {def simpleDownload}

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
                    simpleDownload(url,
                                   currentPath+localname[1:])
                else:
                    download(url,
                             currentPath+localname[1:])
            # Exception handling
            except urllib.error.HTTPError as errinfo:
                print ('\r'+str(errinfo))
                # write errinfo to file
                recordToFile(record,str(errinfo))
            except KeyboardInterrupt as errinfo:
                print ('\rDownload Abort!'+20*' ')
                if smallFileMode:
                    # reset status to 'Queued'
                    recordToFile(record,'Queued')
                else:
                    # set status to 'Paused'
                    recordToFile(record,'Paused')
                onError=True
                break
            except Exception as errinfo:
                print ('\rUnexpected Error!('+str(errinfo)+')')
                # write errinfo to file
                recordToFile(record,str(errinfo))
            except:
                print ('\rUnexpected Error!'+20*' ')
                # write 'Unexpected Error' to file
                recordToFile(record,'Unexpected Error')
            else:
                # download success, write 'Downloaded' to file
                recordToFile(record,'Downloaded')
            
            print ()   # output new line for good layout
        # if status is 'Unexpected Error', 'Downloaded' or 'Downloading' etc. then skip
        elif status in {'UNEXPECTED ERROR','DOWNLOADED','DOWNLOADING','404 NOT FOUND'}:
            pass
        else:
            print ('Unexpected status:',status,'(Download skipped).')
        # end {if status...}
        
        record.seek(len(item.encode())+1,1)  # seek to next item
    # end {for item}

# end {with open ... as record}

if not onError:
    print ('Download List Finished!')


