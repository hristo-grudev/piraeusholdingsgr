import datetime
import json

import scrapy
from scrapy.exceptions import CloseSpider

from scrapy.loader import ItemLoader

from ..items import PiraeusholdingsgrItem
from itemloaders.processors import TakeFirst

import requests

url = "https://www.piraeusholdings.gr/el/Layouts/Com/Services/PressOffice.ashx"

base_payload = "cnID=D09E061CF44C41469C2C31F183E976CB&sType=1&pIndex={}&year={}"
headers = {
  'Connection': 'keep-alive',
  'Pragma': 'no-cache',
  'Cache-Control': 'no-cache',
  'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
  'Accept': 'application/json, text/javascript, */*; q=0.01',
  'X-Requested-With': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': 'https://www.piraeusholdings.gr',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Dest': 'empty',
  'Referer': 'https://www.piraeusholdings.gr/el/press-office',
  'Accept-Language': 'en-US,en;q=0.9,bg;q=0.8',
  'Cookie': 'visid_incap_2456434=4QjzIl54T7K+myq7bcSC1qi8UGAAAAAAQUIPAAAAAAC28hNJejSz+zs3VxQL3opy; ASP.NET_SessionId=abyc52kjdee13qxhd05ksehg; _ga=GA1.2.144613906.1615903915; _gid=GA1.2.1261556812.1615903915; cb-enabled=enabled; incap_ses_1309_2456434=nNLiTIkzoH1Wvwt8uoAqErGrUWAAAAAAVZR/GOfbyXcg1Iuf+nOARg==; _gat=1'
}


class PiraeusholdingsgrSpider(scrapy.Spider):
	name = 'piraeusholdingsgr'
	start_urls = ['https://www.piraeusholdings.gr/el/press-office']
	page = 1
	year = 2002
	current_year = datetime.datetime.now().year
	links = []

	def parse(self, response):
		print(self.year, self.page)
		data = requests.request("POST", url, headers=headers, data=base_payload.format(self.page, self.year))
		raw_data = json.loads(data.text)

		last_page = 0
		for post in raw_data['Data']['Results']:
			title = post['Title']
			date = post['DatePublished']
			link = post['Url']
			if link not in self.links:
				self.links.append(link)
			else:
				last_page = 1
			yield response.follow(link, self.parse_post, cb_kwargs={'date': date, 'title': title})

		if last_page == 0:
			self.page += 1
		elif self.year < self.current_year:
			self.page = 1
			self.year += 1
		else:
			raise CloseSpider('No more pages')
		yield scrapy.Request(response.url, self.parse, dont_filter=True)

	def parse_post(self, response, date, title):
		description = response.xpath('//div[@class="mainArticle"]//text()[normalize-space() and not(ancestor::h1)]').getall()
		description = [p.strip() for p in description]
		description = ' '.join(description).strip()

		item = ItemLoader(item=PiraeusholdingsgrItem(), response=response)
		item.default_output_processor = TakeFirst()
		item.add_value('title', title)
		item.add_value('description', description)
		item.add_value('date', date)

		return item.load_item()
