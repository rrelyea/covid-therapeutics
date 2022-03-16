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
    
def updateZipCodeFilesForDrug(localBasePath, drugs):
  with open(localBasePath + "data/therapeutics/process-dates.csv", "r") as lastProcessed_file:
    lastProcessedDate = lastProcessed_file.readline()
    print("last processed: " + lastProcessedDate)

  newLastProcessedDate = None
  with open(localBasePath + "data/therapeutics/publish-events.json", "r") as read_file:
      publishings = json.load(read_file)
      urls = []

      for publishing in publishings:
        updateDate = publishing["update_date"]
        if updateDate > lastProcessedDate:
          urls.append(publishing["archive_link"]["url"])
          newLastProcessedDate = updateDate

  # download all new files
  for url in sorted(urls):
    filename = os.path.basename(urlparse(url).path)
    publishEventPath = localBasePath + 'data/therapeutics/publish-events/'
    while not os.path.exists(publishEventPath):
      os.mkdir(publishEventPath)
    mabsFile = publishEventPath + filename
    if not exists(mabsFile):
      print("downloading " + url)
      r = requests.get(url, allow_redirects=True)
      therapeuticsFile = open(mabsFile, 'wb')
      therapeuticsFile.write(r.content)
      therapeuticsFile.close()

  for drug in drugs:
      drugPath = localBasePath + 'data/therapeutics/' + drug.lower() + '/'
      while not os.path.exists(drugPath):
        os.mkdir(drugPath)

  # calculate all zip codes, by looking at latest data file, if there is one.
  if len(urls) == 0:
    print("complete. no new data to process.")
    sys.exit()

  url = sorted(urls)[len(sorted(urls)) - 1]
  filename = os.path.basename(urlparse(url).path)
  therapeuticsPath = localBasePath + 'data/therapeutics/'
  publishEventsPath = therapeuticsPath + 'publish-events/'
  while not os.path.exists(publishEventsPath):
    os.mkdir(targetPath)
  mabsFile = publishEventsPath + filename
  therapeuticsFile = open(mabsFile, 'r', encoding='utf8')
  zipSet = set()
  reader = csv.reader(therapeuticsFile)
  for columns in reader:
    zip = get5digitZip(columns[6])
    if zip != "00Zip" and (columns[8] in drugs) and zip[0] == '0':
      zipSet.add(zip)
  therapeuticsFile.close()

  print('zip codes for ' + mabsFile + ':' + str(len(zipSet)))

  for zipCode in sorted(zipSet):
    # print(zipCode, end=', ', flush=True)
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
          if zipFile[index] == None:
            zipFile[index] = open(therapeuticsPath + columns[8].lower() + '/' + str(zipCode)+'.csv', "a",encoding='utf8')
          f = zipFile[index]
          f.write(timeStamp + ',' + zip + ',' + provider)
          for i in range(9, 14):
            if i < len(columns):
              f.write(',' + columns[i])
            else:
              f.write(',')
          f.write('\n')
  return newLastProcessedDate

localBasePath = ""
lastProcessedDate = updateZipCodeFilesForDrug(localBasePath, ['Evusheld', 'Paxlovid', 'Sotrovimab', 'Bebtelovimab'])
with open(localBasePath + "data/therapeutics/process-dates.csv", "w") as lastProcessed_file:
  lastProcessed_file.write(lastProcessedDate)
  print("data/therapeutics/process-dates.csv to " + lastProcessedDate)

