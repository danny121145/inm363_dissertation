"""Download candidate Iran-related announcements from the OFAC archive.

This script performs a one-time collection of candidate announcements returned
by the OFAC Recent Actions archive when searching for the keyword "Iran".

The resulting raw JSON contains only information extracted from the official
source pages. Relevance, action type, sector, tightening, and relief
classifications are added later during manual review.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "ofac_iran_candidate_events_raw.json"
)

ARCHIVE_URL = "https://ofac.treasury.gov/recent-actions"
BASE_URL = "https://ofac.treasury.gov"

SEARCH_KEYWORD = "Iran"

START_YEAR = 2011
END_YEAR = 2026

# This is a fixed research snapshot rather than a dataset that will be refreshed.
COLLECTION_END_DATE = "07/31/2026"
RETRIEVAL_DATE = "2026-08-01"

REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 0.25

DETAIL_LINK_PATTERN = re.compile(
    r'href="(/recent-actions/\d{8}(?:_[^"#?]+)?)"'
)


def collect_year_links(
    session: requests.Session,
    year: int,
) -> set[str]:
    """Collect dated OFAC announcement links returned for one year."""

    start_date = f"01/01/{year}"

    if year == END_YEAR:
        end_date = COLLECTION_END_DATE
    else:
        end_date = f"12/31/{year}"

    year_links: set[str] = set()
    page = 0

    while True:
        params = {
            "search_api_fulltext": SEARCH_KEYWORD,
            "ra-start-date": start_date,
            "ra-end-date": end_date,
            "ra_year": "",
            "page": page,
        }

        response = session.get(
            ARCHIVE_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        page_links = set(
            DETAIL_LINK_PATTERN.findall(response.text)
        )

        new_links = page_links - year_links
        year_links.update(page_links)

        print(
            f"{year}, page {page}: "
            f"{len(page_links)} dated announcement links"
        )

        # During inspection, a full OFAC results page contained 10 dated
        # announcement links. Fewer than 10 indicates the final page.
        #
        # The second condition also prevents an infinite loop if OFAC returns
        # the same page repeatedly.
        if len(page_links) < 10 or not new_links:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return year_links


def extract_text(
    element,
) -> str | None:
    """Return cleaned text from an HTML element."""

    if element is None:
        return None

    text = element.get_text(" ", strip=True)

    return text if text else None


def extract_candidate(
    session: requests.Session,
    relative_link: str,
) -> dict[str, str | None]:
    """Extract source information from one OFAC announcement page."""

    source_reference = urljoin(
        BASE_URL,
        relative_link,
    )

    response = session.get(
        source_reference,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    article = soup.select_one(
        "article.node--type-ofac-recent-action"
    )

    if article is None:
        raise ValueError(
            "Could not find the OFAC recent-action article: "
            f"{source_reference}"
        )

    title_element = soup.select_one(
        "h1.uswds-page-title"
    )

    date_element = article.select_one(
        ".field--name-field-release-date .field__item"
    )

    description_element = article.select_one(
        ".field--name-field-body .field__item"
    )

    press_release_element = article.select_one(
        ".field--name-field-press-release-link a"
    )

    event_date = extract_text(date_element)
    title = extract_text(title_element)
    description = extract_text(description_element)

    press_release_url = None

    if press_release_element is not None:
        href = press_release_element.get("href")

        if href:
            press_release_url = urljoin(
                source_reference,
                href,
            )

    if event_date is None:
        raise ValueError(
            f"Missing official release date: {source_reference}"
        )

    if title is None:
        raise ValueError(
            f"Missing announcement title: {source_reference}"
        )

    if description is None:
        raise ValueError(
            f"Missing announcement body: {source_reference}"
        )

    return {
        "event_date": event_date,
        "title": title,
        "description": description,
        "press_release_url": press_release_url,
        "source_reference": source_reference,
    }


def main() -> None:
    """Collect and save the raw OFAC candidate-announcement dataset."""

    if OUTPUT_PATH.exists():
        raise FileExistsError(
            f"{OUTPUT_PATH} already exists and was not overwritten."
        )

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "inm363-dissertation-research/1.0 "
                "(one-time academic data collection)"
            )
        }
    )

    all_links: set[str] = set()
    yearly_candidate_counts: dict[str, int] = {}

    print("Collecting candidate announcement links...\n")

    for year in range(
        START_YEAR,
        END_YEAR + 1,
    ):
        year_links = collect_year_links(
            session=session,
            year=year,
        )

        yearly_candidate_counts[str(year)] = len(
            year_links
        )

        all_links.update(year_links)

        print(
            f"{year}: {len(year_links)} "
            "candidate announcements\n"
        )

    sorted_links = sorted(all_links)

    print(
        "Total unique candidate links:",
        len(sorted_links),
    )

    records: list[dict[str, str | None]] = []

    print("\nExtracting announcement pages...\n")

    for index, relative_link in enumerate(
        sorted_links,
        start=1,
    ):
        record = extract_candidate(
            session=session,
            relative_link=relative_link,
        )

        records.append(record)

        print(
            f"Processed {index}/{len(sorted_links)}: "
            f"{record['event_date']} | {record['title']}"
        )

        time.sleep(REQUEST_DELAY_SECONDS)

    payload = {
        "source_name": (
            "US Department of the Treasury, "
            "Office of Foreign Assets Control"
        ),
        "archive_url": ARCHIVE_URL,
        "search_keyword": SEARCH_KEYWORD,
        "collection_start_date": "01/01/2011",
        "collection_end_date": COLLECTION_END_DATE,
        "retrieval_date": RETRIEVAL_DATE,
        "candidate_record_count": len(records),
        "yearly_candidate_counts": yearly_candidate_counts,
        "records": records,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"Candidate records: {len(records)}")

    print(
        "Missing titles:",
        sum(
            record["title"] is None
            for record in records
        ),
    )

    print(
        "Missing dates:",
        sum(
            record["event_date"] is None
            for record in records
        ),
    )

    print(
        "Missing descriptions:",
        sum(
            record["description"] is None
            for record in records
        ),
    )


if __name__ == "__main__":
    main()