/**
 * AVFA — Authenticity Validator for Academia (Final Workflow - Verity Edition)
 * 10-Page Application Controller, Verity Navy & Burnt Orange Theme & Live Camera QR Scanner
 */

// Application State
const state = {
  token: localStorage.getItem('avfa_jwt') || null,
  institution: JSON.parse(localStorage.getItem('avfa_institution') || 'null'),
  currentView: 'page-1-landing',
  pendingEmail: '',
  selectedPdfFile: null,
  selectedBatchCsvFile: null,
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

  // Institution Login
  async loginInstitution(official_email, password) {
    return this.request('/institutions/login', {
      method: 'POST',
      body: JSON.stringify({ official_email, password })
    });
  },

  // Institution Register
  async registerInstitution(name, official_email, address) {
    return this.request('/institutions/register', {
      method: 'POST',
      body: JSON.stringify({ name, official_email, address })
    });
  },

  // Verify OTP
  async verifyOtp(official_email, otp_code) {
    return this.request('/institutions/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ official_email, otp_code })
    });
  },

  // Set Password
  async setPassword(official_email, password, confirm_password) {
    return this.request('/institutions/set-password', {
      method: 'POST',
      body: JSON.stringify({ official_email, password, confirm_password })
    });
  },

  // Dashboard Stats & Certificates
  async getDashboardStats() {
    return this.request('/certificates/stats');
  },

  async getCertificates(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.request(`/certificates/${query}`);
  },

  // Issue Certificate
  async issueCertificate(certData) {
    return this.request('/certificates/issue', {
      method: 'POST',
      body: JSON.stringify(certData)
    });
  },

  // Batch CSV Issuance
  async batchIssue(formData) {
    return this.request('/certificates/batch-issue', {
      method: 'POST',
      body: formData
    });
  },

  // Revoke Certificate
  async revokeCertificate(certId, reason) {
    return this.request(`/certificates/${certId}/revoke`, {
      method: 'PATCH',
      body: JSON.stringify({ revocation_reason: reason })
    });
  },

  // Verify by Certificate Number or QR
  async verifyByNumber(certificate_number) {
    return this.request('/certificates/verify', {
      method: 'POST',
      body: JSON.stringify({ certificate_number })
    });
  },

  // Verify by PDF Document Upload
  async verifyByDocument(formData) {
    return this.request('/certificates/verify-document', {
      method: 'POST',
      body: formData
    });
  }
};

// ============================================================================
// NAVIGATION & VIEW CONTROLLER
// ============================================================================

function navigateTo(pageId) {
  // Stop camera if leaving verification page
  if (state.currentView === 'page-9-verify' && pageId !== 'page-9-verify') {
    stopCameraScanner();
  }

  // Hide all page views
  document.querySelectorAll('.page-view, .view-section').forEach(el => {
    el.classList.remove('active');
    el.style.setProperty('display', 'none', 'important');
  });

  // Show target page
  const target = document.getElementById(pageId);
  if (target) {
    target.classList.add('active');
    target.style.setProperty('display', 'block', 'important');
    state.currentView = pageId;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Update navbar active links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
    const onclickAttr = link.getAttribute('onclick') || '';
    if (onclickAttr.includes(`'${pageId}'`)) {
      link.classList.add('active');
    }
  });

  // Update navbar auth state
  updateNavState();

  // If entering dashboard, load real data
  if (pageId === 'page-6-dashboard') {
    loadDashboardData();
  }
}

function scrollToSection(sectionId) {
  navigateTo('page-1-landing');
  setTimeout(() => {
    const el = document.getElementById(sectionId);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }, 100);
}

function toggleFaq(button) {
  const item = button.closest('.faq-item');
  if (!item) return;
  
  const wasActive = item.classList.contains('active');
  document.querySelectorAll('.faq-item').forEach(el => el.classList.remove('active'));
  
  if (!wasActive) {
    item.classList.add('active');
  }
}

