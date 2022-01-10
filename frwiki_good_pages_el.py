# coding=utf-8
# Copyright 2020 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""TODO: Add a description here."""


import pandas as pd
import re

import datasets
from pathlib import Path


def get_open_method(path):
    path = Path(path)
    ext = path.suffix

    if ext == ".gz":
        import gzip
        open_func = gzip.open
    elif ext == ".bz2":
        import bz2
        open_func = bz2.open
    else:
        open_func = open
    return open_func


def read_file(path):
    open_func = get_open_method(path)
    with open_func(path, "rt", encoding="UTF-8") as f:
        return f.read()


# TODO: Add BibTeX citation
# Find for instance the citation on arxiv or on the dataset repo/website
_CITATION = ""

_DESCRIPTION = """\
French Wikipedia dataset for Entity Linking
"""

_HOMEPAGE = "https://github.com/GaaH/frwiki_good_pages_el"

# TODO: Add the licence for the dataset here if you can find it
_LICENSE = ""

# TODO: Add link to the official dataset URLs here
# The HuggingFace dataset library don't host the datasets but only point to the original files
# This can be an arbitrary nested dict/list of URLs (see below in `_split_generators` method)
_URLs = {
    "frwiki": "",
}

_CLASS_LABELS = [
    "B",
    "I",
    "O",
]


def text_to_el_features(doc_qid, doc_title, text, title2qid, title2wikipedia, title2wikidata):
    res = {
        "title": doc_title.replace("_", " "),
        "qid": doc_qid,
    }
    text_dict = {
        "words": [],
        "labels": [],
        "qids": [],
        "titles": [],
        "wikipedia": [],
        "wikidata": [],
    }
    entity_pattern = r"\[E=(.+?)\](.+?)\[/E\]"

    # start index of the previous text
    i = 0
    for m in re.finditer(entity_pattern, text):
        mention_title = m.group(1)
        mention = m.group(2)

        mention_qid = title2qid.get(mention_title, "").replace("_", " ")
        mention_wikipedia = title2wikipedia.get(mention_title, "")
        mention_wikidata = title2wikidata.get(mention_title, "")

        # Removes entity tags in descriptions
        mention_wikipedia = re.sub(entity_pattern, r"\2", mention_wikipedia)
        # Should not be necessary
        mention_wikidata = re.sub(entity_pattern, r"\2", mention_wikidata)

        # mention_qid = title2qid.get(mention_title, "YARIEN")
        # mention_wikipedia = title2wikipedia.get(mention_title, "YARIEN")
        # mention_wikidata = title2wikidata.get(mention_title, "YARIEN")

        mention_words = mention.split()

        j = m.start(0)
        prev_text = text[i:j].split()
        len_prev_text = len(prev_text)
        text_dict["words"].extend(prev_text)
        text_dict["labels"].extend(["O"] * len_prev_text)
        text_dict["qids"].extend([None] * len_prev_text)
        text_dict["titles"].extend([None] * len_prev_text)
        text_dict["wikipedia"].extend([None] * len_prev_text)
        text_dict["wikidata"].extend([None] * len_prev_text)

        text_dict["words"].extend(mention_words)

        # If there is no description, learning can’t be done so we treat the mention as not en entity
        if mention_wikipedia == "":
            len_mention = len(mention_words)
            text_dict["labels"].extend(["O"] * len_mention)
            text_dict["qids"].extend([None] * len_mention)
            text_dict["titles"].extend([None] * len_mention)
            text_dict["wikipedia"].extend([None] * len_mention)
            text_dict["wikidata"].extend([None] * len_mention)
        else:
            len_mention_tail = len(mention_words) - 1
            # wikipedia_words = mention_wikipedia.split()
            # wikidata_words = mention_wikidata.split()
            # title_words = mention_title.replace("_", " ").split()

            text_dict["labels"].extend(["B"] + ["I"] * len_mention_tail)
            text_dict["qids"].extend([mention_qid] + [None] * len_mention_tail)
            text_dict["titles"].extend(
                [mention_title] + [None] * len_mention_tail)
            text_dict["wikipedia"].extend(
                [mention_wikipedia] + [None] * len_mention_tail)
            text_dict["wikidata"].extend(
                [mention_wikidata] + [None] * len_mention_tail)

        i = m.end(0)

    tail = text[i:].split()
    len_tail = len(tail)
    text_dict["words"].extend(tail)
    text_dict["labels"].extend(["O"] * len_tail)
    text_dict["qids"].extend([None] * len_tail)
    text_dict["titles"].extend([None] * len_tail)
    text_dict["wikipedia"].extend([None] * len_tail)
    text_dict["wikidata"].extend([None] * len_tail)
    res.update(text_dict)
    return res


