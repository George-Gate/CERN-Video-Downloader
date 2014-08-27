import os

def recordToFile(record,msg):
    '''Record msg to file, using binary mode'''
    if len(msg.encode())>50:
        while len(msg.encode())>47:
            msg=msg[0:-int((len(msg.encode())-47)/2)-1]
        msg=msg+'...'
    written=record.write( '{: <50}'.format(msg).encode() )
    record.seek(-written,1)
# end {recordToFile}

# get current working directory
                        # currentPath=os.path.dirname(performDownload)
                        # os.chdir(str(currentPath))
currentPath=os.getcwd()

# read download info from 'downloadList.csv'
with open('downloadList.csv') as f:
    downloadlist=f.readlines()

counter=0
# open 'downloadList.csv' for status maintenance
with open('downloadList.csv','rb+') as record:
    for item in downloadlist:
        # parse item
        status, localname, url = item[:-1].split(';')
        status = status.strip(' ').upper()
        # reset error status to 'Queued'
        if status not in {'QUEUED','DOWNLOADING','DOWNLOADED','PAUSED'}:
            # record status
            recordToFile(record,'Queued')
            counter=counter+1
        # end {if status...}
        
        record.seek(len(item.encode())+1,1)  # seek to next item
    # end {for item}

# end {with open ... as record}
print ('Reseted',counter,'items to "Queued", No Error Occurred.')


