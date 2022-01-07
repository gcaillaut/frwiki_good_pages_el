from pathlib import Path
from funcs import read_file
import pandas as pd
from tqdm import tqdm
import shutil

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("good_pages")
    parser.add_argument("dataset")
    parser.add_argument("output_directory")
    args = parser.parse_args()

    output_directory = Path(args.output_directory)
    data_directory = Path(output_directory, "data", "good-pages")
    csv_directory = Path(data_directory, "scrapped")
    pages_directory = Path(csv_directory, "pages")

    good_pages_path = Path(args.good_pages)
    dataset_path = Path(args.dataset)

    dirs_to_create = [csv_directory, pages_directory]
    for dir in dirs_to_create:
        if not dir.is_dir():
            dir.mkdir(parents=True)

    good_pages = set(read_file(good_pages_path).split("\n"))
    dataset = pd.read_csv(dataset_path, dtype=str, na_filter=False)
    dataset = dataset[dataset["path"] != ""]

    files_to_copy = [
        Path(path)
        for title, path in zip(dataset["title"], dataset["path"])
        if title in good_pages
    ]

    shutil.copy(dataset_path, csv_directory)
    shutil.copy("frwiki_good_pages_el.py", output_directory)
    shutil.copy(good_pages_path, data_directory)
    for p in tqdm(files_to_copy):
        shutil.copy(p, pages_directory)
