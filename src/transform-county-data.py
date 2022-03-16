from fileinput import filename
import os
import sys
from os.path import exists
from pandas import to_numeric

def getCounty(fullCountyName):
  county = before(fullCountyName, ",")[1:]
  if "County" in county:
    county = before(county, " County")
  return county

def getState(fullCountyName):
  state = after(fullCountyName, ", ")
  state = state[0:len(state)-1]
  return state

def before(value, a):
    # Find first part and return slice before it.
    pos_a = value.find(a)
    if pos_a == -1: return ""
    return value[0:pos_a]

def after(value, a):
    # Find and validate first part.
    pos_a = value.rfind(a)
    if pos_a == -1: return ""
    # Returns chars after the found string.
    adjusted_pos_a = pos_a + len(a)
    if adjusted_pos_a >= len(value): return ""
    return value[adjusted_pos_a:]

def createCountyAdjacenyFiles(localBasePath):
  with open(localBasePath + "data/counties/county_adjacency.txt", "r", encoding='utf8') as countiesFile:
    currentCounty = ""
    currentState = ""
    currentCountyNumber = 0
    file = None
    lineNo = 0
    firstCountyInFile = False
    lastState = None
    firstCountyInStateFile = False
    firstCountyInFile = None
    countiesPerStateFile = None
    
    while True:
      try:
        line = countiesFile.readline()
      except UnicodeDecodeError as e:
        print("while processing line# " + str(lineNo) + " in county: " + currentCounty + ", " + currentState + " - " + str(e))
        line = "\t\t\t\t"
        lineNo = lineNo + 1
        continue
      # if line is empty
      # end of file is reached
      if not line:
          break
  
      chunks = line.split('\t')
      if chunks[0] != '':
        currentCounty = getCounty(chunks[0])
        currentState = getState(chunks[0])
        if currentState != lastState:
          if countiesPerStateFile != None:
            countiesPerStateFile.close()
          countiesPerStateFilePath = localBasePath + "data/counties/per-state/" + currentState + ".csv"
          countiesPerStateFile = open(countiesPerStateFilePath, 'w')
          countiesPerStateFile.write("< county >")
          lastState = currentState

        countiesPerStateFile.write('\n'+currentCounty)

        targetPath = localBasePath + "data/counties/adjacency/" + currentState + "/" 
        countyFile = targetPath + currentCounty.lower() + ".csv" 
        if currentCounty == "":
          print("while processing line# " + str(lineNo) + " in county: " + currentCounty + ", " + currentState)
        while not os.path.exists(targetPath):
          os.mkdir(targetPath)
        if file != None:
          file.flush()
          os.fsync(file)
          file.close()
        file = None
        file = open(countyFile, 'w')
        firstCountyInFile = True
      try:
        adjacentCounty = getCounty(chunks[2])
        adjacentState = getState(chunks[2])
      except IndexError as e:
        print("while processing line# " + str(lineNo) + " in county: " + currentCounty + ", " + currentState + " - " + str(e))
        lineNo = lineNo + 1
        continue
        print(str(e))
        print(str(lineNo) + ": " + line)
        print(str(lineNo) + ":chunks: " + str(chunks))
      if not (adjacentCounty == currentCounty and adjacentState == currentState):
        if firstCountyInFile:
          firstCountyInFile = False
        else:
          file.write('\n')
        file.write(adjacentCounty.lower() + "," + adjacentState)
      lineNo = lineNo + 1
    file.close()

if len(sys.argv) > 1 and sys.argv[1] == 'onServer':
  localBasePath = ""
else:
  localBasePath = "../../"

createCountyAdjacenyFiles(localBasePath)
