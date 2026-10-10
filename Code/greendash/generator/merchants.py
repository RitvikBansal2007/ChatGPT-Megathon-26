import numpy as np
from dataclasses import dataclass

@dataclass(frozen=True)
class MerchantTemplate:
    template_id: str
    true_category: str
    names: tuple
    amount_range: tuple
    ambiguous: bool = False

TEMPLATES = [
    # Fuel (9)
    MerchantTemplate("FUEL_01", "Fuel", ("SHELL", "SHELL SERVICE STN"), (20, 90)),
    MerchantTemplate("FUEL_02", "Fuel", ("BP CONNECT", "BP"), (20, 90)),
    MerchantTemplate("FUEL_03", "Fuel", ("TEXACO", "TEXACO GARAGE"), (15, 80)),
    MerchantTemplate("FUEL_04", "Fuel", ("ESSO", "ESSO STATION"), (20, 85)),
    MerchantTemplate("FUEL_05", "Fuel", ("JET", "JET PETROL"), (15, 75)),
    MerchantTemplate("FUEL_06", "Fuel", ("ASDA PETROL", "ASDA FUEL"), (25, 70)),
    MerchantTemplate("FUEL_EV_01", "Fuel", ("EV CHARGE POINT", "RAPID CHARGE HUB"), (5, 30)),
    MerchantTemplate("FUEL_EV_02", "Fuel", ("IONITY CHARGING", "GRIDSERVE EV"), (10, 45)),
    MerchantTemplate("FUEL_EV_03", "Fuel", ("POD POINT", "PODPOINT CHARGE"), (2, 25)),
    
    # Electricity (6)
    MerchantTemplate("ELEC_01", "Electricity", ("ELECTRICITY SUPPLY DD", "POWER CO ELECTRICITY"), (30, 140)),
    MerchantTemplate("ELEC_02", "Electricity", ("OVO ENERGY ELEC", "OVO ELEC"), (40, 150)),
    MerchantTemplate("ELEC_03", "Electricity", ("E.ON NEXT ELEC", "EON ELECTRICITY"), (35, 130)),
    MerchantTemplate("ELEC_04", "Electricity", ("EDF ENERGY ELEC", "EDF ELEC DD"), (30, 140)),
    MerchantTemplate("ELEC_05", "Electricity", ("SCOTTISH POWER ELEC", "SP ELEC"), (45, 160)),
    MerchantTemplate("ELEC_06", "Electricity", ("BULB ELECTRICITY", "BULB ELEC"), (25, 120)),

    # Gas (6)
    MerchantTemplate("GAS_01", "Gas", ("GAS SUPPLY DD", "HOME GAS CO"), (25, 160)),
    MerchantTemplate("GAS_02", "Gas", ("BRITISH GAS GAS", "BG GAS DD"), (30, 170)),
    MerchantTemplate("GAS_03", "Gas", ("E.ON NEXT GAS", "EON GAS"), (25, 140)),
    MerchantTemplate("GAS_04", "Gas", ("EDF ENERGY GAS", "EDF GAS DD"), (20, 150)),
    MerchantTemplate("GAS_05", "Gas", ("OVO ENERGY GAS", "OVO GAS"), (35, 180)),
    MerchantTemplate("GAS_06", "Gas", ("SCOTTISH POWER GAS", "SP GAS"), (40, 190)),

    # Public Transport (7)
    MerchantTemplate("PT_01", "Public Transport", ("RAIL TICKET", "CITY BUS", "METRO TRAVEL"), (2, 80)),
    MerchantTemplate("PT_02", "Public Transport", ("TFL TRAVEL CHARGE", "TFL OYSTER"), (1.75, 20)),
    MerchantTemplate("PT_03", "Public Transport", ("NATIONAL RAIL", "TRAINLINE"), (10, 150)),
    MerchantTemplate("PT_04", "Public Transport", ("FIRST BUS", "STAGECOACH BUS"), (2, 10)),
    MerchantTemplate("PT_05", "Public Transport", ("TRAMLINK", "METROLINK TRAM"), (3, 8)),
    MerchantTemplate("PT_06", "Public Transport", ("LNER TICKETS", "AVANTI WEST COAST"), (20, 200)),
    MerchantTemplate("PT_07", "Public Transport", ("ARRIVA BUS", "CROSSCOUNTRY"), (4, 60)),

    # Home Improvement (7)
    MerchantTemplate("HOME_01", "Home Improvement", ("LOFT INSULATION CO", "DIY WAREHOUSE", "WINDOW AND GLAZING"), (20, 3000)),
    MerchantTemplate("HOME_02", "Home Improvement", ("B&Q DIY", "B&Q RETAIL"), (15, 400)),
    MerchantTemplate("HOME_03", "Home Improvement", ("WICKES", "WICKES STORE"), (25, 500)),
    MerchantTemplate("HOME_04", "Home Improvement", ("HOMESPACE INSULATION", "WARM HOME SOL"), (200, 1500)),
    MerchantTemplate("HOME_05", "Home Improvement", ("SOLAR PANELS UK", "SUNERGY INSTALL"), (500, 4500)),
    MerchantTemplate("HOME_06", "Home Improvement", ("SCREWFIX", "TOOLSTATION"), (10, 150)),
    MerchantTemplate("HOME_07", "Home Improvement", ("HOMEBASE", "HOMEBASE LTD"), (30, 250)),

    # Automotive (7)
    MerchantTemplate("AUTO_01", "Automotive", ("QUICK FIT TYRES", "MOT TEST CENTRE", "AUTO SERVICE"), (30, 600)),
    MerchantTemplate("AUTO_02", "Automotive", ("HALFORDS", "HALFORDS AUTOCENTRE"), (10, 250)),
    MerchantTemplate("AUTO_03", "Automotive", ("NCP PARKING", "CITY PARKING"), (3, 35)),
    MerchantTemplate("AUTO_04", "Automotive", ("KWIK FIT", "TYRES AND EXHAUSTS"), (50, 450)),
    MerchantTemplate("AUTO_05", "Automotive", ("EURO CAR PARTS", "CAR SPARES"), (15, 120)),
    MerchantTemplate("AUTO_06", "Automotive", ("ARNOLD CLARK SERVICE", "FORD DEALER MOT"), (150, 800)),
    MerchantTemplate("AUTO_07", "Automotive", ("LOCAL GARAGE", "MOT & REPAIRS"), (40, 500)),

    # Utilities (8)
    MerchantTemplate("UTIL_01", "Utilities", ("DUAL FUEL ENERGY", "WATER SERVICES"), (40, 220)),
    MerchantTemplate("UTIL_02", "Utilities", ("THAMES WATER", "SEVERN TRENT WATER"), (20, 100)),
    MerchantTemplate("UTIL_03", "Utilities", ("OCTOPUS ENERGY", "OCTOPUS DD"), (50, 250)),
    MerchantTemplate("UTIL_04", "Utilities", ("BRITISH GAS DUAL", "BG ENERGY DD"), (60, 300)),
    MerchantTemplate("UTIL_05", "Utilities", ("UNITED UTILITIES", "YORKSHIRE WATER"), (15, 85)),
    MerchantTemplate("UTIL_06", "Utilities", ("VIRGIN MEDIA", "BT GROUP BILL"), (30, 90)),
    MerchantTemplate("UTIL_07", "Utilities", ("SKY SUBSC", "COUNCIL TAX"), (50, 180)),
    MerchantTemplate("UTIL_08", "Utilities", ("EE MOBILE DD", "O2 MOBILE"), (10, 60)),

    # Other (13)
    MerchantTemplate("OTHER_01", "Other", ("UBER TRIP", "BOLT RIDE"), (6, 40)),
    MerchantTemplate("OTHER_02", "Other", ("TESCO STORES", "TESCO EXTRA"), (5, 120)),
    MerchantTemplate("OTHER_03", "Other", ("SAINSBURYS", "SAINSBURYS LOCAL"), (3, 90)),
    MerchantTemplate("OTHER_04", "Other", ("AMAZON PRIME", "AMAZON UK MARKET"), (2, 80)),
    MerchantTemplate("OTHER_05", "Other", ("STARBUCKS", "COSTA COFFEE"), (3, 15)),
    MerchantTemplate("OTHER_06", "Other", ("MCDONALDS", "KFC", "GREGGS"), (2, 20)),
    MerchantTemplate("OTHER_07", "Other", ("APPLE COM BILL", "NETFLIX"), (8, 25)),
    MerchantTemplate("OTHER_08", "Other", ("BOOTS PHARMACY", "SUPERDRUG"), (5, 45)),
    MerchantTemplate("OTHER_09", "Other", ("PRET A MANGER", "CAFE NERO"), (4, 12)),
    MerchantTemplate("OTHER_10", "Other", ("DELIVEROO", "UBER EATS"), (12, 35)),
    MerchantTemplate("OTHER_11", "Other", ("JD SPORTS", "ASOS"), (25, 150)),
    MerchantTemplate("OTHER_12", "Other", ("CINEMA", "THEATRE TICKETS"), (15, 50)),
    MerchantTemplate("OTHER_13", "Other", ("GYM MEMBERSHIP", "LEISURE CENTRE"), (20, 80)),

    # Ambiguous (2) -> exactly 2/65 = ~3%
    MerchantTemplate("SUPER_FUEL", "Fuel", ("SUPERMARKET FUEL STATION", "SAINSBURYS PFS"), (20, 80), ambiguous=True),
    MerchantTemplate("SUPER_GROC", "Other", ("SUPERMARKET", "SAINSBURYS STORE"), (8, 120), ambiguous=True),
]

PREFIXES = ["", "", "CARD PAYMENT TO ", "POS ", "SQ *", "PAYPAL *", "DD ", "VIS "]
TOWNS = ["LONDON", "LEEDS", "BRISTOL", "GLASGOW", "CARDIFF", "MANCHESTER", ""]

def noisy_string(tpl: MerchantTemplate, rng: np.random.Generator) -> str:
    name = str(rng.choice(tpl.names))
    s = str(rng.choice(PREFIXES)) + name
    if rng.random() < 0.5:
        # max 3 digits to avoid flagging as PII (card/account length)
        s += f" {int(rng.integers(1, 999)):03d}"
    town = str(rng.choice(TOWNS))
    if town:
        s += f" {town}"
    r = rng.random()
    if r < 0.2:
        s = s.lower()
    elif r < 0.35:
        s = s.title()
    return s.strip()