class FrWikiGoodPagesELDataset(datasets.GeneratorBasedBuilder):
    """
    """

    VERSION = datasets.Version("0.1.0")

    # This is an example of a dataset with multiple configurations.
    # If you don't want/need to define several sub-sets in your dataset,
    # just remove the BUILDER_CONFIG_CLASS and the BUILDER_CONFIGS attributes.

    # If you need to make complex sub-parts in the datasets with configurable options
    # You can create your own builder configuration class to store attribute, inheriting from datasets.BuilderConfig
    # BUILDER_CONFIG_CLASS = MyBuilderConfig

    # You will be able to load one or the other configurations in the following list with
    # data = datasets.load_dataset('my_dataset', 'first_domain')
    # data = datasets.load_dataset('my_dataset', 'second_domain')
    BUILDER_CONFIGS = [
        datasets.BuilderConfig(name="frwiki", version=VERSION,
                               description="The frwiki dataset for Entity Linking"),
    ]

    # It's not mandatory to have a default configuration. Just use one if it make sense.
    DEFAULT_CONFIG_NAME = "frwiki"

    def _info(self):
        if self.config.name == "frwiki":
            features = datasets.Features({
                "title": datasets.Value("string"),
                "qid": datasets.Value("string"),
                "words": [datasets.Value("string")],
                "wikipedia": [datasets.Value("string")],
                "wikidata": [datasets.Value("string")],
                "labels": [datasets.ClassLabel(names=_CLASS_LABELS)],
                "titles": [datasets.Value("string")],
                "qids": [datasets.Value("string")],
            })

        return datasets.DatasetInfo(
            # This is the description that will appear on the datasets page.
            description=_DESCRIPTION,
            # This defines the different columns of the dataset and their types
            # Here we define them above because they are different between the two configurations
            features=features,
            # If there's a common (input, target) tuple from the features,
            # specify them here. They'll be used if as_supervised=True in
            # builder.as_dataset.
            supervised_keys=None,
            # Homepage of the dataset for documentation
            homepage=_HOMEPAGE,
            # License for the dataset if available
            license=_LICENSE,
            # Citation for the dataset
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        # TODO: This method is tasked with downloading/extracting the data and defining the splits depending on the configuration
        # If several configurations are possible (listed in BUILDER_CONFIGS), the configuration selected by the user is in self.config.name

        # dl_manager is a datasets.download.DownloadManager that can be used to download and extract URLs
        # It can accept any type or nested list/dict and will give back the same structure with the url replaced with path to local files.
        # By default the archives will be extracted and a path to a cached folder where they are extracted is returned instead of the archive
        # my_urls = _URLs[self.config.name]
        # data_dir = dl_manager.download_and_extract(my_urls)
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                # These kwargs will be passed to _generate_examples
                gen_kwargs={
                    "dataset_dir": Path(".", "data", "good-pages"),
                    "split": "train"
                }
            )
        ]

    def _generate_examples(
        # method parameters are unpacked from `gen_kwargs` as given in `_split_generators`
        self, dataset_dir, split
    ):
        """ Yields examples as (key, example) tuples. """
        # This method handles input defined in _split_generators to yield (key, example) tuples from the dataset.
        # The `key` is here for legacy reason (tfds) and is not important in itself.

        with open(Path(dataset_dir, "list-good-pages.txt"), "rt", encoding="UTF-8") as f:
            good_pages_list = f.read().split("\n")

        wiki_df = pd.read_csv(Path(dataset_dir, "scrapped", "final-dataset.csv"),
                              dtype=str, na_filter=False)

        title2qid = dict(zip(wiki_df["title"], wiki_df["qid"]))
        title2path = dict(zip(wiki_df["title"], wiki_df["path"]))
        title2wikipedia = dict(
            zip(wiki_df["title"], wiki_df["wikipedia_description"]))
        title2wikidata = dict(
            zip(wiki_df["title"], wiki_df["wikidata_description"]))

        good_pages_list = [
            gp.strip()
            for gp in good_pages_list
            if title2path[gp] != "" and gp.strip() != ""
        ]

        for id, title in enumerate(good_pages_list):
            qid = title2qid[title]
            path = title2path[title]
            text = read_file(path)

            features = text_to_el_features(
                qid, title, text, title2qid, title2wikipedia, title2wikidata)
            yield id, features
