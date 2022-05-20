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
  # put state data in therapeutics\<drugName>\doses-given-per-week\all.csv
    # state, week1, week2, ..., weekLatest

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
  doseHistoryByZipPath = localBasePath + "data/therapeutics/" + drugName + "/dose-history-by-zip/" + zip + ".csv"
  if not exists(doseHistoryByZipFile):
    dosesGiven = {'total':0} # TODO: why did zip code not exist on 5/20/2022 Action runs?
    return dosesGiven

  with open(doseHistoryByZipPath, "r") as doseHistoryByZipFile:
    dosesGiven = {}

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
        weekNumber = (reportDate.year - 2021) * 52 + reportDate.isocalendar()[1] - 49
        if weekNumber != lastWeekNumber:
          if lastWeekNumber != 0:
            dosesGiven[lastWeekNumber] = dosesAdministeredWeek
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
    if lastWeekNumber != 0:
      dosesGiven[lastWeekNumber] = dosesAdministeredWeek
    dosesGiven['total'] = dosesAdministeredTotal
    #print(dosesGiven)
    return dosesGiven

def accumulateDosesByWeek(providerDosesByWeek, totalsDosesByWeek):
  for dosesInWeek in list(providerDosesByWeek.keys()):
    totalDosesInWeek = 0
    if dosesInWeek in totalsDosesByWeek:
      totalDosesInWeek = totalsDosesByWeek[dosesInWeek]
    totalsDosesByWeek[dosesInWeek] = providerDosesByWeek[dosesInWeek] + totalDosesInWeek
  return totalsDosesByWeek

def weekOrder(dictionary):
   if 'total' in dictionary.keys():
    dictionary.pop('total')
   value = ""
   isFirst = True
   for key in sorted(dictionary.keys()):
     comma = ","
     if isFirst:
       isFirst = False
       comma = ""
     value = value + (comma + str(key) + ":" + str(dictionary[key]))
   return value

def createProviderAndStateDoseHistoryFiles(localBasePath, drugsJson):
  drugs = json.loads(drugsJson)
  for drug in drugs.keys():
    drugName = drug.lower()
    if (drugName == 'lagevrio (molnupiravir)'):
      drugName = "lagevrio"
    lastState = None
    dosesPerState = 0
    providersPerState = 0
    firstWeekPerDrug = None
    stateDosesByWeek = {}
    nationalDosesByWeek = {}
    dosesTotal = 0
    providersTotal = 0
    with open(localBasePath + "data/therapeutics/"+ drugName + "/doses-given-per-week.csv", "w", encoding="utf-8") as outputFile:
      outputFile.write("state, dosesGiven, dosesGivenPerWeek\n")
      with open(localBasePath + "data/therapeutics/" + drugName + "/" + drugName +"-providers.csv", "r", encoding="utf-8") as therapeuticsFile:
        providerList = csv.reader(therapeuticsFile)
        for provider in providerList:
          zip = get5digitZip(provider[6])
          state = provider[5]
          if state != lastState:
            if not (lastState == None or lastState == '' or lastState == 'state_code'):
              outputFile.write(lastState +","+  str(dosesPerState)+",\""+ weekOrder(stateDosesByWeek) +"\"\n")
            dosesTotal = dosesTotal + dosesPerState
            providersTotal = providersTotal + providersPerState
            dosesPerState = 0
            providersPerState = 0
            nationalDosesByWeek = accumulateDosesByWeek(stateDosesByWeek, nationalDosesByWeek)
            stateDosesByWeek = {}
          providerName = provider[0]
          if zip != "00zip" and zip != None:
            dosesInBox = drugs[drug]
            providerDosesByWeek = calculateDosesPerWeek(zip, providerName, drugName, dosesInBox, localBasePath)
            stateDosesByWeek = accumulateDosesByWeek(providerDosesByWeek, stateDosesByWeek)
            firstKey = list(providerDosesByWeek.keys())[0]
            if firstKey != 0 and firstKey != 'total' and (firstWeekPerDrug == None or firstKey < firstWeekPerDrug):
              firstWeekPerDrug = firstKey
            dosesPerState = dosesPerState + providerDosesByWeek['total']
            providersPerState = providersPerState + 1
          lastState = state  
        if not (lastState == None or lastState == '' or lastState == 'state_code'):
          outputFile.write(lastState+","+  str(dosesPerState)+",\""+  weekOrder(stateDosesByWeek) +"\"\n") 
        dosesTotal = dosesTotal + dosesPerState
        outputFile.write("USA"+","+  str(dosesTotal)+",\""+  weekOrder(nationalDosesByWeek) + "\"\n")

localBasePath = ""
createProviderAndStateDoseHistoryFiles(localBasePath, '{"Evusheld":24, "Paxlovid":20, "Sotrovimab":5, "Bebtelovimab":5, "Lagevrio (molnupiravir)":24, "Renal Paxlovid":10}')