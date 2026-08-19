// ============================================================================
// LIVE PASS / FAIL EVALUATION PREVIEW
// ============================================================================
function updatePassFailPreview() {
  const marksObtained = parseFloat(document.getElementById('issue-marks')?.value) || 0;
  const totalMarks = parseFloat(document.getElementById('issue-total-marks')?.value) || 500;
  const badge = document.getElementById('pass-fail-badge');
  if (!badge) return;

  if (totalMarks <= 0) {
    badge.textContent = '⚠️ Invalid Total Marks (must be > 0)';
    badge.style.color = '#DE350B';
    return;
  }

  const pct = (marksObtained / totalMarks) * 100.0;
  if (pct >= 75.0) {
    badge.textContent = `🎯 Calculated: ${pct.toFixed(2)}% ➔ PASSED (First Class with Distinction)`;
    badge.style.color = '#00875A';
  } else if (pct >= 60.0) {
    badge.textContent = `🎯 Calculated: ${pct.toFixed(2)}% ➔ PASSED (First Class)`;
    badge.style.color = '#00875A';
  } else if (pct >= 40.0) {
    badge.textContent = `🎯 Calculated: ${pct.toFixed(2)}% ➔ PASSED`;
    badge.style.color = '#00875A';
  } else {
    badge.textContent = `⚠️ Calculated: ${pct.toFixed(2)}% ➔ FAILED (Below 40% Passing Threshold)`;
    badge.style.color = '#DE350B';
  }
}

/**
 * AVFA — Authenticity Validator for Academia (Final Workflow)
 * 10-Page Application Controller, Midnight Academy Theme & Live Camera QR Scanner
 */

// Application State
const state = {
  token: localStorage.getItem('avfa_jwt') || null,
  institution: JSON.parse(localStorage.getItem('avfa_institution') || 'null'),
  currentView: 'page-1-landing',
  pendingEmail: '',
  selectedPdfFile: null,
  recentCertificates: [],
  activeVerifyTab: 'A',
  html5QrScanner: null,
  isScanning: false,
  cameraFacingMode: 'environment'
};