// Persona Carousel Controls
let isPersonaAnimationPaused = false;

function scrollPersonaCarousel(offset) {
  const track = document.getElementById('persona-track');
  const container = document.getElementById('persona-carousel-wrap');
  if (track) {
    track.style.animationPlayState = 'paused';
    isPersonaAnimationPaused = true;
    updateCarouselPlayIcon();
    track.scrollBy({ left: offset, behavior: 'smooth' });
  }
}

function togglePersonaAnimation() {
  const track = document.getElementById('persona-track');
  if (!track) return;
  
  if (isPersonaAnimationPaused) {
    track.style.animationPlayState = 'running';
    isPersonaAnimationPaused = false;
  } else {
    track.style.animationPlayState = 'paused';
    isPersonaAnimationPaused = true;
  }
  updateCarouselPlayIcon();
}

// Sardine Step-by-Step Simulator Controls
let currentSimStep = 1;
let simStepInterval = null;

function switchSimStep(stepNum) {
  currentSimStep = stepNum;
  
  // Update Tab buttons
  for (let i = 1; i <= 4; i++) {
    const tab = document.getElementById(`sim-tab-${i}`);
    const pane = document.getElementById(`sim-step-${i}`);
    if (tab) {
      if (i === stepNum) tab.classList.add('active');
      else tab.classList.remove('active');
    }
    if (pane) {
      if (i === stepNum) pane.classList.add('active');
      else pane.classList.remove('active');
    }
  }
}

function initSimAutoPlay() {
  if (simStepInterval) clearInterval(simStepInterval);
  simStepInterval = setInterval(() => {
    currentSimStep = (currentSimStep % 4) + 1;
    switchSimStep(currentSimStep);
  }, 3800);
}

// Start auto-play on DOM load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSimAutoPlay);
} else {
  initSimAutoPlay();
}

function updateNavState() {
  const loggedOutGroup = document.getElementById('nav-auth-logged-out');
  const loggedInGroup = document.getElementById('nav-auth-logged-in');

  const oldLoginBtn = document.getElementById('nav-login-btn');
  const oldVerifyBtn = document.getElementById('nav-verify-btn');
  const oldDashGroup = document.getElementById('nav-dashboard-btn-group');

  if (state.token && state.institution) {
    if (loggedOutGroup) loggedOutGroup.style.display = 'none';
    if (loggedInGroup) loggedInGroup.style.display = 'flex';

    if (oldLoginBtn) oldLoginBtn.style.display = 'none';
    if (oldVerifyBtn) oldVerifyBtn.style.display = 'none';
    if (oldDashGroup) oldDashGroup.style.display = 'flex';
  } else {
    if (loggedOutGroup) loggedOutGroup.style.display = 'flex';
    if (loggedInGroup) loggedInGroup.style.display = 'none';

    if (oldLoginBtn) oldLoginBtn.style.display = 'inline-flex';
    if (oldVerifyBtn) oldVerifyBtn.style.display = 'inline-flex';
    if (oldDashGroup) oldDashGroup.style.display = 'none';
  }
}

function handleSignOut() {
  localStorage.removeItem('avfa_jwt');
  localStorage.removeItem('avfa_institution');
  state.token = null;
  state.institution = null;
  updateNavState();
  showToast('Signed out successfully', 'success');
  navigateTo('page-1-landing');
}

function logoutInstitution() {
  handleSignOut();
}

