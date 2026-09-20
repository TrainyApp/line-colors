import sys

from csv_utils import read_csv

sources = [
    ("line-colors.csv", "ris-line-ids.csv"),
    ("line-colors-AT.csv", "hafas-line-ids-AT.csv"),
    ("line-colors-LU.csv", "hafas-line-ids-LU.csv"),
]


def line_keys(path: str) -> list[tuple[str, str]]:
    return [(row["shortOperatorName"], row["lineName"]) for row in read_csv(path)]


def report_duplicates(path: str, keys: list[tuple[str, str]]) -> int:
    duplicates = [line_key for index, line_key in enumerate(keys) if line_key in keys[:index]]
    for line_key in dict.fromkeys(duplicates):
        print(f"{path}: duplicate line {line_key[0]} {line_key[1]}")
    return len(duplicates)


def report(colors_path: str, line_ids_path: str) -> int:
    colors = line_keys(colors_path)
    line_ids = line_keys(line_ids_path)
    mapped = set(line_ids)

    missing = [line_key for line_key in dict.fromkeys(colors) if line_key not in mapped]
    for line_key in missing:
        print(f"{colors_path}: no hafas line id for {line_key[0]} {line_key[1]}")

    unused = [line_key for line_key in dict.fromkeys(line_ids) if line_key not in set(colors)]
    for line_key in unused:
        print(f"{line_ids_path}: no line color for {line_key[0]} {line_key[1]}")

    duplicates = report_duplicates(colors_path, colors) + report_duplicates(line_ids_path, line_ids)

    print(f"{colors_path}: {len(missing)} of {len(set(colors))} lines without hafas line id, "
          f"{len(unused)} unused entries in {line_ids_path}, {duplicates} duplicate lines")
    return len(missing) + duplicates


problem_count = sum(report(colors_path, line_ids_path) for colors_path, line_ids_path in sources)

if problem_count:
    sys.exit(1)