// API Services
const API = {
  baseUrl: '',

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = options.headers || {};

    if (state.token) {
      headers['Authorization'] = `Bearer ${state.token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(url, { ...options, headers });
    const data = await res.json().catch(() => null);

    if (!res.ok) {
      const errorMsg = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
      throw new Error(errorMsg);
    }
    return data;
  },

  // Page 2: Institution Login
  async loginInstitution(official_email, password) {
    return this.request('/institutions/login', {
      method: 'POST',
      body: JSON.stringify({ official_email, password })
    });
  },

  // Page 3: Institution Register
  async registerInstitution(name, official_email, address) {
    return this.request('/institutions/register', {
      method: 'POST',
      body: JSON.stringify({ name, official_email, address })
    });
  },

  // Page 4: Verify OTP
  async verifyOtp(official_email, otp_code) {
    return this.request('/institutions/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ official_email, otp_code })
    });
  },

  // Page 5: Set Password
  async setPassword(official_email, password, confirm_password) {
    return this.request('/institutions/set-password', {
      method: 'POST',
      body: JSON.stringify({ official_email, password, confirm_password })
    });
  },

  // Page 6: Dashboard Stats & Recent Certificates
  async getDashboardStats() {
    return this.request('/certificates/stats');
  },

  async getCertificates(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.request(`/certificates/${query}`);
  },

  async revokeCertificate(certId, reason) {
    return this.request(`/certificates/${certId}/revoke`, {
      method: 'PATCH',
      body: JSON.stringify({ reason: reason || 'Administrative credential audit failed - incomplete prerequisite credits' })
    });
  },

  // Page 7: Issue Certificate
  async issueCertificate(certData) {
    return this.request('/certificates/issue', {
      method: 'POST',
      body: JSON.stringify(certData)
    });
  },

  // Page 9 Tab A: Verify by Certificate Number (Decoded from QR or manually typed)
  async verifyByNumber(certificate_number) {
    return this.request('/certificates/verify', {
      method: 'POST',
      body: JSON.stringify({ certificate_number })
    });
  },

  // Page 9 Tab B: Verify by Document
  async verifyByDocument(formData) {
    return this.request('/certificates/verify-document', {
      method: 'POST',
      body: formData
    });
  }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  updateNavState();

  if (state.token && state.institution) {
    loadDashboardData();
  }
});

// View Router
function navigateTo(pageId) {
  // If navigating away from scanner, stop active camera stream
  if (state.isScanning && pageId !== 'page-9-verify') {
    stopCameraScanner();
  }

  state.currentView = pageId;

  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.remove('active');
  });

  const target = document.getElementById(pageId);
  if (target) {
    target.classList.add('active');
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (pageId === 'page-6-dashboard') {
    loadDashboardData();
  }
}

// Navigation Bar Auth State
function updateNavState() {
  const loginBtn = document.getElementById('nav-login-btn');
  const dashGroup = document.getElementById('nav-dashboard-btn-group');

  if (state.token && state.institution) {
    if (loginBtn) loginBtn.style.display = 'none';
    if (dashGroup) dashGroup.style.display = 'flex';
  } else {
    if (loginBtn) loginBtn.style.display = 'inline-flex';
    if (dashGroup) dashGroup.style.display = 'none';
  }
}

function logoutInstitution() {
  state.token = null;
  state.institution = null;
  localStorage.removeItem('avfa_jwt');
  localStorage.removeItem('avfa_institution');
  updateNavState();
  showToast('Logged out successfully', 'info');
  navigateTo('page-1-landing');
}

// ============================================================================
// PAGE 2: INSTITUTION LOGIN
// ============================================================================
async function handleInstitutionLogin() {
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  try {
    const res = await API.loginInstitution(email, password);
    state.token = res.access_token;
    state.institution = {
      id: res.institution_id,
      name: res.institution_name || 'Academic Institution',
      email: res.official_email || email
    };

    localStorage.setItem('avfa_jwt', res.access_token);
    localStorage.setItem('avfa_institution', JSON.stringify(state.institution));

    updateNavState();
    showToast(`Welcome back, ${state.institution.name}!`, 'success');
    navigateTo('page-6-dashboard');
  } catch (err) {
    showToast(`Login failed: ${err.message}`, 'error');
  }
}

// ============================================================================
// PAGE 3: INSTITUTION REGISTRATION
// ============================================================================
async function handleInstitutionRegister() {
  const name = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const address = document.getElementById('reg-address').value.trim();

  try {
    const res = await API.registerInstitution(name, email, address);
    state.pendingEmail = email;

    if (res.otp_debug) {
      console.log(`%c[AVFA Real OTP]%c Verification Code: ${res.otp_debug}`, 'background: #243B53; color: #FFF; padding: 4px 8px; border-radius: 4px; font-weight: bold;', 'color: #C65D3B; font-weight: bold; font-size: 16px; margin-left: 8px;');
    }

    const emailEl = document.getElementById('otp-target-email');
    if (emailEl) emailEl.textContent = email;

    showToast(res.message || 'OTP sent to official email', 'success');
    navigateTo('page-4-otp');
  } catch (err) {
    if (err.message && err.message.toLowerCase().includes('already registered')) {
      showToast(err.message, 'warning');
      const loginEmail = document.getElementById('login-email');
      if (loginEmail) loginEmail.value = email;
      setTimeout(() => navigateTo('page-2-login'), 1800);
    } else {
      showToast(`Registration failed: ${err.message}`, 'error');
    }
  }
}

// ============================================================================
// PAGE 4: OTP VERIFICATION
// ============================================================================
function handleOtpInput(current, nextId) {
  if (current.value.length >= 1 && nextId) {
    const next = document.getElementById(nextId);
    if (next) next.focus();
  }
}

async function handleVerifyOtp() {
  const code = [
    document.getElementById('otp-1').value,
    document.getElementById('otp-2').value,
    document.getElementById('otp-3').value,
    document.getElementById('otp-4').value,
    document.getElementById('otp-5').value,
    document.getElementById('otp-6').value
  ].join('').trim();

  if (code.length < 6) {
    showToast('Please enter all 6 digits of the OTP code', 'error');
    return;
  }

  const email = state.pendingEmail || document.getElementById('reg-email')?.value.trim();
  if (!email) {
    showToast('Registration email not found. Please start registration first.', 'error');
    navigateTo('page-3-register');
    return;
  }

  try {
    const res = await API.verifyOtp(email, code);
    showToast('OTP verified successfully!', 'success');
    navigateTo('page-5-password');
  } catch (err) {
    showToast(`OTP verification failed: ${err.message}`, 'error');
  }
}

// ============================================================================
// PAGE 5: SET PASSWORD
// ============================================================================
async function handleSetPassword() {
  const pass = document.getElementById('set-pass').value;
  const confirm = document.getElementById('set-pass-confirm').value;

  if (pass !== confirm) {
    showToast('Passwords do not match', 'error');
    return;
  }

  const email = state.pendingEmail || document.getElementById('reg-email')?.value.trim();
  if (!email) {
    showToast('Registration email not found. Please start registration first.', 'error');
    navigateTo('page-3-register');
    return;
  }

  try {
    const res = await API.setPassword(email, pass, confirm);
    showToast(res.message || 'Password set successfully! Please login.', 'success');
    navigateTo('page-2-login');
  } catch (err) {
    showToast(`Failed to set password: ${err.message}`, 'error');
  }
}

// ============================================================================
// PAGE 6: DASHBOARD (POST-LOGIN)
// ============================================================================
let currentFilterStatus = 'ALL';
let pendingRevokeCertId = null;

async function loadDashboardData(search = '') {
  const nameEl = document.getElementById('dash-inst-name');
  if (nameEl && state.institution) {
    nameEl.textContent = state.institution.name;
  }

  try {
    const stats = await API.getDashboardStats();
    const totalIssued = document.getElementById('dash-total-issued');
    const activeCerts = document.getElementById('dash-active-certs');
    const revokedCerts = document.getElementById('dash-revoked-certs');

    if (totalIssued) totalIssued.textContent = stats.certificates_issued;
    if (activeCerts) activeCerts.textContent = stats.active;
    if (revokedCerts) revokedCerts.textContent = stats.revoked;

    let certs = await API.getCertificates(search);
    state.recentCertificates = certs;

    if (currentFilterStatus === 'ISSUED') {
      certs = certs.filter(c => c.status === 'ISSUED');
    } else if (currentFilterStatus === 'REVOKED') {
      certs = certs.filter(c => c.status === 'REVOKED');
    }

    renderDashboardTable(certs);
  } catch (err) {
    console.error('Error loading dashboard data:', err);
  }
}

function renderDashboardTable(certs) {
  const tbody = document.getElementById('dash-cert-table-body');
  if (!tbody) return;

  if (!certs || certs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-text-muted); padding: 2.5rem;">No certificate records matching criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = certs.map(c => {
    let actionHtml = '';
    if (c.status === 'ISSUED') {
      actionHtml = `
        <div style="display: flex; gap: 4px; justify-content: flex-end; align-items: center;">
          <button class="btn btn-sm btn-danger" style="padding: 4px 10px; font-size: 0.78rem; font-weight: 700; background: #DE350B; color: #fff;" onclick="openRevokeModal('${c.id}', '${c.certificate_number}', '${c.student_name.replace(/'/g, "\\'")}')">
            Revoke
          </button>
          <button class="btn btn-sm btn-secondary" style="padding: 4px 8px; font-size: 0.78rem;" onclick="verifyFromDashboard('${c.certificate_number}')">
            Verify
          </button>
          <a href="/generated_certificates/${c.certificate_number}.pdf" target="_blank" class="btn btn-sm btn-ghost" style="padding: 4px 8px; font-size: 0.78rem; color: var(--color-gold);">
            PDF
          </a>
        </div>
      `;
    } else {
      actionHtml = `
        <div style="display: flex; gap: 6px; justify-content: flex-end; align-items: center;">
          <span style="font-size: 0.76rem; color: var(--color-danger); font-weight: 700; background: rgba(222,53,11,0.1); padding: 2px 6px; border-radius: 4px;">Revoked</span>
          <button class="btn btn-sm btn-secondary" style="padding: 4px 8px; font-size: 0.78rem;" onclick="verifyFromDashboard('${c.certificate_number}')">
            Audit Check
          </button>
        </div>
      `;
    }

    return `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: 700; color: var(--color-gold); cursor: pointer;" onclick="verifyFromDashboard('${c.certificate_number}')" title="Click to verify">${c.certificate_number}</td>
        <td style="font-weight: 600;">${c.student_name}</td>
        <td style="font-family: var(--font-mono); font-size: 0.85rem;">${c.student_roll_no}</td>
        <td>${c.course_name}</td>
        <td style="color: var(--color-text-muted); font-size: 0.85rem;">${c.issue_date}</td>
        <td>
          <span class="status-pill ${c.status === 'ISSUED' ? 'valid' : 'revoked'}" style="cursor: pointer;" onclick="filterDashboardStatus('${c.status}')" title="Click to filter by ${c.status}">
            ${c.status === 'ISSUED' ? 'Active' : 'Revoked'}
          </span>
        </td>
        <td style="text-align: right;">
          ${actionHtml}
        </td>
      </tr>
    `;
  }).join('');
}

function handleDashboardSearch(query) {
  loadDashboardData(query);
}

function filterDashboardStatus(status) {
  currentFilterStatus = status;
  
  const allBtn = document.getElementById('filter-all-btn');
  const actBtn = document.getElementById('filter-active-btn');
  const revBtn = document.getElementById('filter-revoked-btn');
  
  if (allBtn && actBtn && revBtn) {
    allBtn.className = status === 'ALL' ? 'btn btn-sm active' : 'btn btn-sm btn-ghost';
    actBtn.className = status === 'ISSUED' ? 'btn btn-sm active' : 'btn btn-sm btn-ghost';
    revBtn.className = status === 'REVOKED' ? 'btn btn-sm active' : 'btn btn-sm btn-ghost';
  }
  
  const query = document.getElementById('dash-search-input')?.value || '';
  loadDashboardData(query);
}

function openRevokeModal(certId, certNumber, studentName) {
  pendingRevokeCertId = certId;
  const modal = document.getElementById('revoke-modal');
  const numEl = document.getElementById('revoke-modal-cert-num');
  const nameEl = document.getElementById('revoke-modal-student-name');
  if (numEl) numEl.textContent = certNumber;
  if (nameEl) nameEl.textContent = studentName;
  if (modal) modal.style.display = 'flex';
}

function closeRevokeModal() {
  pendingRevokeCertId = null;
  const modal = document.getElementById('revoke-modal');
  if (modal) modal.style.display = 'none';
}

async function confirmRevocation() {
  if (!pendingRevokeCertId) return;
  const reason = document.getElementById('revoke-reason-input')?.value.trim() || 'Administrative credential audit failed - incomplete prerequisite credits';
  const confirmBtn = document.getElementById('confirm-revoke-btn');
  if (confirmBtn) confirmBtn.disabled = true;

  try {
    await API.revokeCertificate(pendingRevokeCertId, reason);
    showToast('Certificate revoked successfully and permanently anchored on ledger', 'success');
    closeRevokeModal();
    await loadDashboardData();
  } catch (err) {
    showToast(`Revocation failed: ${err.message}`, 'error');
  } finally {
    if (confirmBtn) confirmBtn.disabled = false;
  }
}

async function verifyFromDashboard(certNumber) {
  navigateTo('page-9-verify');
  const input = document.getElementById('verify-cert-num');
  if (input) input.value = certNumber;
  await handleVerifyByNumber();
}

// ============================================================================
// PAGE 7: ISSUE NEW CERTIFICATE
// ============================================================================
async function handleIssueCertificate() {
  if (!state.token) {
    showToast('Please login as an institution to issue certificates', 'error');
    navigateTo('page-2-login');
    return;
  }

  const student_name = document.getElementById('issue-name').value.trim();
  const student_roll_no = document.getElementById('issue-roll').value.trim();
  const course_name = document.getElementById('issue-course').value.trim();
  const issue_date = document.getElementById('issue-date').value;
  const marksVal = document.getElementById('issue-marks').value.trim();
  const totalMarksVal = document.getElementById('issue-total-marks')?.value.trim() || '500';
  const cgpaVal = document.getElementById('issue-cgpa').value.trim();

  if (!student_name || !student_roll_no || !course_name || !issue_date || !marksVal || !cgpaVal) {
    showToast('All credential parameters (including Marks Obtained, Total Marks, and CGPA) are mandatory.', 'error');
    return;
  }

  const marksNum = parseFloat(marksVal);
  const totalMarksNum = parseFloat(totalMarksVal);
  if (isNaN(marksNum) || isNaN(totalMarksNum) || totalMarksNum <= 0) {
    showToast('Marks Obtained and Total Marks must be valid positive numbers.', 'error');
    return;
  }

  try {
    const newCert = await API.issueCertificate({
      student_name,
      student_roll_no,
      course_name,
      issue_date,
      marks: String(marksNum),
      marks_obtained: String(marksNum),
      total_marks: String(totalMarksNum),
      cgpa: cgpaVal
    });

    document.getElementById('issued-cert-num').textContent = newCert.certificate_number;
    document.getElementById('issued-cert-hash').textContent = newCert.sha256_hash;
    document.getElementById('issued-cert-sig').textContent = newCert.digital_signature;
    document.getElementById('issued-cert-status').innerHTML = `<span class="status-pill valid">${newCert.status}</span>`;

    // Handle generated PDF and Download Certificate button
    if (newCert.pdf_url) {
      const pdfCleanUrl = '/' + newCert.pdf_url.replace(/^\/+/, '');
      const pdfFrame = document.getElementById('issued-pdf-frame');
      const downloadBtn = document.getElementById('download-cert-btn');

      if (pdfFrame) {
        pdfFrame.src = pdfCleanUrl;
      }
      if (downloadBtn) {
        downloadBtn.href = pdfCleanUrl;
        downloadBtn.download = `${newCert.certificate_number}.pdf`;
      }
    }

    showToast('Certificate cryptographically signed and PDF generated!', 'success');
    navigateTo('page-8-issued');
  } catch (err) {
    showToast(`Issuance failed: ${err.message}`, 'error');
  }
}

// ============================================================================
// PAGE 9: VERIFY CERTIFICATE (LIVE CAMERA QR SCANNER & TAB B)
// ============================================================================
function switchVerifyTab(tab) {
  state.activeVerifyTab = tab;
  const btnA = document.getElementById('tab-btn-a');
  const btnB = document.getElementById('tab-btn-b');
  const contentA = document.getElementById('verify-content-a');
  const contentB = document.getElementById('verify-content-b');

  if (tab === 'A') {
    btnA.classList.add('active');
    btnB.classList.remove('active');
    contentA.style.display = 'block';
    contentB.style.display = 'none';
  } else {
    // If leaving Tab A, stop scanner
    stopCameraScanner();
    btnB.classList.add('active');
    btnA.classList.remove('active');
    contentB.style.display = 'block';
    contentA.style.display = 'none';
  }
}

// Start Live Camera QR Scanner
async function startCameraScanner() {
  const idlePlaceholder = document.getElementById('scanner-idle-placeholder');
  const reticle = document.getElementById('scanner-reticle');
  const controls = document.getElementById('camera-controls');

  if (typeof Html5Qrcode === 'undefined') {
    showToast('QR Scanner engine loading... please check internet connection or upload image', 'error');
    return;
  }

  try {
    if (!state.html5QrScanner) {
      state.html5QrScanner = new Html5Qrcode("qr-reader");
    }

    idlePlaceholder.style.display = 'none';
    reticle.style.display = 'block';
    controls.style.display = 'flex';
    state.isScanning = true;

    const config = {
      fps: 15,
      qrbox: { width: 220, height: 220 },
      aspectRatio: 1.333
    };

    await state.html5QrScanner.start(
      { facingMode: state.cameraFacingMode },
      config,
      (decodedText, decodedResult) => {
        onQrCodeScanned(decodedText);
      },
      (errorMessage) => {
        // Continuous parse frames
      }
    );

    showToast('Camera active. Align QR code inside the frame.', 'info');
  } catch (err) {
    console.error('Camera Scanner Error:', err);
    stopCameraScanner();
    showToast(`Camera access issue: ${err.message || err}. Please allow permissions or use file upload.`, 'error');
  }
}

// Stop Live Camera Scanner
async function stopCameraScanner() {
  const idlePlaceholder = document.getElementById('scanner-idle-placeholder');
  const reticle = document.getElementById('scanner-reticle');
  const controls = document.getElementById('camera-controls');

  if (state.html5QrScanner && state.isScanning) {
    try {
      await state.html5QrScanner.stop();
    } catch (e) {
      console.warn('Notice on scanner stop:', e);
    }
  }

  state.isScanning = false;
  if (idlePlaceholder) idlePlaceholder.style.display = 'flex';
  if (reticle) reticle.style.display = 'none';
  if (controls) controls.style.display = 'none';
}

// Switch front / back camera
async function switchCameraFacing() {
  state.cameraFacingMode = (state.cameraFacingMode === 'environment') ? 'user' : 'environment';
  if (state.isScanning) {
    await stopCameraScanner();
    await startCameraScanner();
  }
}

// Scan QR image file from gallery/disk
async function handleQrImageUpload(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];

  if (typeof Html5Qrcode === 'undefined') {
    showToast('QR Scanner engine loading...', 'error');
    return;
  }

  const html5QrCode = new Html5Qrcode("qr-reader");
  try {
    const decodedText = await html5QrCode.scanFile(file, true);
    onQrCodeScanned(decodedText);
  } catch (err) {
    showToast('No readable QR code found in uploaded image.', 'error');
  }
}

// Helper to parse Certificate ID from QR payload, URL, or plain string
function extractCertIdentifier(payload) {
  if (!payload) return '';
  const text = payload.trim();

  // 1. Direct Regex match for standard AVFA format (e.g. CERT-2026-B97DA3E5, AVFA-GIT-2024-001)
  const match = text.match(/\b(CERT-\d{4}-[A-Z0-9]+|AVFA-[A-Z0-9-]+)\b/i);
  if (match) {
    return match[1].toUpperCase();
  }

  // 2. Query string parsing (e.g. ?cert_id=, ?certificate_number=, ?id=, ?verify=, ?hash=)
  if (text.includes('?')) {
    try {
      const url = new URL(text.startsWith('http') ? text : `http://dummy.com/${text}`);
      const param = url.searchParams.get('cert_id') ||
                    url.searchParams.get('certificate_number') ||
                    url.searchParams.get('certificate_id') ||
                    url.searchParams.get('cert_num') ||
                    url.searchParams.get('verify') ||
                    url.searchParams.get('id') ||
                    url.searchParams.get('hash');
      if (param) return param.trim().toUpperCase();
    } catch (e) {
      // ignore
    }
  }

  return text;
}