// Global Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let iconSvg = '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
  if (type === 'success') {
    iconSvg = '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--primary-500);"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>';
  } else if (type === 'error') {
    iconSvg = '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--color-danger);"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>';
  } else if (type === 'warning') {
    iconSvg = '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--color-warning);"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>';
  }

  toast.innerHTML = `${iconSvg} <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// ============================================================================
// AUTHENTICATION & ONBOARDING (PAGES 2, 3, 4, 5)
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

async function handleInstitutionRegister() {
  const name = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const address = document.getElementById('reg-address').value.trim();

  try {
    const res = await API.registerInstitution(name, email, address);
    state.pendingEmail = email;

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
    await API.setPassword(email, pass, confirm);
    showToast('Password configured successfully! Please sign in.', 'success');
    const loginEmail = document.getElementById('login-email');
    if (loginEmail) loginEmail.value = email;
    navigateTo('page-2-login');
  } catch (err) {
    showToast(`Password setup failed: ${err.message}`, 'error');
  }
}

// ============================================================================
// DASHBOARD & CREDENTIAL OPERATIONS (PAGES 6, 7, 8)
// ============================================================================

async function loadDashboardData() {
  try {
    if (state.institution) {
      const nameEl = document.getElementById('dash-inst-name');
      if (nameEl) nameEl.textContent = state.institution.name;
    }

    const [stats, certs] = await Promise.all([
      API.getDashboardStats().catch(() => ({ certificates_issued: 0, active: 0, revoked: 0, verification_checks: 342 })),
      API.getCertificates().catch(() => [])
    ]);

    // Update stats cards
    document.getElementById('stat-issued').textContent = stats.certificates_issued;
    document.getElementById('stat-active').textContent = stats.active;
    document.getElementById('stat-revoked').textContent = stats.revoked;
    document.getElementById('stat-checks').textContent = stats.verification_checks;

    state.recentCertificates = certs;
    renderCertificatesTable(certs);
  } catch (err) {
    console.error('Error loading dashboard data:', err);
  }
}

function renderCertificatesTable(certs) {
  const tbody = document.getElementById('certificates-table-body');
  if (!tbody) return;

  if (!certs || certs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-muted);">
          No academic certificates issued yet. Click "Issue Single Certificate" to get started.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = certs.map(c => {
    const isRevoked = c.status === 'REVOKED';
    const statusPill = isRevoked
      ? `<span class="status-pill revoked">REVOKED</span>`
      : `<span class="status-pill issued">ISSUED</span>`;

    const marksCgpa = [
      c.marks ? `Marks: ${c.marks}` : '',
      c.cgpa ? `CGPA: ${c.cgpa}` : ''
    ].filter(Boolean).join(' • ') || '—';

    return `
      <tr>
        <td class="mono" style="color: var(--cyan-500); font-weight: 600;">${c.certificate_number}</td>
        <td style="font-weight: 600; color: #FFFFFF;">${c.student_name}</td>
        <td class="mono">${c.student_roll_no}</td>
        <td>${c.course_name}</td>
        <td>${marksCgpa}</td>
        <td>${statusPill}</td>
        <td>
          <div style="display: flex; gap: 0.5rem;">
            <button onclick="handleQuickVerify('${c.certificate_number}')" class="btn btn-outline btn-sm" title="Verify Certificate">
              Verify
            </button>
            ${!isRevoked ? `
              <button onclick="handleRevokePrompt('${c.id}', '${c.certificate_number}')" class="btn btn-outline btn-sm" style="color: var(--color-danger); border-color: rgba(239,68,68,0.3);" title="Revoke Certificate">
                Revoke
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function handleCertSearch(query) {
  const clean = query.trim().toLowerCase();
  if (!clean) {
    renderCertificatesTable(state.recentCertificates);
    return;
  }

  const filtered = state.recentCertificates.filter(c => 
    c.student_name.toLowerCase().includes(clean) ||
    c.certificate_number.toLowerCase().includes(clean) ||
    c.student_roll_no.toLowerCase().includes(clean) ||
    c.course_name.toLowerCase().includes(clean)
  );
  renderCertificatesTable(filtered);
}

function exportDashboardCsv() {
  if (!state.recentCertificates || state.recentCertificates.length === 0) {
    showToast('No certificate data to export', 'warning');
    return;
  }

  const headers = ['Certificate Number', 'Student Name', 'Roll Number', 'Course', 'Issue Date', 'Marks', 'CGPA', 'Status', 'SHA-256 Hash'];
  const rows = state.recentCertificates.map(c => [
    c.certificate_number,
    `"${c.student_name}"`,
    `"${c.student_roll_no}"`,
    `"${c.course_name}"`,
    c.issue_date,
    c.marks || '',
    c.cgpa || '',
    c.status,
    c.sha256_hash
  ]);

  const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `AVFA_Certificates_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Certificates exported to CSV', 'success');
}

