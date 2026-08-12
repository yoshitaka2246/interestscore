import csv
from collections import defaultdict

INPUT_CSV = "tracks_summary.csv"

# person_id(手動で書き込んだ人物ラベル)ごとに使われたtrack_idを集める
person_to_ids = defaultdict(set)

with open(INPUT_CSV, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        person_id = row["person_id"].strip()
        if person_id == "" or person_id.upper() == "NG":
            continue
        person_to_ids[person_id].add(int(row["track_id"]))

# 1人物あたりのIDSW = 使われたtrack_idの種類数 - 1
total_idsw = 0

print("person_id : track_id一覧 -> IDSW")
for person_id, ids in sorted(person_to_ids.items()):
    idsw = len(ids) - 1
    total_idsw += idsw
    print(f"{person_id} : {sorted(ids)} -> {idsw}")

print(f"\n検出人数: {len(person_to_ids)}")
print(f"合計IDSW: {total_idsw}")
