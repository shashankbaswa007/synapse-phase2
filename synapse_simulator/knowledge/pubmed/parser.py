"""
NCBI E-utilities Response Parser for PubMed XML/JSON Data.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from synapse_simulator.knowledge.pubmed.models import PubMedArticle


class PubMedParser:
    """Parses NCBI PubMed E-utilities XML and JSON responses into PubMedArticle objects."""

    @staticmethod
    def parse_esearch_json(json_data: Dict[str, Any]) -> List[str]:
        """Parse PMID list from esearch JSON response."""
        try:
            id_list = json_data.get("esearchresult", {}).get("idlist", [])
            return [str(pid) for pid in id_list]
        except Exception:
            return []

    @staticmethod
    def parse_efetch_xml(xml_content: str, query_topic: str = "") -> List[PubMedArticle]:
        """Parse XML string returned by PubMed efetch into PubMedArticle list."""
        articles: List[PubMedArticle] = []
        if not xml_content or not xml_content.strip():
            return articles

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return articles

        # Iterate over PubmedArticle elements
        for art_elem in root.findall(".//PubmedArticle"):
            try:
                # 1. PMID
                pmid_elem = art_elem.find(".//MedlineCitation/PMID")
                if pmid_elem is None or not pmid_elem.text:
                    continue
                pmid = pmid_elem.text.strip()

                # 2. Article Title
                title_elem = art_elem.find(".//ArticleTitle")
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else f"PubMed Article {pmid}"

                # 3. Abstract Text
                abstract_lines = []
                for abs_elem in art_elem.findall(".//Abstract/AbstractText"):
                    if abs_elem.text:
                        label = abs_elem.attrib.get("Label", "")
                        if label:
                            abstract_lines.append(f"{label}: {abs_elem.text.strip()}")
                        else:
                            abstract_lines.append(abs_elem.text.strip())
                abstract = "\n".join(abstract_lines)

                # 4. Publication Year
                year = None
                pub_date = art_elem.find(".//Journal/JournalIssue/PubDate")
                if pub_date is not None:
                    year_elem = pub_date.find("Year")
                    if year_elem is not None and year_elem.text:
                        try:
                            year = int(year_elem.text.strip())
                        except ValueError:
                            pass

                # 5. Journal Title
                journal_elem = art_elem.find(".//Journal/Title")
                journal = journal_elem.text.strip() if journal_elem is not None and journal_elem.text else ""

                # 6. Authors
                authors = []
                for author_elem in art_elem.findall(".//AuthorList/Author"):
                    last = author_elem.findtext("LastName", "")
                    fore = author_elem.findtext("ForeName", "")
                    if last:
                        name = f"{last} {fore}".strip()
                        authors.append(name)

                # 7. MeSH Terms
                mesh_terms = []
                for mesh_elem in art_elem.findall(".//MeshHeadingList/MeshHeading/DescriptorName"):
                    if mesh_elem.text:
                        mesh_terms.append(mesh_elem.text.strip())

                # 8. Keywords
                keywords = []
                for kw_elem in art_elem.findall(".//KeywordList/Keyword"):
                    if kw_elem.text:
                        keywords.append(kw_elem.text.strip())

                article = PubMedArticle(
                    pmid=pmid,
                    title=title,
                    abstract=abstract,
                    publication_year=year,
                    journal=journal,
                    authors=authors,
                    mesh_terms=mesh_terms,
                    keywords=keywords,
                    query_topic=query_topic,
                )
                articles.append(article)
            except Exception:
                continue

        return articles
