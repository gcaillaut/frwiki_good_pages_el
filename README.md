# FRWIKI dataset for Entity Linking

This repository contains scripts to build an Entity Linking Dataset from Wikipedia. It is configured to work with the Frenche Wikipedia, but it should work with other languages too after minor changes.

HTML pages are scrapped from the Wikipedia website, then cleaned to keep only the text. Links between pages are used to annotate named entities.

## How it works

Following the work done in [Pointer Sentinel Mixture Models](https://arxiv.org/pdf/1609.07843.pdf), the dataset is build on _featured_ and _good_ Wikipedia pages, mainly because scrapping the whole website would be dereasonable. [Pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot) is used to get the html pages listing _good_ and _featured_ articles (_Bons articles_ and _Articles de qualité_ in French). 

```shell
# From the get_data script

# Download pages listing good and featured articles
python core/pwb.py listpages -cat:Wikipédia:Bons_articles/Justification_de_leur_promotion -save:$CAT_DIR
python core/pwb.py listpages -cat:Catégorie:Wikipédia:Articles_de_qualité/Justification_de_leur_promotion -save:$CAT_DIR

# Build a file listing titles of good featured articles
python list_good_pages.py "$CAT_DIR" "$OUT_DIR/list-good-pages.txt"
```


Then _good_ and _featured_ pages are downloaded, cleaned and scanned to detect all links to other Wikipedia pages. Those links are tagged between `[E][/E]` tags. For instance, the following HTML link:
```html
<a href="/wiki/Paris" title="Paris">la ville lumière</a>
```
will be replaced by `[E=Paris]la ville lumière[/E]` in the cleaned document. Everything that is not text is removed, as well as some sections, such as references sections.

```shell
# From the get_data script

# Get the list of all pages to download by extracting links from good pages
python get_pages_list.py "$OUT_DIR/list-good-pages.txt" "$OUT_DIR/list-all-pages.txt" "$OUT_DIR/list-all-pages.csv" $HTML_DIR --compress gzip

# Download html pages
python download_html_pages.py "$OUT_DIR/list-all-pages.csv" "$SCRAP_DIR/all-pages-paths.csv" "$SCRAP_DIR/all-pages-paths-errors.csv" $HTML_DIR --compress gzip

# Clean html pages
python clean_html_pages.py "$SCRAP_DIR/all-pages-paths.csv" $PAGES_DIR "$SCRAP_DIR/frwiki.csv" "$SCRAP_DIR/frwiki-errors.csv" --compress gzip
```

Wikidata features of all the downloaded pages are then extracted from a Wikidata dump, that should be downloaded beforehand. Wikidata features includes QID, labels, description and aliases. Types are also suggested, but one should probably not rely on it since it is based on quick-and-dirty rules. Suggested types are: GEOLOC, PERSON, DATE, ORG and OTHER.

```shell
# From the get_data script

# Retrieve Wikidata properties for each page
python getwikidatapropertiesfromdump.py $WIKIDATA_DUMP_PATH "$SCRAP_DIR/frwiki.csv" "$SCRAP_DIR/wikidata.csv"
```

Finally, all the extracted data are gathered into one CSV file whose columns are:

- __qid__: QID of the page (the Wikidata id).
- __title__: Wikipedia title of the page.
- __path__: Path of the cleaned page on disk.
- __url__: URL to the page.
- __wikipedia_description__: Description extracted from Wikipedia. It corresponds to the first paragraph of the page.
- __wikidata_description__: Description extracted from Wikidata.
- __label__: Label extracted from Wikidata.
- __aliases__: Aliases extracted from Wikidata.
- __type__: Suggested type of the entity, guessed from Wikidata properties (but, seriously, do not rely on it).

```shell
# From the get_data script

# Build the final dataset
python build_final_dataset.py "$SCRAP_DIR/frwiki.csv" "$SCRAP_DIR/wikidata.csv" "$SCRAP_DIR/final-dataset.csv"
```

## Steps to build the dataset from scratch

First, download a copy of the wikidata json dump. Instructions can be found [here](https://www.wikidata.org/wiki/Wikidata:Database_download#JSON_dumps_(recommended)).
Run the file `get_data.ps1` (or `run_data.sh` on unix) to download the data required to build the dataset. This will download a copy of the pywikibot repository.


Then, use the `datasets` module from HuggingFace to load the dataset described in `frwiki_good_articles_el.py`.


## Why don’t you rely on the XML Wikipedia dump?

Because it is way too complicated, there is no easy-to-use tools to properly parse MediaWiki documents. [Wikitextprocessor](https://github.com/tatuylonen/wikitextprocessor) seems really promising but is not yet capable of parsing non-English Wikipedia dumps.