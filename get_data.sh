#!/usr/bin/bash

OUT_DIR="data/good-pages"
CAT_DIR="${OUT_DIR}/categories"
SCRAP_DIR="${OUT_DIR}/scrapped"
HTML_DIR="${SCRAP_DIR}/html"
PAGES_DIR="${SCRAP_DIR}/pages"
WIKIDATA_DUMP_PATH="../data/wikidumps/wikidata-20211101-all.json.bz2"

# Create outputs directories
for DIR in ${OUT_DIR} ${CAT_DIR} ${SCRAP_DIR} ${HTML_DIR} ${PAGES_DIR}; do
    if [ ! -d ${DIR} ]; then
        mkdir ${DIR}
    fi
done

# Download pywikibot
if [ ! -d "core" ]; then
    git clone --recursive --branch stable --depth 1 https://gerrit.wikimedia.org/r/pywikibot/core.git
fi

# Copy pywikibot config and custom scripts to the relevant locatinons
cp user-config.py core

# Download pages listing good and featured articles
python core/pwb.py listpages -cat:Wikipédia:Bons_articles/Justification_de_leur_promotion -save:${CAT_DIR}
python core/pwb.py listpages -cat:Catégorie:Wikipédia:Articles_de_qualité/Justification_de_leur_promotion -save:${CAT_DIR}

# Build a file listing titles of good and featured articles
python list_good_pages.py "$CAT_DIR" "$OUT_DIR/list-good-pages.txt"

# Get the list of all pages to download by extracting links from good pages
python get_pages_list.py "$OUT_DIR/list-good-pages.txt" "$OUT_DIR/list-all-pages.txt" "$OUT_DIR/list-all-pages.csv" $HTML_DIR --compress gzip

# Download html pages
cd wikiscrap
scrapy crawl wikispider -a input_path="../$OUT_DIR/list-all-pages.csv" -O "../$SCRAP_DIR/html-pages.jl"
cd ..

# Clean html pages
python clean_html_pages.py "$SCRAP_DIR/html-pages.jl" "$SCRAP_DIR/cleaned-pages.jl" "$SCRAP_DIR/clean-errors.csv"

# Retrieve Wikidata properties for each page
python getwikidatapropertiesfromdump.py $WIKIDATA_DUMP_PATH "$SCRAP_DIR/cleaned-pages.jl" "$SCRAP_DIR/wikidata.csv"

# Build the final dataset
python build_final_dataset.py "$OUT_DIR/list-good-pages.txt" "$SCRAP_DIR/cleaned-pages.jl" "$SCRAP_DIR/wikidata.csv" "$SCRAP_DIR/corpus.jsonl.gz" "$SCRAP_DIR/entities.jsonl.gz"
