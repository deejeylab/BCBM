"""
공공데이터포털 3종 API 클라이언트 모듈 (표준 라이브러리 기반)
1. 식품의약품안전처_건강기능식품정보 (HtfsInfoService03)
   - getHtfsList01 (목록 조회)
   - getHtfsItem01 (상세 정보 조회)
2. 식품의약품안전처_건강기능식품 (원료/개별인정/규격)
   - 원재료, 기능성 내용, 섭취 주의사항
3. 식품의약품안전처_의약품안전정보서비스(DUR)품목정보 (DURPrdlstInfoService03)
   - getUsjntTabooInfoList03 (병용금기 조회)
"""

import sys
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from config import Config

# Windows 콘솔 인코딩 대응
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class PublicDataClient:
    """공공데이터포털 3종 API 호출 및 데이터 수집 클라이언트"""

    def __init__(self, service_key: Optional[str] = None):
        self.service_key = service_key or Config.DATA_GO_KR_API_KEY
        if not self.service_key or self.service_key.startswith("your_"):
            raise ValueError("[오류] 공공데이터포털 API 키(DATA_GO_KR_API_KEY)가 설정되지 않았습니다.")

    def _request(self, base_url: str, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP GET 요청 공통 처리 (JSON 응답 우선)"""
        req_params = {
            "serviceKey": self.service_key,
            "type": "json",
            "pageNo": "1",
            "numOfRows": "10",
        }
        req_params.update(params)

        query_string = urllib.parse.urlencode(req_params)
        full_url = f"{base_url}/{operation}?{query_string}"

        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/xml"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8")
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"raw_xml": content}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTPError {e.code}", "msg": str(e.read().decode("utf-8", errors="ignore"))}
        except Exception as e:
            return {"error": "RequestException", "msg": str(e)}

    # --------------------------------------------------------------------------
    # 1. 식품의약품안전처_건강기능식품정보 (HtfsInfoService03)
    #    - getHtfsList01 (목록 조회)
    # --------------------------------------------------------------------------
    def get_health_food_list(self, product_name: Optional[str] = None, page_no: int = 1, num_of_rows: int = 5):
        """건강기능식품 목록 조회 (제품명 등)"""
        params = {
            "pageNo": str(page_no),
            "numOfRows": str(num_of_rows)
        }
        if product_name:
            params["prdlst_nm"] = product_name

        return self._request(
            base_url=Config.API_1_HTFS_INFO_URL,
            operation="getHtfsList01",
            params=params
        )

    def get_health_food_detail(self, prdlst_report_no: str):
        """건강기능식품 상세 규격 및 섭취방법 조회 (품목제조관리번호 기준)"""
        return self._request(
            base_url=Config.API_1_HTFS_INFO_URL,
            operation="getHtfsItem01",
            params={"prdlst_report_no": prdlst_report_no}
        )

    # --------------------------------------------------------------------------
    # 2. 식품의약품안전처_건강기능식품 (기능성 원료 / 개별인정형)
    # --------------------------------------------------------------------------
    def get_health_food_raw_material(self, raw_material_name: str, page_no: int = 1, num_of_rows: int = 5):
        """건강기능식품 원료/개별인정형 조회"""
        return self._request(
            base_url=Config.API_2_HTFS_RAW_URL,
            operation="getHtfsIndvdlRecogInfoList03",
            params={
                "APLC_RAWMTRL_NM": raw_material_name,
                "pageNo": str(page_no),
                "numOfRows": str(num_of_rows)
            }
        )

    # --------------------------------------------------------------------------
    # 3. 식품의약품안전처_의약품안전정보서비스(DUR)품목정보 (DURPrdlstInfoService03)
    #    - getUsjntTabooInfoList03 (병용금기 조회)
    # --------------------------------------------------------------------------
    def get_dur_contraindications(self, item_name: Optional[str] = None, ingr_name: Optional[str] = None, page_no: int = 1, num_of_rows: int = 5):
        """의약품 병용금기 정보 조회 (품목명 또는 성분명 기준)"""
        params = {
            "pageNo": str(page_no),
            "numOfRows": str(num_of_rows)
        }
        if item_name:
            params["itemName"] = item_name
        if ingr_name:
            params["ingrName"] = ingr_name

        return self._request(
            base_url=Config.API_3_DUR_PRDLST_URL,
            operation="getUsjntTabooInfoList03",
            params=params
        )


if __name__ == "__main__":
    print("=== [공공데이터포털 3종 API 연동 테스트] ===")
    client = PublicDataClient()

    print("\n1. 식품의약품안전처_건강기능식품정보 (홍삼 검색):")
    res1 = client.get_health_food_list(product_name="홍삼", num_of_rows=2)
    header1 = res1.get("header", {})
    body1 = res1.get("body", {})
    print(f" - 응답 코드: {header1.get('resultCode')} ({header1.get('resultMsg')})")
    print(f" - 검색 건수: {body1.get('totalCount')}건")
    if body1.get("items"):
        item = body1["items"][0]
        print(f" - 첫 번째 제품: {item.get('PRDLST_NM')} (제조사: {item.get('BSSH_NM')})")
        print(f" - 섭취 시 주의사항: {str(item.get('IFTKN_ATNT_MATR_CN'))[:120]}...")

    print("\n3. 식품의약품안전처_의약품안전정보서비스(DUR)품목정보 (아스피린 병용금기 검색):")
    res3 = client.get_dur_contraindications(item_name="아스피린", num_of_rows=2)
    header3 = res3.get("header", {})
    body3 = res3.get("body", {})
    print(f" - 응답 코드: {header3.get('resultCode')} ({header3.get('resultMsg')})")
    print(f" - 병용금기 건수: {body3.get('totalCount')}건")
    if body3.get("items"):
        item = body3["items"][0]
        print(f" - 병용금기 성분: {item.get('INGR_KOR_NAME')} + {item.get('MIXTURE_INGR_KOR_NAME')}")
        print(f" - 금기 사유: {item.get('PROHBT_CONTENT')}")
