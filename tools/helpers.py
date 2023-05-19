import requests
import pickle
import pandas
import shutil

import numpy as np

from datetime import datetime
from bs4 import BeautifulSoup

__emptyDictEntry = {}
__jsonStringToType = {
	"string": "",
	"number": np.nan,
	"object": None,
	"array": [],
}
for key, value in schema['properties'].items():
	if value['type'] == 'array':
		__emptyDictEntry[key] = []
	elif value['type'] in __jsonStringToType:
		__emptyDictEntry[key] = __jsonStringToType[value['type']]

	else:
		raise TypeError(f"Unknown JSON type in schema: {value['type']}")

catalog = pd.DataFrame(columns = schema['properties'].keys())
catalog.head()


def getDefaultEntryDict():
	return copy.deepcopy(__emptyDictEntry)

def splitPath(location: str, defaultSuffix: str) -> (str, str):
	filename, extension = os.path.splittext(location)

	if not len(extension):
		extension = f'.{defaultSuffix}'
		filename = f"{filename}{extension}"

	return filename, extension

# Get the contents of a webpage
def getPage(url: str, savePage: str = "") -> str:
	pageHtml = requests.get(url).content.decode('ASCII')
	if savePage:
	    backupPage(pageHtml, savePage)
	    
    return pageHtml

# Find the tables on a web page
def getTables(url: str, savePage: str = "") -> str:
    pageHtml = getPage(url, savePage)

    return BeautifulSoup(pageHtml).find_all("table")

def backupPage(page: str, location: str):
	now = datetime.now()
	filename, extension = splitPath(location, default = '.raw')
	
	outputLocation = f'{location[:location.rfind(extension)]}_{now.year}-{now.month}-{now.day}{extension}'
	with open(outputLocation, 'w+') as outRef:
            outRef.write(page)
    shutil.copy(outputLocation, location)

def backupTable(table: pandas.DataFrame, location: str):
	now = datetime.now()
	filename, extension = os.path.splittext(location)

	if not len(extension):
		filename = f"{filename}.json"
		extension = '.json'
	
	outputLocation = f'{location[:location.rfind(extension)]}_{now.year}-{now.month}-{now.day}{extension}'
	with open(outputLocation, 'w+') as outRef:
            table.to_json(outRef, orient = 'table')
    shutil.copy(outputLocation, location)
    return

def restoreTable(location: str) -> pandas.DataFrame:
	with open(location, 'r') as ref:
		pushchinoDf = pandas.DataFrame.from_records(json.load(ref)['data'])
	return


#def cleanupBackups():

#def removeBackups():

