import re
from typing import Optional

from csv_utils import read_csv, write_csv, create_map, parse_ris_operators, parse_special_lines, parse_stroke_colors
from fetch_administrations import fetch_administration_map

full_line_id = re.compile(r"[0-9]-.*", re.IGNORECASE)


def build_lines(colors_path: str, line_ids_path: str, columns: list[str],
                agency_id_column: str, agency_name_column: str) -> list[dict[str, str]]:
    line_ids: dict[tuple[str, str], list[str]] = {}
    for row in read_csv(line_ids_path):
        ids = line_ids.setdefault((row["shortOperatorName"], row["lineName"]), [])
        if row["hafasLineId"] not in ids:
            ids.append(row["hafasLineId"])

    out = []
    for color in read_csv(colors_path):
        line_key = (color["shortOperatorName"], color["lineName"])
        if line_key not in line_ids:
            print(f"{colors_path}: no hafas line id for {line_key[0]} {line_key[1]}, skipping")
            continue
        for hafas_line_id in line_ids[line_key]:
            line = {column: color.get(column, "") for column in columns}
            line["hafasOperatorCode"] = line["hafasOperatorCode"] or line["shortOperatorName"]
            line["hafasLineId"] = hafas_line_id
            line["delfiAgencyID"] = color[agency_id_column]
            line["delfiAgencyName"] = color[agency_name_column]
            out.append(line)
    return out


def build_country_lines(colors_path: str, line_ids_path: str, columns: list[str]) -> list[dict[str, str]]:
    return build_lines(colors_path, line_ids_path, columns, "GTFSAgencyID", "GTFSAgencyName")


def insertion_index(lines: list[dict[str, str]], operator: str) -> int:
    for index in reversed(range(len(lines))):
        if lines[index]["shortOperatorName"] == operator:
            return index + 1
    for index, line in enumerate(lines):
        if line["shortOperatorName"] > operator:
            return index
    return len(lines)


def merge_lines(lines: list[dict[str, str]], new_lines: list[dict[str, str]]) -> None:
    known_keys = {(line["shortOperatorName"], line["lineName"], line["hafasLineId"]) for line in lines}
    for new_line in new_lines:
        line_key = (new_line["shortOperatorName"], new_line["lineName"], new_line["hafasLineId"])
        if line_key in known_keys:
            continue
        known_keys.add(line_key)
        lines.insert(insertion_index(lines, new_line["shortOperatorName"]), new_line)


columns = list(read_csv("line-colors.csv")[0].keys())

lines = build_lines("line-colors.csv", "ris-line-ids.csv", columns, "delfiAgencyID", "delfiAgencyName")

merge_lines(lines, build_country_lines("line-colors-AT.csv", "hafas-line-ids-AT.csv", columns))
merge_lines(lines, build_country_lines("line-colors-LU.csv", "hafas-line-ids-LU.csv", columns))

operators = create_map(read_csv("hafas-operators.csv"))
manual_operators = parse_ris_operators("ris-operators.csv")
special_lines = parse_special_lines("special-lines.csv")
stroke_colors = parse_stroke_colors("stroke-colors.csv")
administrations = fetch_administration_map()

def find_ris_operator_code(hafas_operator: str, short_operator_name: str) -> Optional[str]:
    exact_key = (hafas_operator, short_operator_name)
    if exact_key in manual_operators:
        return manual_operators[exact_key]
    if (hafas_operator, "") in manual_operators:
        return manual_operators[hafas_operator, ""]
    name = operators.get(hafas_operator, hafas_operator)
    return administrations.get(name)


for line in lines:
    operator_id = line["hafasOperatorCode"]
    if operator_id and not re.match(full_line_id, line["hafasLineId"]):
        ris_operator_code = find_ris_operator_code(operator_id, line["shortOperatorName"])
        if ris_operator_code is not None:
            line["risOperatorCode"] = ris_operator_code
    composite_line_key = (line["hafasOperatorCode"], line["hafasLineId"])
    if composite_line_key in special_lines.keys():
        line["risOperatorCode"] = special_lines[composite_line_key]
    if composite_line_key in stroke_colors.keys():
        line["strokeColor"] = stroke_colors[composite_line_key]

write_csv("ris-line-colors.csv", columns + ['risOperatorCode', 'strokeColor'], lines)
