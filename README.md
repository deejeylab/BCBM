# Best Combo or Big Mistake (BCBM)

> **D&J Lab - 의약품 및 건강기능식품 병용 안전성 & 약리활성 시너지 분석 플랫폼**  
> "매일 먹는 약과 영양제, 과연 최적의 조합일까요? 아니면 치명적인 실수일까요?"

---

## 🌟 프로젝트 개요

**Best Combo or Big Mistake (BCBM)**는 대한민국 공공데이터포털(식약처)의 신뢰성 높은 인허가/DUR 데이터와 글로벌 6대 생명과학·약리학 데이터베이스를 융합하여, **의약품과 건강기능식품 병용 시 발생할 수 있는 약물상호작용(DDI/HDI), 법적 병용금기, 그리고 약리활성 상승 시너지(Synergy)**를 다차원으로 정밀 추정하는 웹 플랫폼입니다.

---

## 🔬 연동 7대 바이오 & 약리학 데이터베이스

1. **식품의약품안전처_DUR품목정보** (`data.go.kr`): 의약품 간 법적 병용금기, 특정연령대금기, 효능군중복 필터링
2. **식품의약품안전처_건강기능식품정보** (`data.go.kr`): 건기식 완제품 제조신고 정보 및 섭취 시 주의사항(약물 병용 주의문구) 실시간 추출
3. **PubMed / NCBI E-Utilities**: 성분 조합에 관한 최신 의학·약학 학술 논문 및 초록 실시간 수집
4. **KEGG (Kyoto Encyclopedia of Genes and Genomes)**: 인체 생화학 대사 경로(Pathway) 오버랩 및 타깃 단백질 분석
5. **DrugCombDB**: 4대 표준 약물 조합 시너지 지표(ZIP, Bliss, Loewe, HSA 점수) 정량화 모델
6. **DrugBank**: 임상 검증 약물상호작용(DDI/HDI) 심각도(Major/Moderate/Minor), 약동학/약력학 기전 및 복약 권고사항
7. **DGIdb (Drug-Gene Interaction Database)**: 약물-유전자 상호작용 표적 유전자 및 작용 기전(Inhibitor, Blocker, Agonist 등) 분석
8. **PubChem & ChEMBL**: 화합물 식별(CID), Canonical SMILES, 2D 화학 구조 이미지 및 ChEMBL 작용 기전(MoA)

---

## 📁 프로젝트 폴더 구조

```text
BCBM/
├── index.html                  # GitHub Pages 즉시 배포용 루트 랜딩/검색 페이지
├── server.py                   # 경량 고성능 멀티스레드 웹 서버 & REST API 백엔드
├── synergy_engine.py           # 7대 DB 통합 병렬 분석 엔진 (ThreadPoolExecutor 적용)
├── config.py                   # 환경 변수 보안 로더 및 마스킹 검증 유틸리티
├── data_go_client.py           # 식약처 DUR 및 건기식 공공데이터포털 클라이언트
├── kegg_client.py              # KEGG REST API 인체 경로/표적 매핑 클라이언트
├── pubmed_client.py            # NCBI PubMed E-Utilities 논문 수집기
├── dgidb_client.py             # DGIdb GraphQL 약물-유전자 표적 연동기
├── chembl_pubchem_client.py    # PubChem/ChEMBL 화합물 구조 및 기전 연동기
├── drugbank_client.py          # DrugBank DDI/HDI 심각도 및 기전 분석기
├── drugcomb_client.py          # DrugCombDB 시너지 점수(ZIP, Bliss, Loewe) 산출기
├── requirements.txt            # Python 의존성 패키지 목록
├── .env.example                # GitHub 공유용 환경 변수 템플릿 (보안 키 미포함)
├── .gitignore                  # 실제 .env 및 민감 파일 Git 추적 차단 규칙
├── README.md                   # 프로젝트 문서
└── static/
    ├── index.html              # 웹 애플리케이션 프론트엔드 UI
    ├── style.css               # 전 세대 친화적 네온사인 & 파스텔톤 반응형 스타일
    ├── app.js                  # 동적 입력창 관리 & 백엔드 통신 & GitHub Pages 데모 폴백
    └── images/
        ├── logo1.png           # 랜딩 페이지 메인 원형 버튼 로고 (D&J Monogram)
        └── logo2.png           # 검색 페이지 좌측 상단 헤더 로고 (D&J Lab)
```

