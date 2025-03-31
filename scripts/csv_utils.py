import csv
from pathlib import Path

def read_csv(path: str) -> list[dict]:
    line_text = Path(f'../{path}').read_text(encoding="utf-8")
    return list(csv.DictReader(line_text.splitlines()))


def parse_special_lines(path: str) -> dict[(str, str), str]:
    out = {}
    for special_line in read_csv(path):
        if 'risOperatorCode' in special_line.keys():
            out[special_line["hafasOperatorCode"], special_line["hafasLineId"]] = special_line["risOperatorCode"]
    return out

def create_map(array: list[dict[str, str]]) -> dict[str, str]:
    out = {}
    for item in array:
        iterator = iter(item.items())
        _, key = next(iterator)
        _, value = next(iterator)
        out[key] = value
    return out