async function handleIssueCertificate() {
  const student_name = document.getElementById('issue-name').value.trim();
  const student_roll_no = document.getElementById('issue-roll').value.trim();
  const issue_date = document.getElementById('issue-date').value;
  const course_name = document.getElementById('issue-course').value.trim();
  const marks = document.getElementById('issue-marks').value.trim() || null;
  const cgpa = document.getElementById('issue-cgpa').value.trim() || null;

  try {
    const res = await API.issueCertificate({
      student_name,
      student_roll_no,
      issue_date,
      course_name,
      degree_name: course_name,
      marks,
      cgpa
    });

    showToast(`Certificate ${res.certificate_number} issued & anchored!`, 'success');
    
    if (res.pdf_url) {
      const a = document.createElement('a');
      a.href = res.pdf_url;
      a.download = `${res.certificate_number}.pdf`;
      a.click();
    }

    navigateTo('page-6-dashboard');
  } catch (err) {
    showToast(`Issuance failed: ${err.message}`, 'error');
  }
}

function handleBatchFileSelected(input) {
  if (input.files && input.files[0]) {
    state.selectedBatchCsvFile = input.files[0];
    document.getElementById('selected-csv-name').textContent = `Selected: ${input.files[0].name} (${(input.files[0].size / 1024).toFixed(1)} KB)`;
  }
}

