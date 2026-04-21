from typing import Dict, List
from urllib.parse import urlencode
from playwright.async_api import async_playwright
import logging
import re 

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def make_search_url(page_number: int) -> str:
    base_url = "https://www.seloger.com/classified-search"
    params = {
        "distributionTypes": "Buy",
        "estateTypes": "Apartment",
        "locations": "AD08FR13100",
        "page": page_number
    }
    return f"{base_url}?{urlencode(params)}"


async def block_resources(route):
    if route.request.resource_type in ["image", "font"]:
        await route.abort()
    else:
        await route.continue_()
        
async def parse_search(page) -> List[Dict]:
    listings = []
    elements = await page.query_selector_all(".css-szi97n .css-79elbk")

    for element in elements:
        # safer extraction
        link_el = await element.query_selector("a")

        title = await link_el.get_attribute("title") if link_el else ""
        link = await link_el.get_attribute("href") if link_el else ""

        price_el = await element.query_selector(".css-f1oeq4 .css-wesefx")
        price = await price_el.get_attribute("aria-label") if price_el else ""

        address_el = await element.query_selector(".css-oaskuq")
        address = await address_el.inner_text() if address_el else ""
        
        cp = ""
        ville = ""
        if address:
            match = re.search(r"\((\d{5})\)", address)
            if match:
                cp = match.group(1)
                ville = address.split(",")[0].strip()
        

        # facts
        facts_elements = await element.query_selector_all(
            ".css-18z5qnv .css-1tod18j .css-9u48bm"
        )

        facts = []
        for el in facts_elements:
            text = (await el.inner_text()).strip()
            if text != "·":
                facts.append(text)

        piece = ""
        nb_room = ""
        m2 = ""

        for fact in facts:
            if "pièce" in fact:
                piece = fact.split()[0]
            elif "chambre" in fact:
                nb_room = fact.split()[0]
            elif "m²" in fact:
                m2 = fact.split()[0]

        listings.append({
            "title": title,
            "link": link,
            "price": price,
            "piece": piece,
            "nb_room": nb_room,
            "m2": m2,
            "address": address,
            "cp": cp,
            "ville": ville
        })

    return listings


async def scrape_search(url: str, max_pages: int = 10) -> List[Dict]:
    log.info("Scraping search page %s", url)

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            }
        )

        await context.route("**/*", block_resources)

        page = await browser.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_selector(".css-1okavp1 .css-15z7lft", timeout=60000)

        total_pages_text = await page.locator(".css-1okavp1 .css-15z7lft").inner_text()
        # extract only digits (handles spaces like \u202f)
        numbers = re.findall(r"\d+", total_pages_text)

        total_count = int("".join(numbers)) if numbers else 1

        total_pages = (total_count // 30) + (1 if total_count % 30 > 0 else 0)

        if max_pages and max_pages <= total_pages:
            total_pages = max_pages

        log.info("Total pages: %s", total_pages)

        for i in range(1, total_pages + 1):
            page_url = make_search_url(i) 
            await page.goto(page_url)

            listings = await parse_search(page)
            results.extend(listings)

            log.info("Page %s: %s listings", i, len(listings))

        await browser.close()

    return results