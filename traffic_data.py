import xml.etree.ElementTree as ET
import requests
import json
from datetime import datetime

# Lista de regiones con sus respectivas URLs de archivos XML
REGIONS = {
    "Cataluña": "http://infocar.dgt.es/datex2/sct/SituationPublication/all/content.xml",
    "País Vasco": "http://infocar.dgt.es/datex2/dt-gv/SituationPublication/all/content.xml",
    "Resto España": "http://infocar.dgt.es/datex2/dgt/SituationPublication/all/content.xml"
}

# Definir el espacio de nombres para el XML
NS = {'_0': 'http://datex2.eu/schema/1_0/1_0'}

# Traducción de tipos de incidentes
INCIDENT_TYPE_TRANSLATIONS = {
    "damagedVehicle": "Vehículo Averiado",
    "roadClosed": "Corte Total",
    "restrictions": "Restricciones",
    "narrowLanes": "Carriles Estrechos",
    "flooding": "Inundación",
    "vehicleStuck": "Vehiculo Parado",
    "both": "Ambos Sentidos",
    "negative": "Decreciente",
    "positive": "Creciente",
    "useUnderSpecifiedRestrictions": "Uso con restricciones",
    "congested": "Congestionada",
    "freeFlow": "Sin retención",
    "constructionWork": "Obras",
    "impossible": "Imposible circular",
    "objectOnTheRoad": "Objeto en Calzada",
    "heavy": "Retención",
    "vehicleOnFire": "Vehiculo en llamas",
    "narrowLanes": "Estrechamiento de carriles",
    "intermittentShortTermClosures": "Cortes intermitentes",
    "laneClosures": "Cierre de algún carril",
    "rockfalls": "Caida de piedras",
    "trafficContolInOperation": "Itinerario alternativo",
    "laneOrCarriagewayClosed": "Arcen cerrado"
    
}

# Función para traducir tipos de incidentes
def translate_incident_type(value):
    return INCIDENT_TYPE_TRANSLATIONS.get(value, value)

# Función para convertir la fecha y hora a un formato más bonito
def format_datetime(datetime_str):
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%d/%m/%Y - %H:%M:%S")
    except ValueError:
        return datetime_str

# Función para procesar un archivo XML desde una URL y extraer los datos necesarios
def process_xml_from_url(url, region_name, all_incidents):
    try:
        # Descargar el archivo XML desde la URL
        response = requests.get(url)
        response.raise_for_status()

        # Parsear el contenido XML
        root = ET.fromstring(response.content)

        # Procesar los incidentes en el archivo XML
        for situation in root.findall(".//_0:situation", NS):
            situation_record = situation.find(".//_0:situationRecord", NS)

            if situation_record is not None:
                description = []

                # Extraer la fecha de creación
                creation_time = situation_record.find(".//_0:situationRecordCreationTime", NS)
                if creation_time is not None:
                    description.append(f"<b>Fecha de Creación:</b> {format_datetime(creation_time.text)}")

                # Extraer el tipo de obstrucción
                obstructionType = situation_record.find(".//_0:obstructionType", NS)
                if obstructionType is not None:
                    obstruction_type = translate_incident_type(obstructionType.text)
                    description.append(f"<b>Tipo de Obstrucción:</b> {obstruction_type}")
                
                # Extraer el tipo de obstrucción ambiental
                environmental_obstruction = situation_record.find(".//_0:environmentalObstructionType", NS)
                if environmental_obstruction is not None:
                    obstruction_type = translate_incident_type(environmental_obstruction.text)
                    description.append(f"<b>Tipo de Obstrucción:</b> {obstruction_type}")

                # Extraer el tipo de incidente
                vehicle_obstruction_type = situation_record.find(".//_0:vehicleObstructionType", NS)
                if vehicle_obstruction_type is not None:
                    incident_type  = translate_incident_type(vehicle_obstruction_type.text)
                    description.append(f"<b>Tipo de Incidente:</b> {incident_type}")

                # Extraer la construccion
                construction = situation_record.find(".//_0:constructionWorkType", NS)
                if construction is not None:
                    construction = translate_incident_type(construction.text)
                    description.append(f"<b>Tipo de Incidente </b> {construction}")

                # Extraer la dirección
                direction = situation_record.find(".//_0:directionRelative", NS)
                if direction is not None:
                    direction = translate_incident_type(direction.text)
                    description.append(f"<b>Dirección:</b> {direction}")

                # Extraer aviso
                lane = situation_record.find(".//_0:networkManagementType", NS)
                if lane is not None and lane.text:
                    warning_translated = translate_incident_type(lane.text)
                    description.append(f"<b>Aviso: </b> {warning_translated}")

                # Extraer impacto
                impact = situation_record.find(".//_0:impactOnTraffic", NS)
                if impact is not None:
                    impact = translate_incident_type(impact.text)
                    description.append(f"<b>Impacto: </b> {impact}")
                
                # Extraer la carretera
                road_number = situation_record.find(".//_0:roadNumber", NS)
                if road_number is not None:
                    description.append(f"<b>Carretera:</b> {road_number.text}")

                # Extraer el punto kilométrico
                point_km = situation_record.find(".//_0:referencePointDistance", NS)
                if point_km is not None:
                    description.append(f"<b>Punto Kilométrico:</b> {float(point_km.text) / 1000:.1f} km")

                # Extraer la ubicación
                location = situation_record.find(".//_0:pointCoordinates", NS)
                if location is not None:
                    latitude = location.find(".//_0:latitude", NS)
                    longitude = location.find(".//_0:longitude", NS)
                    if latitude is not None and longitude is not None:
                        coordinates = [float(longitude.text), float(latitude.text)]

                        # Crear el incidente en formato GeoJSON
                        incident = {
                            "type": "Feature",
                            "properties": {
                                "description": "<br>".join(description)
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": coordinates
                            }
                        }
                        all_incidents.append(incident)

    except Exception as e:
        print(f"Error procesando {region_name} desde {url}: {e}")

# Lista para almacenar todos los incidentes
all_incidents = []

# Procesar todos los archivos XML de las regiones especificadas
for region_name, url in REGIONS.items():
    print(f"\nProcesando región: {region_name} desde {url}")
    process_xml_from_url(url, region_name, all_incidents)

# Crear el archivo GeoJSON con todos los incidentes
geojson_data = {
    "type": "FeatureCollection",
    "features": all_incidents
}

# Guardar el archivo GeoJSON
geojson_file = "traffic_data.geojson"
with open(geojson_file, "w") as f:
    json.dump(geojson_data, f, indent=2, ensure_ascii=False)

print(f"\nArchivo GeoJSON global generado con éxito: {geojson_file}")