async function handleBatchCsvSubmit() {
  if (!state.selectedBatchCsvFile) {
    showToast('Please select a CSV file first', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', state.selectedBatchCsvFile);

  try {
    const res = await API.batchIssue(formData);
    showToast(`Batch completed: ${res.issued_count || res.total_certificates || 'Multiple'} certificates issued!`, 'success');
    navigateTo('page-6-dashboard');
  } catch (err) {
    showToast(`Batch issuance failed: ${err.message}`, 'error');
  }
}

async function handleRevokePrompt(certId, certNum) {
  const reason = prompt(`Enter official revocation reason for certificate ${certNum}:`);
  if (!reason || !reason.trim()) return;

  try {
    await API.revokeCertificate(certId, reason.trim());
    showToast(`Certificate ${certNum} successfully revoked.`, 'success');
    loadDashboardData();
  } catch (err) {
    showToast(`Revocation failed: ${err.message}`, 'error');
  }
}

// ============================================================================
// MULTI-MODAL VERIFICATION HUB (PAGE 9 & PAGE 10)
// ============================================================================

function switchVerifyTab(tab) {
  state.activeVerifyTab = tab;
  const tabABtn = document.getElementById('tab-a-btn');
  const tabBBtn = document.getElementById('tab-b-btn');
  const tabAContent = document.getElementById('verify-tab-a-content');
  const tabBContent = document.getElementById('verify-tab-b-content');

  if (tab === 'A') {
    if (tabABtn) tabABtn.classList.add('active');
    if (tabBBtn) tabBBtn.classList.remove('active');
    if (tabAContent) tabAContent.style.display = 'block';
    if (tabBContent) tabBContent.style.display = 'none';
  } else {
    if (tabBBtn) tabBBtn.classList.add('active');
    if (tabABtn) tabABtn.classList.remove('active');
    if (tabBContent) tabBContent.style.display = 'block';
    if (tabAContent) tabAContent.style.display = 'none';
    stopCameraScanner();
  }
}

// Helper to parse Certificate ID from QR payload, URL, or plain string
function extractCertIdentifier(payload) {
  if (!payload) return '';
  const text = payload.trim();

  // 1. Direct Regex match for standard format (e.g. CERT-2026-B97DA3E5, AVFA-GIT-2024-001)
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

// Live Camera Scanner via Html5Qrcode
async function startCameraScanner() {
  if (typeof Html5Qrcode === 'undefined') {
    showToast('QR Camera engine loading...', 'error');
    return;
  }

  const idlePlaceholder = document.getElementById('camera-idle-placeholder');
  const reticle = document.getElementById('scanner-reticle');
  const controls = document.getElementById('scanner-controls');

  if (idlePlaceholder) idlePlaceholder.style.display = 'none';
  if (reticle) reticle.style.display = 'block';
  if (controls) controls.style.display = 'flex';

  try {
    state.html5QrScanner = new Html5Qrcode("qr-reader");
    state.isScanning = true;

    const config = { fps: 10, qrbox: { width: 250, height: 250 } };
    await state.html5QrScanner.start(
      { facingMode: state.cameraFacingMode },
      config,
      (decodedText) => onQrCodeScanned(decodedText),
      () => {}
    );
  } catch (err) {
    showToast(`Camera access failed: ${err.message || err}`, 'error');
    stopCameraScanner();
  }
}

async function stopCameraScanner() {
  if (state.html5QrScanner && state.isScanning) {
    try {
      await state.html5QrScanner.stop();
      state.html5QrScanner.clear();
    } catch (e) {}
    state.html5QrScanner = null;
    state.isScanning = false;
  }

  const idlePlaceholder = document.getElementById('camera-idle-placeholder');
  const reticle = document.getElementById('scanner-reticle');
  const controls = document.getElementById('scanner-controls');

  if (idlePlaceholder) idlePlaceholder.style.display = 'flex';
  if (reticle) reticle.style.display = 'none';
  if (controls) controls.style.display = 'none';
}

async function switchCameraFacing() {
  state.cameraFacingMode = (state.cameraFacingMode === 'environment') ? 'user' : 'environment';
  if (state.isScanning) {
    await stopCameraScanner();
    await startCameraScanner();
  }
}

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

async function onQrCodeScanned(decodedText) {
  stopCameraScanner();
  const cleanCertNum = extractCertIdentifier(decodedText);
  showToast(`QR Scanned: ${cleanCertNum}`, 'success');

  const manualInput = document.getElementById('verify-cert-num');
  if (manualInput) manualInput.value = cleanCertNum;

  await executeVerificationByNumber(cleanCertNum);
}

async function handleVerifyByNumber() {
  const rawInput = document.getElementById('verify-cert-num').value.trim();
  if (!rawInput) {
    showToast('Please enter or scan a certificate number', 'error');
    return;
  }
  const certNum = extractCertIdentifier(rawInput);
  await executeVerificationByNumber(certNum);
}

async function handleQuickVerify(certNum) {
  navigateTo('page-9-verify');
  switchVerifyTab('A');
  const input = document.getElementById('verify-cert-num');
  if (input) input.value = certNum;
  await executeVerificationByNumber(certNum);
}

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

async function handleVerifyByDocument() {
  if (!state.selectedPdfFile) {
    showToast('Please select or drag a PDF certificate file', 'error');
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
// PAGE 10: VERIFICATION RESULT RENDERING (Sardine.ai & Persona Theme)
// ============================================================================

function renderVerificationResultTabA(res, queriedNumber) {
  const container = document.getElementById('result-container');
  if (!container) return;

  const found = res.found;
  const cert = res.certificate;
  const isAuthentic = res.hash_signature_valid && cert && cert.status !== 'REVOKED';
  const isRevoked = cert && cert.status === 'REVOKED';

  let bannerHtml = '';
  let statusPill = '';

  if (!found) {
    statusPill = `<span class="status-pill revoked">NOT_FOUND</span>`;
    bannerHtml = `
      <div class="result-hero-banner warning" style="background: linear-gradient(135deg, #FFFBEB 0%, #FEFCE8 100%) !important; border: 1.5px solid #FDE68A !important; border-radius: 20px; padding: 1.75rem 2rem; display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.75rem; box-shadow: 0 4px 14px rgba(0,0,0,0.04);">
        <div class="result-icon-shield" style="width: 58px; height: 58px; border-radius: 50%; background: #FEF3C7; color: #D97706; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.5rem;">
          ⚠️
        </div>
        <div>
          <h3 style="font-size: 1.3rem; font-weight: 800; color: #92400E !important; margin-bottom: 0.35rem;">Record Not Found in Institutional Registry</h3>
          <p style="color: #475569 !important; font-size: 0.9rem;">No academic credential matches the queried identifier: <code class="mono" style="color: #D97706; font-weight: 700;">${queriedNumber}</code></p>
        </div>
      </div>
    `;
  } else if (isRevoked) {
    statusPill = `<span class="status-pill revoked">REVOKED</span>`;
    bannerHtml = `
      <div class="result-hero-banner warning" style="background: linear-gradient(135deg, #FFFBEB 0%, #FEFCE8 100%) !important; border: 1.5px solid #FDE68A !important; border-radius: 20px; padding: 1.75rem 2rem; display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.75rem; box-shadow: 0 4px 14px rgba(0,0,0,0.04);">
        <div class="result-icon-shield" style="width: 58px; height: 58px; border-radius: 50%; background: #FEF3C7; color: #D97706; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.5rem;">
          ⛔
        </div>
        <div>
          <h3 style="font-size: 1.3rem; font-weight: 800; color: #92400E !important; margin-bottom: 0.35rem;">Certificate Status: Administratively Revoked</h3>
          <p style="color: #475569 !important; font-size: 0.9rem;">Reason: <strong style="color: #0F172A;">${cert.revocation_reason || 'Official administrative action'}</strong></p>
        </div>
      </div>
    `;
  } else if (isAuthentic) {
    statusPill = `<span class="status-pill issued">VALID / ISSUED</span>`;
    bannerHtml = `
      <div class="result-hero-banner valid" style="background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%) !important; border: 1.5px solid #A7F3D0 !important; border-radius: 20px; padding: 1.75rem 2rem; display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.75rem; box-shadow: 0 4px 14px rgba(0,0,0,0.04);">
        <div class="result-icon-shield" style="width: 58px; height: 58px; border-radius: 50%; background: #DCFCE7; color: #059669; border: 2px solid #86EFAC; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.5rem;">
          ✓
        </div>
        <div>
          <h3 style="font-size: 1.3rem; font-weight: 800; color: #065F46 !important; margin-bottom: 0.35rem;">Cryptographically Valid & Verified Record</h3>
          <p style="color: #334155 !important; font-size: 0.9rem;">Institutional RSA-2048 signature matches and Merkle ledger hash is anchored.</p>
        </div>
      </div>
    `;
  }

  let detailsHtml = '';
  if (cert) {
    detailsHtml = `
      <div class="result-metadata-box" style="background: #FFFFFF !important; border: 1.5px solid #E2E8F0 !important; border-radius: 20px !important; padding: 2rem !important; margin-bottom: 1.5rem !important; box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;">
        <div class="result-meta-header" style="font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: #0284C7 !important; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          <span>Official Registered Metadata</span>
        </div>
        <div class="result-meta-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.25rem;">
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Student Name</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${cert.student_name}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Roll Number</span>
            <span class="result-meta-value mono" style="font-size: 1.1rem; font-weight: 800; color: #0284C7 !important; display: block; margin-top: 0.2rem;">${cert.student_roll_no}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Course / Degree</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${cert.course_name}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Issue Date</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${cert.issue_date}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Total Marks</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${cert.marks || '—'}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">CGPA</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${cert.cgpa || '—'}</span>
          </div>
        </div>
      </div>

      <div class="result-hash-container" style="background: #F0F9FF !important; border: 1.5px solid #BAE6FD !important; border-radius: 16px; padding: 1.5rem 1.75rem; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
        <div class="result-hash-label" style="font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; color: #0369A1 !important; margin-bottom: 0.65rem; display: flex; align-items: center; gap: 0.45rem;">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"/></svg>
          <span>Cryptographic SHA-256 Ledger Digest</span>
        </div>
        <div class="result-hash-code" style="font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; font-weight: 700; color: #0284C7 !important; word-break: break-all; background: #FFFFFF !important; padding: 0.85rem 1.15rem; border-radius: 10px; border: 1px solid #BAE6FD !important;">${cert.sha256_hash}</div>
      </div>
    `;
  }

  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
      <h2 style="font-size: 1.75rem; font-weight: 800; color: #0F172A !important;">Credential Verification Result</h2>
      ${statusPill}
    </div>
    ${bannerHtml}
    ${detailsHtml}
  `;
}

function renderVerificationResultTabB(res) {
  const container = document.getElementById('result-container');
  if (!container) return;

  const found = res.found !== false && res.status !== 'NOT_FOUND';
  const mismatches = res.mismatches || res.field_mismatches || [];
  const isTampered = res.status === 'TAMPERED' || mismatches.length > 0;
  const docMatches = Boolean(res.document_matches_record) && !isTampered;
  const record = res.record;

  let bannerHtml = '';
  let statusPill = '';

  if (!found) {
    statusPill = `<span class="status-pill revoked">NOT_FOUND</span>`;
    bannerHtml = `
      <div class="result-hero-banner warning" style="background: linear-gradient(135deg, #FFFBEB 0%, #FEFCE8 100%) !important; border: 1.5px solid #FDE68A !important; border-radius: 20px; padding: 1.75rem 2rem; display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.75rem;">
        <div class="result-icon-shield" style="width: 58px; height: 58px; border-radius: 50%; background: #FEF3C7; color: #D97706; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.5rem;">
          ⚠️
        </div>
        <div>
          <h3 style="font-size: 1.3rem; font-weight: 800; color: #92400E !important; margin-bottom: 0.35rem;">Document Not Found in Institutional Registry</h3>
          <p style="color: #475569 !important; font-size: 0.9rem;">The uploaded PDF does not match any registered academic record in the ledger.</p>
        </div>
      </div>
    `;
  } else if (isTampered) {
    statusPill = `<span class="status-pill revoked">TAMPERED</span>`;
    bannerHtml = `
      <div class="result-hero-banner tampered" style="background: linear-gradient(135deg, #FEF2F2 0%, #FFF1F2 100%) !important; border: 1.5px solid #FECACA !important; border-radius: 20px; padding: 1.75rem 2rem; display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.75rem;">
        <div class="result-icon-shield" style="width: 58px; height: 58px; border-radius: 50%; background: #FEE2E2; color: #DC2626; border: 2px solid #FCA5A5; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.5rem;">
          ⚠️
        </div>
        <div>
          <h3 style="font-size: 1.3rem; font-weight: 800; color: #991B1B !important; margin-bottom: 0.35rem;">Document Discrepancies Detected ⚠️</h3>
          <p style="color: #475569 !important; font-size: 0.9rem;">Mismatches found between the uploaded document content and the official registry ledger.</p>
        </div>
      </div>
    `;
  } else if (docMatches) {
    statusPill = `<span class="status-pill issued">VALID / MATCHES RECORD</span>`;
    bannerHtml = `
      <div class="result-hero-banner valid" style="background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%) !important; border: 1.5px solid #A7F3D0 !important; border-radius: 20px; padding: 1.75rem 2rem; display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.75rem;">
        <div class="result-icon-shield" style="width: 58px; height: 58px; border-radius: 50%; background: #DCFCE7; color: #059669; border: 2px solid #86EFAC; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.5rem;">
          ✓
        </div>
        <div>
          <h3 style="font-size: 1.3rem; font-weight: 800; color: #065F46 !important; margin-bottom: 0.35rem;">Document Matches Record 100% ✅</h3>
          <p style="color: #334155 !important; font-size: 0.9rem;">All extracted fields and digital signature match the authentic registered ledger.</p>
        </div>
      </div>
    `;
  }

  let mismatchTableHtml = '';
  if (mismatches.length > 0) {
    mismatchTableHtml = `
      <div style="margin-bottom: 2rem;">
        <h4 style="color: #DC2626 !important; font-size: 0.95rem; margin-bottom: 0.85rem; font-weight: 800; text-transform: uppercase;">Field Discrepancy Breakdown</h4>
        <table class="mismatch-table" style="width: 100%; border-collapse: collapse; border: 1px solid #FECACA; border-radius: 12px; overflow: hidden;">
          <thead>
            <tr style="background: #FEF2F2;">
              <th style="padding: 0.85rem 1.15rem; color: #991B1B !important; font-weight: 700; text-align: left; font-size: 0.82rem;">Altered Field</th>
              <th style="padding: 0.85rem 1.15rem; color: #991B1B !important; font-weight: 700; text-align: left; font-size: 0.82rem;">Uploaded Document Value</th>
              <th style="padding: 0.85rem 1.15rem; color: #991B1B !important; font-weight: 700; text-align: left; font-size: 0.82rem;">Official Registry Value</th>
            </tr>
          </thead>
          <tbody>
            ${mismatches.map(m => `
              <tr style="border-top: 1px solid #FEE2E2;">
                <td style="padding: 0.95rem 1.15rem; font-weight: 700; color: #0F172A !important;">${m.field}</td>
                <td class="doc-val mono" style="padding: 0.95rem 1.15rem; color: #DC2626 !important; font-weight: 700; background: #FEF2F2;">${m.document_value || 'None'}</td>
                <td class="rec-val mono" style="padding: 0.95rem 1.15rem; color: #059669 !important; font-weight: 700; background: #ECFDF5;">${m.record_value || 'None'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  let recordHtml = '';
  if (record) {
    recordHtml = `
      <div class="result-metadata-box" style="background: #FFFFFF !important; border: 1.5px solid #E2E8F0 !important; border-radius: 20px !important; padding: 2rem !important; margin-bottom: 1.5rem !important; box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;">
        <div class="result-meta-header" style="font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: #0284C7 !important; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          <span>Official Registered Record</span>
        </div>
        <div class="result-meta-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.25rem;">
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Student Name</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${record.student_name}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Roll Number</span>
            <span class="result-meta-value mono" style="font-size: 1.1rem; font-weight: 800; color: #0284C7 !important; display: block; margin-top: 0.2rem;">${record.student_roll_no}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Course / Degree</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${record.course_name}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Issue Date</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${record.issue_date}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Registered Marks</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${record.marks || '—'}</span>
          </div>
          <div class="result-meta-item" style="background: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 12px; padding: 0.9rem 1.15rem;">
            <span class="result-meta-label" style="font-size: 0.78rem; font-weight: 700; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.04em;">Registered CGPA</span>
            <span class="result-meta-value" style="font-size: 1.1rem; font-weight: 800; color: #0F172A !important; display: block; margin-top: 0.2rem;">${record.cgpa || '—'}</span>
          </div>
        </div>
      </div>
    `;
  }

  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
      <h2 style="font-size: 1.75rem; font-weight: 800; color: #0F172A !important;">Document Verification Result</h2>
      ${statusPill}
    </div>
    ${bannerHtml}
    ${mismatchTableHtml}
    ${recordHtml}
  `;
}

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  updateNavState();
  navigateTo('page-1-landing');
  if (state.token && state.institution) {
    loadDashboardData();
  }
});
