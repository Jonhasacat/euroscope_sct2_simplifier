import re
import shlex

"""
This script is intended to reduce an sct2 file to a size where 
it can be reliably loaded in EuroScope for training purposes.

The resulting file should not be used on the live network, 
as it may have inconsistencies or be missing certain information.

To use the script, simply update the COORD_ variables to correspond 
with the area you want to include in the output file.
In order to simplify the implementation, we only support a 
perfect square of filtering via a range of LAT and LONG coordinates.
"""

state: str = ""

COORD_LOW_LAT = "N38.36.40.508"
COORD_HIGH_LAT = "N49.29.27.327"
COORD_LOW_LONG = "W113.04.46.834"
COORD_HIGH_LONG = "W130.24.26.636"

ALWAYS_KEEP_STATES = [
    'INFO',
    'SID',
    'STAR'
]

SIMPLE_COORDINATE_FILTER_MAP = {
    'VOR': (3, 4),
    'NDB': (3, 4),
    'AIRPORT': (3, 4),
    'RUNWAY': (5, 6),
    'FIXES': (2, 3),
    'LOW AIRWAY': (2, 3),
    'HIGH AIRWAY': (2, 3),
    'LABELS': (2, 3),
}


def process_file(input_path, output_path):
    global state
    input_file = open(input_path)
    output_file = open(output_path, "w")
    was_last_line_blank = False
    for line in input_file:
        is_line_blank = False
        should_keep = True
        if line.startswith('['):
            # Should change state
            state = re.search(r"\[([A-Za-z0-9_\s*]+)\]", line).group(1)
        elif line.startswith(';') or re.match(r'^\s*$', line) or state == "":
            pass
        else:
            should_keep = should_keep_line(line)
        if should_keep and re.match(r'^\s*$', line):
            if was_last_line_blank:
                should_keep = False
            is_line_blank = True
        if should_keep:
            output_file.write(line)
            was_last_line_blank = is_line_blank


def simple_coordinate_check(line):
    global state
    clean_line = line.split(';')[0]
    parts = shlex.split(clean_line)
    cfg = SIMPLE_COORDINATE_FILTER_MAP.get(state)
    lat = parts[cfg[0]-1]
    long = parts[cfg[1]-1]
    return coordinate_in_boundary(lat, long)


def should_keep_line(line: str) -> bool:
    if state in ALWAYS_KEEP_STATES:
        return True
    if state in SIMPLE_COORDINATE_FILTER_MAP:
        return simple_coordinate_check(line)
    # Default to False, because we don't have a filter for that section yet
    return False


def coordinate_in_boundary(lat, long) -> bool:
    if compare_coordinates(lat, COORD_LOW_LAT) < 0:
        return False
    if compare_coordinates(lat, COORD_HIGH_LAT) > 0:
        return False
    if compare_coordinates(long, COORD_LOW_LONG) < 0:
        return False
    if compare_coordinates(long, COORD_HIGH_LONG) > 0:
        return False
    return True


def compare_coordinates(left, right) -> int:
    left_match = re.search(r"[NESW]([0-9]*)\.([0-9]*)\.([0-9]*)\.([0-9]*)", left)
    right_match = re.search(r"[NESW]([0-9]*)\.([0-9]*)\.([0-9]*)\.([0-9]*)", right)
    for group in range(1, 5):
        lg = int(left_match.group(group))
        rg = int(right_match.group(group))
        if lg > rg:
            return 1
        elif lg < rg:
            return -1
    return 0


if __name__ == '__main__':
    input_name = input("Input SCT2 file path: ")
    if not input_name.lower().endswith('.sct2'):
        raise Exception("Input file must be of type sct2")
    output_name = input("Output SCT2 file path: ")
    if not output_name.lower().endswith('.sct2'):
        raise Exception("Output file must be of type sct2")
    process_file(input_name, output_name)
