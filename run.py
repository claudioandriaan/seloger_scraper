import json
from pathlib import Path
import asyncio
import argparse
from datetime import datetime
import seloger

output = Path(__file__).parent / "data"
output.mkdir(exist_ok=True)
# update the output file name to be more descriptive like data_YY-MM-DD.json
output_file_name = f"data_{datetime.now().strftime('%Y-%m-%d')}.json"
output_file = output / output_file_name

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, help="Number of pages")
    args = parser.parse_args()

    print("Running Seloger scraper...")

    search_data = await seloger.scrape_search(
        url="https://www.seloger.com/classified-search?distributionTypes=Buy&estateTypes=Apartment&locations=AD08FR13100",
        max_pages=args.pages
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(search_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())