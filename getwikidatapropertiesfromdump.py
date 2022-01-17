from pathlib import Path
import bz2
import re
import json
import csv
import pandas as pd
from itertools import islice

from tqdm import tqdm


def is_instance_of(item, instances):
    try:
        for claim in item["claims"].get("P31", ()):
            target_id = claim["mainsnak"]["datavalue"]["value"]["id"]
            if target_id in instances:
                return True
    except KeyError:
        return False
    return False


def has_property(item, properties):
    item_properties = set(item["claims"].keys())
    return len(item_properties.intersection(properties)) > 0


def item_is_date(item):
    instances = {"Q73187956", "Q577", "Q14795564"}
    properties = {"P2894", "P837"}
    return is_instance_of(item, instances) or has_property(item, properties)


def item_is_person(item):
    instances = {"Q5", "Q1114461", "Q95074", "Q15632617",
                 "Q15773347", "Q3658341", "Q3375722"}
    properties = {"P1477", "P735", "P21", "P734", "P569"}
    return is_instance_of(item, instances) or has_property(item, properties)


def item_is_geoloc(item):
    instances = {"Q5119", "Q484170", "Q6465",
                 "Q200250", "Q1200957", "Q3266850"}
    properties = {"P625", "P17", "P30", "P131",
                  "P974", "P200", "P609", "P3896", }
    return is_instance_of(item, instances) or has_property(item, properties)


def item_is_organization(item):
    instances = {"Q1058914", "Q4830453", "Q18388277",
                 "Q891723", "Q249556", "Q43229", "Q3563237", "Q155076", "Q6881511", "Q740752", "Q3551775", "Q3918", "Q3591586"}
    properties = {"P452", "P112", "P1454", "P355"}
    return is_instance_of(item, instances) or has_property(item, properties)


def get_item_type(item):
    if item_is_date(item):
        return "DATE"
    elif item_is_person(item):
        return "PERSON"
    elif item_is_geoloc(item):
        return "GEOLOC"
    elif item_is_organization(item):
        return "ORG"
    else:
        return "OTHER"


def get_description(item):
    descriptions = item["descriptions"]
    desc = descriptions.get("fr", None)
    if desc is not None:
        desc = desc["value"]
    else:
        desc = ""
    return desc


def get_aliases(item):
    aliases = item["aliases"]
    al = aliases.get("fr", [])
    return [x["value"] for x in al]


def get_label(item):
    labels = item["labels"]
    lab = labels.get("fr", None)
    if lab is not None:
        lab = lab["value"]
    else:
        lab = ""
    return lab


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("dump")
    parser.add_argument("input_path")
    parser.add_argument("output_path")

    args = parser.parse_args()

    dump_path = Path(args.dump)
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    valid_qids = set()
    with open(input_path, "rt", encoding="UTF-8") as f:
        for line in f:
            item = json.loads(line)
            valid_qids.add(item["qid"])
    valid_qids = valid_qids.difference({""})

    cols = {
        "qid": [],
        "wikidata_description": [],
        "label": [],
        "aliases": [],
        "type": [],
    }

    treated_items = 0
    with tqdm(total=len(valid_qids)) as pbar:
        with bz2.open(dump_path, "rt", encoding="UTF-8") as dump:
            item_pattern = re.compile(r'{"type":"item","id":"(Q\d+)",')
            for line in islice(dump, None):
                line = line.strip()
                if line == "[" or line == "]":
                    continue
                if line[-1] == ",":
                    line = line[:-1]

                m = item_pattern.match(line)
                if m is not None:
                    qid = m.group(1)
                    if qid in valid_qids:
                        item = json.loads(line)
                        description = get_description(item)
                        label = get_label(item)
                        aliases = get_aliases(item)
                        item_type = get_item_type(item)

                        cols["qid"].append(qid)
                        cols["wikidata_description"].append(
                            description)
                        cols["label"].append(label)
                        cols["aliases"].append("::".join(aliases))
                        cols["type"].append(item_type)

                        treated_items += 1
                        pbar.update()
                        # Early stop if all qids have been treated
                        if treated_items >= len(valid_qids):
                            break

    df = pd.DataFrame(cols)
    df.to_csv(output_path, index=False, encoding="UTF-8",
              quoting=csv.QUOTE_NONNUMERIC)
