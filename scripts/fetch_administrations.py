import ssl
import requests

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.maximum_version = ssl.TLSVersion.TLSv1_3

context.set_ciphers(
    "ECDHE-ECDSA-AES128-GCM-SHA256:"
    "ECDHE-RSA-AES128-GCM-SHA256:"
    "ECDHE-ECDSA-AES256-GCM-SHA384:"
    "ECDHE-RSA-AES256-GCM-SHA384:"
    "ECDHE-ECDSA-CHACHA20-POLY1305:"
    "ECDHE-RSA-CHACHA20-POLY1305"
)

session = requests.Session()
adapter = requests.adapters.HTTPAdapter()
adapter.init_poolmanager(10, 10, ssl_context=context)
session.mount("https://", adapter)

def fix_id(admin_id: str, is_sbahn: bool) -> str:
    if len(admin_id) == 6 and not is_sbahn:
        return admin_id[0:4]
    else:
        return admin_id

def fetch_administration_map() -> dict[str, str]:
    response = session.get('https://www.bahn.de/web/api/reisebegleitung/wagenreihung/administrations')
    if response.status_code == 200:
        json_data = response.json()
        administration_map = {
            admin["operatorName"]: fix_id(admin["administrationID"], "S-Bahn" in admin["operatorName"])
            for admin in json_data.get("administrations", [])
        }
        return administration_map
    else:
        raise Exception(f"Failed to fetch data; HTTP status code: {response.status_code}")