// Decoded QR payload handler -> Extracts Certificate ID and auto-verifies
async function onQrCodeScanned(decodedText) {
  console.log('QR Code Decoded:', decodedText);

  // Stop camera feed
  stopCameraScanner();

  const cleanCertNum = extractCertIdentifier(decodedText);
  showToast(`QR Scanned: ${cleanCertNum}`, 'success');

  // Auto-fill manual input as reference
  const manualInput = document.getElementById('verify-cert-num');
  if (manualInput) manualInput.value = cleanCertNum;

  // Execute verification immediately
  await executeVerificationByNumber(cleanCertNum);
}

// Manual verify button click handler
window.handleManualVerify = handleVerifyByNumber;
async function handleVerifyByNumber() {
  const rawInput = document.getElementById('verify-cert-num').value.trim();
  if (!rawInput) {
    showToast('Please enter or scan a certificate number', 'error');
    return;
  }
  const certNum = extractCertIdentifier(rawInput);
  await executeVerificationByNumber(certNum);
}

// Execution core for Tab A (QR Scan & Manual Number)
async function executeVerificationByNumber(certNum) {
  try {
    const res = await API.verifyByNumber(certNum);
    renderVerificationResultTabA(res, certNum);
    navigateTo('page-10-result');
  } catch (err) {
    showToast(`Verification failed: ${err.message}`, 'error');
  }
}

