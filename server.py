"""
웹 애플리케이션 백엔드 서버 (server.py)
- Vercel 서버리스 배포(FastAPI ASGI) 및 로컬 환경(표준 HTTP 서버 / Uvicorn) 완벽 지원
- 최상위(Top-level) 'app' FastAPI 인스턴스 정의로 Vercel 빌더 자동 인식
- 엔드포인트:
  * GET / : index.html 서빙 (Vercel CDN 및 로컬)
  * GET /static/* : 정적 자산(CSS, JS, Logo 이미지 등) 서빙
  * POST /api/analyze : 성분 목록(2개 이상)에 대한 병용 시너지 & 병용금기 다차원 분석
  * GET /api/status : 7대 바이오 데이터베이스 연동 상태 확인
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from typing import List, Dict, Any

from config import Config
from synergy_engine import SynergyEngine

# Windows 콘솔 인코딩 대응
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# 국문-영문 주요 의약품 및 건기식 유효성분 자동 번역/매핑 사전
COMPOUND_DICTIONARY = {
    # 주요 의약품
    "아스피린": ("aspirin", "drug"),
    "와파린": ("warfarin", "drug"),
    "메트포르민": ("metformin", "drug"),
    "아토르바스타틴": ("atorvastatin", "drug"),
    "스타틴": ("atorvastatin", "drug"),
    "로수바스타틴": ("rosuvastatin", "drug"),
    "심바스타틴": ("simvastatin", "drug"),
    "타이레놀": ("acetaminophen", "drug"),
    "아세트아미노펜": ("acetaminophen", "drug"),
    "이부프로펜": ("ibuprofen", "drug"),
    "오메프라졸": ("omeprazole", "drug"),
    "암로디핀": ("amlodipine", "drug"),
    "로사르탄": ("losartan", "drug"),
    "클로피도그렐": ("clopidogrel", "drug"),
    "플라빅스": ("clopidogrel", "drug"),

    # 주요 건강기능식품 및 천연물 활성 성분
    "홍삼": ("ginsenoside", "supplement"),
    "인삼": ("ginsenoside", "supplement"),
    "진세노사이드": ("ginsenoside", "supplement"),
    "오메가3": ("omega-3", "supplement"),
    "오메가-3": ("omega-3", "supplement"),
    "epa": ("icosapent", "supplement"),
    "dha": ("docosahexaenoic acid", "supplement"),
    "은행잎": ("ginkgo biloba", "supplement"),
    "은행잎추출물": ("ginkgo biloba", "supplement"),
    "징코": ("ginkgo biloba", "supplement"),
    "밀크씨슬": ("silymarin", "supplement"),
    "밀크시슬": ("silymarin", "supplement"),
    "실리마린": ("silymarin", "supplement"),
    "루테인": ("lutein", "supplement"),
    "지아잔틴": ("zeaxanthin", "supplement"),
    "베르베린": ("berberine", "supplement"),
    "커큐민": ("curcumin", "supplement"),
    "강황": ("curcumin", "supplement"),
    "코엔자임q10": ("coenzyme q10", "supplement"),
    "코엔자임 q10": ("coenzyme q10", "supplement"),
    "코큐텐": ("coenzyme q10", "supplement"),
    "테아닌": ("theanine", "supplement"),
    "l-테아닌": ("theanine", "supplement"),
    "글루코사민": ("glucosamine", "supplement"),
    "프로바이오틱스": ("probiotics", "supplement"),
    "유산균": ("probiotics", "supplement"),
    "녹차추출물": ("epigallocatechin gallate", "supplement"),
    "카테킨": ("catechin", "supplement"),
    "마그네슘": ("magnesium", "supplement"),
    "칼슘": ("calcium", "supplement"),
    "비타민c": ("ascorbic acid", "supplement"),
    "비타민 c": ("ascorbic acid", "supplement"),
    "비타민d": ("cholecalciferol", "supplement"),
    "비타민 d": ("cholecalciferol", "supplement"),
    "아연": ("zinc", "supplement"),
    "홍국": ("red yeast rice", "supplement"),
    "모나콜린k": ("monacolin k", "supplement"),
    "쏘팔메토": ("saw palmetto", "supplement"),

    # 바나바 / 바나나잎 / 코로솔산 관련 표기
    "바나바": ("corosolic acid", "supplement"),
    "바나바잎": ("corosolic acid", "supplement"),
    "바나나잎": ("corosolic acid", "supplement"),
    "바나바추출물": ("corosolic acid", "supplement"),
    "바나바잎추출물": ("corosolic acid", "supplement"),
    "바나나잎추출물": ("corosolic acid", "supplement"),
    "코로솔산": ("corosolic acid", "supplement"),
    "코르솔산": ("corosolic acid", "supplement"),
    "콜로소린산": ("corosolic acid", "supplement"),

    # 크롬 관련
    "크롬": ("chromium", "supplement"),
    "크로뮴": ("chromium", "supplement"),
    "피콜린산크롬": ("chromium picolinate", "supplement"),
    "크롬피콜리네이트": ("chromium picolinate", "supplement"),

    # 베르베린 관련
    "바바린": ("berberine", "supplement"),
    "황련": ("berberine", "supplement"),

    # 기타 주요 영양/대사 성분
    "바나듐": ("vanadium", "supplement"),
    "알파리포산": ("alpha-lipoic acid", "supplement"),
    "치옥트산": ("thioctic acid", "drug"),
    "이노시톨": ("inositol", "supplement"),
    "미오이노시톨": ("myo-inositol", "supplement"),
    "셀레늄": ("selenium", "supplement"),
    "셀렌": ("selenium", "supplement"),
    "콜라겐": ("collagen", "supplement"),
    "msm": ("methylsulfonylmethane", "supplement"),
    "식이유황": ("methylsulfonylmethane", "supplement"),
    "글루타치온": ("glutathione", "supplement"),
    "nac": ("acetylcysteine", "supplement"),
    "n-아세틸시스테인": ("acetylcysteine", "drug"),
    "아르기닌": ("arginine", "supplement"),
    "l-아르기닌": ("arginine", "supplement"),
    "타우린": ("taurine", "supplement"),
    "프로폴리스": ("propolis", "supplement"),
    "스피루리나": ("spirulina", "supplement"),
    "클로렐라": ("chlorella", "supplement"),
    "레시틴": ("lecithin", "supplement"),
    "포스파티딜세린": ("phosphatidylserine", "supplement"),
    "가르시니아": ("hydroxycitric acid", "supplement"),
    "hca": ("hydroxycitric acid", "supplement"),
    "히알루론산": ("hyaluronic acid", "supplement"),
    "엽산": ("folic acid", "supplement"),
    "비오틴": ("biotin", "supplement"),
    "철분": ("iron", "supplement")
}


def resolve_substance(name: str) -> Dict[str, str]:
    """입력된 성분명에 대한 영문 학명 및 분류 자동 해결"""
    clean_name = name.strip()
    lower_name = clean_name.lower().replace(" ", "")

    for dict_key, (eng_name, s_type) in COMPOUND_DICTIONARY.items():
        if dict_key in lower_name or lower_name in dict_key:
            return {
                "input": clean_name,
                "kor": clean_name,
                "eng": eng_name,
                "type": s_type
            }

    # 기본 영문 알파벳인 경우 그대로 사용
    return {
        "input": clean_name,
        "kor": clean_name,
        "eng": clean_name,
        "type": "unknown"
    }


# 싱글톤 분석 엔진 인스턴스
_synergy_engine = None

def get_engine() -> SynergyEngine:
    global _synergy_engine
    if _synergy_engine is None:
        _synergy_engine = SynergyEngine()
    return _synergy_engine


# ==============================================================================
# Vercel 배포용 FastAPI ASGI 프레임워크 바인딩
# ==============================================================================
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    class FastAPI:
        def __init__(self, *args, **kwargs): pass
        def get(self, *args, **kwargs): return lambda fn: fn
        def post(self, *args, **kwargs): return lambda fn: fn
        def mount(self, *args, **kwargs): pass
        def add_middleware(self, *args, **kwargs): pass


# ------------------------------------------------------------------------------
# Vercel이 AST 탐색 시 즉시 식별하는 최상위(Top-level) 'app' 인스턴스 정의 (CRITICAL)
# ------------------------------------------------------------------------------
app = FastAPI(
    title="Best Combo or Big Mistake",
    description="D&J Lab - 의약품 및 건강기능식품 병용 안전성 & 약리활성 시너지 분석 플랫폼",
    version="1.0.0",
    redirect_slashes=False
)

if FASTAPI_AVAILABLE:
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Vercel 프록시 및 Rewrite 경로 복원 미들웨어
    @app.middleware("http")
    async def restore_vercel_path_middleware(request: Request, call_next):
        # Vercel이 rewrites로 인해 /server.py로 호출했을 때 원본 경로 복원
        matched = (
            request.headers.get("x-matched-path")
            or request.headers.get("x-forwarded-uri")
            or request.headers.get("x-original-uri")
        )
        if matched and request.scope.get("path") in ["/server.py", "/server"]:
            clean_path = matched.split("?")[0]
            if clean_path.startswith("/api/") or clean_path in ["/status", "/analyze"]:
                request.scope["path"] = clean_path
        return await call_next(request)

    # 정적 파일 서빙 마운트 (/static/*)
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    @app.get("/index.html")
    async def vercel_root():
        """루트 경로 접속 시 index.html 서빙"""
        index_file = BASE_DIR / "index.html"
        if not index_file.exists():
            index_file = STATIC_DIR / "index.html"
        return FileResponse(str(index_file))

    @app.get("/api/status")
    @app.get("/api/status/")
    @app.get("/status")
    @app.get("/status/")
    async def vercel_api_status():
        """7대 바이오 데이터베이스 연동 상태 확인"""
        return {
            "status": "ONLINE",
            "databases": Config.check_status()
        }

    @app.post("/api/analyze")
    @app.post("/api/analyze/")
    @app.post("/analyze")
    @app.post("/analyze/")
    async def vercel_api_analyze(request: Request):
        """성분 목록(2개 이상)에 대한 병용 시너지 및 안전성 분석 API"""
        try:
            payload = await request.json()
            ingredients = payload.get("ingredients", [])

            valid_ingredients = [i.strip() for i in ingredients if i and i.strip()]
            if len(valid_ingredients) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="최소 2개 이상의 의약품 또는 성분을 입력해야 분석이 가능합니다."
                )

            engine = get_engine()
            resolved = [resolve_substance(name) for name in valid_ingredients]

            # 2개 성분 기본 분석 (첫 번째 vs 두 번째)
            sub1 = resolved[0]
            sub2 = resolved[1]

            analysis_result = engine.analyze(
                drug_name_kor=sub1["kor"],
                drug_name_eng=sub1["eng"],
                supplement_product_name=sub2["kor"],
                supplement_ingredient_eng=sub2["eng"]
            )

            # 3개 이상 성분 입력 시 다자간 조합 매트릭스 계산 (0.01초 초고속 산출)
            pairwise_results = []
            if len(resolved) > 2:
                for i in range(len(resolved)):
                    for j in range(i + 1, len(resolved)):
                        p1, p2 = resolved[i], resolved[j]
                        if i == 0 and j == 1:
                            pairwise_results.append({
                                "pair": f"{p1['kor']} + {p2['kor']}",
                                "synergy_score": analysis_result["evaluation"]["synergy_score"],
                                "synergy_level": analysis_result["evaluation"]["synergy_level"],
                                "safety_level": analysis_result["evaluation"]["safety_level"],
                                "summary": analysis_result["evaluation"]["summary"]
                            })
                        else:
                            pairwise_results.append(engine.evaluate_pairwise_summary(p1, p2))

            return {
                "status": "SUCCESS",
                "input_substances": resolved,
                "primary_analysis": analysis_result,
                "pairwise_analyses": pairwise_results,
                "count": len(resolved)
            }
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    # Vercel이 /server.py로 직접 라우팅할 때를 대비한 전천후 디스패처
    @app.api_route("/server.py", methods=["GET", "POST", "OPTIONS"])
    @app.api_route("/server", methods=["GET", "POST", "OPTIONS"])
    async def vercel_direct_server_dispatcher(request: Request):
        if request.method == "POST":
            return await vercel_api_analyze(request)
        elif request.method == "GET":
            return await vercel_api_status()
        return JSONResponse(status_code=200, content={"status": "OK"})


# ==============================================================================
# 로컬 개발 환경용 경량 HTTP 서버 (FastAPI/Uvicorn 미설치 환경에서도 동작 보장)
# ==============================================================================
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """동시 요청 처리가 가능한 멀티스레드 HTTP 서버"""
    daemon_threads = True


class FallbackRequestHandler(SimpleHTTPRequestHandler):
    """표준 라이브러리 기반 HTTP 핸들러"""

    def translate_path(self, path):
        clean_path = path.split("?", 1)[0].split("#", 1)[0]
        if clean_path == "/" or clean_path == "":
            root_index = BASE_DIR / "index.html"
            if root_index.exists():
                return str(root_index)
            return str(STATIC_DIR / "index.html")
        if clean_path.startswith("/static/"):
            clean_path = clean_path[len("/static/"):]
            return str(STATIC_DIR / clean_path.lstrip("/"))
        return str(BASE_DIR / clean_path.lstrip("/"))

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json(200, {
                "status": "ONLINE",
                "databases": Config.check_status()
            })
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/analyze":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)
                ingredients = payload.get("ingredients", [])

                valid_ingredients = [i.strip() for i in ingredients if i and i.strip()]
                if len(valid_ingredients) < 2:
                    self._send_json(400, {
                        "error": "최소 2개 이상의 의약품 또는 성분을 입력해야 분석이 가능합니다."
                    })
                    return

                engine = get_engine()
                resolved = [resolve_substance(name) for name in valid_ingredients]

                sub1 = resolved[0]
                sub2 = resolved[1]

                analysis_result = engine.analyze(
                    drug_name_kor=sub1["kor"],
                    drug_name_eng=sub1["eng"],
                    supplement_product_name=sub2["kor"],
                    supplement_ingredient_eng=sub2["eng"]
                )

                # 3개 이상 성분 입력 시 다자간 조합 매트릭스 계산 (0.01초 초고속 산출)
                pairwise_results = []
                if len(resolved) > 2:
                    for i in range(len(resolved)):
                        for j in range(i + 1, len(resolved)):
                            p1, p2 = resolved[i], resolved[j]
                            if i == 0 and j == 1:
                                pairwise_results.append({
                                    "pair": f"{p1['kor']} + {p2['kor']}",
                                    "synergy_score": analysis_result["evaluation"]["synergy_score"],
                                    "synergy_level": analysis_result["evaluation"]["synergy_level"],
                                    "safety_level": analysis_result["evaluation"]["safety_level"],
                                    "summary": analysis_result["evaluation"]["summary"]
                                })
                            else:
                                pairwise_results.append(engine.evaluate_pairwise_summary(p1, p2))

                response_data = {
                    "status": "SUCCESS",
                    "input_substances": resolved,
                    "primary_analysis": analysis_result,
                    "pairwise_analyses": pairwise_results,
                    "count": len(resolved)
                }
                self._send_json(200, response_data)

            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_json(500, {"error": str(e)})
            return

        self._send_json(404, {"error": "Not Found"})


def run_server(port=None):
    port = port or Config.PORT or 8000
    if FASTAPI_AVAILABLE:
        try:
            import uvicorn
            print(f"=== [Best Combo or Big Mistake] FastAPI / Uvicorn 서버 가동 ===")
            print(f" -> 접속 주소: http://127.0.0.1:{port}")
            uvicorn.run("server:app", host="127.0.0.1", port=port, reload=True)
            return
        except Exception as e:
            print(f"Uvicorn 가동 실패({e}). 표준 HTTP 서버로 자동 전환합니다.")

    # 표준 HTTP 서버 폴백 실행
    server_address = ("127.0.0.1", port)
    httpd = ThreadedHTTPServer(server_address, FallbackRequestHandler)
    print(f"=== [Best Combo or Big Mistake] 표준 HTTP 서버 가동 ===")
    print(f" -> 접속 주소: http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
