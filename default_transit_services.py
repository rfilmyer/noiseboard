from collections import OrderedDict

muni = {"name": "MUNI Arrivals", "agency": "sf-muni",
        "stops": OrderedDict([('15553', 'NB'), ('13338', 'WB'), ('15554', 'SB')])}
caltrain = {"name": "Caltrain@22nd", "agency": "caltrain", "stops": OrderedDict([('70022', 'SB')])}
bart = {"name": "BART", "agency": "bart", "stops": OrderedDict([('10', ''), ('99', '')]),
        "mapping": {"1561": "SFO/M", "385": "Daly", "389": "Daly", "720": "SFO",
                    "1230": "Pitt", "736": "Frmt", "920": "Dubl",
                    "764": "Mbrae", "243": "Daly", "722": "SFO", "917": "Frmt", 
                    "1351": "Rich", "1009": "Rich", "237": "Rich"}}