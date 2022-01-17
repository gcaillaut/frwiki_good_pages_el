from pathlib import Path
from urllib.parse import quote
import requests
import gzip
from unidecode import unidecode
import bz2


def wikipedia_url_from_title(title):
    title = title.replace(" ", "_")
    return f"https://fr.wikipedia.org/wiki/{quote(title)}"


def title_to_path(title):
    title = unidecode(title)
    for forbidden in r""":*?/\" «»!<>]['""":
        title = title.replace(forbidden, "")
    return title


def html_path_from_title(title, cache_dir, compress="none"):
    compression_ext = {
        "none": ".html",
        "gzip": ".html.gz",
        "bz2": ".html.bz2",
    }
    title = title_to_path(title)
    prefix = "frwiki_"
    ext = compression_ext[compress]
    path = Path(cache_dir, prefix + title + ext)
    return path


def cleaned_page_path_from_title(title, cache_dir, compress="none"):
    compression_ext = {
        "none": ".txt",
        "gzip": ".txt.gz",
        "bz2": ".txt.bz2",
    }
    title = title_to_path(title)
    prefix = "frwiki_"
    ext = compression_ext[compress]
    path = Path(cache_dir, prefix + title + ext)
    return path


def get_html_page(title, cache_dir=".", compress="none"):
    path = html_path_from_title(title, cache_dir, compress=compress)
    if path.is_file():
        text = read_file(path)
    else:
        url = wikipedia_url_from_title(title)
        text = download_page(url)
        write_file(text, path)
    return text


def download_page(url):
    r = requests.get(url)
    return r.text


def get_open_method(path):
    path = Path(path)
    ext = path.suffix

    if ext == ".gz":
        open_func = gzip.open
    elif ext == ".bz2":
        open_func = bz2.open
    else:
        open_func = open
    return open_func


def read_file(path):
    open_func = get_open_method(path)
    with open_func(path, "rt", encoding="UTF-8") as f:
        return f.read()


def write_file(text, path):
    open_func = get_open_method(path)
    with open_func(path, "wt", encoding="UTF-8") as f:
        f.write(text)
