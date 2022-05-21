from fileinput import filename
import json
from io import StringIO
import os
import sys
from os.path import exists
import requests
from urllib.parse import urlparse
import csv

def get5digitZip(rawZip):
  if len(rawZip) == 3:
    return '00' + rawZip
  elif len(rawZip) == 4:
    return '0' + rawZip 
  elif len(rawZip) == 5:
    return rawZip 
  elif len(rawZip) > 5:
    return rawZip[0:5]
  else:
    return None

def updateLastProcessedDate(therapeuticsSubfolder, lastProcessedDate, stopProcessingDate):
  with open("data/therapeutics/"+therapeuticsSubfolder+"process-dates.csv", "w") as lastProcessed_file:
    lastProcessed_file.write(lastProcessedDate + ',' + stopProcessingDate)
    print("  data/therapeutics/"+therapeuticsSubfolder+"process-dates.csv set to: " + lastProcessedDate + ',' + stopProcessingDate)

def downloadAllPublishEventFiles(therapeuticsSubfolder):
  with open("data/therapeutics/"+therapeuticsSubfolder+"process-dates.csv", "r") as lastProcessed_file:
    processDates = lastProcessed_file.readline().split(',')
    lastProcessedDate = processDates[0]
    stopProcessingDate = processDates[1]
    print("  last processed: " + lastProcessedDate)
    print("  stop procesing: " + stopProcessingDate)

  newLastProcessedDate = None
  with open("data/therapeutics/"+therapeuticsSubfolder+"publish-events.json", "r") as read_file:
      publishings = json.load(read_file)
      urls = []

      for publishing in publishings:
        updateDate = publishing["update_date"]
        if updateDate > lastProcessedDate and updateDate < stopProcessingDate :
          urls.append(publishing["archive_link"]["url"])

  publishEventPath = "data/therapeutics/"+therapeuticsSubfolder+"publish-events/"

  # download all new files
  for url in sorted(urls):
    filename = os.path.basename(urlparse(url).path)
    while not os.path.exists(publishEventPath):
      os.mkdir(publishEventPath)
    mabsFile = publishEventPath + filename
    if not exists(mabsFile):
      print("downloading " + url)
      r = requests.get(url, allow_redirects=True)
      therapeuticsFile = open(mabsFile, 'wb')
      therapeuticsFile.write(r.content)
      therapeuticsFile.close()
  return sorted(urls), lastProcessedDate, stopProcessingDate

