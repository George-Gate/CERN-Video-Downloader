from pathlib import Path
import os
import csv
import json

# get current working directory
                                    # rootPath=Path(makelist)
                                    # rootPath=rootPath.parent
                                    # os.chdir(str(rootPath))
rootPath=Path(os.getcwd())

# URL template for desktop slide 1080p video
urlTemplate=['https://mediastream.cern.ch/MediaArchive/Video/Public/WebLectures/2014/(%eventID)/(%eventID)_desktop_slides_1080p_4000.mp4',
             'https://mediastream.cern.ch/MediaArchive/Video/Public/WebLectures/2014/(%eventID)/(%eventID)_desktop_camera_1080p_4000.mp4',
             'https://mediastream.cern.ch/MediaArchive/Video/Public/WebLectures/2014/(%eventID)/lecture.json',
             'https://mediastream.cern.ch/MediaArchive/Video/Public/WebLectures/2014/(%eventID)/thumbs/(%picName)']
localname=['(%lectureID).(%counter)_slides_1080p.mp4',
           '(%lectureID).(%counter)_camera_1080p.mp4',
           'lecture.json',
           'thumbs/(%picName)']

# check if 'downloadList.csv' exists
p=Path('downloadList.csv')
if not p.exists():
    p.open('w').close()

# Read URL list from 'downloadList.csv' first
URLlist=set()
with open('downloadList.csv',newline='') as f:
    reader=csv.reader(f,delimiter=';')
    try:
        for status, name, URL in reader:
            URLlist.add(URL)
    except ValueError:
        print ('Error: "downloadList.csv" end with new line. This may lead to repeated download.\n',
                ' Please delete the new line and restart this program.')
        raise ValueError

# write download list to 'downlodaList.csv' using csv.writer
with open('downloadList.csv','a') as f:
    csvwriter = csv.writer(f,delimiter=';')
    for idList in rootPath.glob('**/eventID'):
        # find all 'eventID' files in sub-directories and read the event id
        print (idList.parent.relative_to(rootPath))
        # generate relative path of 'eventID'
        lectureID=str(idList.parent.relative_to(rootPath))[0:2]
        with idList.open() as eventID:
            counter=0
            for ID in eventID.readlines():
                if ID!='\n':
                    counter=counter+1
                    # generate download entry information
                    for i in [0,1,2]:
                        item=['{: <50}'.format('Queued'),
                              './'+str(idList.parent.relative_to(rootPath))+'/'
                                  +str(counter)+'/'
                                  +localname[i].replace('(%lectureID)',lectureID)
                                               .replace('(%counter)',str(counter)),
                              urlTemplate[i].replace('(%eventID)',ID[:-1])]
                        # write to the file
                        if item[2] not in URLlist:
                            URLlist.add(item[2])
                            csvwriter.writerow(item)
                    
                    # try to read lecture.json and add pic entry
                    jfile=Path(str(idList.parent)+'/'+str(counter)+'/lecture.json')
                    if jfile.exists():
                        with jfile.open() as f:
                            lecture = json.load(f)
                        lecture = lecture['lecture']['thumbs']
                        for x in lecture:
                            item=['{: <50}'.format('Queued'),
                                  './'+str(idList.parent.relative_to(rootPath))+'/'
                                      +str(counter)+'/'
                                      +localname[3].replace('(%picName)',x['src']),
                                  urlTemplate[3].replace('(%eventID)',ID[:-1])
                                                .replace('(%picName)',x['src'])]
                            if item[2] not in URLlist:
                                URLlist.add(item[2])
                                csvwriter.writerow(item)
                    # end {if jfile}
                #end {if ID}
            # end {for ID}
        # end {with eventID}
    # end {for idList}
# end {with f}



