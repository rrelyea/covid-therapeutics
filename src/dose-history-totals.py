from fileinput import filename
import json
from io import StringIO
import os
import sys
from os.path import exists
import requests
from urllib.parse import urlparse
import csv
from datetime import date
import math

# loop through all providers. walk through dose data stored in zip codes. figure out doses given each week per provider and per state.
  # put provider data in therapeutics\<drugName>\provider-dose-history-per-week\GC_-87.86627_30.65662.csv
    # eow, doses_given, inventory
  # put state data in therapeutics\<drugName>\state-dose-history-per-week\WA.json
    # eow, doses_given, inventory
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


def calculateDosesPerWeek(zip, providerName, drugName, dosesInBox, localBasePath):
  with open(localBasePath + "data/therapeutics/" + drugName + "/dose-history-by-zip/" + zip + ".csv", "r") as doseHistoryByZipFile:
    lastAvailable = 0
    weeklyDosesGiven = 0
    lastWeekNumber = 0
    dosesAdministeredTotal = 0
    dosesAdministeredWeek = 0
    lastReportDate = None
    providerList = csv.reader(doseHistoryByZipFile, delimiter=',', quoting=csv.QUOTE_ALL, doublequote=True)
    for providerReport in providerList:
      PRpublishDate = providerReport[0][0:10]
      PRproviderName = providerReport[2]
      if providerReport[6] != '':
        PRavailable = int(providerReport[6])
      else:
        PRavailable = 0
      PRreportDate = providerReport[7][:10]
      
      if providerName == PRproviderName and PRreportDate != "" and PRreportDate != lastReportDate:
        dosesAdministered = lastAvailable - PRavailable
        dt_tuple=tuple([str(x) for x in PRreportDate.split('/')])
        dateStr = dt_tuple[2]+"-"+dt_tuple[0]+"-"+dt_tuple[1]
        reportDate = date(int(dt_tuple[2]), int(dt_tuple[0]), int(dt_tuple[1]))
        weekNumber = (reportDate.year - 2021) * 52 + reportDate.isocalendar()[1]
        if weekNumber != lastWeekNumber:
          #print(lastWeekNumber, dosesAdministeredWeek, dosesAdministeredTotal)
          dosesAdministeredWeek = 0
        administeredToday = 0
        if dosesAdministered > 0 and dosesAdministered < dosesInBox and PRavailable != None:
          dosesAdministeredTotal = dosesAdministeredTotal + dosesAdministered
          dosesAdministeredWeek = dosesAdministeredWeek + dosesAdministered
        elif dosesAdministered < 0:
          if dosesAdministered < -(dosesInBox/2):
            boxes = math.ceil(abs(dosesAdministered) / dosesInBox)
            administeredToday = (boxes * dosesInBox) + dosesAdministered
            dosesAdministeredTotal = dosesAdministeredTotal + administeredToday
            dosesAdministeredWeek = dosesAdministeredWeek + administeredToday
        lastReportDate = PRreportDate
        lastAvailable = PRavailable
        lastWeekNumber = weekNumber
    #print(lastWeekNumber, dosesAdministeredWeek, dosesAdministeredTotal)
    return dosesAdministeredTotal

def createProviderAndStateDoseHistoryFiles(localBasePath, drugsJson):
  drugs = json.loads(drugsJson)
  for drug in drugs.keys():
    drugName = drug
    if (drugName == 'Lagevrio (molnupiravir)'):
      drugName = "lagevrio"
    lastState = None
    dosesPerState = 0
    providersPerState = 0
    dosesTotal = 0
    providersTotal = 0
    print ("drugName", "state", "providers", "dosesGiven")
    with open(localBasePath + "data/therapeutics/" + drugName + "/" + drugName +"-providers.csv", "r", encoding="utf-8") as therapeuticsFile:
      providerList = csv.reader(therapeuticsFile)
      for provider in providerList:
        zip = get5digitZip(provider[6])
        state = provider[5]
        if state != lastState:
          if not (lastState == None or lastState == '' or lastState == 'state_code'):
            print (drugName, lastState, providersPerState, dosesPerState)
          dosesTotal = dosesTotal + dosesPerState
          providersTotal = providersTotal + providersPerState
          dosesPerState = 0
          providersPerState = 0
        providerName = provider[0]
        if zip != "00zip" and zip != None:
          dosesInBox = drugs[drug]
          dosePerProvider = calculateDosesPerWeek(zip, providerName, drugName, dosesInBox, localBasePath)
          dosesPerState = dosesPerState + dosePerProvider
          providersPerState = providersPerState + 1
        lastState = state  
      if not (lastState == None or lastState == '' or lastState == 'state_code'):
        print (drugName, lastState, providersPerState, dosesPerState)
      dosesTotal = dosesTotal + dosesPerState
      print (drugName,"USA", providersTotal, dosesTotal)
      print ()

localBasePath = ""
createProviderAndStateDoseHistoryFiles(localBasePath, '{"Evusheld":24, "Paxlovid":20, "Sotrovimab":5, "Bebtelovimab":5, "Lagevrio (molnupiravir)":24}')