import csv
import pandas as pd
import re
from urllib.parse import quote
from itertools import islice
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from funcs import wikipedia_url_from_title


_wikinamespaces = [
    "Média",
    "Spécial",
    "Discussion",
    "Utilisateur",
    "Discussion utilisateur",
    "Wikipédia",
    "Discussion Wikipédia",
    "Fichier",
    "Discussion fichier",
    "MediaWiki",
    "Discussion MediaWiki",
    "Modèle",
    "Discussion modèle",
    "Aide",
    "Discussion aide",
    "Catégorie",
    "Discussion catégorie",
    "Portail",
    "Discussion Portail",
    "Projet",
    "Discussion Projet",
    "Référence",
    "Discussion Référence",
    "Module",
    "Discussion module",
    "Gadget",
    "Discussion gadget",
    "Définition de gadget",
    "Discussion définition de gadget",
    "Sujet",
]
_wikinamespaces = [x.lower().strip().replace(" ", "_")for x in _wikinamespaces]
_wikinamespaces = _wikinamespaces + [quote(x).lower() for x in _wikinamespaces]
_wikinamespaces = _wikinamespaces + [x + ":" for x in _wikinamespaces]


def is_title_to_main_ns(title):
    title = title.lower().strip()
    if "#" in title:
        return False

    for x in _wikinamespaces:
        if title.startswith(x):
            return False
    return True


def is_url_to_main_ns(url):
    url = url.lower().strip()
    m = re.search("/wiki/(.+)", url)
    if m is not None:
        return is_title_to_main_ns(m.group(1))
    return False


def is_internal_link(tag):
    url_prefix = "/wiki/"
    is_link = tag.name == "a" and tag.get("href", "").startswith(
        url_prefix) and tag.has_attr("title")
    if is_link:
        return is_title_to_main_ns(tag["title"]) and is_url_to_main_ns(tag["href"])
    return False


def is_section_to_remove(tag):
    headings = ["notes et références", "notes", "annexes",
                "voir aussi", "bibliographie", "références", "liens externes"]
    return tag.name.startswith("h") and tag.text.lower().strip() in headings


def is_headline(tag):
    # classes = ["bandeau-container" "homonymie" "plainlinks" "hatnote"]
    return tag.has_attr("class") and "bandeau-container" in tag["class"]


def is_infobox(tag):
    # classes = ["bandeau-container" "homonymie" "plainlinks" "hatnote"]
    return tag.has_attr("class") and ("infobox_v3" in tag["class"] or "infobox" in tag["class"])


def is_edit_link(tag):
    return tag.has_attr("class") and "mw-edit" in tag["class"]


def is_toc(tag):
    return tag["id"] == "toc"


# if __name__ == "__main__":
#     outdir = Path("data", "good-articles", "scrapped")
#     pages_outdir = Path(outdir, "pages")
#     csv_outpath = Path(outdir, "frwiki.csv")
#     errors_outpath = Path(outdir, "errors.csv")

#     title2qid = {}

#     treated_pages = set()

#     list_path = Path("data", "good-articles", "list-good-pages.txt")
#     with open(str(list_path), "rt", encoding="UTF-8") as f:
#         pages = {x.replace(" ", "_").strip()
#                  for x in f.read().split("\n") if x.strip() != ""}

#     good_pages = set(pages)
#     linked_pages = set()

#     mappings_path = Path(outdir, "mappings.csv")

#     if csv_outpath.is_file():
#         df = pd.read_csv(csv_outpath)
#         treated_pages = set(df["title"])
#         del df

#     cols = {
#         "qid": [],
#         "title": [],
#         "path": [],
#         "url": [],
#     }
#     errors = {
#         "title": [],
#         "url": [],
#     }

#     counter = 0

#     def flush_cols():
#         def _f(d, out):
#             df = pd.DataFrame(d)
#             exists = out.is_file()
#             mode = "at" if exists else "wt"
#             header = not exists
#             df.to_csv(str(out), index=False, mode=mode, header=header,
#                       quoting=csv.QUOTE_NONNUMERIC, encoding="UTF-8")
#             for k in d.keys():
#                 d[k] = []

#         _f(cols, csv_outpath)
#         _f(errors, errors_outpath)

#     while len(pages) > 0:
#         title = pages.pop()
#         title = title.replace(" ", "_")
#         print(f"Treating `{title}`...", end="")
#         if title not in good_pages and title in treated_pages:
#             print("\tSkipped")
#             continue

#         page_url = wikipedia_url_from_title(title)

#         try:
#             r = requests.get(page_url)
#             html_string = r.text
#             soup = BeautifulSoup(html_string, "lxml")

#             page_exists = len(soup.select("div.noarticletext")) == 0

#             if page_exists:
#                 wikidata_link = soup.find(
#                     lambda t: t.name == "a" and t.get("href", "").startswith("https://www.wikidata.org/wiki/Special:EntityPage/Q"))
#                 qid = wikidata_link["href"].split("/")[-1]
#                 title2qid[title] = qid

#                 main = soup.select("div#mw-content-text")[0]
#                 main = main.select("div.mw-parser-output")[0]

#                 def _tag_to_remove_selector(t):
#                     return is_headline(t) or is_infobox(t)

#                 # Rm sections
#                 for t in main.select("span.mw-editsection"):
#                     t.extract()
#                 for t in main.find_all(_tag_to_remove_selector):
#                     t.extract()
#                 for t in main.find_all(is_section_to_remove):
#                     for t2 in t.find_all_next():
#                         t2.extract()
#                     t.extract()

#                 p_tags = main.find_all("p", recursive=False)
#                 for p in p_tags:
#                     for t in p.find_all("sup"):
#                         t.extract()

#                     for t in p.find_all(is_internal_link):
#                         text = t.string
#                         url = t["href"]
#                         target_title = t["title"].replace(" ", "_")
#                         t.replace_with(f"[E={target_title}]{text}[/E]")

#                         if target_title not in good_pages:
#                             linked_pages.add(target_title)
#                         if title in good_pages:
#                             pages.add(target_title)

#                 content = "\n".join(p.text for p in p_tags).strip()
#                 outpath = Path(pages_outdir, f"{qid}.txt")
#             else:
#                 qid = ""
#                 outpath = None

#             cols["title"].append(title)
#             cols["url"].append(page_url)
#             cols["qid"].append(qid)
#             if outpath is None:
#                 cols["path"].append("")
#             else:
#                 cols["path"].append(outpath.as_posix())
#                 with open(str(outpath), "wt", encoding="UTF-8") as f:
#                     f.write(content)

#             counter += 1
#             treated_pages.add(title)
#             print("\tDone")
#             if counter > 50:
#                 counter = 0
#                 flush_cols()
#         except:
#             errors["title"].append(title)
#             errors["url"].append(page_url)
#             print("\Error")

#     flush_cols()
