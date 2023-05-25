import os
import pickle
import pandas
import requests
import shutil

import numpy as np

from datetime import datetime
from bs4 import BeautifulSoup


def splitPath(location: str, defaultSuffix: str) -> (str, str):
	filename, extension = os.path.splitext(location)

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

	return BeautifulSoup(pageHtml, features="lxml").find_all("table")

def backupPage(page: str, location: str):
	now = datetime.now()
	filename, extension = splitPath(location, defaultSuffix = '.raw')
	
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
