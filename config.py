"""
환경 변수 및 API 설정 관리 모듈
- 공공데이터포털 3대 핵심 API
- PubMed / NCBI E-Utilities API
- KEGG REST API
- 4대 확장 바이오/약리학 데이터베이스:
  1. DrugCombDB (약물 조합 시너지 지표)
  2. DrugBank (DDI Checker API)
  3. DGIdb (Drug-Gene Interaction GraphQL API)
  4. PubChem & ChEMBL (화합물 구조, 활성 프로파일, IC50)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def load_env_file():
    """python-dotenv 없이도 .env 파일을 안전하게 파싱하여 os.environ에 등록"""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_env_file()


class Config:
    """애플리케이션 환경 설정 클래스"""
    
    # --------------------------------------------------------------------------
    # 공공데이터포털 (data.go.kr)
    # --------------------------------------------------------------------------
    DATA_GO_KR_API_KEY: str = os.getenv("DATA_GO_KR_API_KEY", "")
    DATA_GO_KR_API_KEY_ENCODED: str = os.getenv("DATA_GO_KR_API_KEY_ENCODED", "")

    API_1_HTFS_INFO_URL: str = os.getenv(
        "API_1_HTFS_INFO_URL", 
        "https://apis.data.go.kr/1471000/HtfsInfoService03"
    )
    API_2_HTFS_RAW_URL: str = os.getenv(
        "API_2_HTFS_RAW_URL", 
        "http://apis.data.go.kr/1471000/HtfsIndvdlRecogInfoService03"
    )
    API_3_DUR_PRDLST_URL: str = os.getenv(
        "API_3_DUR_PRDLST_URL", 
        "http://apis.data.go.kr/1471000/DURPrdlstInfoService03"
    )

    # --------------------------------------------------------------------------
    # PubMed / NCBI E-Utilities
    # --------------------------------------------------------------------------
    NCBI_API_KEY: str = os.getenv("NCBI_API_KEY", "")
    NCBI_EMAIL: str = os.getenv("NCBI_EMAIL", "")

    # --------------------------------------------------------------------------
    # KEGG REST API
    # --------------------------------------------------------------------------
    KEGG_BASE_URL: str = os.getenv("KEGG_BASE_URL", "https://rest.kegg.jp")

    # --------------------------------------------------------------------------
    # 4대 추가 약리학 & 시너지 데이터베이스
    # --------------------------------------------------------------------------
    # 1. DrugCombDB
    DRUGCOMBDB_URL: str = os.getenv("DRUGCOMBDB_URL", "http://drugcombdb.denglab.org")

    # 2. DrugBank
    DRUGBANK_API_KEY: str = os.getenv("DRUGBANK_API_KEY", "")
    DRUGBANK_BASE_URL: str = os.getenv("DRUGBANK_BASE_URL", "https://api.drugbank.com/v1")

    # 3. DGIdb
    DGIDB_GRAPHQL_URL: str = os.getenv("DGIDB_GRAPHQL_URL", "https://dgidb.org/api/graphql")

    # 4. PubChem & ChEMBL
    PUBCHEM_PUG_REST_URL: str = os.getenv("PUBCHEM_PUG_REST_URL", "https://pubchem.ncbi.nlm.nih.gov/rest/pug")
    CHEMBL_API_URL: str = os.getenv("CHEMBL_API_URL", "https://www.ebi.ac.uk/chembl/api/data")

    # --------------------------------------------------------------------------
    # LLM / AI API & 서버
    # --------------------------------------------------------------------------
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @classmethod
    def mask_key(cls, key: str) -> str:
        if not key or key.startswith("your_"):
            return "(미설정)"
        if len(key) <= 6:
            return "***"
        return f"{key[:3]}...{key[-3:]} (길이: {len(key)})"

    @classmethod
    def check_status(cls) -> Dict[str, Any]:
        return {
            "공공데이터포털 인증키": cls.mask_key(cls.DATA_GO_KR_API_KEY),
            "1. 건기식정보 URL": cls.API_1_HTFS_INFO_URL,
            "2. 건기식원료 URL": cls.API_2_HTFS_RAW_URL,
            "3. 의약품 DUR URL": cls.API_3_DUR_PRDLST_URL,
            "PubMed / NCBI": cls.mask_key(cls.NCBI_API_KEY),
            "KEGG REST": cls.KEGG_BASE_URL,
            "1. DrugCombDB": cls.DRUGCOMBDB_URL,
            "2. DrugBank DDI": f"{cls.DRUGBANK_BASE_URL} (Key: {cls.mask_key(cls.DRUGBANK_API_KEY)})",
            "3. DGIdb GraphQL": cls.DGIDB_GRAPHQL_URL,
            "4. PubChem / ChEMBL": f"{cls.PUBCHEM_PUG_REST_URL} / {cls.CHEMBL_API_URL}",
        }


if __name__ == "__main__":
    print("=== [통합 바이오/약리학 데이터베이스 연동 점검] ===")
    status = Config.check_status()
    for k, v in status.items():
        print(f" - {k}: {v}")
