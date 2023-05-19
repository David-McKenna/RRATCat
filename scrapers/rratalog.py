import bs4.element
import copy

from astropy.coordinates import SkyCoord
from typing import Union

# RRatalog
rratalogMap = {
    "Name": None,
    "P": "Period",
    "Pdot": "dPeriod",
    "DM": "Dispersion Measure",
    "RA": None,
    "Dec": None,
    'l': None,
    'b': None,
    'Burst Rate': None,
    'log[B]': None,
    'Age log[t]': None,
    'Distance': None,
    #"S_140 MHz": "S140",
    #"S_350 MHz": "S350",
    #"S_1400 MHz": "S1400",
    #"Pulse Width 140 MHz": "W140",
    #"Pulse Width 350 MHz": "W350",
    #"Pulse Width 1400 MHz": "W1400",
    "S_140 MHz": None,
    "S_350 MHz": None,
    "S_1400 MHz": None,
    "Pulse Width 140 MHz": None,
    "Pulse Width 350 MHz": None,
    "Pulse Width 1400 MHz": None,
    'RM': None,
    'Linear Polarzation': None,
    "Survey": None
}
def parseRRATalog(inputBS: Union[str, bs4.element.ResultSet]) -> list[dict]:
    rratalogDf = pd.read_html(str(inputBS), header = 0, skiprows = [1])[0]
    
    rratalogDict = rratalogDf.to_dict('index')
    rratalogList = [rratalogDict[i] for i in range(len(rratalogDict.keys()))]
    newRows = []
    
    for row in rratalogList:
        # Spelling is intentional, it's wrong in the catalog
        # We'll grab it when parsing the LOTAAS sources
        #if 'LOTASS' in row['Survey']:
        #    continue
        workingDict = getDefaultEntryDict()
            
        coord = SkyCoord(ra = row['RA'], dec = row['Dec'], frame = 'icrs', unit = ('hourangle', 'degree'))
        catalog = row['Survey'].replace(' ', '').split('/') + ['RRATalog']
        if len(catalog) == 1:
            catalog = catalog[0]
        
        workingDict.update({'JName': row['Name'].replace('*', ''),
                            'Right Ascension': coord.ra.rad,
                            'Declination': coord.dec.rad,
                            'SkyCoord': copy.deepcopy(coord)
                            'Catalogs': catalog,
                            })

        for key, val in row.items():
            if val != '--':
                if rratalogMap[key] != None:
                    workingDict[rratalogMap[key]] = float(row[key])

        newRows.append(workingDict)
    
    return newRows