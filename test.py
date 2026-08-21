
import json
import glob

CHAR_DIR = "dataset/characters"

def main():
    files = sorted(glob.glob(f"{CHAR_DIR}/*.json"))
    if not files:
        print(f"No files found in {CHAR_DIR}/ -- check the path.")
        return

    print(f"Found {len(files)} character files. Inspecting a few known ones + one random sample.\n")

    known_5star = ["hu_tao", "hutao", "zhongli", "venti"]
    known_4star = ["xiangling", "bennett", "chongyun", "xingqiu"]

    checked = set()
    for f in files:
        stem = f.split("/")[-1].replace(".json", "").lower()
        if stem in known_5star or stem in known_4star:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            result = data.get("result", data)
            keys = list(result.keys()) if isinstance(result, dict) else "(not a dict)"
            print(f"--- {f} ---")
            print(f"  top-level keys: {keys}")
            for k, v in (result.items() if isinstance(result, dict) else []):
                if any(term in k.lower() for term in ["rar", "star", "quality"]):
                    print(f"  candidate field: {k} = {v}")
            print()
            checked.add(stem)

    if not checked:
        with open(files[0], encoding="utf-8") as fh:
            data = json.load(fh)
        result = data.get("result", data)
        print(f"None of the known-name files matched by filename. Showing {files[0]} instead:")
        print(json.dumps(result, indent=2)[:1500])

if __name__ == "__main__":
    main()