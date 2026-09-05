// MedVault AI - Clinical Intelligence Frontend Application
let currentPatient = null;
let currentSummaryView = "patient"; // "patient" or "physician"
let currentFilter = {
  search: "",
  category: "ALL",
  status: "ALL"
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  fetchCurrentPatient();
});

function initEventListeners() {
  // Persona Selector
  document.getElementById("personaSelect").addEventListener("change", (e) => {
    loadPersona(e.target.value);
  });

  // Export PDF Button
  document.getElementById("btnExportPdf").addEventListener("click", () => {
    window.location.href = "/api/export-pdf";
  });

  // Tabs Left Pane
  const tabBtnDoc = document.getElementById("tabBtnDoc");
  const tabBtnIntake = document.getElementById("tabBtnIntake");
  const tabDocContent = document.getElementById("tabDocContent");
  const tabIntakeContent = document.getElementById("tabIntakeContent");

  tabBtnDoc.addEventListener("click", () => {
    tabBtnDoc.className = "flex-1 py-2 text-center border-b-2 border-teal-600 text-teal-700 bg-white font-semibold";
    tabBtnIntake.className = "flex-1 py-2 text-center text-slate-500 hover:text-slate-800 font-semibold";
    tabDocContent.classList.remove("hidden");
    tabIntakeContent.classList.add("hidden");
  });

  tabBtnIntake.addEventListener("click", () => {
    tabBtnIntake.className = "flex-1 py-2 text-center border-b-2 border-teal-600 text-teal-700 bg-white font-semibold";
    tabBtnDoc.className = "flex-1 py-2 text-center text-slate-500 hover:text-slate-800 font-semibold";
    tabIntakeContent.classList.remove("hidden");
    tabDocContent.classList.add("hidden");
  });

  // Filter Controls
  document.getElementById("testSearchInput").addEventListener("input", (e) => {
    currentFilter.search = e.target.value.toLowerCase();
    renderLabTable();
  });

  document.getElementById("categoryFilter").addEventListener("change", (e) => {
    currentFilter.category = e.target.value;
    renderLabTable();
  });

  document.getElementById("statusFilter").addEventListener("change", (e) => {
    currentFilter.status = e.target.value;
    renderLabTable();
  });

  // Summary Toggle Buttons
  const togglePatient = document.getElementById("togglePatientSummary");
  const togglePhysician = document.getElementById("togglePhysicianSummary");

  togglePatient.addEventListener("click", () => {
    currentSummaryView = "patient";
    togglePatient.className = "px-2.5 py-1 text-[11px] font-bold rounded-md bg-teal-600 text-white shadow-xs transition";
    togglePhysician.className = "px-2.5 py-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 rounded-md transition";
    renderSummaryView();
  });

  togglePhysician.addEventListener("click", () => {
    currentSummaryView = "physician";
    togglePhysician.className = "px-2.5 py-1 text-[11px] font-bold rounded-md bg-teal-600 text-white shadow-xs transition";
    togglePatient.className = "px-2.5 py-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 rounded-md transition";
    renderSummaryView();
  });

  // Modal Toggles
  setupModal("btnUploadModal", "modalUpload", "btnCloseUpload");
  setupModal("btnAuditLog", "modalAudit", "btnCloseAudit");
  setupModal("btnSafetyModal", "modalSafety", "btnCloseSafety");
  setupModal("btnEditIntake", "modalEditIntake", "btnCloseIntakeModal", populateIntakeForm);
  setupModal(null, "modalVerifyEdit", "btnCloseVerify");
  document.getElementById("btnCancelVerify").addEventListener("click", () => closeModal("modalVerifyEdit"));
  document.getElementById("btnCancelIntake").addEventListener("click", () => closeModal("modalEditIntake"));

  // File Upload Handlers
  setupUploadDropzone();

  // Quick-test sample reports buttons
  document.querySelectorAll(".btnLoadSampleReport").forEach(btn => {
    btn.addEventListener("click", () => {
      const fileName = btn.getAttribute("data-file");
      loadSampleReportFile(fileName);
    });
  });

  // Verification Save Handler
  document.getElementById("btnSaveVerify").addEventListener("click", handleSaveVerification);

  // Intake Save Handler
  document.getElementById("btnSaveIntake").addEventListener("click", handleSaveIntake);
}

