import argparse
import re
import sys
from collections import defaultdict

from csv_utils import read_csv

train_line = re.compile(r"(RB|RE|IRE|RS|S).?[0-9]", re.IGNORECASE)
full_line_id = re.compile(r"[0-9]-.*", re.IGNORECASE)

parser = argparse.ArgumentParser(description="Find lines in ris-line-colors.csv that cannot be matched")
train_filter = parser.add_mutually_exclusive_group()
train_filter.add_argument("--trains", action="store_true", help="only check train lines (RB, RE, IRE, RS, S)")
train_filter.add_argument("--no-trains", action="store_true", help="only check non-train lines")
args = parser.parse_args()


def is_train(line: dict[str, str]) -> bool:
    return bool(train_line.match(line["lineName"]))


def is_missing_id(line: dict[str, str]) -> bool:
    if not line["hafasLineId"]:
        return True
    # trains are matched via risOperatorCode, unless the hafasLineId already contains the operator
    return is_train(line) and not line["risOperatorCode"] and bool(train_line.match((line["hafasLineId"])))


lines = read_csv("ris-line-colors.csv")
if args.trains:
    lines = [line for line in lines if is_train(line)]
elif args.no_trains:
    lines = [line for line in lines if not is_train(line)]

missing = defaultdict(list)
for line in lines:
    if is_missing_id(line):
        missing[line["shortOperatorName"], line["hafasOperatorCode"]].append(line)

for (operator, hafas_operator), operator_lines in sorted(missing.items()):
    hafas_operator = f" (hafasOperatorCode {hafas_operator})" if hafas_operator else ""
    names = ", ".join(line["lineName"] for line in operator_lines)
    print(f"{operator}{hafas_operator}: {len(operator_lines)} lines without id: {names}")

missing_count = sum(len(operator_lines) for operator_lines in missing.values())
print(f"ris-line-colors.csv: {missing_count} of {len(lines)} lines without hafasLineId or risOperatorCode "
      f"({len(missing)} operators)")

if missing_count:
    sys.exit(1)
