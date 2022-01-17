import pandas as pd
from pandas.io import parsers
from funcs import read_file
from pathlib import Path
import csv
import json
from tqdm import tqdm
import gzip


def extract_wikipedia_description(text):
    return text.split("\n\n")[0]


def wikipedia_description_from_path(path):
    return extract_wikipedia_description(read_file(path))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("good_pages_path")
    parser.add_argument("cleaned_pages_path")
    parser.add_argument("wikidata_path")
    parser.add_argument("output_corpus_path")
    parser.add_argument("output_entities_path")

    args = parser.parse_args()

    with open(args.good_pages_path, "rt", encoding="UTF-8") as f:
        good_pages_list = set(f.read().split("\n")).difference("")

    # Columns: qid, title, path, url
    title2text = {}
    title2qid = {}
    frwiki_cols = {"qid": [], "title": [],
                   "url": [], "wikipedia_description": []}
    with open(args.cleaned_pages_path, "rt", encoding="UTF-8") as f:
        for line in f:
            item = json.loads(line)
            title = item["title"]
            title2qid[title] = item["qid"]
            if title in good_pages_list:
                title2text[title] = item["text"]

            frwiki_cols["qid"].append(item["qid"])
            frwiki_cols["title"].append(title)
            frwiki_cols["url"].append(item["url"])
            frwiki_cols["wikipedia_description"].append(
                extract_wikipedia_description(item["text"]))
    frwiki = pd.DataFrame(frwiki_cols)
    del frwiki_cols

    # Columns: qid, title, wikidata_description, label, aliases, type
    wikidata = pd.read_csv(args.wikidata_path, dtype=str,
                           index_col="qid", na_filter=False)

    output_corpus_path = Path(args.output_corpus_path)
    output_entities_path = Path(args.output_entities_path)

    merged = pd.merge(frwiki, wikidata, how="left",
                      left_on="qid", right_index=True)
    del frwiki
    del wikidata

    with gzip.open(output_corpus_path, "wt", encoding="UTF-8") as outfile:
        for title in good_pages_list.intersection(title2qid.keys()):
            item = {
                "title": title,
                "qid": title2qid[title],
                "text": title2text[title],
            }
            json.dump(item, outfile)
            outfile.write("\n")

    with gzip.open(output_entities_path, "wt", encoding="UTF-8") as outfile:
        for rowid in range(len(merged)):
            item = {c: merged[c][rowid] for c in merged.columns}
            json.dump(item, outfile)
            outfile.write("\n")