function setupModal(triggerId, modalId, closeId, onOpen = null) {
  const modal = document.getElementById(modalId);
  if (triggerId) {
    document.getElementById(triggerId).addEventListener("click", () => {
      if (onOpen) onOpen();
      modal.classList.remove("hidden");
    });
  }
  document.getElementById(closeId).addEventListener("click", () => {
    modal.classList.add("hidden");
  });
}

function openModal(modalId) {
  document.getElementById(modalId).classList.remove("hidden");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.add("hidden");
}

async function fetchCurrentPatient() {
  try {
    const res = await fetch("/api/current-patient");
    currentPatient = await res.json();
    renderAll();
  } catch (err) {
    console.error("Error fetching patient:", err);
  }
}

async function loadPersona(personaId) {
  try {
    const res = await fetch(`/api/load-sample/${personaId}`, { method: "POST" });
    currentPatient = await res.json();
    renderAll();
  } catch (err) {
    console.error("Error loading persona:", err);
  }
}

function renderAll() {
  if (!currentPatient) return;
  renderPatientBanner();
  renderSourceViewer();
  renderIntakeTab();
  renderLabTable();
  renderLongitudinalTrends();
  renderConflicts();
  renderSummaryView();
  renderAuditTrail();
  if (window.lucide) {
    lucide.createIcons();
  }
}

function renderPatientBanner() {
  document.getElementById("patientName").textContent = currentPatient.name;
  document.getElementById("patientDemographics").textContent = `${currentPatient.intake.age} Yrs, ${currentPatient.intake.sex}`;
  document.getElementById("patientId").textContent = `ID: ${currentPatient.patient_id}`;

  // Conditions
  const condContainer = document.getElementById("patientConditionsContainer");
  condContainer.innerHTML = "";
  if (currentPatient.intake.conditions && currentPatient.intake.conditions.length > 0) {
    currentPatient.intake.conditions.forEach(cond => {
      const span = document.createElement("span");
      span.className = "bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded text-[11px] font-medium";
      span.textContent = cond;
      condContainer.appendChild(span);
    });
  } else {
    condContainer.innerHTML = `<span class="text-slate-400 text-[11px]">No conditions listed</span>`;
  }

  // Allergies
  const allergyContainer = document.getElementById("patientAllergiesContainer");
  allergyContainer.innerHTML = "";
  if (currentPatient.intake.allergies && currentPatient.intake.allergies.length > 0) {
    currentPatient.intake.allergies.forEach(all => {
      const span = document.createElement("span");
      span.className = "bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded text-[11px] font-bold";
      span.textContent = all.substance;
      allergyContainer.appendChild(span);
    });
  } else {
    allergyContainer.innerHTML = `<span class="bg-slate-100 text-slate-600 border border-slate-200 px-2 py-0.5 rounded text-[11px]">No Known Drug Allergies (NKDA)</span>`;
  }
}

function renderSourceViewer() {
  const docCount = currentPatient.reports ? currentPatient.reports.length : 0;
  document.getElementById("sourceDocumentCount").textContent = `${docCount} Document${docCount === 1 ? '' : 's'}`;

  const viewer = document.getElementById("rawDocumentViewer");
  if (!currentPatient.reports || currentPatient.reports.length === 0) {
    viewer.innerHTML = `<span class="text-slate-500 italic">No document uploaded yet.</span>`;
    return;
  }

  const latestReport = currentPatient.reports[currentPatient.reports.length - 1];
  document.getElementById("docFileName").textContent = latestReport.filename;
  document.getElementById("docReportDate").textContent = latestReport.report_date;
  document.getElementById("docLabName").textContent = latestReport.lab_name;

  // Split raw text into lines with id for highlight anchoring
  const lines = latestReport.raw_text.split("\n");
  viewer.innerHTML = lines.map((line, idx) => {
    const safeLine = escapeHtml(line);
    return `<div id="src-line-${idx}" class="py-0.5 hover:bg-slate-800 transition rounded px-1">${safeLine || '&nbsp;'}</div>`;
  }).join("");
}

