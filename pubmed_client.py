"""
PubMed / NCBI E-Utilities API 연동 클라이언트
- 의약품 유효성분과 건강기능식품 유효성분 간의 병용 섭취 문헌 검색
- 약리활성 시너지(Synergy), 상호작용(Drug Interaction), 대사효소(CYP) 관련 초록 수집
- 근거 논문 메타데이터(PMID, 제목, 저널, 출판연도, 링크, 초록 요약) 추출
"""

import sys
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from config import Config

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class PubMedClient:
    """NCBI E-Utilities REST API 클라이언트"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: Optional[str] = None, email: Optional[str] = None):
        self.api_key = api_key or Config.NCBI_API_KEY
        self.email = email or Config.NCBI_EMAIL
        # API 키가 없으면 초당 최대 3회 (안전을 위해 0.35초 딜레이)
        self.request_delay = 0.12 if (self.api_key and not self.api_key.startswith("your_")) else 0.35
        self._last_request_time = 0.0

    def _throttle(self):
        """NCBI Rate Limit 준수 딜레이"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_time = time.time()

    def _build_params(self, extra_params: Dict[str, Any]) -> Dict[str, Any]:
        params = {"db": "pubmed"}
        if self.api_key and not self.api_key.startswith("your_"):
            params["api_key"] = self.api_key
        if self.email and not self.email.startswith("your_"):
            params["email"] = self.email
        params.update(extra_params)
        return params

    def search_articles(self, drug_name: str, supplement_ingredient: str, max_results: int = 5) -> List[str]:
        """두 성분의 병용 효과, 시너지 및 약물 상호작용 관련 논문 PMID 검색"""
        self._throttle()
        # 시너지 및 상호작용 키워드 쿼리 구성
        query = (
            f'("{drug_name}"[Title/Abstract] AND "{supplement_ingredient}"[Title/Abstract]) '
            f'AND (synergy OR synergistic OR "drug interaction" OR interaction OR "adverse effect" OR contraindication OR pharmacokinetics)'
        )
        params = self._build_params({
            "term": query,
            "retmode": "json",
            "retmax": str(max_results),
            "sort": "relevance"
        })

        url = f"{self.BASE_URL}/esearch.fcgi?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityBio/1.0"})

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                id_list = data.get("esearchresult", {}).get("idlist", [])
                return id_list
        except Exception as e:
            return []

    def fetch_article_summaries(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """PMID 목록에 대한 상세 요약 및 초록 조회"""
        if not pmids:
            return []

        self._throttle()
        params = self._build_params({
            "id": ",".join(pmids),
            "retmode": "xml"
        })

        url = f"{self.BASE_URL}/efetch.fcgi?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityBio/1.0"})

        results = []
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                xml_text = resp.read().decode("utf-8")
                root = ET.fromstring(xml_text)

                for article in root.findall(".//PubmedArticle"):
                    pmid_elem = article.find(".//MedlineCitation/PMID")
                    pmid = pmid_elem.text if pmid_elem is not None else ""

                    title_elem = article.find(".//ArticleTitle")
                    title = "".join(title_elem.itertext()).strip() if title_elem is not None else "No Title"

                    journal_elem = article.find(".//Journal/Title")
                    journal = journal_elem.text if journal_elem is not None else ""

                    year_elem = article.find(".//JournalIssue/PubDate/Year")
                    if year_elem is None:
                        year_elem = article.find(".//JournalIssue/PubDate/MedlineDate")
                    year = year_elem.text if year_elem is not None else ""

                    # 초록 파싱
                    abstract_parts = []
                    for abs_text in article.findall(".//Abstract/AbstractText"):
                        label = abs_text.attrib.get("Label", "")
                        text = "".join(abs_text.itertext()).strip()
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                    abstract = "\n".join(abstract_parts) if abstract_parts else "(초록 전문 미제공)"

                    # 시너지 및 상호작용 관련 키워드 감지
                    abstract_lower = abstract.lower()
                    interaction_types = []
                    if any(w in abstract_lower for w in ["synergistic", "synergy", "potentiate", "enhanced effect", "additive"]):
                        interaction_types.append("시너지(상승 효과)")
                    if any(w in abstract_lower for w in ["antagonis", "inhibit", "reduced effect"]):
                        interaction_types.append("길항(작용 감소)")
                    if any(w in abstract_lower for w in ["toxicity", "adverse", "risk of bleeding", "contraindication"]):
                        interaction_types.append("위험/독성 증가")

                    results.append({
                        "pmid": pmid,
                        "title": title,
                        "journal": journal,
                        "year": year,
                        "abstract": abstract[:500] + ("..." if len(abstract) > 500 else ""),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "detected_interactions": interaction_types or ["일반 상호작용 연구"]
                    })
        except Exception as e:
            pass

        return results

    def search_and_analyze(self, drug_name: str, supplement_ingredient: str, max_results: int = 3) -> Dict[str, Any]:
        """검색부터 요약/상호작용 감지까지 원스톱 실행"""
        pmids = self.search_articles(drug_name, supplement_ingredient, max_results=max_results)
        articles = self.fetch_article_summaries(pmids)

        return {
            "drug_name": drug_name,
            "supplement_ingredient": supplement_ingredient,
            "total_papers_found": len(pmids),
            "papers": articles,
            "evidence_available": len(articles) > 0
        }


if __name__ == "__main__":
    print("=== PubMed API 연동 및 문헌 조사 테스트 ===")
    pubmed = PubMedClient()
    
    print("\n[테스트] 아스피린(Aspirin)과 오메가3(EPA/DHA) 병용 시너지/상호작용 문헌 검색:")
    res = pubmed.search_and_analyze(drug_name="aspirin", supplement_ingredient="omega-3", max_results=2)
    print(f" - 검색된 총 논문 수: {res['total_papers_found']}건")
    for p in res["papers"]:
        print(f"\n * [{p['pmid']}] {p['title']} ({p['journal']}, {p['year']})")
        print(f"   - 링크: {p['url']}")
        print(f"   - 감지된 특성: {', '.join(p['detected_interactions'])}")
        print(f"   - 초록 발췌: {p['abstract'][:150]}...")
