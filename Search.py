import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.service import Service

import re

def LoadDriver(
        geckodriver_path: str = "./geckodriver.exe",
        firefox_binary_path: str = "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
        firefox_profile_path: str = None,
        _headless: bool = True
    ):
    options = webdriver.FirefoxOptions()
    options.binary_location = firefox_binary_path
    if _headless:
        options.add_argument("-headless")
    
    service = Service(executable_path=geckodriver_path)

    if firefox_profile_path is not None:
        profile = webdriver.FirefoxProfile(firefox_profile_path)
    else:
        profile = None

    driver = webdriver.Firefox(service=service, options=options, firefox_profile=profile)
    
    return driver

class SearchHandler:
    def __init__(self, webdriver, filtered_phrases) -> None:
        self.driver = webdriver
        self.filtered_phrases = filtered_phrases
    def Search(self, 
            URL_Part1: str, URL_Part2: str, 
            Query: str, 
            listingTitle_Selector, listingPrice_Selector, listing_Selector, listingURL_Selector,
            UseSelenium: bool = False,
        ):
        '''Returns a `list` of `Listing` objects at the URL constructed by `{URL_Part1}{Query}{URL_Part2}.\n `_Selector` fields are CSS selectors, `listing_Selector` is absolute and should return all listing objects on a page. The other selector fields are relative to listing divs on the page.'''
        output_listings = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }

        requestURL = f"{URL_Part1}{Query}{URL_Part2}"

        if self.driver is not None: # If the driver is set, it overrides the UseSelenium field. This is because you shouldn't set the driver if you don't want to use it.
            self.driver.get(requestURL)
            requestData = self.driver.page_source
        else:
            if UseSelenium:
                raise ValueError("Search has UseSelenium set to true, but no driver was passed to SearchHandler.Search()")
            requestData = requests.get(requestURL, headers=headers).text
        
        soup = BeautifulSoup(
            requestData,
            features='lxml'
        )
        listings = soup.select(listing_Selector)
        for item in listings:
            listingTitle = item.select_one(listingTitle_Selector)
            listingPrice = item.select_one(listingPrice_Selector)
            listingURL = item.select_one(listingURL_Selector)
            if listingTitle is None or listingPrice is None or listingURL is None:
                continue
            
            # Start of Spaghetti
            if "ebay" in requestURL.lower():
                listingSubtitle = item.select_one("div.s-item__info.clearfix > div.s-item__subtitle > span.SECONDARY_INFO")
                if listingSubtitle is not None:
                    listingSubtitle = listingSubtitle.text
                    for phrase in self.filtered_phrases:
                        if phrase.lower() in listingSubtitle.lower():
                            break
                    if phrase is not None:
                        if phrase.lower() in listingSubtitle.lower():
                            continue 
            # End of Spaghetti

            listingTitle = listingTitle.text
            listingPrice = listingPrice.text
            listingURL = listingURL["href"]

            phrase = None
            for phrase in self.filtered_phrases:
                if phrase.lower() in listingTitle.lower():
                    break
            if phrase is not None:
                if phrase.lower() in listingTitle.lower():
                    continue

            Query = Query.lower().replace("\"", "")
            if Query.lower().replace("\"", "") not in listingTitle.lower() and Query.lower().replace("\"", "").replace(" ", "").replace("rtx", "").replace("rx", "").replace("gtx", "") not in listingTitle.lower():
                continue
            
            # GPU-specific hard coded filters, maybe replaceable with more fancy phrase filtering?
            if " ti " in listingTitle.lower() and " ti" not in Query:
                continue
            elif " ti" in Query and "ti " not in listingTitle.lower():
                continue

            if "xt " in listingTitle.lower() and " xt" not in Query:
                continue
            elif " xt" in Query and "xt " not in listingTitle.lower():
                if " xtx" not in Query:
                    continue

            if "xtx " in listingTitle.lower() and " xtx" not in Query:
                continue
            elif " xtx" in Query and "xtx " not in listingTitle.lower():
                continue

            listing = Listing(
                title = listingTitle,
                price = listingPrice,
                url = listingURL
            )

            output_listings.append(listing)
        return output_listings

class Listing:
    def __init__(self, title, url, price) -> None:
        self.Title = title
        self.URL = url
        self.Price = self.SetPrice(price) if isinstance(price, str) else price
    def SetPrice(self, price: str):
        price = price.split(".")[0] if "." in price and "EUR" not in price else price
        matches = re.findall(pattern="\\,\\d{2}(?!\\d)", string=price)
        if len(matches) > 0:
            for match in matches:
                price = price.replace(match, "").replace(".", "")
        price_ = ""
        for char in price:
            if char.isdigit():
                price_ += char
        if price_ == "": 
            price_ = 0
        return int(price_)