function highlightSourceSnippet(snippet) {
  // Switch to Document Tab if on Intake
  document.getElementById("tabBtnDoc").click();

  const viewer = document.getElementById("rawDocumentViewer");
  const children = viewer.children;
  let targetChild = null;

  // Clean snippet for fuzzy matching
  const cleanSnippet = snippet.toLowerCase().trim();

  for (let el of children) {
    el.classList.remove("highlight-source");
    if (cleanSnippet && el.textContent.toLowerCase().includes(cleanSnippet.slice(0, 20))) {
      targetChild = el;
    }
  }

  if (targetChild) {
    targetChild.classList.add("highlight-source");
    targetChild.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function renderIntakeTab() {
  const intake = currentPatient.intake;
  const sympContainer = document.getElementById("intakeSymptomsList");
  sympContainer.innerHTML = (intake.symptoms && intake.symptoms.length > 0)
    ? intake.symptoms.map(s => `<div class="bg-slate-50 border border-slate-200 px-2 py-1 rounded text-slate-700 font-medium">• ${s}</div>`).join("")
    : `<div class="text-slate-400 italic">None reported</div>`;

  const condContainer = document.getElementById("intakeConditionsList");
  condContainer.innerHTML = (intake.conditions && intake.conditions.length > 0)
    ? intake.conditions.map(c => `<div class="bg-slate-50 border border-slate-200 px-2 py-1 rounded text-slate-700 font-medium">• ${c}</div>`).join("")
    : `<div class="text-slate-400 italic">None reported</div>`;

  const medContainer = document.getElementById("intakeMedicationsList");
  medContainer.innerHTML = (intake.medications && intake.medications.length > 0)
    ? intake.medications.map(m => `<div class="bg-teal-50 border border-teal-200 px-2 py-1 rounded text-teal-900 font-medium">💊 <b>${m.name}</b> (${m.dosage}) ${m.frequency ? '- ' + m.frequency : ''}</div>`).join("")
    : `<div class="text-slate-400 italic">No active medications</div>`;

  const allContainer = document.getElementById("intakeAllergiesList");
  allContainer.innerHTML = (intake.allergies && intake.allergies.length > 0)
    ? intake.allergies.map(a => `<div class="bg-rose-50 border border-rose-200 px-2 py-1 rounded text-rose-900 font-bold">⚠️ ${a.substance} (${a.reaction || 'Reaction unspecified'})</div>`).join("")
    : `<div class="text-slate-500 bg-slate-50 border border-slate-200 px-2 py-1 rounded">No known drug allergies reported</div>`;
}

function renderLabTable() {
  const tbody = document.getElementById("labTableBody");
  tbody.innerHTML = "";

  const labs = currentPatient.current_labs || [];
  let filtered = labs.filter(t => {
    // Search
    const matchSearch = !currentFilter.search || t.name.toLowerCase().includes(currentFilter.search);
    // Category
    const matchCat = currentFilter.category === "ALL" || t.category === currentFilter.category;
    // Status
    let matchStatus = true;
    if (currentFilter.status === "ABNORMAL") {
      matchStatus = (t.status === "HIGH" || t.status === "LOW");
    } else if (currentFilter.status === "HIGH") {
      matchStatus = (t.status === "HIGH");
    } else if (currentFilter.status === "LOW") {
      matchStatus = (t.status === "LOW");
    }
    return matchSearch && matchCat && matchStatus;
  });

  document.getElementById("labCountBadge").textContent = `${filtered.length} of ${labs.length} Tests Shown`;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-400">No laboratory test values match current filter criteria.</td></tr>`;
    return;
  }

  filtered.forEach(t => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-teal-50/40 transition";

    // Status Badge
    let badgeClass = "badge-unspecified";
    let statusText = t.status;
    if (t.status === "HIGH") {
      badgeClass = "badge-high";
      statusText = "▲ HIGH";
    } else if (t.status === "LOW") {
      badgeClass = "badge-low";
      statusText = "▼ LOW";
    } else if (t.status === "NORMAL") {
      badgeClass = "badge-normal";
      statusText = "✔ NORMAL";
    } else if (t.status === "RANGE_NOT_PROVIDED") {
      badgeClass = "badge-unspecified";
      statusText = "⚪ NO RANGE IN SOURCE";
    }

    // Ref text
    const refRangeHtml = t.reference_range.is_present_in_source 
      ? `<span class="font-mono text-slate-700">${t.reference_range.text}</span>` 
      : `<span class="text-[10px] text-slate-400 italic">Not in source report</span>`;

    // Verification
    const verifHtml = t.verified 
      ? `<span class="text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-bold text-[10px] flex items-center space-x-1"><i data-lucide="check" class="w-3 h-3"></i><span>Verified</span></span>`
      : `<span class="text-slate-600 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded text-[10px] font-mono">${Math.round(t.confidence*100)}% AI</span>`;

    tr.innerHTML = `
      <td class="py-2.5 px-3">
        <div class="font-bold text-slate-800">${t.name}</div>
        <div class="text-[10px] text-slate-500">${t.category}</div>
      </td>
      <td class="py-2.5 px-3">
        <span class="font-bold text-sm text-slate-900">${t.value}</span>
        <span class="text-slate-500 text-[11px] ml-1">${t.unit}</span>
      </td>
      <td class="py-2.5 px-3">
        ${refRangeHtml}
      </td>
      <td class="py-2.5 px-3">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">${statusText}</span>
      </td>
      <td class="py-2.5 px-3">
        <button class="btnHighlightDoc text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-0.5 rounded border border-slate-200 flex items-center space-x-1" title="Inspect source in PDF">
          <i data-lucide="file-text" class="w-3 h-3 text-teal-600"></i>
          <span class="truncate max-w-[80px]">P${t.page_number}</span>
        </button>
      </td>
      <td class="py-2.5 px-3">
        ${verifHtml}
      </td>
      <td class="py-2.5 px-3 text-right space-x-1">
        <button class="btnVerifyTest bg-white hover:bg-teal-50 border border-teal-300 text-teal-700 font-semibold px-2 py-1 rounded text-[11px] transition" data-id="${t.id}">
          Verify / Edit
        </button>
      </td>
    `;

    // Button event bindings
    tr.querySelector(".btnHighlightDoc").addEventListener("click", () => {
      highlightSourceSnippet(t.source_snippet);
    });

    tr.querySelector(".btnVerifyTest").addEventListener("click", () => {
      openVerifyModal(t);
    });

    tbody.appendChild(tr);
  });
}

