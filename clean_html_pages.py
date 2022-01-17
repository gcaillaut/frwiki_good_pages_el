from pathlib import Path
import csv
import traceback
import pandas as pd
import json
from funcs import read_file, write_file, cleaned_page_path_from_title
from scrap_frwiki import is_headline, is_infobox, is_section_to_remove, is_internal_link
from tqdm import tqdm
from bs4 import BeautifulSoup


def remove_non_text_tags(root):
    def _tag_to_remove_selector(t):
        return is_headline(t) or is_infobox(t)

    # Rm sections
    for t in root.select("span.mw-editsection"):
        t.extract()
    for t in root.find_all(_tag_to_remove_selector):
        t.extract()
    for t in root.find_all(is_section_to_remove):
        for t2 in t.find_all_next():
            t2.extract()
        t.extract()

    p_tags = root.find_all("p", recursive=False)
    for p in p_tags:
        for t in p.find_all("sup"):
            t.extract()


def replace_math_elements(root):
    for t in root.select("span.mwe-math-element"):
        if t.img is not None:
            t.replace_with(t.img.attrs["alt"])
        else:
            txt = t.text.replace("\n", "")
            i = txt.find(r"{\displaystyle")
            txt = txt[:i]
            t.replace_with(txt)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("csv_output_errors")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    errors_outpath = Path(args.csv_output_errors)

    errors = {
        "title": [],
        "url": [],
        "message": [],
        "traceback": [],
    }

    already_cleaned = set()
    if output_path.is_file():
        with open(output_path, "rt", encoding="UTF-8") as f:
            for line in f:
                item = json.loads(line)
                already_cleaned.add(item["title"])

    item_count = 0
    with open(input_path, "rt", encoding="UTF-8") as file:
        for item_count, _ in enumerate(file):
            pass

    with open(input_path, "rt", encoding="UTF-8") as file:
        with open(output_path, "at", encoding="UTF-8") as outfile:
            for line in tqdm(file, total=item_count):
                item = json.loads(line)
                page_title = item["page"]
                page_url = item["url"]
                html_text = item["text"]

                if page_title in already_cleaned:
                    continue

                try:
                    soup = BeautifulSoup(html_text, "lxml")
                    page_exists = len(soup.select("div.noarticletext")) == 0

                    if page_exists:
                        wikidata_link = soup.find(
                            lambda t: t.name == "a" and t.get("href", "").startswith("https://www.wikidata.org/wiki/Special:EntityPage/Q"))
                        if wikidata_link is None:
                            qid = ""
                        else:
                            qid = wikidata_link["href"].split("/")[-1]

                        main = soup.select("div#mw-content-text")[0]
                        main = main.select("div.mw-parser-output")[0]

                        remove_non_text_tags(main)
                        p_tags = main.find_all("p", recursive=False)
                        for p in p_tags:
                            replace_math_elements(p)
                            for t in p.find_all(is_internal_link):
                                link_text = t.text
                                url = t["href"]
                                target_title = t["title"].replace(" ", "_")
                                t.replace_with(
                                    f"[E={target_title}]{link_text}[/E]")

                        content = "\n".join(p.text for p in p_tags).strip()
                    else:
                        qid = ""

                    cleaned_item = {
                        "title": page_title,
                        "url": page_url,
                        "qid": qid,
                        "text": content,
                    }
                    json.dump(cleaned_item, outfile)
                    outfile.write("\n")
                    already_cleaned.add(page_title)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    errors["title"].append(page_title)
                    errors["url"].append(page_url)
                    errors["message"].append(str(e))
                    errors["traceback"].append(
                        traceback.format_exception(None, e, e.__traceback__)[0])

    err_df = pd.DataFrame(errors)
    if errors_outpath.is_file():
        mode = "at"
        header = False
    else:
        mode = "wt"
        header = True
    err_df.to_csv(errors_outpath, index=False,
                  quoting=csv.QUOTE_NONNUMERIC, encoding="UTF-8", mode=mode, header=header)
