from pathlib import Path
import csv
import traceback
import pandas as pd
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
    parser.add_argument("pages_output_directory")
    parser.add_argument("csv_output")
    parser.add_argument("csv_output_errors")
    parser.add_argument("--compress", default="none")

    args = parser.parse_args()

    input_path = Path(args.input)
    pages_outdir = Path(args.pages_output_directory)
    csv_outpath = Path(args.csv_output)
    errors_outpath = Path(args.csv_output_errors)

    df_html = pd.read_csv(input_path, dtype=str, na_filter=False)
    df_html.drop_duplicates("page", inplace=True)

    cols = {
        "qid": [],
        "title": [],
        "path": [],
        "url": [],
    }
    errors = {
        "title": [],
        "url": [],
        "message": [],
        "traceback": [],
    }

    already_cleaned = set()
    if csv_outpath.is_file():
        df = pd.read_csv(csv_outpath, dtype=str, na_filter=False)
        already_cleaned = set(df["title"])
        del df

    def flush_cols():
        def _f(d, out):
            df = pd.DataFrame(d)
            exists = out.is_file()
            mode = "at" if exists else "wt"
            header = not exists
            df.to_csv(str(out), index=False, mode=mode, header=header,
                      quoting=csv.QUOTE_NONNUMERIC, encoding="UTF-8")
            for k in d.keys():
                d[k] = []

        _f(cols, csv_outpath)
        _f(errors, errors_outpath)

    counter = 0
    iterator = zip(df_html["page"], df_html["path"], df_html["url"])
    for page_title, page_path, page_url in tqdm(iterator, total=len(df_html)):
        if page_title in already_cleaned:
            continue

        try:
            html_text = read_file(page_path)
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
                        t.replace_with(f"[E={target_title}]{link_text}[/E]")

                content = "\n".join(p.text for p in p_tags).strip()
                outpath = cleaned_page_path_from_title(
                    page_title, pages_outdir, args.compress)
            else:
                qid = ""
                outpath = None

            cols["title"].append(page_title)
            cols["url"].append(page_url)
            cols["qid"].append(qid)
            if outpath is None:
                cols["path"].append("")
            else:
                cols["path"].append(outpath.as_posix())
                write_file(content, outpath)

            already_cleaned.add(page_title)
            counter += 1
            if counter > 50:
                flush_cols()
                counter = 0
        except KeyboardInterrupt:
            break
        except Exception as e:
            errors["title"].append(page_title)
            errors["url"].append(page_url)
            errors["message"].append(str(e))
            errors["traceback"].append(
                traceback.format_exception(None, e, e.__traceback__)[0])

    flush_cols()
