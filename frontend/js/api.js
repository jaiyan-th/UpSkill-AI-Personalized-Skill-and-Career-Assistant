/**
 * UpSkill AI — Central API Integration Layer
 * All backend calls go through this file.
 * Backend base: http://localhost:5000
 */

const API = (() => {
  const BASE = 'http://localhost:5000';

  // ─── Token helpers ────────────────────────────────────────────────────────
  const getToken = () => localStorage.getItem('upskill_token');
  const setToken = (t) => localStorage.setItem('upskill_token', t);
  const removeToken = () => localStorage.removeItem('upskill_token');

  const getUser = () => {
    const u = localStorage.getItem('upskill_user');
    return u ? JSON.parse(u) : null;
  };
  const setUser = (u) => localStorage.setItem('upskill_user', JSON.stringify(u));
  const removeUser = () => localStorage.removeItem('upskill_user');

  // ─── Core fetch wrapper ──────────────────────────────────────────────────
  async function req(method, path, body = null, isFormData = false) {
    const headers = {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!isFormData) headers['Content-Type'] = 'application/json';

    const opts = { method, headers };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);

    const res = await fetch(BASE + path, opts);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      // 401 → auto logout
      if (res.status === 401) API.auth.logout();
      throw new Error(data.message || data.error || `HTTP ${res.status}`);
    }
    return data;
  }

  // ─── Auth ─────────────────────────────────────────────────────────────────
  const auth = {
    async login(email, password) {
      const data = await req('POST', '/api/auth/login', { email, password });
      setToken(data.token);
      setUser(data.user);
      return data;
    },
    async register(name, email, password) {
      const data = await req('POST', '/api/auth/register', { name, email, password });
      setToken(data.token);
      setUser(data.user);
      return data;
    },
    async me() {
      return req('GET', '/api/auth/me');
    },
    logout() {
      removeToken();
      removeUser();
      window.location.href = 'index.html';
    },
    isLoggedIn() {
      return !!getToken();
    }
  };

  // ─── Dashboard ────────────────────────────────────────────────────────────
  const dashboard = {
    get: () => req('GET', '/api/dashboard/')
  };

  // ─── Resume Analysis ──────────────────────────────────────────────────────
  const resume = {
    async upload(file, targetRole) {
      console.log('[API] Uploading resume:', file.name, file.size, 'bytes');
      const form = new FormData();
      form.append('resume', file);
      if (targetRole) form.append('job_description', targetRole);
      console.log('[API] FormData created, calling endpoint...');
      try {
        const result = await req('POST', '/api/ai/resume/upload', form, true);
        console.log('[API] Upload successful:', result);
        return result;
      } catch (error) {
        console.error('[API] Upload failed:', error);
        throw error;
      }
    },
    atsOptimize: (resumeText) => req('POST', '/api/ai/resume/ats-optimization', { resume_text: resumeText }),
    compareJob: (resumeText, jobDesc) => req('POST', '/api/ai/resume/compare-job', { resume_text: resumeText, job_description: jobDesc }),
    history: () => req('GET', '/api/resume/history')
  };

  // ─── Mock Interview ───────────────────────────────────────────────────────
  const interview = {
    start: (role, level, skills = [], resume_summary = null) =>
      req('POST', '/api/ai/interview/start', { role, level, skills, resume_summary }),
    answer: (answer) =>
      req('POST', '/api/ai/interview/answer', { answer }),
    end: () =>
      req('POST', '/api/ai/interview/end'),
    history: () =>
      req('GET', '/api/interview/history'),
    insights: () =>
      req('GET', '/api/interview/insights')
  };

  // ─── Career Coach Chat ────────────────────────────────────────────────────
  const coach = {
    chat: (message, context = null) =>
      req('POST', '/api/ai/chat/message', { message, context }),
    clear: () =>
      req('POST', '/api/ai/chat/clear')
  };

  // ─── Learning Path ────────────────────────────────────────────────────────
  const learning = {
    get: () => req('GET', '/api/learning-path/'),
    generatePath: (currentSkills, targetRole, hoursPerWeek = 10) =>
      req('POST', '/api/ai/skills/learning-path', { current_skills: currentSkills, target_role: targetRole, hours_per_week: hoursPerWeek })
  };

  // ─── Skill Gap ────────────────────────────────────────────────────────────
  const skills = {
    analyzeGaps: (currentSkills, targetRole, experienceLevel) =>
      req('POST', '/api/ai/skills/analyze-gaps', { current_skills: currentSkills, target_role: targetRole, experience_level: experienceLevel }),
    assessReadiness: (currentSkills, targetRole) =>
      req('POST', '/api/ai/skills/assess-readiness', { current_skills: currentSkills, target_role: targetRole })
  };

  // ─── UI Helpers exposed globally ──────────────────────────────────────────
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
      box-shadow:0 8px 24px rgba(0,0,0,0.4);
      animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;

    const style = document.createElement('style');
    style.textContent = `@keyframes slideIn{from{transform:translateY(20px);opacity:0}to{transform:none;opacity:1}}`;
    document.head.appendChild(style);

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

  function guardPage() {
    if (!auth.isLoggedIn()) {
      window.location.href = 'index.html';
      return false;
    }
    return true;
  }

  function populateUserInfo() {
    const user = getUser();
    if (!user) return;
    document.querySelectorAll('[data-user-name]').forEach(el => el.textContent = user.name);
    document.querySelectorAll('[data-user-email]').forEach(el => el.textContent = user.email);
    // avatar initials fallback
    document.querySelectorAll('.user-avatar img').forEach(img => {
      img.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=00b074&color=fff`;
      img.alt = user.name;
    });
  }

  // ─── NEW: Voice Analysis ──────────────────────────────────────────────────
  const voice = {
    analyze: (transcript, durationSeconds) =>
      req('POST', '/api/voice/analyze', { transcript, duration_seconds: durationSeconds }),
    compare: (answers) =>
      req('POST', '/api/voice/compare', { answers }),
    batchAnalyze: (transcripts) =>
      req('POST', '/api/voice/batch-analyze', { transcripts })
  };

  // ─── NEW: Code Evaluation ─────────────────────────────────────────────────
  const code = {
    evaluate: (code, language, problemDescription, testCases = []) =>
      req('POST', '/api/code/evaluate', { code, language, problem_description: problemDescription, test_cases: testCases }),
    generateTests: (problemDescription, language) =>
      req('POST', '/api/code/generate-tests', { problem_description: problemDescription, language }),
    checkPlagiarism: (code, language) =>
      req('POST', '/api/code/check-plagiarism', { code, language })
  };

  // ─── NEW: Proctoring ──────────────────────────────────────────────────────
  const proctor = {
    logEvent: (sessionId, eventType, details = null, snapshot = null) =>
      req('POST', '/api/proctor/log-event', { session_id: sessionId, event_type: eventType, details, snapshot }),
    saveSnapshot: (sessionId, imageData, frameNumber) =>
      req('POST', '/api/proctor/save-snapshot', { session_id: sessionId, image_data: imageData, frame_number: frameNumber }),
    getIntegrity: (sessionId) =>
      req('GET', `/api/proctor/integrity/${sessionId}`),
    getSnapshots: (sessionId, limit = 10) =>
      req('GET', `/api/proctor/snapshots/${sessionId}?limit=${limit}`),
    getReport: (sessionId) =>
      req('GET', `/api/proctor/report/${sessionId}`)
  };

  // ─── NEW: Analytics ───────────────────────────────────────────────────────
  const analytics = {
    getDashboard: () =>
      req('GET', '/api/analytics/dashboard'),
    getTrends: (days = 30) =>
      req('GET', `/api/analytics/trends?days=${days}`),
    getSkillProgress: () =>
      req('GET', '/api/analytics/skill-progress'),
    getLearning: () =>
      req('GET', '/api/analytics/learning'),
    getAchievements: () =>
      req('GET', '/api/analytics/achievements'),
    getInsights: () =>
      req('GET', '/api/analytics/insights'),
    getSummary: () =>
      req('GET', '/api/analytics/summary')
  };

  return { 
    auth, dashboard, resume, interview, coach, learning, skills, 
    voice, code, proctor, analytics,  // NEW APIs
    showToast, setLoading, guardPage, populateUserInfo, getUser, getToken 
  };
})();

// Inject spinner keyframe globally
const ks = document.createElement('style');
ks.textContent = `@keyframes spin{to{transform:rotate(360deg)}}`;
document.head.appendChild(ks);
