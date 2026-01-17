import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional


def fetch_pubmed_articles_with_metadata(
    query: str,
    max_results: int = 3,
    use_mock_if_empty: bool = True,
    timeout: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search PubMed using NCBI eUtils and fetch article metadata (title, abstract, authors, date, url).

    Returns:
        List of article dicts. If use_mock_if_empty=True, may return a mock article on empty/error.
    """
    if not query or not query.strip():
        return _mock_articles() if use_mock_if_empty else []

    headers = {"User-Agent": "ClinisightAI/1.0 (learning project)"}

    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }

    try:
        search_json = requests.get(search_url, params=search_params, headers=headers, timeout=timeout).json()
        id_list = search_json.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return _mock_articles() if use_mock_if_empty else []

        ids = ",".join(id_list)

        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {"db": "pubmed", "id": ids, "retmode": "xml"}

        fetch_resp = requests.get(fetch_url, params=fetch_params, headers=headers, timeout=timeout)
        fetch_resp.raise_for_status()

        soup = BeautifulSoup(fetch_resp.text, "lxml")
        articles_xml = soup.find_all("pubmedarticle")
        if not articles_xml:
            return _mock_articles() if use_mock_if_empty else []

        articles_info: List[Dict[str, Any]] = []

        for article in articles_xml:
            # PMID (for stable URL + mapping)
            pmid_tag = article.find("pmid")
            pmid = pmid_tag.get_text(strip=True) if pmid_tag else None

            # Title
            title_tag = article.find("articletitle")
            title = title_tag.get_text(strip=True) if title_tag else "No title"

            # Abstract (join AbstractText parts if present)
            abstract_parts = article.find_all("abstracttext")
            if abstract_parts:
                abstract = " ".join([a.get_text(" ", strip=True) for a in abstract_parts])
            else:
                abstract_tag = article.find("abstract")
                abstract = abstract_tag.get_text(" ", strip=True) if abstract_tag else "No abstract available"

            # Authors
            authors_list = []
            for author in article.find_all("author"):
                last = author.find("lastname")
                fore = author.find("forename")
                if fore and last:
                    authors_list.append(f"{fore.get_text(strip=True)} {last.get_text(strip=True)}")
                elif last:
                    authors_list.append(last.get_text(strip=True))
            if not authors_list:
                authors_list = ["No authors listed"]

            # Publication date (try PubDate, else MedlineDate)
            pub_date = _extract_pub_date(article)

            # URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "https://pubmed.ncbi.nlm.nih.gov/"

            articles_info.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors_list,
                    "publication_date": pub_date,
                    "article_url": url,
                }
            )

        if not articles_info and use_mock_if_empty:
            return _mock_articles()

        return articles_info

    except Exception:
        return _mock_articles() if use_mock_if_empty else []


def _extract_pub_date(article_soup) -> str:
    date_tag = article_soup.find("pubdate")
    if date_tag:
        # Prefer MedlineDate when present
        medline = date_tag.find("medlinedate")
        if medline and medline.get_text(strip=True):
            return medline.get_text(strip=True)

        year = date_tag.find("year")
        month = date_tag.find("month")
        day = date_tag.find("day")

        y = year.get_text(strip=True) if year else ""
        m = month.get_text(strip=True) if month else ""
        d = day.get_text(strip=True) if day else ""

        if y and m and d:
            return f"{m} {d}, {y}"
        if y and m:
            return f"{m} {y}"
        if y:
            return y

    return "No date"


def _mock_articles() -> List[Dict[str, Any]]:
    return [
        {
            "pmid": "12345678",
            "title": "Simulated Study on Fever",
            "abstract": "This is a simulated abstract on the treatment of fever in adults.",
            "authors": ["John Doe", "Jane Smith"],
            "publication_date": "March 2024",
            "article_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        }
    ]
