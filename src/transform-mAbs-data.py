import pandas as pd
import sys

def sortDataFile(fileName):
  dataFile = pd.read_csv(fileName)
  print ("sorting: " + fileName)
  
  # ensure standard casing, so that sorting works better.
  dataFile['city'] = dataFile['city'].str.title()
  dataFile['county'] = dataFile['county'].str.title()

  dataFile.sort_values(["state_code", "county", "city", "provider_name", "address1"], 
                      axis=0,
                      ascending=[True, True, True, True, True], 
                      inplace=True)

  dataFile.to_csv(fileName, index=False)

def sortTestToTreatFile(fileName):
  dataFile = pd.read_csv(fileName)
  print ("sorting: " + fileName)
  
  # ensure standard casing, so that sorting works better.
  dataFile['city'] = dataFile['city'].str.title()

  dataFile.sort_values(["state", "city", "zip", "provider_name"], 
                      axis=0,
                      ascending=[True, True, True, True], 
                      inplace=True)

  dataFile.to_csv(fileName, index=False)


if len(sys.argv) > 1:
  dataFile = sys.argv[1]

if "testToTreat" in dataFile:
  sortTestToTreatFile(dataFile)
else:
  sortDataFile(dataFile)
