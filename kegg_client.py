"""
KEGG REST API 연동 클라이언트 (https://rest.kegg.jp/)
- 의약품(Drug) 및 천연물/화합물(Compound) 엔트리 검색
- 약물 타깃 단백질(Target) 및 생화학 경로(Pathway) 정보 추출
- 표적 유전자 기반 인체 대사 경로(Human Pathway) 자동 매핑
- 의약품과 건기식 유효성분 간의 분자 경로 중복도(Pathway Overlap) 및 상호작용 기전 분석
"""

import sys
import re
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional
from config import Config

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class KEGGClient:
    """KEGG REST API 클라이언트"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or Config.KEGG_BASE_URL).rstrip("/")
        self._pathway_cache = {}

    def _get(self, path: str) -> str:
        """KEGG REST 요청 수행"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AntigravityBio/1.0 (Research)"}
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    def get_human_pathway_name(self, pathway_id: str) -> str:
        """hsaXXXXX 경로 ID에 대한 공식 국문/영문 명칭 조회 (캐싱 적용)"""
        clean_id = pathway_id.replace("path:", "").strip()
        if not self._pathway_cache:
            text = self._get("list/pathway/hsa")
            for line in text.strip().splitlines():
                if "\t" in line:
                    pid, name = line.split("\t", 1)
                    self._pathway_cache[pid.strip()] = name.replace(" - Homo sapiens (human)", "").strip()
        return self._pathway_cache.get(clean_id, clean_id)

    def find_drug(self, query: str) -> List[Dict[str, str]]:
        text = self._get(f"find/drug/{urllib.parse.quote(query)}")
        results = []
        for line in text.strip().splitlines():
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                results.append({"entry": parts[0].strip(), "name": parts[1].strip()})
        return results

    def find_compound(self, query: str) -> List[Dict[str, str]]:
        text = self._get(f"find/compound/{urllib.parse.quote(query)}")
        results = []
        for line in text.strip().splitlines():
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                results.append({"entry": parts[0].strip(), "name": parts[1].strip()})
        return results

    def get_entry_details(self, entry_id: str) -> Dict[str, Any]:
        """KEGG 엔트리 상세 플랫파일 파싱 및 타깃 유전자와 인체 경로 매핑"""
        text = self._get(f"get/{entry_id}")
        data = {
            "entry": entry_id,
            "name": [],
            "formula": "",
            "targets": [],
            "target_genes": [],
            "hsa_ids": [],
            "pathways": {},
            "classes": []
        }

        current_field = None
        for line in text.splitlines():
            if not line.startswith(" "):
                current_field = line[:12].strip()
                content = line[12:].strip()
            else:
                content = line[12:].strip()

            if not current_field or not content:
                continue

            if current_field == "NAME":
                names = [n.strip() for n in content.split(";") if n.strip()]
                data["name"].extend(names)
            elif current_field == "FORMULA":
                data["formula"] = content
            elif current_field == "TARGET":
                data["targets"].append(content)
                # HSA ID 추출: [HSA:5742]
                hsa_matches = re.findall(r"HSA:(\d+)", content)
                data["hsa_ids"].extend(hsa_matches)
                # 유전자 심볼 추출 (경로 번호 제외)
                gene_match = re.match(r"^([A-Za-z0-9_-]+)", content)
                if gene_match:
                    sym = gene_match.group(1).strip()
                    if not re.match(r"^(hsa|map)\d+", sym, re.IGNORECASE):
                        data["target_genes"].append(sym)
            elif current_field == "PATHWAY":
                parts = content.split(None, 1)
                if len(parts) == 2:
                    data["pathways"][parts[0]] = parts[1]
            elif current_field in ("CLASS", "REMARK"):
                data["classes"].append(content)

        # 타깃 HSA 유전자가 있으면 인체(hsa) 생화학 경로를 자동 추가 조회
        for hsa_id in data["hsa_ids"][:3]:
            link_text = self._get(f"link/pathway/hsa:{hsa_id}")
            for line in link_text.strip().splitlines():
                if "\t" in line:
                    _, path_id = line.split("\t", 1)
                    clean_pid = path_id.replace("path:", "").strip()
                    if clean_pid not in ("hsa01100", "hsa01200"):
                        pname = self.get_human_pathway_name(clean_pid)
                        data["pathways"][clean_pid] = pname

        # 중복 제거
        data["target_genes"] = list(dict.fromkeys(data["target_genes"]))
        return data

    def analyze_pathway_overlap(self, drug_query: str, supplement_compound: str) -> Dict[str, Any]:
        """의약품과 건기식 성분 간의 공유 생화학 경로 및 타깃 분석"""
        drug_entries = self.find_drug(drug_query) or self.find_compound(drug_query)
        supp_entries = self.find_compound(supplement_compound) or self.find_drug(supplement_compound)

        if not drug_entries or not supp_entries:
            return {
                "drug_query": drug_query,
                "supplement_query": supplement_compound,
                "drug_found": bool(drug_entries),
                "supplement_found": bool(supp_entries),
                "shared_pathways": {},
                "shared_count": 0,
                "mechanism_synergy_potential": "LOW"
            }

        drug_detail = self.get_entry_details(drug_entries[0]["entry"])
        supp_detail = self.get_entry_details(supp_entries[0]["entry"])

        drug_pathways = drug_detail.get("pathways", {})
        supp_pathways = supp_detail.get("pathways", {})

        shared_pathways = {}
        for p_id, p_name in drug_pathways.items():
            if p_id in supp_pathways:
                shared_pathways[p_id] = p_name

        return {
            "drug_info": {
                "entry": drug_entries[0]["entry"],
                "name": drug_entries[0]["name"],
                "pathways": drug_pathways,
                "target_genes": drug_detail["target_genes"],
                "targets": drug_detail["targets"][:5]
            },
            "supplement_info": {
                "entry": supp_entries[0]["entry"],
                "name": supp_entries[0]["name"],
                "pathways": supp_pathways,
                "target_genes": supp_detail["target_genes"],
                "targets": supp_detail["targets"][:5]
            },
            "shared_pathways": shared_pathways,
            "shared_count": len(shared_pathways),
            "mechanism_synergy_potential": "HIGH" if len(shared_pathways) >= 2 else ("MODERATE" if len(shared_pathways) == 1 else "LOW")
        }
