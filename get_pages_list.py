from pathlib import Path
import requests
import csv
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from tqdm import tqdm
from scrap_frwiki import is_internal_link, is_url_to_main_ns, is_title_to_main_ns
from clean_html_pages import remove_non_text_tags

from funcs import html_path_from_title, get_html_page, wikipedia_url_from_title

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("input")
    parser.add_argument("txt_output")
    parser.add_argument("csv_output")
    parser.add_argument("html_cache_dir")
    parser.add_argument("--compress", default="none")

    args = parser.parse_args()

    # input_path = Path("data", "good-articles", "list-good-pages.txt")
    # out_path = Path("data", "good-articles",
    #                 "scrapped", "list-all-pages.txt")
    # csv_outpath = Path("data", "good-articles",
    #                    "scrapped", "list-all-pages.csv")

    input_path = Path(args.input)
    out_path = Path(args.txt_output)
    csv_outpath = Path(args.csv_output)
    html_cache_dir = Path(args.html_cache_dir)

    # if args.action == "get":

    with open(str(input_path), "rt", encoding="UTF-8") as f:
        good_pages = {
            l.strip().replace(" ", "_")
            for l in f if l.strip() != ""
        }

    cols = {
        "page": [],
        "linked_from": [],
        "url": [],
    }

    all_pages = set()

    for title in tqdm(good_pages, total=len(good_pages)):
        # print(f"Treating `{title}`...", end="\t")
        url = wikipedia_url_from_title(title)
        text = get_html_page(
            title, cache_dir=html_cache_dir, compress=args.compress)
        all_pages.add(title)

        cols["page"].append(title)
        cols["linked_from"].append("")
        cols["url"].append(url)

        soup = BeautifulSoup(text, "lxml")
        page_exists = len(soup.select("div.noarticletext")) == 0
        if page_exists:
            main = soup.select("div#mw-content-text")[0]
            main = main.select("div.mw-parser-output")[0]

            remove_non_text_tags(main)
            p_tags = main.find_all("p", recursive=False)
            for p in p_tags:
                for t in p.find_all(is_internal_link):
                    target_title = t["title"].replace(" ", "_")
                    all_pages.add(target_title)
                    target_url = "https://fr.wikipedia.org" + t["href"]
                    # print(f"\t{target_title}")

                    cols["page"].append(target_title)
                    cols["linked_from"].append(title)
                    cols["url"].append(target_url)
        # print("Done.")

    with open(str(out_path), "wt", encoding="UTF-8") as f:
        f.write("\n".join(all_pages))

    df = pd.DataFrame(cols)
    df.to_csv(str(csv_outpath), index=False,
              quoting=csv.QUOTE_NONNUMERIC, encoding="UTF-8")

