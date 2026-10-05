from pydantic import BaseModel
from datetime import datetime, date

class Historiek(BaseModel):
    historiek_id: int
    tijdstip: datetime
    value: float
    device_id: int
    vat_id: int

class Historieken(BaseModel):
    history: list[Historiek]

class DTOHistoriek(BaseModel):
    value: float
    device_id: int
    vat_id: int

class Vat(BaseModel):
    vat_id: int
    naam: str
    
class Vaten(BaseModel):
    vaten: list[Vat]
        
class DTOVat(BaseModel):
    naam: str

# class DTOTijdsPeriode(BaseModel):
#     startdatum: date
#     einddatum: date

class VatMetTijd(BaseModel):
    vat_id: int
    naam: str
    aanmaakdatum: datetime
    
class VatenMetTijd(BaseModel):
    vaten: list[VatMetTijd]

class Config(BaseModel):
    config_id: int
    naam: str
    value: float
    sensor_id: int

class ConfigList(BaseModel):
    settings: list[Config]

class DTOConfigValues(BaseModel):
    ALARM_gewicht: float
    ALARM_temp: float
    ALARM_druk: float
    tarragewicht: float
    
    
    
    
    
    
# class DTOLampStatus(BaseModel):
#     nieuwe_status: int

# class LampStatus(BaseModel):
#     lamp: int
#     status: int