function handlePdfFileSelected(input) {
  if (input.files && input.files[0]) {
    state.selectedPdfFile = input.files[0];
    document.getElementById('selected-file-name').textContent = `Selected: ${input.files[0].name} (${(input.files[0].size / 1024).toFixed(1)} KB)`;
  }
}

// Tab B Submit: Verify by Document Upload
async function handleVerifyByDocument() {
  if (!state.selectedPdfFile) {
    showToast('Please select or drag-and-drop a PDF certificate file', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', state.selectedPdfFile);

  try {
    const res = await API.verifyByDocument(formData);
    renderVerificationResultTabB(res);
    navigateTo('page-10-result');
  } catch (err) {
    showToast(`Document verification failed: ${err.message}`, 'error');
  }
}

// ============================================================================
// PAGE 10: VERIFICATION RESULT RENDERING
// ============================================================================

// Render Result for Tab A (By Scanned QR / Certificate Number)
function renderVerificationResultTabA(res, queriedNumber) {
  const container = document.getElementById('result-container');
  if (!container) return;

  const found = res.found;
  const cert = res.certificate;
  const isAuthentic = res.hash_signature_valid;
  const isTampered = res.tamper_detected;

  let indicatorHtml = '';
  if (!found) {
    indicatorHtml = `
      <div class="indicator-banner warning">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 24px; height: 24px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
        <div>
          <div>Record Not Found in Institutional Registry</div>
          <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">No record exists for certificate identifier: ${queriedNumber}</div>
        </div>
      </div>
    `;
  } else if (isAuthentic && !isTampered) {
    indicatorHtml = `
      <div class="indicator-banner valid">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 24px; height: 24px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
        <div>
          <div>Record Authentic ✅</div>
          <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">Cryptographic hash matches immutable institutional registry. RSA-2048 signature valid.</div>
        </div>
      </div>
    `;
  } else {
    indicatorHtml = `
      <div class="indicator-banner tampered">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 24px; height: 24px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
        <div>
          <div>Tamper / Revocation Warning ⚠️</div>
          <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">${cert && cert.status === 'REVOKED' ? `Credential has been revoked: ${cert.revocation_reason || 'Administrative audit'}` : 'Cryptographic integrity violation detected.'}</div>
        </div>
      </div>
    `;
  }

  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.5rem;">
      <h2 style="font-family: var(--font-heading); font-size: 1.75rem; font-weight: 700; color: var(--color-primary);">Verification Result (QR / Certificate ID)</h2>
      <span class="status-pill ${cert && cert.status === 'ISSUED' ? 'valid' : 'revoked'}">${cert ? cert.status : 'NOT_FOUND'}</span>
    </div>

    ${indicatorHtml}

    ${cert ? `
      <div style="background: #FAF8F5; border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 1.5rem; margin-bottom: 1.75rem;">
        <h4 style="color: var(--color-gold); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; font-weight: 700;">Credential Details</h4>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; font-size: 0.92rem;">
          <div><span style="color: var(--color-text-muted);">Student Name:</span> <strong style="color: var(--color-text-main);">${cert.student_name}</strong></div>
          <div><span style="color: var(--color-text-muted);">Roll Number:</span> <strong style="font-family: var(--font-mono); color: var(--color-text-main);">${cert.student_roll_no}</strong></div>
          <div><span style="color: var(--color-text-muted);">Course / Degree:</span> <strong style="color: var(--color-text-main);">${cert.course_name}</strong></div>
          <div><span style="color: var(--color-text-muted);">Issue Date:</span> <strong style="color: var(--color-text-main);">${cert.issue_date}</strong></div>
          <div><span style="color: var(--color-text-muted);">Marks (Obtained / Total):</span> <strong style="color: var(--color-text-main);">${cert.marks || '450'} / ${cert.total_marks || '500'}</strong></div>
          <div><span style="color: var(--color-text-muted);">Academic Evaluation:</span> <strong style="color: ${cert.result_status && cert.result_status.includes('FAIL') ? 'var(--color-danger)' : 'var(--color-success)'}; font-weight: 800;">${cert.result_status || 'PASSED'}</strong></div>
          <div><span style="color: var(--color-text-muted);">CGPA:</span> <strong style="color: var(--color-text-main);">${cert.cgpa || '9.82'}</strong></div>
        </div>

        <div style="margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid var(--color-border);">
          <div style="font-size: 0.72rem; color: var(--color-primary); text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">SHA-256 Hash Digest</div>
          <div style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--color-text-muted); word-break: break-all; margin-top: 0.25rem;">${cert.sha256_hash}</div>
        </div>
      </div>
    ` : ''}

    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
      <button class="btn btn-primary btn-block" onclick="navigateTo('page-9-verify')">Scan Another Certificate</button>
      <button class="btn btn-secondary btn-block" onclick="navigateTo('page-1-landing')">Back to Home</button>
    </div>
  `;
}

// Render Result for Tab B (By Document Upload)
function renderVerificationResultTabB(res) {
  const container = document.getElementById('result-container');
  if (!container) return;

  const found = res.found !== false && res.status !== 'NOT_FOUND';
  const mismatches = res.mismatches || res.field_mismatches || [];
  const docMatches = Boolean(res.document_matches_record) && (res.status === 'ISSUED' || res.status === 'VALID') && mismatches.length === 0;
  const record = res.record;

  let indicatorHtml = '';
  if (!found) {
    indicatorHtml = `
      <div class="indicator-banner warning">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 24px; height: 24px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
        <div>
          <div>Document Not Found in Registry</div>
          <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">The uploaded PDF does not match any registered academic record.</div>
        </div>
      </div>
    `;
  } else if (docMatches && mismatches.length === 0) {
    indicatorHtml = `
      <div class="indicator-banner valid">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 24px; height: 24px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
        <div>
          <div>Document Matches Record ✅</div>
          <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">All extracted fields and digital signature match the authentic registered ledger.</div>
        </div>
      </div>
    `;
  } else {
    indicatorHtml = `
      <div class="indicator-banner tampered">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 24px; height: 24px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
        <div>
          <div>Document Discrepancies Detected ⚠️</div>
          <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">Mismatches found between the uploaded document and the official registered record.</div>
        </div>
      </div>
    `;
  }

  let mismatchTableHtml = '';
  if (mismatches.length > 0) {
    mismatchTableHtml = `
      <div style="margin-bottom: 1.75rem;">
        <h4 style="color: var(--color-danger); font-size: 0.88rem; margin-bottom: 0.75rem; font-weight: 700;">Field Mismatch Breakdown</h4>
        <table class="mismatch-table">
          <thead>
            <tr>
              <th>Field Name</th>
              <th>Document Value (Uploaded)</th>
              <th>Record Value (Official Registry)</th>
            </tr>
          </thead>
          <tbody>
            ${mismatches.map(m => `
              <tr>
                <td style="font-weight: 600; color: var(--color-gold);">${m.field}</td>
                <td style="color: var(--color-danger); font-weight: 700;">${m.document_value}</td>
                <td style="color: var(--color-success); font-weight: 700;">${m.record_value}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.5rem;">
      <h2 style="font-family: var(--font-heading); font-size: 1.75rem; font-weight: 700; color: var(--color-primary);">Document Verification Result</h2>
      <span class="status-pill ${docMatches && mismatches.length === 0 ? 'valid' : 'revoked'}">${res.status || (docMatches ? 'ISSUED' : 'TAMPERED')}</span>
    </div>

    ${indicatorHtml}

    <div style="background: #FAF8F5; border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; font-size: 0.88rem;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span style="color: var(--color-text-muted);">Certificate Number:</span>
        <strong style="font-family: var(--font-mono); color: var(--color-gold);">${res.certificate_number || 'N/A'}</strong>
      </div>
      <div style="display: flex; justify-content: space-between;">
        <span style="color: var(--color-text-muted);">Status:</span>
        <strong style="color: var(--color-primary);">${res.status || 'NOT_FOUND'}</strong>
      </div>
    </div>

    ${mismatchTableHtml}

    ${record ? `
      <div style="background: #FAF8F5; border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 1.5rem; margin-bottom: 1.75rem;">
        <h4 style="color: var(--color-gold); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; font-weight: 700;">Official Registered Record</h4>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; font-size: 0.92rem;">
          <div><span style="color: var(--color-text-muted);">Student Name:</span> <strong style="color: var(--color-text-main);">${record.student_name}</strong></div>
          <div><span style="color: var(--color-text-muted);">Roll Number:</span> <strong style="font-family: var(--font-mono); color: var(--color-text-main);">${record.student_roll_no}</strong></div>
          <div><span style="color: var(--color-text-muted);">Course / Degree:</span> <strong style="color: var(--color-text-main);">${record.course_name}</strong></div>
          <div><span style="color: var(--color-text-muted);">Issue Date:</span> <strong style="color: var(--color-text-main);">${record.issue_date}</strong></div>
        </div>
      </div>
    ` : ''}

    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
      <button class="btn btn-primary btn-block" onclick="navigateTo('page-9-verify')">Verify Another Document</button>
      <button class="btn btn-secondary btn-block" onclick="navigateTo('page-1-landing')">Back to Home</button>
    </div>
  `;
}

// Toast System
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span><span>${message}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
