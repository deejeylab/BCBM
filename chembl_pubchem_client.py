"""
PubChem & ChEMBL 연동 클라이언트
- PubChem PUG REST: 화합물 식별(CID), 분자식, 분자량, Canonical SMILES, 2D 화학 구조 이미지 URL
- ChEMBL REST API: ChEMBL ID, 작용 기전(Mechanism of Action), 효능 표적 단백질, IC50/활성 프로파일
"""

import sys
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional
from config import Config

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class PubChemChEMBLClient:
    """PubChem 및 ChEMBL 공공 화합물/약리학 데이터베이스 클라이언트"""

    def __init__(self):
        self.pubchem_url = Config.PUBCHEM_PUG_REST_URL.rstrip("/")
        self.chembl_url = Config.CHEMBL_API_URL.rstrip("/")

    # --------------------------------------------------------------------------
    # PubChem 기능
    # --------------------------------------------------------------------------
    def get_pubchem_compound(self, name: str) -> Dict[str, Any]:
        """PubChem에서 화합물 기본 속성 및 SMILES, 구조 이미지 조회"""
        encoded_name = urllib.parse.quote(name)
        url = f"{self.pubchem_url}/compound/name/{encoded_name}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey,IUPACName/JSON"
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityBio/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
                cid = props.get("CID")
                return {
                    "cid": cid,
                    "formula": props.get("MolecularFormula"),
                    "molecular_weight": props.get("MolecularWeight"),
                    "smiles": props.get("CanonicalSMILES"),
                    "inchikey": props.get("InChIKey"),
                    "iupac_name": props.get("IUPACName"),
                    "structure_image_url": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG" if cid else None
                }
        except Exception:
            return {}

    # --------------------------------------------------------------------------
    # ChEMBL 기능
    # --------------------------------------------------------------------------
    def get_chembl_molecule_and_mechanisms(self, name: str) -> Dict[str, Any]:
        """ChEMBL에서 약물 분자 ID 및 작용 기전(Mechanism of Action) 조회"""
        encoded_name = urllib.parse.quote(name)
        search_url = f"{self.chembl_url}/molecule/search?q={encoded_name}&format=json&limit=1"
        req = urllib.request.Request(search_url, headers={"User-Agent": "AntigravityBio/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                mols = data.get("molecules", [])
                if not mols:
                    return {}
                mol = mols[0]
                chembl_id = mol.get("molecule_chembl_id")

                # 작용 기전 조회
                mech_url = f"{self.chembl_url}/mechanism?molecule_chembl_id={chembl_id}&format=json&limit=5"
                mech_req = urllib.request.Request(mech_url, headers={"User-Agent": "AntigravityBio/1.0"})
                mechanisms = []
                try:
                    with urllib.request.urlopen(mech_req, timeout=10) as m_resp:
                        m_data = json.loads(m_resp.read().decode("utf-8"))
                        for item in m_data.get("mechanisms", []):
                            mechanisms.append({
                                "mechanism_of_action": item.get("mechanism_of_action"),
                                "action_type": item.get("action_type"),
                                "target_chembl_id": item.get("target_chembl_id")
                            })
                except Exception:
                    pass

                return {
                    "chembl_id": chembl_id,
                    "pref_name": mol.get("pref_name"),
                    "max_phase": mol.get("max_phase"),
                    "first_approval": mol.get("first_approval"),
                    "mechanisms": mechanisms
                }
        except Exception:
            return {}

    def fetch_compound_profile(self, name: str) -> Dict[str, Any]:
        """PubChem과 ChEMBL 데이터를 통합한 분자 프로파일 반환"""
        return {
            "query_name": name,
            "pubchem": self.get_pubchem_compound(name),
            "chembl": self.get_chembl_molecule_and_mechanisms(name)
        }


if __name__ == "__main__":
    print("=== PubChem & ChEMBL 연동 클라이언트 테스트 ===")
    client = PubChemChEMBLClient()
    profile = client.fetch_compound_profile("aspirin")
    print(f" - PubChem CID: {profile['pubchem'].get('cid')}")
    print(f" - 분자식: {profile['pubchem'].get('formula')}, 분자량: {profile['pubchem'].get('molecular_weight')}")
    print(f" - Canonical SMILES: {profile['pubchem'].get('smiles')}")
    print(f" - ChEMBL ID: {profile['chembl'].get('chembl_id')}")
    print(f" - ChEMBL 작용 기전 수: {len(profile['chembl'].get('mechanisms', []))}개")
    for m in profile['chembl'].get('mechanisms', []):
        print(f"   * {m.get('mechanism_of_action')} ({m.get('action_type')})")
