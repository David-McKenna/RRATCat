import bs4.element 
import copy

from psrqpy import QueryATNF
from astropy.coordinates import SkyCoord

LOTAAS_FREQ = 135 # MHz

lotaasNameMapping = {
    "J0250+58": "J0250+5854",
    "J2053+17": "J2053+1718",
    "J1658+36": "J1658+3630",
    "J1404+11": "J1404+1159",
}

psrcatMapping = {
    'JName': 'JNAME',
    'Peirod': 'P0',
    'ePeriod': 'P0_ERR',
    'Dispersion Measure': 'DM',
    'eDispersion Measure': 'DM_ERR',
}
def __parseLOTAASBS(inputBS: bs4.element.ResultSet) -> list[dict]:
    # Extract the main table (contains 4 sub tables)
    inputBS = inputBS[0]
    #print(pd.read_html(str(inputBS), index_col = 0))
    inputBS = inputBS.find_all("tr")
    newRows = []
    
    
    
    psrcat = QueryATNF(['JName', 'RaJ', 'DecJ', 'DM', 'P0', 'P1', 'W50', 'S150', 'Type'])
    for idx, row in enumerate(inputBS):
        row = row.find_all('td')

        if len(row) == 9 and row[0].text != '#':
            workingDict = getDefaultEntryDict()
            workingDict['Catalogs'] = 'LOTAAS'                
            
            name = row[1].text


            if name in lotaasNameMapping.keys():
                name = lotaasNameMapping[name]


            idx = psrcat.dataframe.index[psrcat.dataframe['JNAME'] == name].tolist()
            if len(idx) == 1:
                entry = psrcat.dataframe.loc[idx[0]]
                coord = SkyCoord(ra = entry['RAJ'], dec = entry['DECJ'], frame = 'icrs', unit = ('hourangle', 'degree'))
                
                for inputKey, outputKey in psrcatMapping.items():
                    workingDict[inputKey] = entry['outputKey']

            else:
                ra = f"{row[1].text[1:3]}h{row[1].text[3:5]}m"
                dec = f"{row[1].text[5].replace('–', '-')}{int(row[1].text[6:8])}d"
                coord = SkyCoord(ra = ra, dec = dec, frame = 'icrs', unit = ('hourangle, degree'))
                
                workingDict.update({'JName': row[1].text,
                                    'Period': float(row[2].text) / 1000,
                                    'Dispersion Measure': float(row[3].text),
                                    })


                
            workingDict.update({'Right Ascension': coord.ra.rad,
                                'Declination': coord.dec.rad,
                                'SkyCoord': copy.deepcopy(coord),
                                })

            # Edge case 'Originally thought to be a rrat'
            if not 'rrat' in row[8].text.lower() or 'originally' in row[8].text.lower():
                workingDict['Category'] = 'Pulsar'
            else:
                workingDict['Category'] = 'RRAT'
            
            newRows.append(workingDict)
    return newRows

def parseLOTAAS(url: str = "https://www.astron.nl/lotaas/index-full.html"):
    inputBS = getTables(url, 'lotaas.page')
    return __parseLOTAASBS(inputBS)