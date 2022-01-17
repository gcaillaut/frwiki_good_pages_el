import pandas as pd
import scrapy
from tqdm import tqdm
from ..items import WikiscrapItem


class WikiSpider(scrapy.Spider):
    name = "wikispider"

    def __init__(self, input_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        df = pd.read_csv(input_path, dtype=str, na_filter=False)
        df = df[["page", "url"]].drop_duplicates()
        self.titles = list(df["page"])
        self.urls = list(df["url"])

    def start_requests(self):
        for title, url in tqdm(zip(self.titles, self.urls), total=len(self.titles)):
            kwargs = {"title": title, "url": url}
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=kwargs)

    def parse(self, response, title, url):
        # self.log(f"Processing {title}")
        item = WikiscrapItem(page=title, url=url, text=response.text)
        yield item
        # page = response.url.split("/")[-2]
        # filename = f'quotes-{page}.html'
        # with open(filename, 'wb') as f:
        #     f.write(response.body)
        # self.log(f'Saved file {filename}')
