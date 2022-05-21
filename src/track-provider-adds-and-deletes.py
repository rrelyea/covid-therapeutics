from fileinput import filename
import json
from io import StringIO
import os
import sys
from os.path import exists
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
    return ""
   
def trackProviderAddsAndDeletes(localBasePath, dataRelativePath, drugs, stateIndex, orderLabelIndex):
  states = list()
  with open(localBasePath + "data/states/state-health-info.csv", "r") as states_file:
    reader = csv.reader(states_file)
    for columns in reader:
      state_code = columns[3]
      states.append(state_code)

  with open(localBasePath + "data/"+dataRelativePath+"publish-events.json", "r") as read_file:
      publishings = json.load(read_file)
      urls = []

      for publishing in publishings:
        updateDate = publishing["update_date"]
        urls.append(publishing["archive_link"]["url"])

      for drug in drugs:
        print(drug + " started.")
        drugPath = localBasePath + 'data/therapeutics/' + drug.lower() + '/'
        doseHistoryPath = drugPath + drug.lower() + '-providers-added-removed.txt'
        with open(doseHistoryPath, "w") as doseHistory_file:
          doseHistory_file.write("State Date       Time   Providers Details\n")
          for state_code in states:
            providers = list()
            for url in sorted(urls):
              lastProviders = providers
              filename = os.path.basename(urlparse(url).path)
              therapeuticsPath = localBasePath + 'data/' + dataRelativePath
              publishEventsPath = therapeuticsPath + 'publish-events/'
              mabsFile = publishEventsPath + filename
              therapeuticsFile = open(mabsFile, 'r', encoding='utf8')
              providers = list()
              reader = csv.reader(therapeuticsFile)
              for columns in reader:
                state = columns[stateIndex].upper()
                if state == state_code:
                  if orderLabelIndex == -1:
                    order_label = drug
                  else:
                    order_label = columns[8]

                  if order_label == drug:
                    provider = columns[0].title()
                    city = columns[3].title()
                    zip = get5digitZip(columns[stateIndex+1])
                    providers.append(state + "," + city + "," + zip + "," + provider)
              therapeuticsFile.close()

              if len(lastProviders) > 0:
                added = list(set(providers) - set(lastProviders))
                added.sort()
                removed = list(set(lastProviders) - set(providers))
                removed.sort()
                if len(added) > 0:
                  doseHistory_file.write(state_code + "    " + filename[10:20] + " " + filename[21:26] + "  +" + "{:<9}".format(str(len(added))))
                  doseHistory_file.write(str(added) + '\n')
                if len(removed) > 0:
                  doseHistory_file.write(state_code + "    " + filename[10:20] + " " + filename[21:26] + "  -" + "{:<9}".format(str(len(removed))))
                  doseHistory_file.write(str(removed) + '\n')
  return

localBasePath = ""
#trackProviderAddsAndDeletes(localBasePath, "therapeutics", ['Evusheld', 'Paxlovid', 'Sotrovimab', 'Bebtelovimab'], 5, 8)
trackProviderAddsAndDeletes(localBasePath, "therapeutics/testToTreat/", ["testToTreat"] , 4, -1)
