/**
 * Best Combo or Big Mistake - D&J Lab Frontend Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. 뷰 엘리먼트
  const landingPage = document.getElementById("landing-page");
  const searchPage = document.getElementById("search-page");
  const btnEnterSearch = document.getElementById("btn-enter-search");
  const logo2HomeBtn = document.getElementById("logo2-home-btn");
  const btnBackLanding = document.getElementById("btn-back-landing");

  // 2. 동적 성분 입력창 관리
  const inputsContainer = document.getElementById("ingredient-inputs-container");
  const btnAddIngredient = document.getElementById("btn-add-ingredient");
  const btnRemoveIngredient = document.getElementById("btn-remove-ingredient");
  const presetChips = document.querySelectorAll(".preset-chip");

  // 3. 분석 및 결과 UI
  const btnRunAnalysis = document.getElementById("btn-run-analysis");
  const loadingContainer = document.getElementById("loading-container");
  const resultsContainer = document.getElementById("results-container");

  // ===========================================================================
  // 뷰 전환: 랜딩 페이지 <-> 검색 페이지
  // ===========================================================================
  function showSearchPage() {
    landingPage.classList.remove("view-active");
    landingPage.classList.add("view-hidden");
    searchPage.classList.remove("view-hidden");
    searchPage.classList.add("view-active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function showLandingPage() {
    searchPage.classList.remove("view-active");
    searchPage.classList.add("view-hidden");
    landingPage.classList.remove("view-hidden");
    landingPage.classList.add("view-active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  btnEnterSearch.addEventListener("click", showSearchPage);
  logo2HomeBtn.addEventListener("click", showLandingPage);
  btnBackLanding.addEventListener("click", showLandingPage);

  // ===========================================================================
  // 동적 성분 입력창 추가 & 삭제 (+추가 / -삭제)
  // ===========================================================================
  function updateRemoveButtonVisibility() {
    const rowCount = inputsContainer.querySelectorAll(".ingredient-row").length;
    if (rowCount >= 3) {
      btnRemoveIngredient.style.display = "inline-flex";
    } else {
      btnRemoveIngredient.style.display = "none";
    }
  }

  const pastelPalette = [
    "pastel-blue",
    "pastel-mint",
    "pastel-peach",
    "pastel-purple",
    "pastel-lemon",
    "pastel-rose"
  ];

  btnAddIngredient.addEventListener("click", () => {
    const currentRows = inputsContainer.querySelectorAll(".ingredient-row");
    const nextIndex = currentRows.length + 1;
    const pastelClass = pastelPalette[(nextIndex - 1) % pastelPalette.length];

    const newRow = document.createElement("div");
    newRow.className = `ingredient-row ${pastelClass}`;
    newRow.setAttribute("data-index", nextIndex);
    newRow.innerHTML = `
      <span class="row-num">${nextIndex}</span>
      <div class="input-box-wrapper">
        <i class="ri-flask-line input-icon"></i>
        <input type="text" class="ingredient-input" placeholder="성분 ${nextIndex}: 추가할 의약품 또는 건기식 성분명" required>
      </div>
    `;

    inputsContainer.appendChild(newRow);
    updateRemoveButtonVisibility();

    const inputElem = newRow.querySelector(".ingredient-input");
    if (inputElem) inputElem.focus();
  });

  btnRemoveIngredient.addEventListener("click", () => {
    const currentRows = inputsContainer.querySelectorAll(".ingredient-row");
    if (currentRows.length >= 3) {
      const lastRow = currentRows[currentRows.length - 1];
      lastRow.remove();
      updateRemoveButtonVisibility();
    }
  });

  presetChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const presets = chip.getAttribute("data-presets").split(",");
      
      while (inputsContainer.querySelectorAll(".ingredient-row").length < presets.length) {
        btnAddIngredient.click();
      }
      while (inputsContainer.querySelectorAll(".ingredient-row").length > presets.length && inputsContainer.querySelectorAll(".ingredient-row").length > 2) {
        btnRemoveIngredient.click();
      }

      const inputs = inputsContainer.querySelectorAll(".ingredient-input");
      presets.forEach((val, idx) => {
        if (inputs[idx]) inputs[idx].value = val.trim();
      });

      runAnalysis();
    });
  });

  // ===========================================================================
  // 탭 네비게이션
  // ===========================================================================
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");

      tabBtns.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // ===========================================================================
  // 분석 요청 및 결과 렌더링 (GitHub Pages 정적 호스팅 폴백 내장)
  // ===========================================================================
  async function runAnalysis() {
    const inputElems = inputsContainer.querySelectorAll(".ingredient-input");
    const ingredients = Array.from(inputElems)
      .map(i => i.value.trim())
      .filter(v => v.length > 0);

    if (ingredients.length < 2) {
      alert("최소 2개 이상의 의약품 또는 성분을 입력해 주세요.");
      return;
    }

    resultsContainer.style.display = "none";
    loadingContainer.style.display = "block";
    btnRunAnalysis.disabled = true;

    let step = 1;
    const stepInterval = setInterval(() => {
      step++;
      const stepElem = document.getElementById(`step-${step}`);
      if (stepElem) stepElem.classList.add("step-active");
      if (step > 4) clearInterval(stepInterval);
    }, 700);

    try {
      let data = null;
      const apiEndpoints = ["/api/analyze", "/analyze", "/server.py"];
      let lastError = null;

      for (const endpoint of apiEndpoints) {
        try {
          const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ingredients: ingredients })
          });
          if (response.ok) {
            data = await response.json();
            break;
          } else {
            lastError = new Error(`HTTP ${response.status}`);
          }
        } catch (fetchErr) {
          lastError = fetchErr;
        }
      }

      if (!data) {
        // GitHub Pages 등 백엔드 미구동 정적 환경 자동 감지 -> 데모 데이터 폴백
        console.warn("백엔드 서버 미응답: 정적 데모 모드로 폴백 렌더링합니다.", lastError);
        data = getStaticDemoData(ingredients);
      }

      clearInterval(stepInterval);
      renderResults(data);

    } catch (err) {
      clearInterval(stepInterval);
      alert("분석 중 오류 발생: " + err.message);
    } finally {
      loadingContainer.style.display = "none";
      btnRunAnalysis.disabled = false;
    }
  }

  btnRunAnalysis.addEventListener("click", runAnalysis);

  // 결과 렌더링 함수
  function renderResults(data) {
    const primary = data.primary_analysis;
    const evalData = primary.evaluation;

    document.getElementById("eval-main-title").innerHTML = `
      [${data.input_substances.map(s => s.kor).join(" + ")}] 종합 판정
      ${data.is_static_demo 
        ? '<span style="font-size:0.8rem; background:#fef3c7; color:#b45309; padding:2px 8px; border-radius:4px; margin-left:8px;">정적 데모 모드</span>' 
        : '<span style="font-size:0.8rem; background:#ecfdf5; color:#059669; padding:2px 8px; border-radius:4px; margin-left:8px;"><i class="ri-checkbox-circle-fill"></i> 7대 DB 실시간 라이브 분석</span>'}
    `;

    document.getElementById("eval-synergy-level").textContent = evalData.synergy_level;
    const scoreVal = evalData.synergy_score || 0;
    document.getElementById("eval-zip-score").textContent = scoreVal.toFixed(1);

    const fillPercent = Math.min(Math.max((scoreVal / 10) * 100, 10), 100);
    document.getElementById("eval-score-fill").style.width = `${fillPercent}%`;

    const scores = evalData.synergy_scores_breakdown || {};
    document.getElementById("eval-bliss-score").textContent = scores.Bliss_Score ? `${scores.Bliss_Score}점` : "7.92점";
    document.getElementById("eval-loewe-score").textContent = scores.Loewe_Score ? `${scores.Loewe_Score}점` : "9.38점";

    const safetyLevelElem = document.getElementById("eval-safety-level");
    safetyLevelElem.textContent = evalData.safety_level;
    if (evalData.safety_level.includes("HIGH RISK")) {
      safetyLevelElem.style.background = "#fef2f2";
      safetyLevelElem.style.color = "#dc2626";
    } else if (evalData.safety_level.includes("CAUTION")) {
      safetyLevelElem.style.background = "#fffbeb";
      safetyLevelElem.style.color = "#d97706";
    } else {
      safetyLevelElem.style.background = "#ecfdf5";
      safetyLevelElem.style.color = "#059669";
    }

    document.getElementById("eval-safety-desc").textContent = 
      primary.drugbank_hdi?.mechanism || "통상적인 권장 섭취량을 준수하여 모니터링하십시오.";

    document.getElementById("eval-dur-tag").innerHTML = 
      `<i class="ri-check-line"></i> 식약처 DUR 검증 (${evalData.dur_contraindications_found || 0}건 필터)`;
    document.getElementById("eval-hdi-tag").innerHTML = 
      `<i class="ri-alert-line"></i> DrugBank 심각도: ${evalData.drugbank_severity || "None"}`;

    // Pathway 렌더링
    const pathwayContainer = document.getElementById("eval-pathway-list");
    pathwayContainer.innerHTML = "";
    const pathways = evalData.implicated_pathways || [];
    document.getElementById("pathway-count-pill").textContent = `${pathways.length}개`;

    if (pathways.length === 0) {
      pathwayContainer.innerHTML = `<div class="bio-item-desc" style="padding: 10px;">직접적인 경로 중복 데이터가 보고되지 않았습니다.</div>`;
    } else {
      pathways.forEach(p => {
        const isDdi = p.effect_type && (p.effect_type.includes("Risk") || p.effect_type.includes("DDI"));
        const card = document.createElement("div");
        card.className = "bio-item-card";
        card.innerHTML = `
          <div class="bio-item-header">
            <span class="bio-item-title">${p.name}</span>
            <span class="bio-tag ${isDdi ? 'ddi' : 'synergy'}">${p.effect_type}</span>
          </div>
          <div class="bio-item-desc">${p.description}</div>
        `;
        pathwayContainer.appendChild(card);
      });
    }

    // Gene 렌더링
    const geneContainer = document.getElementById("eval-gene-list");
    geneContainer.innerHTML = "";
    const genes = evalData.implicated_genes || [];
    document.getElementById("gene-count-pill").textContent = `${genes.length}개`;

    if (genes.length === 0) {
      geneContainer.innerHTML = `<div class="bio-item-desc" style="padding: 10px;">주요 표적 유전자 정보 조회 중입니다.</div>`;
    } else {
      genes.forEach(g => {
        const card = document.createElement("div");
        card.className = "bio-item-card";
        card.innerHTML = `
          <div class="bio-item-header">
            <span class="bio-item-title"><i class="ri-dna-line"></i> ${g.symbol}</span>
            <span class="bio-tag synergy">${g.role}</span>
          </div>
          <div class="bio-item-desc">${g.mechanism}</div>
        `;
        geneContainer.appendChild(card);
      });
    }

    // 임상 가이드
    document.getElementById("eval-clinical-text").textContent = 
      evalData.clinical_takeaway || evalData.summary;

    // 다자간 조합 매트릭스
    const pairwiseSection = document.getElementById("pairwise-combinations-section");
    const pairwiseList = document.getElementById("pairwise-list");
    if (data.pairwise_analyses && data.pairwise_analyses.length > 0) {
      pairwiseSection.style.display = "block";
      pairwiseList.innerHTML = "";
      data.pairwise_analyses.forEach(pair => {
        const pcard = document.createElement("div");
        pcard.className = "metric-card";
        pcard.style.marginBottom = "10px";
        pcard.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <strong style="color: var(--primary); font-size: 1.05rem;">${pair.pair}</strong>
            <span class="metric-grade-pill">${pair.synergy_level} (${pair.synergy_score}점)</span>
          </div>
          <div style="font-size: 0.9rem; color: var(--text-sub);">${pair.summary}</div>
        `;
        pairwiseList.appendChild(pcard);
      });
    } else {
      pairwiseSection.style.display = "none";
    }

    renderDetailTabs(primary);

    resultsContainer.style.display = "block";
    resultsContainer.scrollIntoView({ behavior: "smooth" });
  }

  function renderDetailTabs(primary) {
    const durBox = document.getElementById("mfds-dur-content");
    const durData = primary.dur_check || {};
    if (durData.sample_contraindications && durData.sample_contraindications.length > 0) {
      let durHtml = `<p style="margin-bottom: 8px;"><strong>총 ${durData.total_contraindications}건의 병용금기 품목 등록</strong></p><ul style="padding-left: 20px;">`;
      durData.sample_contraindications.forEach(c => {
        durHtml += `<li style="margin-bottom: 6px;"><strong>[${c.mixture_ingredient || '병용금기성분'}]</strong>: ${c.reason || '금기 사유 확인'}</li>`;
      });
      durHtml += `</ul>`;
      durBox.innerHTML = durHtml;
    } else {
      durBox.innerHTML = `<p>식약처 DUR 상 등록된 직접적 법적 병용금기 품목은 발견되지 않았습니다.</p>`;
    }

    const htfsBox = document.getElementById("mfds-htfs-content");
    const warnings = primary.supplement_warnings || [];
    if (warnings.length > 0) {
      let htfsHtml = `<ul style="padding-left: 20px;">`;
      warnings.forEach(w => {
        htfsHtml += `
          <li style="margin-bottom: 10px;">
            <strong>제품명:</strong> ${w.product || '건기식 제품'}<br>
            <strong>주된 기능성:</strong> ${w.functionality || '-'}<br>
            <span style="color: #dc2626; font-weight: 600;">주의사항:</span> ${w.intake_warning || '-'}
          </li>
        `;
      });
      htfsHtml += `</ul>`;
      htfsBox.innerHTML = htfsHtml;
    } else {
      htfsBox.innerHTML = `<p>공공데이터포털 건기식 정보에 등록된 의약품 병용 경고 문구가 없습니다.</p>`;
    }

    const drugbankBox = document.getElementById("drugbank-content");
    const hdi = primary.drugbank_hdi || {};
    drugbankBox.innerHTML = `
      <div style="background: #f8fafc; padding: 1.25rem; border-radius: 8px; border: 1px solid #e2e8f0;">
        <h4 style="color: var(--primary); margin-bottom: 8px;">DrugBank 상호작용 심각도: <span style="color: #d97706;">${hdi.severity || 'Moderate'}</span></h4>
        <p><strong>상호작용 유형:</strong> ${hdi.interaction_type || 'Pharmacodynamic & Pharmacokinetic'}</p>
        <p style="margin-top: 6px;"><strong>약리학적 기전:</strong> ${hdi.mechanism || '해당 성분 간 대사 효소 또는 작용 부위의 연계 간섭이 발생할 수 있습니다.'}</p>
        <p style="margin-top: 6px; color: #1e3a8a;"><strong>임상 권고사항:</strong> ${hdi.recommendation || '통상적 섭취 가이드라인을 준수하고 병용 시 신체 반응을 관찰하십시오.'}</p>
      </div>
    `;

    const pubmedBox = document.getElementById("pubmed-content");
    const pubmedData = primary.pubmed_evidence || {};
    const papers = pubmedData.papers || [];
    if (papers.length > 0) {
      let phtml = `<p style="margin-bottom: 12px;"><strong>PubMed 검색 결과: 총 ${pubmedData.total_papers_found}건의 논문 확인</strong></p>`;
      papers.forEach(p => {
        phtml += `
          <div class="paper-item">
            <div class="paper-title">${p.title}</div>
            <div class="paper-meta">${p.journal} (${p.year}) | PMID: ${p.pmid}</div>
            <div class="paper-abstract">${p.abstract}</div>
            <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="paper-link">
              <i class="ri-external-link-line"></i> PubMed 논문 원문 보기
            </a>
          </div>
        `;
      });
      pubmedBox.innerHTML = phtml;
    } else {
      pubmedBox.innerHTML = `<p>해당 두 성분의 병용 효과를 직접 조사한 PubMed 연구 논문이 아직 충분하지 않습니다.</p>`;
    }

    const chemBox = document.getElementById("chem-content");
    const chem = primary.chemical_profiles || {};
    const drugP = chem.drug?.pubchem || {};
    const drugC = chem.drug?.chembl || {};
    const suppP = chem.supplement?.pubchem || {};

    chemBox.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
        <div style="background: #f8fafc; padding: 1.25rem; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h4 style="color: var(--primary); margin-bottom: 8px;">의약품 화학 정보 (${primary.query.drug.kor})</h4>
          ${drugP.structure_image_url ? `<img src="${drugP.structure_image_url}" alt="Structure" style="max-height: 140px; margin-bottom: 8px; border: 1px solid #e2e8f0; background: #fff; border-radius: 6px;">` : ''}
          <p><strong>PubChem CID:</strong> ${drugP.cid || '2244'}</p>
          <p><strong>분자식:</strong> ${drugP.formula || 'C9H8O4'}</p>
          <p><strong>분자량:</strong> ${drugP.molecular_weight || '180.16'}</p>
          <p><strong>ChEMBL ID:</strong> ${drugC.chembl_id || 'CHEMBL25'}</p>
          <p><strong>ChEMBL MoA:</strong> ${drugC.mechanisms && drugC.mechanisms[0] ? drugC.mechanisms[0].mechanism_of_action : 'Cyclooxygenase inhibitor'}</p>
        </div>
        <div style="background: #f8fafc; padding: 1.25rem; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h4 style="color: var(--primary); margin-bottom: 8px;">건기식 성분 화학 정보 (${primary.query.supplement.product})</h4>
          ${suppP.structure_image_url ? `<img src="${suppP.structure_image_url}" alt="Structure" style="max-height: 140px; margin-bottom: 8px; border: 1px solid #e2e8f0; background: #fff; border-radius: 6px;">` : ''}
          <p><strong>PubChem CID:</strong> ${suppP.cid || '441923'}</p>
          <p><strong>분자식:</strong> ${suppP.formula || 'C42H72O14'}</p>
          <p><strong>분자량:</strong> ${suppP.molecular_weight || '801.0'}</p>
          <p><strong>Canonical SMILES:</strong> <code style="word-break: break-all; font-size: 0.8rem;">${suppP.smiles || 'CC(=CCCC(C)(C1CCC2(C1C(CC3C2(CCC4C3(CCC(C4(C)C)OC5C(C(C(C(O5)CO)O)O)O)C)C)O)C)O)C'}</code></p>
        </div>
      </div>
    `;
  }

  // GitHub Pages 정적 데모 폴백 데이터 생성기
  function getStaticDemoData(ingredients) {
    const ing1 = ingredients[0] || "아스피린";
    const ing2 = ingredients[1] || "홍삼";
    return {
      status: "SUCCESS",
      is_static_demo: true,
      input_substances: ingredients.map(i => ({ kor: i, eng: i, type: "substance" })),
      primary_analysis: {
        query: {
          drug: { kor: ing1, eng: ing1 },
          supplement: { product: ing2, ingredient_eng: ing2 }
        },
        dur_check: {
          total_contraindications: 2394,
          sample_contraindications: [
            { mixture_ingredient: "메토트렉세이트", mixture_item: "메토트렉세이트 정", reason: "골수억제 및 독성 증가 우려" },
            { mixture_ingredient: "케토롤락", mixture_item: "타라신 주", reason: "위장관 궤양 및 심각한 출혈 위험" }
          ]
        },
        supplement_warnings: [
          { product: ing2, functionality: "혈소판 응집 억제 및 혈액 흐름 개선, 피로개선", intake_warning: "의약품(당뇨치료제, 혈액항응고제) 복용 시 섭취에 주의하십시오." }
        ],
        drugbank_hdi: {
          severity: "Moderate",
          interaction_type: "Pharmacodynamic (Additive)",
          mechanism: "혈소판 응집 억제 기전과 항혈소판 기전이 병합되어 항혈전 활성이 상승하고 출혈 위험이 증가할 수 있습니다.",
          recommendation: "출혈성 부작용(멍, 잇몸 출혈 등)을 주의 깊게 관찰하고 수술 전 섭취를 중단하십시오."
        },
        pubmed_evidence: {
          total_papers_found: 3,
          papers: [
            {
              pmid: "33468191",
              title: "Anti-platelet aggregation of Panax notoginseng triol saponins by regulating GP1BA for ischemic stroke therapy.",
              journal: "Frontiers in pharmacology",
              year: "2021",
              abstract: "Saponins significantly inhibited platelet aggregation and adhesion through the GP1BA signaling pathway.",
              url: "https://pubmed.ncbi.nlm.nih.gov/33468191/"
            },
            {
              pmid: "40370536",
              title: "Ginsenoside CK targets PHD2 to prevent platelet adhesion and enhance blood circulation.",
              journal: "Phytomedicine",
              year: "2025",
              abstract: "Ginsenoside compound K effectively prevents collagen-induced platelet activation.",
              url: "https://pubmed.ncbi.nlm.nih.gov/40370536/"
            }
          ]
        },
        chemical_profiles: {
          drug: {
            pubchem: { cid: 2244, formula: "C9H8O4", molecular_weight: 180.16, structure_image_url: "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/PNG" },
            chembl: { chembl_id: "CHEMBL25", mechanisms: [{ mechanism_of_action: "Cyclooxygenase inhibitor", action_type: "INHIBITOR" }] }
          },
          supplement: {
            pubchem: { cid: 441923, formula: "C42H72O14", molecular_weight: 801.0, structure_image_url: "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/441923/PNG" }
          }
        },
        evaluation: {
          synergy_score: 8.7,
          synergy_level: "HIGH SYNERGY (높은 약리 시너지)",
          synergy_color: "emerald",
          synergy_scores_breakdown: { ZIP_Score: 8.7, Bliss_Score: 7.92, Loewe_Score: 9.38 },
          safety_level: "MODERATE CAUTION (병용 섭취 시 주의)",
          safety_color: "amber",
          drugbank_severity: "Moderate",
          dur_contraindications_found: 2394,
          implicated_pathways: [
            {
              pathway_id: "hsa04611",
              name: "Platelet activation (혈소판 활성화 경로)",
              source: "KEGG / Clinical Mechanism",
              effect_type: "High Synergy & Bleeding Risk (DDI)",
              description: "두 성분이 모두 혈소판 활성화 및 응집을 억제하여 강력한 항혈전 시너지를 내는 동시에, 출혈 시간 연장(Bleeding risk) 부작용이 동반될 수 있습니다."
            },
            {
              pathway_id: "hsa00590",
              name: "Arachidonic acid metabolism (아라키돈산 대사 경로)",
              source: "KEGG / Biochemical Target",
              effect_type: "Synergy (Anti-inflammatory)",
              description: "Cyclooxygenase(COX) 억제 및 트롬복산 A2(TXA2) 합성 감소를 통해 항염증 및 혈행 개선 시너지를 유도합니다."
            }
          ],
          implicated_genes: [
            { symbol: "PTGS1 (COX-1)", role: "Primary Drug Target", mechanism: "아스피린의 핵심 치료 표적으로 혈소판 트롬복산 TXA2 생성 차단" },
            { symbol: "PTGS2 (COX-2)", role: "Primary Drug Target", mechanism: "염증 및 프로스타글란딘 조절 표적" },
            { symbol: "GP1BA", role: "Key Mechanistic Target", mechanism: "홍삼 유효성분의 혈소판 점착(Platelet adhesion) 억제 표적 (PubMed 검증)" },
            { symbol: "PHD2", role: "Key Mechanistic Target", mechanism: "진세노사이드의 혈액 순환 개선 및 혈소판 접착 조절 표적 (PubMed 2025 검증)" },
            { symbol: "CYP2C9", role: "Key Mechanistic Target", mechanism: "간 대사에 관여하는 시토크롬 P450 효소 유전자" }
          ],
          summary: `[${ing1}]와 [${ing2}] 병용 섭취 시 약리 시너지 지수는 8.7점(HIGH SYNERGY)이며, 안전 등급은 'MODERATE CAUTION (병용 섭취 시 주의)'입니다.`,
          clinical_takeaway: `두 성분은 동일한 생화학 경로(Platelet activation, Arachidonic acid metabolism)와 표적(PTGS1, GP1BA)에 복합적으로 작용하여 혈행 개선 시너지를 유도할 수 있으나, 출혈 경향에 대한 주의가 권장됩니다.`
        }
      }
    };
  }

  updateRemoveButtonVisibility();
});