---

## 🔒 보안 가이드 (API Key 보안 유지)

* 본 저장소에는 **실제 API 키가 절대 커밋되지 않도록 `.gitignore`에 `.env`가 등록**되어 있습니다.
* 모든 API 호출은 브라우저 클라이언트가 아닌 **백엔드 서버(`server.py`)**를 통해서만 안전하게 프록시되므로, 브라우저 개발자 도구(F12) 등에서 API 키가 절대 노출되지 않습니다.
* 협업자나 배포 환경에서는 `.env.example` 파일을 복사하여 `.env`를 생성하고 본인의 API 키를 입력하여 사용합니다.

```bash
# 환경 설정 파일 복사
cp .env.example .env
```

---

## 🚀 로컬 실행 방법

### 1. Python 패키지 설치
Python 3.8 이상이 설치된 환경에서 아래 명령어를 실행합니다:
```bash
pip install -r requirements.txt
```

### 2. 백엔드 서버 구동
```bash
python server.py
```

### 3. 웹 브라우저 접속
서버 구동 후 브라우저에서 아래 주소로 접속합니다:
```text
http://127.0.0.1:8000
```

---

## 🌐 GitHub 배포(Publish) 가이드

### A. GitHub 저장소(Repository)에 코드 올리기
1. 터미널에서 `BCBM` 폴더로 이동합니다.
2. Git 초기화 및 커밋:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit for Best Combo or Big Mistake platform"
   ```
3. GitHub에서 신규 리포지토리를 생성한 후 원격 저장소에 푸시합니다:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<사용자명>/<저장소명>.git
   git push -u origin main
   ```
4. **보안 검증**: GitHub 웹 페이지에서 `.env` 파일이 올라가지 않았는지 확인합니다. (정상적으로 `.env.example`만 노출되어야 합니다.)

### B. GitHub Pages로 정적 웹페이지 데모 공개하기
1. GitHub 저장소의 **[Settings] → [Pages]** 메뉴로 이동합니다.
2. **Branch** 설정을 `main` / `/(root)`로 지정하고 **[Save]**를 클릭합니다.
3. 약 1~2분 후 `https://<사용자명>.github.io/<저장소명>/` 주소로 프론트엔드 사이트가 즉시 활성화됩니다.
   * *참고: GitHub Pages는 정적 호스팅이므로, 백엔드 서버가 연결되지 않아도 내장된 데모 모드로 UI와 종합 판정 기능이 정상 구동됩니다.*

### C. Vercel 클라우드 서버리스 배포 (가장 간편한 풀스택 배포)
1. [Vercel](https://vercel.com)에 로그인 후 **[Add New...] → [Project]**를 선택하여 GitHub 저장소를 Import합니다.
2. Vercel이 `server.py`의 최상위 `app` FastAPI 인스턴스와 `vercel.json`을 자동 감지합니다. (Framework Preset: Other 유지)
3. **[Environment Variables]** 섹션에서 다음 환경 변수를 추가합니다:
   * `DATA_GO_KR_API_KEY`: 공공데이터포털 식약처 디코딩(Decoding) 키
   * `DRUGBANK_API_KEY`: (선택) DrugBank API 키
   * `PUBMED_API_KEY`: (선택) NCBI PubMed API 키
4. **[Deploy]**를 누르면 약 30초 내에 전 세계 글로벌 CDN과 Python 서버리스 API가 동시에 배포 완료됩니다!

### D. 기타 클라우드 배포 (Render, Railway, Fly.io)
* **Render**: Web Service로 리포지토리 연결 후 `python server.py`를 Start Command로 지정하고 Environment Variables에 키들을 등록하면 배포 가능합니다.
* **Railway / Fly.io / AWS**: Dockerfile 또는 requirements.txt 기반으로 즉시 구동 가능합니다.

---

## 📄 라이선스 및 면책조항

본 서비스에서 제공하는 분석 결과는 대한민국 식품의약품안전처 공공데이터 및 공개 학술 데이터베이스에 기반한 참고 연구 정보입니다. 개인의 건강 상태에 따른 구체적인 처방 및 복약 지도는 반드시 의사 또는 약사와 상담하십시오.
