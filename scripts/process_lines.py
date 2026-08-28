import re

from csv_utils import read_csv, write_csv, create_map, parse_special_lines, parse_stroke_colors
from fetch_administrations import fetch_administration_map

full_line_id = re.compile(r"[0-9]-.*", re.IGNORECASE)


def build_country_lines(colors_path: str, line_ids_path: str, columns: list[str]) -> list[dict[str, str]]:
    line_ids = {
        (row["shortOperatorName"], row["lineName"]): row["hafasLineId"]
        for row in read_csv(line_ids_path)
    }

    out = []
    for color in read_csv(colors_path):
        line_key = (color["shortOperatorName"], color["lineName"])
        if line_key not in line_ids:
            print(f"{colors_path}: no hafas line id for {line_key[0]} {line_key[1]}, skipping")
            continue
        line = {column: color.get(column, "") for column in columns}
        line["hafasLineId"] = line_ids[line_key]
        line["delfiAgencyID"] = color["GTFSAgencyID"]
        line["delfiAgencyName"] = color["GTFSAgencyName"]
        out.append(line)
    return out


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


lines = read_csv("line-colors.csv")
columns = list(lines[0].keys())

merge_lines(lines, build_country_lines("line-colors-AT.csv", "hafas-line-ids-AT.csv", columns))

operators = create_map(read_csv("hafas-operators.csv"))
manual_operators = create_map(read_csv("ris-operators.csv"))
special_lines = parse_special_lines("special-lines.csv")
stroke_colors = parse_stroke_colors("stroke-colors.csv")
administrations = fetch_administration_map()

relevant_operators = (
    operator_name for row in lines if
    (operator_name := row["hafasOperatorCode"]) and
    not re.match(full_line_id, row["hafasLineId"])
)

relevant_operators_with_name = {}

for relevant_operator in relevant_operators:
    name = operators[relevant_operator]
    matching_id = manual_operators[relevant_operator] if relevant_operator in manual_operators else None
    matching_id = administrations[name] if name in administrations and matching_id is None else matching_id
    if matching_id is None:
        continue
    relevant_operators_with_name[relevant_operator] = matching_id

for line in lines:
    operator_id = line["hafasOperatorCode"]
    if operator_id in relevant_operators_with_name:
        line["risOperatorCode"] = relevant_operators_with_name[operator_id]
    composite_line_key = (line["hafasOperatorCode"], line["hafasLineId"])
    if composite_line_key in special_lines.keys():
        line["risOperatorCode"] = special_lines[composite_line_key]
    if composite_line_key in stroke_colors.keys():
        line["strokeColor"] = stroke_colors[composite_line_key]

write_csv("ris-line-colors.csv", columns + ['risOperatorCode', 'strokeColor'], lines)