def updateZipCodeFilesForDrug(therapeuticsSubfolder, drugs, sortedUrls, lastProcessedDate, stopProcessingDate):
  newLastProcessedDate = None

  for drug in drugs:
      drugPath = 'data/therapeutics/' + drug.lower() + '/'
      doseHistoryPath = drugPath + 'dose-history-by-zip/'
      if lastProcessedDate < "2020-03-02T00:00:00.000" and os.path.exists(drugPath):
        for root, directories, files in os.walk(doseHistoryPath):
          for file in files:
            os.remove(os.path.join(root, file))
        os.rmdir(doseHistoryPath)
      while not os.path.exists(drugPath):
        os.mkdir(drugPath)
      while not os.path.exists(doseHistoryPath):
        os.mkdir(doseHistoryPath)

  # calculate all zip codes by processing from publish event after lastProcessedDate to stopProcessingDate
  if len(sortedUrls) == 0:
    print("  zip code work complete. no new data to process.")
    return newLastProcessedDate, stopProcessingDate

  for url in sortedUrls:
    filename = os.path.basename(urlparse(url).path)
    therapeuticsPath = 'data/therapeutics/'
    publishEventsPath = therapeuticsPath + 'publish-events/'
    while not os.path.exists(publishEventsPath):
      os.mkdir(publishEventsPath)
    mabsFile = publishEventsPath + filename
    therapeuticsFile = open(mabsFile, 'r', encoding='utf8')
    zipSet = set()
    reader = csv.reader(therapeuticsFile)
    for columns in reader:
      zip = get5digitZip(columns[6])
      if zip != "00Zip" and zip != None and (columns[8] in drugs):
        zipSet.add(zip)
      else:
        print("skipped " + str(columns))
    therapeuticsFile.close()

    print('zip codes for ' + mabsFile + ': ' + str(len(zipSet)), flush=True)
    for zipCode in sorted(zipSet):
      zipFile = [None] * len(drugs)
      filename = os.path.basename(urlparse(url).path)
      therapeuticsFile = publishEventsPath + filename
      timeStamp = filename.replace('rxn6-qnx8_','').replace('.csv','')
      with open(therapeuticsFile, 'r', encoding='utf8') as data:
        reader = csv.reader(data)
        for columns in reader:
          zip = get5digitZip(columns[6])
          provider = columns[0]
          if "," in provider:
            provider = '"' + provider + '"'
          if zip == zipCode and columns[8] in drugs:
            index = drugs.index(columns[8])
            drugShortName = columns[8].replace(' ','-').lower()
            if drugShortName.endswith('-(molnupiravir)'):
              drugShortName = "lagevrio"
            if zipFile[index] == None:
              zipFile[index] = open(therapeuticsPath + drugShortName + '/dose-history-by-zip/' + str(zipCode)+'.csv', "a",encoding='utf8')
            f = zipFile[index]
            f.write(timeStamp + ',' + zip + ',' + provider)
            if (timeStamp < "2022-03-16"):
              for i in range(9, 14):
                if i < len(columns):
                  f.write(',' + columns[i])
                else:
                  f.write(',')
            elif (timeStamp < "2022-03-31T15-09-22"):
              f.write(",NLP") #allotted_update  - no longer published by healthdata.gov
              f.write(",NLP") #last delivery    - no longer published by healthdata.gov
              f.write(",NLP") #allotted doses   - no longer published by healthdata.gov
              f.write("," + columns[9])     #available doses
              f.write("," + columns[13])    #last report date
            else:
              f.write(",NLP") #allotted_update  - no longer published by healthdata.gov
              f.write(",NLP") #last delivery    - no longer published by healthdata.gov
              f.write(",NLP") #allotted doses   - no longer published by healthdata.gov
              f.write("," + columns[9])     #available doses
              f.write("," + columns[12])    #last report date

            f.write('\n')
  return newLastProcessedDate, stopProcessingDate

therapeuticsSubfolders = ["", "testToTreat/"]
for therapeuticsSubfolder in therapeuticsSubfolders:
  updatedLastProcessedDate = None
  print()
  print("starting work for [data/therapeutics/" + therapeuticsSubfolder + "]:")
  sortedUrls, lastProcessedDate, stopProcessingDate = downloadAllPublishEventFiles(therapeuticsSubfolder)
  print("  new data for [data/therapeutics/"+therapeuticsSubfolder+"]: " + str(sortedUrls))
  if therapeuticsSubfolder == "":
    updatedLastProcessedDate, stopProcessingDate = updateZipCodeFilesForDrug(therapeuticsSubfolder, ['Evusheld', 'Paxlovid', 'Sotrovimab', 'Bebtelovimab', 'Lagevrio (molnupiravir)'], sortedUrls, lastProcessedDate, stopProcessingDate)
  else:
    if len(sortedUrls) > 0:
      lastUrlProcessed = sortedUrls[len(sortedUrls)-1]
      dateTimeCharStartIndex = lastUrlProcessed.index('_') + 1
      date = lastUrlProcessed[dateTimeCharStartIndex:dateTimeCharStartIndex+11]
      time = (lastUrlProcessed[dateTimeCharStartIndex + 11:len(lastUrlProcessed)-4]+".000").replace('-',':')
      print(date, time)
      updatedLastProcessedDate = date + time
  if updatedLastProcessedDate != None:
    updateLastProcessedDate(therapeuticsSubfolder, updatedLastProcessedDate, stopProcessingDate)

