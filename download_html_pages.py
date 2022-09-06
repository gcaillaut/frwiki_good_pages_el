from itertools import count, cycle, repeat
from pathlib import Path
import csv
import pandas as pd
from funcs import write_file, html_path_from_title, download_page
from tqdm import tqdm


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("csv_outpath")
    parser.add_argument("csv_errors_outpath")
    parser.add_argument("html_dir")
    parser.add_argument("--compress", default="none")

    args = parser.parse_args()

    input_path = Path(args.input_path)
    csv_outpath = Path(args.csv_outpath)
    csv_err_outpath = Path(args.csv_errors_outpath)
    html_cache_dir = Path(args.html_dir)

    # input_path = Path("data", "good-articles",
    #                   "scrapped", "list-all-pages.csv")

    # csv_outpath = Path("data", "good-articles",
    #                    "scrapped", "all-pages-paths.csv")

    # csv_err_outpath = Path("data", "good-articles",
    #                        "scrapped", "all-pages-paths-errors.csv")

    df_pages = pd.read_csv(input_path, dtype=str, na_filter=False)
    df_pages = df_pages[["page", "url"]].drop_duplicates()

    cols = {
        "page": [],
        "path": [],
        "url": [],
    }
    errors = {
        "page": [],
        "path": [],
        "url": [],
    }

    existing_html_pages = {
        p
        for p in html_cache_dir.iterdir()
    }

    def flush_cols():
        def _f(d, outpath):
            e = outpath.is_file()
            h = not e
            m = "at" if e else "wt"
            df = pd.DataFrame(d)
            df.to_csv(str(outpath), index=False, quoting=csv.QUOTE_NONNUMERIC,
                      encoding="UTF-8", mode=m, header=h)
            for k in d.keys():
                d[k] = []

        _f(cols, csv_outpath)
        _f(errors, csv_err_outpath)

    try:
        for i, (title, url) in tqdm(enumerate(zip(df_pages["page"], df_pages["url"])), total=len(df_pages)):
            path = html_path_from_title(
                title, html_cache_dir, compress=args.compress)
            try:
                # print(f"Downloading `{title}`...")

                # if path not in existing_html_pages:
                if not path.is_file():
                    text = download_page(url)
                    write_file(text, path)
                    existing_html_pages.add(path)

                cols["page"].append(title)
                cols["path"].append(path.as_posix())
                cols["url"].append(url)

                if i % 100 == 0:
                    flush_cols()
            except KeyboardInterrupt as e:
                raise e
            except:
                errors["page"].append(title)
                errors["path"].append(path.as_posix())
                errors["url"].append(url)
    except KeyboardInterrupt:
        print("Keyboard interrupt")
    finally:
        print("Saving progress...")
        flush_cols()
        print("Done.")

########################################

    # try:
    #     while len(pages) > 0:
    #         title = pages.pop()
    #         print(f"Downloading `{title}`...", end="\t")
    #         url = url_from_title(title)
    #         path = html_path_from_title(title)

    #         cols["title"].append(title)
    #         cols["path"].append(path)
    #         cols["url"].append(url)

    #         if title not in good_pages and path.is_file():
    #             print("Already exists, skipped.")
    #             continue

    #         text = get_html_page(title)
    #         print("Done.")

    #         if title in good_pages:
    #             soup = BeautifulSoup(text, "lxml")
    #             page_exists = len(soup.select("div.noarticletext")) == 0
    #             if page_exists:
    #                 main = soup.select("div#mw-content-text")[0]
    #                 main = main.select("div.mw-parser-output")[0]
    #                 for t in main.find_all(is_internal_link):
    #                     target_title = t["title"].replace(" ", "_")
    #                     pages.add(target_title)
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     df = pd.DataFrame(cols)
    #     df.to_csv(str(csv_outpath), index=False,
    #               quoting=csv.QUOTE_NONNUMERIC, encoding="UTF-8")
