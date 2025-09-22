#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import subprocess
import sys

coverage_file = "mounted-output/coverage.xml"
base_branch = sys.argv[1] if len(sys.argv) > 1 else "develop"

git_diff_cmd = ["git", "diff", f"origin/{base_branch}...HEAD", "--unified=0", "--no-color", "--", "src/"]
diff_output = subprocess.run(git_diff_cmd, capture_output=True, text=True, check=True).stdout

changed_lines = {}
current_file = None
for line in diff_output.splitlines():
    if line.startswith("+++ b/"):
        current_file = line[6:]
        changed_lines[current_file] = set()
    elif line.startswith("@@") and current_file:
        parts = line.split(" ")
        for part in parts[2:3]:
            if part.startswith("+"):
                start, length = part[1:].split(",") if "," in part else (part[1:], "1")
                start, length = int(start), int(length)
                changed_lines[current_file].update(range(start, start + int(length)))

tree = ET.parse(coverage_file)
root = tree.getroot()
covered_lines = {}
for cls in root.findall(".//class"):
    filename = cls.attrib["filename"]
    hits = set()
    for line in cls.findall("lines/line"):
        if int(line.attrib.get("hits", "0")) > 0:
            hits.add(int(line.attrib["number"]))
    covered_lines[filename] = hits

total_changed = 0
total_covered = 0
for f, lines in changed_lines.items():
    cov_lines = covered_lines.get(f, set())
    total_changed += len(lines)
    total_covered += len(lines & cov_lines)

delta_coverage = (total_covered / total_changed * 100) if total_changed else 100.0
print(f"Delta coverage vs {base_branch}: {delta_coverage:.2f}%")
sys.exit(0)
