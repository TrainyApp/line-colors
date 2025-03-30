import csv
import re

from csv_utils import read_csv, create_map, parse_special_lines
from fetch_administrations import fetch_administration_map

standalone_line_mapper = re.compile(r"rb|re|mex-\\d+", re.IGNORECASE)

lines = read_csv("line-colors.csv")
operators = create_map(read_csv("hafas-operators.csv"))
manual_operators = create_map(read_csv("ris-operators.csv"))
special_lines = parse_special_lines("special-lines.csv")
administrations = fetch_administration_map()

relevant_operators = (
    operator_name for row in lines if
    (operator_name := row["hafasOperatorCode"]) and
    re.match(standalone_line_mapper, row["hafasLineId"])
)

relevant_operators_with_name = {}

for relevant_operator in relevant_operators:
    name = operators[relevant_operator]
    matching_id = administrations[name] if name in administrations else None
    matching_id = manual_operators[relevant_operator] if relevant_operator in manual_operators else matching_id
    if matching_id is None:
        continue
    relevant_operators_with_name[relevant_operator] = matching_id

for line in lines:
    operator_id = line["hafasOperatorCode"]
    if operator_id in relevant_operators_with_name:
        line["risOperatorCode"] = relevant_operators_with_name[operator_id]
    composite_line_key = (line["hafasLineId"], line["hafasOperatorCode"])
    if composite_line_key in special_lines:
        line["risOperatorCode"] = special_lines[composite_line_key]

with open('../ris-line-colors.csv', 'w', encoding='utf-8', newline="\n") as f:
    writer = csv.DictWriter(f, fieldnames=list(lines[0].keys()) + ['risOperatorCode'])
    writer.writeheader()
    writer.writerows(lines)
