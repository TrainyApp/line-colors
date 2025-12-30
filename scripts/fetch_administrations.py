import requests

def fix_id(admin_id: str, is_sbahn: bool) -> str:
    if len(admin_id) == 6 and not is_sbahn:
        return admin_id[0:4]
    else:
        return admin_id

def fetch_administration_map() -> dict[str, str]:
    response = requests.get('https://www.bahn.de/web/api/reisebegleitung/wagenreihung/administrations')
    if response.status_code == 200:
        json_data = response.json()
        administration_map = {
            admin["operatorName"]: fix_id(admin["administrationID"], "S-Bahn" in admin["operatorName"])
            for admin in json_data.get("administrations", [])
        }
        return administration_map
    else:
        raise Exception(f"Failed to fetch data; HTTP status code: {response.status_code}")
