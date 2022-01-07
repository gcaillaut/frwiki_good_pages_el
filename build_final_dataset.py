import pandas as pd
from pandas.io import parsers
from funcs import read_file
from pathlib import Path
import csv
from tqdm import tqdm


def extract_wikipedia_description(text):
    return text.split("\n\n")[0]


def wikipedia_description_from_path(path):
    return extract_wikipedia_description(read_file(path))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("frwiki_path")
    parser.add_argument("wikidata_path")
    parser.add_argument("output_path")

    args = parser.parse_args()

    # Columns: qid, title, path, url
    frwiki = pd.read_csv(args.frwiki_path, dtype=str, na_filter=False)
    # Columns: qid, title, wikidata_description, label, aliases, type
    wikidata = pd.read_csv(args.wikidata_path, dtype=str,
                           index_col="qid", na_filter=False)

    output_path = Path(args.output_path)

    merged = pd.merge(frwiki, wikidata, how="left",
                      left_on="qid", right_index=True)
    # joined = frwiki.join(wikidata, lsuffix="_frwiki", rsuffix="_wikidata", on="qid")
    del frwiki
    del wikidata

    # cols = {
    #     "qid": [],
    #     "title": [],
    #     "aliases": [],
    #     "type": [],
    #     "path": [],
    #     "url": [],
    #     "wikidata_description": [],
    #     "wikipedia_description": [],
    #     "label": [],
    # }

    # for x in tqdm(merged.itertuples(index=False), total=len(merged)):
    #     try:
    #         desc = wikipedia_description_from_path(x.path)
    #         cols["qid"].append(x.qid)
    #         cols["title"].append(x.title)
    #         cols["aliases"].append(x.aliases)
    #         cols["type"].append(x.type)
    #         cols["path"].append(x.path)
    #         cols["url"].append(x.url)
    #         cols["wikidata_description"].append(x.wikidata_description)
    #         cols["wikipedia_description"].append(desc)
    #         cols["label"].append(x.label)
    #     except FileNotFoundError:
    #         print(f"File `{x.path}` does not exists")

    wikipedia_descriptions = []
    for path in tqdm(merged["path"]):
        try:
            desc = wikipedia_description_from_path(path)
            wikipedia_descriptions.append(desc)
        except FileNotFoundError:
            wikipedia_descriptions.append("")
            print(f"File `{path}` does not exists")

    merged["wikipedia_description"] = wikipedia_descriptions

    merged.to_csv(output_path, index=False,
                  quoting=csv.QUOTE_NONNUMERIC, encoding="UTF-8")
