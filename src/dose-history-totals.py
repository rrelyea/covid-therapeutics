from fileinput import filename
import json
from io import StringIO
from os.path import exists
from urllib.parse import urlparse
import csv
from datetime import date
import math

# loop through all providers. walk through dose data stored in zip codes. figure out doses given each week per provider and per state.
  # put state data in therapeutics\<drugName>\doses-given-per-week.csv

  # state = state or territory abbreviation
  # dosesGiven = cumulative number of doses given in that state/territory since healthdata.gov started publishing data on 12/28/2021.
  # dosesGivenPerWeek = sample: "7:0,8:0,9:4,10:5,12:6,13:7,14:3,15:5,16:2,17:4,18:12,19:13,20:28,21:4,22:1,23:4,24:7,25:3,26:8,27:0"
  #                     during week #7, 0 doses were given. during week 26, 8 doses were given. highest week # is usually the current week, which will have partial results.
  #                     ignore week 55...some states have a week #55, which I haven't debugged yet.
  # population = state/territory/usa population - source is https://www2.census.gov/programs-surveys/popest/datasets/2020-2021/state/totals/NST-EST2021-alldata.csv
  # IC_Adults_Estimated = population * .027 * .779
  #                       AMA says 2.7% of US population is immunocompromised: https://www.ama-assn.org/delivering-care/public-health/what-tell-immunocompromised-patients-about-covid-19-vaccines
  #                       Census.gov says 77.9% of US population are adults: https://www.census.gov/library/visualizations/interactive/adult-and-under-the-age-of-18-populations-2020-census.html
  # PercentICAdultsProtected = dosesGiven / IC_Adults_Estimated * 100
  # AvailableDoses = total doses reported in latest provider inventory reports
  
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
  if not exists(doseHistoryByZipPath):
    dosesGiven = {'total':0} # TODO: why did zip code not exist on 5/20/2022 Action runs?
    return dosesGiven

  with open(doseHistoryByZipPath, "r") as doseHistoryByZipFile:
    dosesGiven = {}

    lastAvailable = 0
    lastWeekNumber = 0
    dosesAdministeredTotal = 0
    dosesAdministeredWeek = 0
    lastReportDate = None
    providerList = csv.reader(doseHistoryByZipFile, delimiter=',', quoting=csv.QUOTE_ALL, doublequote=True)
    for providerReport in providerList:
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

def getPopByStateCode(localBasePath):
  filename = localBasePath + "data/states/state-health-info.csv"
  popByStateCode = {}
  with open(filename, "r", encoding="utf-8") as stateHealthInfoFile:
    stateList = csv.reader(stateHealthInfoFile, delimiter=',', quoting=csv.QUOTE_ALL, doublequote=True)
    for state in stateList:
      stateCode = state[3]
      pop = state[11]
      if (stateCode != 'state_code'):
        popByStateCode[stateCode] = pop
  return popByStateCode

def getPop(state, popByStateCode):
  if state in popByStateCode:
    return popByStateCode[state]
  else:
    return ""

def getICAdultEstimate(drugName, state, popByStateCode):
  if drugName == "evusheld" and state in popByStateCode:
    return "{:.0f}".format(int(popByStateCode[state]) * .027 * .779)
  else:
    return ""

def getPercentICProtected(drugName, state, popByStateCode, dosesGiven):
  if drugName != "evusheld":
    return ""
  ICAdultsStr = getICAdultEstimate(drugName, state, popByStateCode)
  if ICAdultsStr != '' and dosesGiven != '':
    percentProtected = float(dosesGiven) / float(ICAdultsStr) * 100.0
    return "{:.2f}".format(percentProtected)+"%"
  else:
    return ""

def createProviderAndStateDoseHistoryFiles(localBasePath, drugsJson):
  popByStateCode = getPopByStateCode(localBasePath)
  drugs = json.loads(drugsJson)
  for drug in drugs.keys():
    drugName = drug.lower().replace(' ','-')
    if drugName.endswith('-(molnupiravir)'):
      drugName = "lagevrio"
    lastState = None
    dosesPerState = 0
    providersPerState = 0
    firstWeekPerDrug = None
    stateDosesByWeek = {}
    nationalDosesByWeek = {}
    dosesTotal = 0
    availableTotal = 0
    availablePerState = 0
    providersTotal = 0
    with open(localBasePath + "data/therapeutics/"+ drugName + "/doses-given-per-week.csv", "w", encoding="utf-8") as outputFile:
      outputFile.write("state, dosesGiven, dosesGivenPerWeek, population, IC_Adults_Estimated, PercentICAdultsProtected, availableDoses\n")
      with open(localBasePath + "data/therapeutics/" + drugName + "/" + drugName +"-providers.csv", "r", encoding="utf-8") as therapeuticsFile:
        providerList = csv.reader(therapeuticsFile)
        for provider in providerList:
          zip = get5digitZip(provider[6])
          state = provider[5]
          if state != lastState:
            if not (lastState == None or lastState == '' or lastState == 'state_code'):
              outputFile.write(lastState +"," + str(dosesPerState)+",\""+ weekOrder(stateDosesByWeek) +"\","+getPop(lastState, popByStateCode)+"," +getICAdultEstimate(drugName, lastState, popByStateCode)+"," + getPercentICProtected(drugName, lastState, popByStateCode, dosesPerState) + "," + str(availablePerState) +"\n")
            dosesTotal = dosesTotal + dosesPerState
            providersTotal = providersTotal + providersPerState
            availableTotal = availableTotal + availablePerState
            dosesPerState = 0
            providersPerState = 0
            availablePerState = 0
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
            if provider[9] != '':
              availablePerState = availablePerState + int(float(provider[9]))
            providersPerState = providersPerState + 1
          lastState = state  
        if not (lastState == None or lastState == '' or lastState == 'state_code'):
          outputFile.write(lastState+","+ str(dosesPerState)+",\""+  weekOrder(stateDosesByWeek) +"\","+getPop(lastState, popByStateCode)+","+getICAdultEstimate(drugName, lastState, popByStateCode)+"," + getPercentICProtected(drugName, lastState, popByStateCode, dosesPerState) + ","+ str(availablePerState) +"\n")
        dosesTotal = dosesTotal + dosesPerState
        providersTotal = providersTotal + providersPerState
        availableTotal = availableTotal + availablePerState
        outputFile.write("USA"+"," + str(dosesTotal)+",\""+  weekOrder(nationalDosesByWeek) +"\","+getPop("USA", popByStateCode)+","+getICAdultEstimate(drugName, "USA", popByStateCode)+"," + getPercentICProtected(drugName, "USA", popByStateCode, dosesTotal) + "," + str(availableTotal) +"\n")

localBasePath = ""
createProviderAndStateDoseHistoryFiles(localBasePath, '{"Evusheld":24, "Paxlovid":20, "Sotrovimab":5, "Bebtelovimab":5, "Lagevrio (molnupiravir)":24, "Renal Paxlovid":10}')