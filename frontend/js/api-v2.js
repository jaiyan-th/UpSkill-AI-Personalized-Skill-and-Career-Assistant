/**
 * UpSkill AI — Production-Ready API Client v2
 * Session: sessionStorage (clears on browser close) + 24h JWT expiry
 * Security: token decoded + expiry checked on every page load
 */

const API = (() => {
  // ─── Configuration ────────────────────────────────────────────────────────
  const CONFIG = {
    BASE_URL: 'http://localhost:5000',
    TIMEOUT: 30000,
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    RETRY_STATUS_CODES: [408, 429, 500, 502, 503, 504]
  };

  // ─── Token Management ─────────────────────────────────────────────────────
  // Use sessionStorage so the session is cleared when the browser/tab is closed.
  // This prevents the "still logged in next day" problem.
  const TokenManager = {
    get: () => sessionStorage.getItem('upskill_token'),
    set: (token) => sessionStorage.setItem('upskill_token', token),
    remove: () => sessionStorage.removeItem('upskill_token'),

    getUser: () => {
      try {
        const u = sessionStorage.getItem('upskill_user');
        return u ? JSON.parse(u) : null;
      } catch { return null; }
    },
    setUser: (user) => sessionStorage.setItem('upskill_user', JSON.stringify(user)),
    removeUser: () => sessionStorage.removeItem('upskill_user'),

    clear: () => {
      sessionStorage.clear();          // wipe everything in session
      localStorage.removeItem('upskill_token');   // also clear any legacy localStorage token
      localStorage.removeItem('upskill_user');
    }
  };

  // ─── JWT Helpers ──────────────────────────────────────────────────────────
  function _decodeToken(token) {
    try {
      const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(b64));
    } catch { return null; }
  }

  function isTokenValid() {
    const token = TokenManager.get();
    if (!token) return false;
    const payload = _decodeToken(token);
    if (!payload || !payload.exp) return false;
    // Add 10-second buffer to avoid edge-case race conditions
    return payload.exp * 1000 > Date.now() + 10000;
  }

  function getTokenExpiresIn() {
    const token = TokenManager.get();
    if (!token) return 0;
    const payload = _decodeToken(token);
    if (!payload || !payload.exp) return 0;
    return Math.max(0, payload.exp * 1000 - Date.now());
  }

  // ─── Auto-logout timer ────────────────────────────────────────────────────
  let _expiryTimer = null;

  function _scheduleAutoLogout() {
    if (_expiryTimer) clearTimeout(_expiryTimer);
    const ms = getTokenExpiresIn();
    if (ms <= 0) return;
    _expiryTimer = setTimeout(() => {
      showToast('Your session has expired. Please log in again.', 'warning');
      setTimeout(() => _doLogout(), 2000);
    }, ms);
  }

  function _doLogout() {
    if (_expiryTimer) clearTimeout(_expiryTimer);
    TokenManager.clear();
    window.location.href = 'index.html';
  }

  // ─── Utility Functions ────────────────────────────────────────────────────
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const calculateBackoff = (attempt) => CONFIG.RETRY_DELAY * Math.pow(2, attempt - 1);

  // ─── Core HTTP Client ─────────────────────────────────────────────────────
  async function request(method, path, body = null, options = {}) {
    const {
      isFormData = false,
      skipAuth = false,
      timeout = CONFIG.TIMEOUT,
      retries = CONFIG.MAX_RETRIES
    } = options;

    // Pre-flight: check token expiry before sending
    if (!skipAuth && !isTokenValid()) {
      handleUnauthorized('Token expired before request');
      throw new APIError('Session expired. Please log in again.', 'TOKEN_EXPIRED', 401);
    }

    let lastError = null;

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const headers = {};
        const token = TokenManager.get();

        if (token && !skipAuth) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        if (!isFormData) {
          headers['Content-Type'] = 'application/json';
        }

        const fetchOptions = {
          method,
          headers,
          signal: AbortSignal.timeout(timeout)
        };

        if (body) {
          fetchOptions.body = isFormData ? body : JSON.stringify(body);
        }

        const response = await fetch(CONFIG.BASE_URL + path, fetchOptions);

        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          data = await response.json();
        } else {
          data = { success: false, error: { code: 'INVALID_RESPONSE', message: 'Server returned non-JSON response' } };
        }

        if (response.ok) {
          if (data.success !== undefined) return data;
          return { success: true, data };
        }

        // 401 — always logout immediately, no retry
        if (response.status === 401) {
          handleUnauthorized(data.error?.message || 'Unauthorized');
          throw new APIError(
            data.error?.message || 'Session expired. Please log in again.',
            data.error?.code || 'UNAUTHORIZED',
            401
          );
        }

        if (attempt < retries && CONFIG.RETRY_STATUS_CODES.includes(response.status)) {
          await sleep(calculateBackoff(attempt));
          continue;
        }

        const errorMessage = data.error?.message || data.message || `HTTP ${response.status}`;
        const errorCode = data.error?.code || 'API_ERROR';
        throw new APIError(errorMessage, errorCode, response.status, data.error?.details);

      } catch (error) {
        lastError = error;

        if (error.name === 'AbortError' || error.name === 'TimeoutError') {
          if (attempt < retries) { await sleep(calculateBackoff(attempt)); continue; }
          throw new APIError('Request timed out. Please try again.', 'TIMEOUT', 408);
        }

        if (error instanceof APIError) throw error;

        if (attempt < retries) { await sleep(calculateBackoff(attempt)); continue; }
        throw new APIError('Network error. Please check your connection.', 'NETWORK_ERROR', 0);
      }
    }

    throw lastError;
  }

  // ─── Custom Error Class ───────────────────────────────────────────────────
  class APIError extends Error {
    constructor(message, code, status, details = null) {
      super(message);
      this.name = 'APIError';
      this.code = code;
      this.status = status;
      this.details = details;
    }
  }

  // ─── Auth Handlers ────────────────────────────────────────────────────────
  function handleUnauthorized(reason = '') {
    console.warn('[Auth] Unauthorized:', reason);
    TokenManager.clear();
    if (!window.location.pathname.includes('index.html') &&
        !window.location.pathname.includes('register.html')) {
      window.location.href = 'index.html';
    }
  }

  function handleError(error, context = '') {
    console.error(`[API Error${context ? ' - ' + context : ''}]:`, error);
    const message = error instanceof APIError ? error.message : (error.message || 'An unexpected error occurred');
    showToast(message, 'error');
    return null;
  }

  // ─── API Endpoints ────────────────────────────────────────────────────────

  const auth = {
    async login(email, password) {
      const response = await request('POST', '/api/auth/login', { email, password }, { skipAuth: true });
      if (response.success && response.data) {
        TokenManager.set(response.data.token);
        TokenManager.setUser(response.data.user);
        _scheduleAutoLogout(); // start expiry countdown
      }
      return response;
    },

    async register(name, email, password) {
      const response = await request('POST', '/api/auth/register', { name, email, password }, { skipAuth: true });
      if (response.success && response.data) {
        TokenManager.set(response.data.token);
        TokenManager.setUser(response.data.user);
        _scheduleAutoLogout();
      }
      return response;
    },

    async me() {
      return request('GET', '/api/auth/me');
    },

    logout() {
      _doLogout();
    },

    isLoggedIn() {
      return isTokenValid();
    }
  };

  const dashboard = { get: () => request('GET', '/api/dashboard/') };

  const resume = {
    async upload(file, targetRole) {
      const form = new FormData();
      form.append('resume', file);
      if (targetRole) form.append('job_description', targetRole);
      return request('POST', '/api/ai/resume/upload', form, { isFormData: true, timeout: 60000 });
    },
    atsOptimize: (resumeText) =>
      request('POST', '/api/ai/resume/ats-optimization', { resume_text: resumeText }),
    compareJob: (resumeText, jobDesc) =>
      request('POST', '/api/ai/resume/compare-job', { resume_text: resumeText, job_description: jobDesc }),
    history: () => request('GET', '/api/resume/history')
  };

  const interview = {
    start: (role, level, skills = [], resume_summary = null) =>
      request('POST', '/api/ai/interview/start', { role, level, skills, resume_summary }),
    answer: (sessionId, answer) =>
      request('POST', '/api/ai/interview/answer', { session_id: sessionId, answer }),
    end: (sessionId) =>
      request('POST', '/api/ai/interview/end', { session_id: sessionId }),
    history: () => request('GET', '/api/interview/history'),
    insights: () => request('GET', '/api/interview/insights')
  };

  const coach = {
    chat: (message, context = null) =>
      request('POST', '/api/ai/chat/message', { message, context }),
    clear: () => request('POST', '/api/ai/chat/clear')
  };

  const learning = {
    get: () => request('GET', '/api/learning-path/'),
    generatePath: (currentSkills, targetRole, hoursPerWeek = 10) =>
      request('POST', '/api/ai/skills/learning-path', {
        current_skills: currentSkills,
        target_role: targetRole,
        hours_per_week: hoursPerWeek
      })
  };

  const skills = {
    analyzeGaps: (currentSkills, targetRole, experienceLevel) =>
      request('POST', '/api/ai/skills/analyze-gaps', {
        current_skills: currentSkills,
        target_role: targetRole,
        experience_level: experienceLevel
      }),
    assessReadiness: (currentSkills, targetRole) =>
      request('POST', '/api/ai/skills/assess-readiness', {
        current_skills: currentSkills,
        target_role: targetRole
      })
  };

  const voice = {
    analyze: (transcript, durationSeconds) =>
      request('POST', '/api/voice/analyze', { transcript, duration_seconds: durationSeconds }),
    compare: (answers) => request('POST', '/api/voice/compare', { answers }),
    batchAnalyze: (transcripts) => request('POST', '/api/voice/batch-analyze', { transcripts })
  };

  const code = {
    evaluate: (code, language, problemDescription, testCases = []) =>
      request('POST', '/api/code/evaluate', {
        code, language,
        problem_description: problemDescription,
        test_cases: testCases
      }),
    generateTests: (problemDescription, language) =>
      request('POST', '/api/code/generate-tests', { problem_description: problemDescription, language }),
    checkPlagiarism: (code, language) =>
      request('POST', '/api/code/check-plagiarism', { code, language })
  };

  const proctor = {
    logEvent: (sessionId, eventType, details = null, snapshot = null) =>
      request('POST', '/api/proctor/log-event', { session_id: sessionId, event_type: eventType, details, snapshot }),
    saveSnapshot: (sessionId, imageData, frameNumber) =>
      request('POST', '/api/proctor/save-snapshot', { session_id: sessionId, image_data: imageData, frame_number: frameNumber }),
    getIntegrity: (sessionId) => request('GET', `/api/proctor/integrity/${sessionId}`),
    getSnapshots: (sessionId, limit = 10) => request('GET', `/api/proctor/snapshots/${sessionId}?limit=${limit}`),
    getReport: (sessionId) => request('GET', `/api/proctor/report/${sessionId}`)
  };

  const analytics = {
    getDashboard: () => request('GET', '/api/analytics/dashboard'),
    getTrends: (days = 30) => request('GET', `/api/analytics/trends?days=${days}`),
    getSkillProgress: () => request('GET', '/api/analytics/skill-progress'),
    getLearning: () => request('GET', '/api/analytics/learning'),
    getAchievements: () => request('GET', '/api/analytics/achievements'),
    getInsights: () => request('GET', '/api/analytics/insights'),
    getSummary: () => request('GET', '/api/analytics/summary')
  };

  // ─── UI Helpers ───────────────────────────────────────────────────────────
  function showToast(message, type = 'info') {
    const existing = document.getElementById('upskill-toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.id = 'upskill-toast';
    const colors = { success: '#00b074', error: '#ef4444', info: '#60a5fa', warning: '#f97316' };
    toast.style.cssText = `
      position:fixed; bottom:2rem; right:2rem; z-index:9999;
      background:${colors[type] || colors.info}; color:#fff;
      padding:0.85rem 1.5rem; border-radius:8px;
      font-family:Inter,sans-serif; font-size:0.9rem; font-weight:500;
      box-shadow:0 8px 24px rgba(0,0,0,0.4); animation:slideIn 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  function setLoading(btn, loading, text = '') {
    if (!btn) return;
    if (loading) {
      btn.dataset.origText = btn.innerHTML;
      btn.innerHTML = `<span style="display:inline-flex;align-items:center;gap:8px;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 0.8s linear infinite">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>${text || 'Loading...'}</span>`;
      btn.disabled = true;
    } else {
      btn.innerHTML = btn.dataset.origText || text;
      btn.disabled = false;
    }
  }

  // ─── Page Guard ───────────────────────────────────────────────────────────
  // Synchronously hides the page body until token is validated,
  // then either shows it or redirects — no flash of protected content.
  function guardPage() {
    // 1. Hide body immediately to prevent flash
    document.body.style.visibility = 'hidden';

    // 2. Quick local check first
    if (!isTokenValid()) {
      TokenManager.clear();
      window.location.href = 'index.html';
      return false;
    }

    // 3. Schedule auto-logout for when token expires
    _scheduleAutoLogout();

    // 4. Async backend verify — if user was deleted or token revoked
    auth.me().then(res => {
      if (res && res.success) {
        document.body.style.visibility = 'visible'; // show page
      } else {
        TokenManager.clear();
        window.location.href = 'index.html';
      }
    }).catch(() => {
      // Server unreachable — show page anyway (offline tolerance)
      document.body.style.visibility = 'visible';
    });

    return true;
  }

  function populateUserInfo() {
    const user = TokenManager.getUser();
    if (!user) return;
    document.querySelectorAll('[data-user-name]').forEach(el => el.textContent = user.name);
    document.querySelectorAll('[data-user-email]').forEach(el => el.textContent = user.email);
    document.querySelectorAll('.user-avatar img').forEach(img => {
      img.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=00b074&color=fff`;
      img.alt = user.name;
    });
  }

  // ─── Public API ───────────────────────────────────────────────────────────
  return {
    auth, dashboard, resume, interview, coach, learning,
    skills, voice, code, proctor, analytics,
    showToast, setLoading, guardPage, populateUserInfo,
    getUser: TokenManager.getUser,
    getToken: TokenManager.get,
    getBaseUrl: () => CONFIG.BASE_URL,
    APIError, handleError
  };
})();

// Inject animations
const style = document.createElement('style');
style.textContent = `
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: none; opacity: 1; } }
`;
document.head.appendChild(style);

