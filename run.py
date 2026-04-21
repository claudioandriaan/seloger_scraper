import json
from pathlib import Path
import asyncio
import argparse

import seloger

output = Path(__file__).parent / "data"
output.mkdir(exist_ok=True)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, help="Number of pages")
    args = parser.parse_args()

    print("Running Seloger scraper...")

    search_data = await seloger.scrape_search(
        url="https://www.seloger.com/classified-search?distributionTypes=Buy&estateTypes=Apartment&locations=AD08FR13100",
        max_pages=args.pages
    )

    with open(output / "search.json", "w", encoding="utf-8") as f:
        json.dump(search_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())