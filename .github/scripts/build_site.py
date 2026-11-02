"""公開用のサイトを _site に組み立てる。

「〔本名〕」「〔ふりがな〕」を環境変数 REAL_NAME / REAL_NAME_KANA の値に置き換える。
HTML のコメントは公開用のファイルから取り除く。
未記入の印（〔…〕や class="todo"）が1つでも残っていたら、公開せずに止める。
手元で仮の名前を使って見た目を確かめるときは --preview を付ける（印が残っていても止めない）。
"""
import argparse
import os
import pathlib
import re
import shutil
import sys

PLACEHOLDERS = {"〔本名〕": "REAL_NAME", "〔ふりがな〕": "REAL_NAME_KANA"}
TEXT_SUFFIXES = {".html", ".xml", ".txt", ".css", ".json"}
EXCLUDE = {".git", ".github", "_site", ".claude"}
UNSAFE = re.compile(r'[<>&"\\]')
LEFTOVER = re.compile(r'〔[^〕]*〕|class="todo"')
COMMENT = re.compile(r"<!--.*?-->", re.S)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default=".")
    parser.add_argument("--out", default="_site")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    values = {}
    for mark, env in PLACEHOLDERS.items():
        value = os.environ.get(env, "").strip()
        if not value:
            sys.exit(f"{env} が設定されていません。GitHub のリポジトリ設定でシークレットを登録してください。")
        if UNSAFE.search(value):
            sys.exit(f"{env} に使えない記号（< > & \" \\）が含まれています。")
        values[mark] = value

    src = pathlib.Path(args.src).resolve()
    out = pathlib.Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)

    replaced = 0
    leftovers = []
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if rel.parts[0] in EXCLUDE or path.is_dir():
            continue
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix not in TEXT_SUFFIXES:
            shutil.copy2(path, dest)
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            text = COMMENT.sub("", text)
        for mark, value in values.items():
            replaced += text.count(mark)
            text = text.replace(mark, value)
        leftovers += [f"{rel.as_posix()}: {m.group(0)}" for m in LEFTOVER.finditer(text)]
        dest.write_text(text, encoding="utf-8", newline="\n")

    print(f"本名・ふりがなを {replaced} か所に差し込みました。")
    if leftovers:
        print(f"未記入の印が {len(leftovers)} か所残っています:")
        for item in leftovers:
            print(f"  {item}")
        if not args.preview:
            sys.exit("未記入の印が残っているため、公開を中止しました。")


if __name__ == "__main__":
    main()