function renderLongitudinalTrends() {
  const container = document.getElementById("trendCardsGrid");
  container.innerHTML = "";

  const trends = currentPatient.trends || [];
  if (trends.length === 0) {
    container.innerHTML = `<div class="col-span-full py-4 text-center text-slate-400 text-xs">Single report session: longitudinal comparison will activate when prior records are present.</div>`;
    return;
  }

  trends.forEach(tr => {
    let arrowIcon = "arrow-right";
    let colorClass = "text-slate-600";
    let bgClass = "bg-slate-50 border-slate-200";

    if (tr.direction === "UP") {
      arrowIcon = "trending-up";
      colorClass = "text-rose-600";
      bgClass = "bg-rose-50/50 border-rose-200";
    } else if (tr.direction === "DOWN") {
      arrowIcon = "trending-down";
      colorClass = "text-emerald-600";
      bgClass = "bg-emerald-50/50 border-emerald-200";
    }

    const card = document.createElement("div");
    card.className = `p-3 rounded-xl border ${bgClass} text-xs flex flex-col justify-between`;
    card.innerHTML = `
      <div class="flex items-center justify-between font-bold text-slate-800 mb-1">
        <span>${tr.test_name}</span>
        <span class="${colorClass} flex items-center space-x-0.5 text-[11px]">
          <i data-lucide="${arrowIcon}" class="w-3.5 h-3.5"></i>
          <span>${tr.delta > 0 ? '+' : ''}${tr.delta} ${tr.unit}</span>
        </span>
      </div>
      <div class="flex items-center justify-between text-slate-500 text-[11px] mt-2 pt-2 border-t border-slate-200/60">
        <div>Prior: <b class="text-slate-700">${tr.previous_value}</b></div>
        <div>➔</div>
        <div>Current: <b class="text-slate-900">${tr.current_value} ${tr.unit}</b></div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderConflicts() {
  const container = document.getElementById("conflictsContainer");
  container.innerHTML = "";

  const conflicts = currentPatient.conflicts || [];
  document.getElementById("conflictBadge").textContent = `${conflicts.length} Safety Flag${conflicts.length === 1 ? '' : 's'}`;

  if (conflicts.length === 0) {
    container.innerHTML = `
      <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-emerald-900 text-xs flex items-center space-x-2">
        <i data-lucide="check-circle" class="w-4 h-4 text-emerald-600 shrink-0"></i>
        <span>No cross-record discrepancies or contraindications detected across current documents.</span>
      </div>
    `;
    return;
  }

  conflicts.forEach(c => {
    let sevBadge = "bg-amber-100 text-amber-800 border-amber-300";
    let borderClass = "border-amber-200 bg-amber-50/60";
    if (c.severity === "CRITICAL") {
      sevBadge = "bg-rose-100 text-rose-800 border-rose-300";
      borderClass = "border-rose-200 bg-rose-50/70";
    }

    const card = document.createElement("div");
    card.className = `border rounded-xl p-3 ${borderClass} space-y-1.5 shadow-2xs`;
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-bold text-slate-900 text-xs">${c.title}</span>
        <span class="text-[10px] px-2 py-0.5 rounded font-bold border ${sevBadge}">${c.severity}</span>
      </div>
      <p class="text-[11px] text-slate-700 leading-snug">${c.description}</p>
      <div class="text-[10px] text-slate-500 bg-white/70 rounded p-1.5 border border-slate-200/50">
        <b>Recommended Action:</b> ${c.recommendation}
      </div>
      <div class="flex justify-between text-[9px] text-slate-400 pt-1">
        <span>Src A: ${c.source_a}</span>
        <span>Src B: ${c.source_b}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderSummaryView() {
  const card = document.getElementById("summaryContentCard");
  const rawText = currentSummaryView === "patient" ? currentPatient.summary_patient : currentPatient.summary_physician;
  
  if (window.marked) {
    card.innerHTML = marked.parse(rawText || "");
  } else {
    card.textContent = rawText || "";
  }

  // Doctor questions
  const qList = document.getElementById("doctorQuestionsList");
  qList.innerHTML = "";
  const questions = currentPatient.questions_for_doctor || [];
  if (questions.length > 0) {
    questions.forEach(q => {
      const li = document.createElement("li");
      li.className = "leading-tight";
      li.textContent = q;
      qList.appendChild(li);
    });
  } else {
    qList.innerHTML = `<li class="text-teal-700 italic">No specific questions generated.</li>`;
  }
}

function renderAuditTrail() {
  const list = document.getElementById("auditLogList");
  list.innerHTML = "";
  const logs = currentPatient.audit_log || [];
  if (logs.length === 0) {
    list.innerHTML = `<div class="text-slate-400 italic">No events logged yet.</div>`;
    return;
  }

  logs.forEach(log => {
    const item = document.createElement("div");
    item.className = "bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs";
    item.innerHTML = `
      <div class="flex justify-between items-center text-[10px] text-slate-400 mb-1">
        <span class="font-mono font-bold text-teal-700">${log.action}</span>
        <span>${log.timestamp}</span>
      </div>
      <p class="text-slate-700 font-medium">${log.details}</p>
      <div class="text-[10px] text-slate-500 mt-1">Actor: <b>${log.actor}</b></div>
    `;
    list.appendChild(item);
  });
}

// Verification Modal Handlers
function openVerifyModal(test) {
  document.getElementById("editTestId").value = test.id;
  document.getElementById("editTestName").value = test.name;
  document.getElementById("editTestValue").value = test.value;
  document.getElementById("editTestUnit").value = test.unit;
  document.getElementById("editTestRefRange").value = test.reference_range.text || "Not in report";
  document.getElementById("editTestSnippet").textContent = test.source_snippet;
  document.getElementById("editTestNotes").value = test.notes || "";
  openModal("modalVerifyEdit");
}

async function handleSaveVerification() {
  const testId = document.getElementById("editTestId").value;
  const val = parseFloat(document.getElementById("editTestValue").value);
  const unit = document.getElementById("editTestUnit").value;
  const reviewer = document.getElementById("editReviewerName").value;
  const notes = document.getElementById("editTestNotes").value;

  try {
    const res = await fetch("/api/verify-test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        test_id: testId,
        verified_value: val,
        verified_unit: unit,
        verified_by: reviewer,
        notes: notes
      })
    });
    currentPatient = await res.json();
    closeModal("modalVerifyEdit");
    renderAll();
  } catch (err) {
    alert("Failed to save verification: " + err);
  }
}

// Patient Intake Edit Handlers
function populateIntakeForm() {
  const intake = currentPatient.intake;
  document.getElementById("intakeFormAge").value = intake.age;
  document.getElementById("intakeFormSex").value = intake.sex;
  document.getElementById("intakeFormSymptoms").value = (intake.symptoms || []).join(", ");
  document.getElementById("intakeFormConditions").value = (intake.conditions || []).join(", ");
  
  const medsStr = (intake.medications || []).map(m => `${m.name}: ${m.dosage}`).join(", ");
  document.getElementById("intakeFormMeds").value = medsStr;

  const allStr = (intake.allergies || []).map(a => `${a.substance}: ${a.reaction || 'Reaction'}`).join(", ");
  document.getElementById("intakeFormAllergies").value = allStr;
}

async function handleSaveIntake() {
  const age = parseInt(document.getElementById("intakeFormAge").value);
  const sex = document.getElementById("intakeFormSex").value;
  const symptoms = document.getElementById("intakeFormSymptoms").value.split(",").map(s => s.trim()).filter(Boolean);
  const conditions = document.getElementById("intakeFormConditions").value.split(",").map(c => c.trim()).filter(Boolean);

  const medsRaw = document.getElementById("intakeFormMeds").value.split(",");
  const medications = medsRaw.map(m => {
    const parts = m.split(":");
    return { name: parts[0]?.trim() || "", dosage: parts[1]?.trim() || "as directed" };
  }).filter(m => m.name);

  const allRaw = document.getElementById("intakeFormAllergies").value.split(",");
  const allergies = allRaw.map(a => {
    const parts = a.split(":");
    return { substance: parts[0]?.trim() || "", reaction: parts[1]?.trim() || "rash/allergic" };
  }).filter(a => a.substance);

  try {
    const res = await fetch("/api/intake", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        age: age,
        sex: sex,
        symptoms: symptoms,
        conditions: conditions,
        medications: medications,
        allergies: allergies
      })
    });
    currentPatient = await res.json();
    closeModal("modalEditIntake");
    renderAll();
  } catch (err) {
    alert("Failed to update intake: " + err);
  }
}

// Upload Setup
function setupUploadDropzone() {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-teal-600", "bg-teal-100/50");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-teal-600", "bg-teal-100/50");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-teal-600", "bg-teal-100/50");
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      uploadFile(fileInput.files[0]);
    }
  });
}

async function uploadFile(file) {
  const statusMsg = document.getElementById("uploadStatusMessage");
  statusMsg.classList.remove("hidden", "text-rose-600", "text-emerald-600");
  statusMsg.classList.add("text-slate-600");
  statusMsg.textContent = `Extracting and analyzing '${file.name}'...`;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload-report", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Failed to parse document");
    }

    currentPatient = await res.json();
    statusMsg.classList.remove("text-slate-600");
    statusMsg.classList.add("text-emerald-600");
    statusMsg.textContent = `Successfully processed '${file.name}'!`;

    setTimeout(() => {
      closeModal("modalUpload");
      statusMsg.classList.add("hidden");
      renderAll();
    }, 900);

  } catch (err) {
    statusMsg.classList.remove("text-slate-600");
    statusMsg.classList.add("text-rose-600");
    statusMsg.textContent = "Error: " + err.message;
  }
}

// Quick Load Demo Sample PDF directly from server
async function loadSampleReportFile(fileName) {
  const statusMsg = document.getElementById("uploadStatusMessage");
  statusMsg.classList.remove("hidden", "text-rose-600");
  statusMsg.classList.add("text-slate-600");
  statusMsg.textContent = `Loading sample report '${fileName}'...`;

  try {
    // In our backend, we can create a quick mock upload call or upload the file content
    const response = await fetch(`/api/current-patient`);
    // Alternatively upload directly via formData
    statusMsg.textContent = `Processing and extracting '${fileName}'...`;
    
    // We trigger persona or load based on file
    if (fileName.includes("Metabolic")) {
      await loadPersona("sarah-jenkins");
    } else if (fileName.includes("Lipid")) {
      await loadPersona("robert-vance");
    } else if (fileName.includes("Thyroid")) {
      await loadPersona("elena-rostova");
    }
    
    setTimeout(() => {
      closeModal("modalUpload");
      statusMsg.classList.add("hidden");
    }, 600);

  } catch (err) {
    statusMsg.classList.add("text-rose-600");
    statusMsg.textContent = "Error loading sample: " + err.message;
  }
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
