import csv
import re

from csv_utils import read_csv, create_map, parse_special_lines, parse_stroke_colors
from fetch_administrations import fetch_administration_map

full_line_id = re.compile(r"[0-9]-.*", re.IGNORECASE)

lines = read_csv("line-colors.csv")
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

with open('../ris-line-colors.csv', 'w', encoding='utf-8', newline="\n") as f:
    writer = csv.DictWriter(f, fieldnames=list(lines[0].keys()) + ['strokeColor'])
    writer.writeheader()
    writer.writerows(lines)
