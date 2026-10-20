"""
DGIdb (Drug-Gene Interaction Database) GraphQL API 클라이언트
- 약물(또는 건기식 활성 성분)의 분자 타깃 유전자 및 상호작용 유형(Inhibitor, Agonist, Blocker 등) 조회
- 약물-유전자 상호작용 점수(Interaction Score) 및 데이터 출처 수집
"""

import sys
import json
import urllib.request
from typing import Dict, List, Any, Optional
from config import Config

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class DGIdbClient:
    """DGIdb v5 GraphQL API 클라이언트"""

    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or Config.DGIDB_GRAPHQL_URL

    def query_drug_gene_interactions(self, drug_name: str) -> List[Dict[str, Any]]:
        """약물명을 기준으로 상호작용하는 표적 유전자 및 작용 기전 조회"""
        query = """
        query GetDrugInteractions($names: [String!]!) {
          drugs(names: $names) {
            nodes {
              name
              conceptId
              interactions {
                gene {
                  name
                  conceptId
                }
                interactionScore
                interactionTypes {
                  type
                  directionality
                }
                sources {
                  sourceDbName
                }
              }
            }
          }
        }
        """
        payload = {
            "query": query,
            "variables": {"names": [drug_name.upper(), drug_name.capitalize(), drug_name.lower()]}
        }

        req = urllib.request.Request(
            self.endpoint_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AntigravityBio/1.0"
            }
        )

        results = []
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                nodes = data.get("data", {}).get("drugs", {}).get("nodes", [])
                for node in nodes:
                    for interaction in node.get("interactions", []):
                        gene_name = interaction.get("gene", {}).get("name")
                        types = [t.get("type") for t in interaction.get("interactionTypes", []) if t.get("type")]
                        score = interaction.get("interactionScore", 0.0)
                        sources = [s.get("sourceDbName") for s in interaction.get("sources", []) if s.get("sourceDbName")]
                        results.append({
                            "drug": node.get("name"),
                            "gene": gene_name,
                            "interaction_types": types or ["unspecified"],
                            "score": round(score, 3) if isinstance(score, (int, float)) else score,
                            "sources": list(set(sources))[:3]
                        })
        except Exception as e:
            pass

        # 유전자명 기준 중복 제거 및 점수 순 정렬
        seen_genes = set()
        deduped = []
        for r in sorted(results, key=lambda x: x.get("score") or 0, reverse=True):
            if r["gene"] not in seen_genes:
                seen_genes.add(r["gene"])
                deduped.append(r)
        return deduped

    def find_shared_targets(self, drug_name: str, supplement_compound: str) -> Dict[str, Any]:
        """의약품과 건기식 성분 간의 공유 표적 유전자(Shared Target Genes) 분석"""
        drug_targets = self.query_drug_gene_interactions(drug_name)
        supp_targets = self.query_drug_gene_interactions(supplement_compound)

        drug_gene_map = {t["gene"]: t for t in drug_targets}
        supp_gene_map = {t["gene"]: t for t in supp_targets}

        shared_genes = set(drug_gene_map.keys()) & set(supp_gene_map.keys())
        shared_details = []
        for g in shared_genes:
            shared_details.append({
                "gene": g,
                "drug_action": drug_gene_map[g]["interaction_types"],
                "drug_score": drug_gene_map[g]["score"],
                "supp_action": supp_gene_map[g]["interaction_types"],
                "supp_score": supp_gene_map[g]["score"],
            })

        return {
            "drug_name": drug_name,
            "supplement_compound": supplement_compound,
            "drug_target_count": len(drug_targets),
            "supplement_target_count": len(supp_targets),
            "shared_target_genes": list(shared_genes),
            "shared_count": len(shared_genes),
            "shared_details": shared_details,
            "target_overlap_synergy": "HIGH" if len(shared_genes) >= 2 else ("MODERATE" if len(shared_genes) == 1 else "LOW")
        }


if __name__ == "__main__":
    print("=== DGIdb GraphQL 클라이언트 테스트 ===")
    dgidb = DGIdbClient()
    res = dgidb.query_drug_gene_interactions("aspirin")
    print(f" - Aspirin 표적 유전자 수: {len(res)}개")
    for r in res[:3]:
        print(f"   * Gene: {r['gene']}, Action: {r['interaction_types']}, Score: {r['score']}")
