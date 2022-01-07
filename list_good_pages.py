import re
from pathlib import Path
from itertools import chain

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    cat_dir = Path(args.input)
    outpath = Path(args.output)
    prefixes = ("Wikipédia_Bons_articles_Justification_de_leur_promotion_2*",
                "Wikipédia_Articles_de_qualité_Justification_de_leur_promotion_2*")
    files = chain.from_iterable(cat_dir.glob(p) for p in prefixes)
    titles = set()

    for filepath in files:
        with open(str(filepath), "rt", encoding="UTF-8") as f:
            for line in f:
                m = re.match(r"\*.+?{{a-label\|(.+?)}}", line)
                if m is not None:
                    t = m.group(1).strip().replace(" ", "_")
                    titles.add(t)

    with open(str(outpath), "wt", encoding="UTF-8") as out:
        out.write("\n".join(sorted(titles)))
