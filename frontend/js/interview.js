/**
 * Mock Interview System — Fixed & Production-Ready
 * v2: Question-type-aware input mode (text enabled only for coding/aptitude/writing)
 */

class InterviewManager {
    constructor() {
        this.sessionId = null;
        this.currentQuestionIndex = 0;
        this.totalQuestions = 5;
        this.role = '';
        this.level = '';
        this.timer = null;
        this.timeRemaining = 0;
        this.mediaStream = null;
        this.recognition = null;
        this.isRecording = false;
        this.proctorInterval = null;
        this.tabSwitchCount = 0;

        this.init();
    }

    // ── Question type config ──────────────────────────────────────────────────
    // Types that require the candidate to TYPE a written answer
    static TEXT_REQUIRED_TYPES = new Set(['coding', 'aptitude', 'writing']);

    // Per-type UI config
    static TYPE_CONFIG = {
        behavioral:    { label: 'Behavioral',    color: '#60a5fa', icon: '💬', textRequired: false, placeholder: 'Use Voice Input to answer this question.' },
        technical:     { label: 'Technical',     color: '#c084fc', icon: '⚙️', textRequired: false, placeholder: 'Use Voice Input to answer this question.' },
        coding:        { label: 'Coding',        color: '#00b074', icon: '💻', textRequired: true,  placeholder: 'Write your code here...',           font: 'monospace' },
        aptitude:      { label: 'Aptitude',      color: '#fbbf24', icon: '🧠', textRequired: true,  placeholder: 'Enter your solution step by step...' },
        writing:       { label: 'Writing',       color: '#f97316', icon: '✍️', textRequired: true,  placeholder: 'Write your detailed answer here...' },
        problem_solving:{ label: 'Problem Solving', color: '#34d399', icon: '🔍', textRequired: true, placeholder: 'Describe your approach and solution...' },
    };

    _getTypeConfig(type) {
        return InterviewManager.TYPE_CONFIG[type] || InterviewManager.TYPE_CONFIG['behavioral'];
    }

    init() {
        this.setupEventListeners();
        this.setupSpeechRecognition();
        this.setupProctoring();
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => this.cleanup());
    }

    cleanup() {
        this.stopCamera();
        clearInterval(this.timer);
        clearInterval(this.proctorInterval);
        if (this.recognition) {
            try { this.recognition.stop(); } catch(e) {}
        }
    }

    setupEventListeners() {
        document.getElementById('start-btn')?.addEventListener('click', () => this.startInterview());
        document.getElementById('submit-btn')?.addEventListener('click', () => this.submitAnswer());
        document.getElementById('skip-btn')?.addEventListener('click', () => this.skipQuestion());
        document.getElementById('end-btn')?.addEventListener('click', () => this.endInterview());
        document.getElementById('voice-btn')?.addEventListener('click', () => this.toggleVoiceRecording());
        document.getElementById('retry-btn')?.addEventListener('click', () => this.resetInterview());
        document.getElementById('camera-toggle')?.addEventListener('click', () => this.toggleCamera());
        document.getElementById('mic-toggle')?.addEventListener('click', () => this.toggleMicrophone());

        document.querySelectorAll('.exp-pill').forEach(pill => {
            pill.addEventListener('click', (e) => {
                document.querySelectorAll('.exp-pill').forEach(p => p.classList.remove('active'));
                e.target.classList.add('active');
                this.level = e.target.dataset.level;
            });
        });

        // Prevent copy-paste in answer textarea ONLY for non-coding questions
        // (coding questions allow paste for code snippets)
        const answerInput = document.getElementById('answer-input');
        if (answerInput) {
            answerInput.addEventListener('copy', e => {
                if (!InterviewManager.TEXT_REQUIRED_TYPES.has(this.currentQuestionType)) e.preventDefault();
            });
            answerInput.addEventListener('paste', e => {
                if (!InterviewManager.TEXT_REQUIRED_TYPES.has(this.currentQuestionType)) e.preventDefault();
            });
            answerInput.addEventListener('cut', e => {
                if (!InterviewManager.TEXT_REQUIRED_TYPES.has(this.currentQuestionType)) e.preventDefault();
            });
        }
    }

    setupSpeechRecognition() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return;
        this.recognition = new SR();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            const input = document.getElementById('answer-input');
            if (input) input.value = transcript;
        };

        this.recognition.onerror = () => {
            this.isRecording = false;
            this.updateVoiceButton();
        };

        this.recognition.onend = () => {
            if (this.isRecording) {
                try { this.recognition.start(); } catch(e) {}
            }
        };
    }

    setupProctoring() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.sessionId) {
                this.tabSwitchCount++;
                this.logProctorEvent('tab_switch', `Tab switched ${this.tabSwitchCount} times`);
                this.showProctorWarning('⚠️ Tab switching detected!');
            }
        });

        window.addEventListener('blur', () => {
            if (this.sessionId) {
                this.logProctorEvent('window_blur', 'Window lost focus');
            }
        });
    }

    async enableCamera() {
        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 },
                audio: true
            });

            const video = document.getElementById('camera-preview');
            if (video) {
                video.srcObject = this.mediaStream;
                video.play();
            }

            const panel = document.getElementById('camera-panel');
            if (panel) panel.classList.add('active');

            const cameraStatus = document.querySelector('.camera-status');
            if (cameraStatus) cameraStatus.textContent = 'Camera is active';

            this._setControlActive('camera-toggle');
            this._setControlActive('mic-toggle');

            this.startPeriodicSnapshots();
            return true;
        } catch (error) {
            console.warn('Camera access denied:', error);
            API.showToast('Camera access denied. Interview will continue without proctoring.', 'warning');
            return false;
        }
    }

    _setControlActive(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.style.background = 'rgba(0,176,116,0.12)';
        el.style.borderColor = 'rgba(0,176,116,0.2)';
        el.style.color = '#00b074';
    }

    startPeriodicSnapshots() {
        this.proctorInterval = setInterval(() => {
            if (this.sessionId) this.captureSnapshot();
        }, 30000);
    }

    async captureSnapshot() {
        try {
            const video = document.getElementById('camera-preview');
            if (!video || !video.srcObject) return;

            const canvas = document.createElement('canvas');
            canvas.width = 320;
            canvas.height = 240;
            canvas.getContext('2d').drawImage(video, 0, 0, 320, 240);
            const snapshot = canvas.toDataURL('image/jpeg', 0.6);

            await this.logProctorEvent('snapshot', 'Periodic snapshot', snapshot);
        } catch (e) {
            console.warn('Snapshot error:', e);
        }
    }

    async logProctorEvent(eventType, details, snapshot = null) {
        if (!this.sessionId) return;
        try {
            // Use the correct proctor endpoint
            await API.proctor.logEvent(this.sessionId, eventType, { details }, snapshot);
        } catch (e) {
            console.warn('Proctor log error:', e);
        }
    }

    showProctorWarning(message) {
        const warning = document.createElement('div');
        warning.textContent = message;
        warning.style.cssText = `
            position:fixed; top:20px; right:20px;
            background:rgba(239,68,68,0.9); color:#fff;
            padding:1rem 1.5rem; border-radius:8px;
            font-weight:500; z-index:9999;
        `;
        document.body.appendChild(warning);
        setTimeout(() => warning.remove(), 3000);
    }

    async startInterview() {
        const btn = document.getElementById('start-btn');
        API.setLoading(btn, true, 'Starting...');

        try {
            // Camera is optional — don't block on failure
            await this.enableCamera();

            this.role = document.getElementById('role-select')?.value || 'Software Developer';
            this.level = document.querySelector('.exp-pill.active')?.dataset.level || 'Entry';

            const response = await API.interview.start(this.role, this.level);

            if (!response.success) {
                throw new Error(response.error?.message || 'Failed to start interview');
            }

            const data = response.data;
            this.sessionId = data.session_id;
            this.totalQuestions = data.total_questions || 5;
            this.currentQuestionIndex = 0;
            this.timeRemaining = (data.duration_minutes || 5) * 60;

            this.displayQuestion(data.first_question, data.question_type, data.text_required);
            this.startTimer();

            document.getElementById('setup-view').style.display = 'none';
            document.getElementById('interview-view').style.display = 'block';
            document.getElementById('eval-section').style.display = 'none';

            this.updateProgress();
            API.showToast('Interview started! Good luck 🎯', 'success');

        } catch (error) {
            console.error('Start interview error:', error);
            API.showToast(error.message || 'Failed to start interview', 'error');
        } finally {
            API.setLoading(btn, false);
        }
    }

    displayQuestion(questionText, questionType, textRequired) {
        const cfg = this._getTypeConfig(questionType);

        // Store current question meta on instance
        this.currentQuestionType = questionType;
        this.currentTextRequired = (textRequired !== undefined)
            ? textRequired
            : cfg.textRequired;

        // Set question text
        const qText = document.getElementById('q-text');
        if (qText) qText.textContent = questionText || 'Loading question...';

        // Update question type badge
        this._updateTypeBadge(cfg);

        // Configure answer input
        const input = document.getElementById('answer-input');
        if (input) {
            input.value = '';
            if (this.currentTextRequired) {
                input.disabled = false;
                input.placeholder = cfg.placeholder;
                input.style.fontFamily = cfg.font === 'monospace'
                    ? "'Courier New', Courier, monospace"
                    : 'var(--font-family)';
                input.style.fontSize = cfg.font === 'monospace' ? '0.85rem' : '0.9rem';
                input.style.opacity = '1';
                input.style.cursor = 'text';
                input.style.borderColor = cfg.color;
                input.style.background = cfg.font === 'monospace'
                    ? 'rgba(0,0,0,0.3)'
                    : 'var(--bg-input)';
            } else {
                input.disabled = true;
                input.placeholder = cfg.placeholder;
                input.style.fontFamily = 'var(--font-family)';
                input.style.fontSize = '0.9rem';
                input.style.opacity = '0.45';
                input.style.cursor = 'not-allowed';
                input.style.borderColor = 'var(--border-color)';
                input.style.background = 'rgba(255,255,255,0.01)';
            }
        }

        // Voice button: show only for non-text-required types
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.style.display = this.currentTextRequired ? 'none' : 'inline-flex';
        }

        // Submit button label
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.textContent = this.currentTextRequired ? 'Submit Answer' : 'Submit Response';
        }

        // Hide feedback from previous question
        const fb = document.getElementById('ai-feedback');
        if (fb) fb.style.display = 'none';
    }

    _updateTypeBadge(cfg) {
        let badge = document.getElementById('q-type-badge');
        if (!badge) {
            // Create badge if it doesn't exist
            badge = document.createElement('div');
            badge.id = 'q-type-badge';
            badge.style.cssText = `
                display:inline-flex; align-items:center; gap:.35rem;
                padding:.25rem .75rem; border-radius:12px;
                font-size:.72rem; font-weight:600; text-transform:uppercase;
                letter-spacing:.05em; margin-bottom:.75rem;
                border:1px solid; transition:all .2s;
            `;
            const qLabel = document.querySelector('.q-label');
            if (qLabel) qLabel.parentNode.insertBefore(badge, qLabel.nextSibling);
        }
        badge.textContent = `${cfg.icon} ${cfg.label}`;
        badge.style.color = cfg.color;
        badge.style.borderColor = cfg.color + '44';
        badge.style.background = cfg.color + '18';

        // Input mode hint below badge
        let hint = document.getElementById('q-input-hint');
        if (!hint) {
            hint = document.createElement('p');
            hint.id = 'q-input-hint';
            hint.style.cssText = 'font-size:.75rem; margin-bottom:.75rem; transition:color .2s;';
            badge.insertAdjacentElement('afterend', hint);
        }
        if (this.currentTextRequired) {
            hint.textContent = '✏️ Type your answer in the field below.';
            hint.style.color = cfg.color;
        } else {
            hint.textContent = '🎤 Use Voice Input or speak your answer aloud.';
            hint.style.color = 'var(--text-muted)';
        }
    }

    startTimer() {
        const display = document.getElementById('timer-display');
        if (!display) return;

        clearInterval(this.timer);
        this.timer = setInterval(() => {
            this.timeRemaining--;
            const m = Math.floor(this.timeRemaining / 60);
            const s = this.timeRemaining % 60;
            display.textContent = `${m}:${s.toString().padStart(2, '0')}`;

            if (this.timeRemaining === 60) {
                API.showToast('⏰ 1 minute remaining!', 'warning');
            }
            if (this.timeRemaining <= 0) {
                clearInterval(this.timer);
                this.showEvaluation();
            }
        }, 1000);
    }

    async submitAnswer() {
        const input = document.getElementById('answer-input');
        const answer = input?.value.trim();

        // For text-required questions, enforce a real answer
        if (this.currentTextRequired) {
            if (!answer) {
                API.showToast('Please type your answer before submitting.', 'warning');
                input?.focus();
                return;
            }
        }

        if (!this.sessionId) {
            API.showToast('No active session. Please start the interview first.', 'error');
            return;
        }

        // For voice/behavioral questions with no text, use a placeholder
        const finalAnswer = answer || '[Answered verbally]';

        const btn = document.getElementById('submit-btn');
        const skipBtn = document.getElementById('skip-btn');
        API.setLoading(btn, true, 'Evaluating...');
        if (skipBtn) skipBtn.disabled = true;

        try {
            const response = await API.interview.answer(this.sessionId, finalAnswer);

            if (!response.success) {
                throw new Error(response.error?.message || 'Failed to submit answer');
            }

            const data = response.data;

            // Show feedback
            const feedback = data.evaluation?.feedback;
            if (feedback) {
                const fb = document.getElementById('ai-feedback');
                if (fb) {
                    fb.innerHTML = `<strong style="color:#60a5fa;">AI Feedback:</strong> ${feedback}`;
                    fb.style.display = 'block';
                }
            }

            if (data.is_final) {
                setTimeout(() => this.showEvaluation(), 1500);
            } else {
                this.currentQuestionIndex++;
                setTimeout(() => {
                    this.displayQuestion(data.next_question, data.question_type, data.text_required);
                    this.updateProgress();
                }, 1500);
            }

        } catch (error) {
            console.error('Submit answer error:', error);
            API.showToast(error.message || 'Failed to submit answer', 'error');
        } finally {
            API.setLoading(btn, false);
            if (skipBtn) skipBtn.disabled = false;
        }
    }

    async skipQuestion() {
        const input = document.getElementById('answer-input');
        // For text-required questions, put a skip marker so backend accepts it
        // Backend will score it 0 automatically
        if (input) {
            if (this.currentTextRequired) {
                input.value = 'Skipped';
                input.disabled = false; // temporarily enable so value is read
            } else {
                input.value = '[Skipped — no verbal answer provided]';
            }
        }
        await this.submitAnswer();
    }

    async endInterview() {
        if (!confirm('Are you sure you want to end the interview?')) return;
        clearInterval(this.timer);
        clearInterval(this.proctorInterval);
        await this.showEvaluation();
    }

    async showEvaluation() {
        if (!this.sessionId) return;

        try {
            // FIX: pass sessionId
            const response = await API.interview.end(this.sessionId);

            if (!response.success) {
                throw new Error(response.error?.message || 'Failed to get evaluation');
            }

            const evaluation = response.data.evaluation;

            document.getElementById('interview-view').style.display = 'none';

            const evalGrid = document.getElementById('eval-grid');
            if (evalGrid) {
                evalGrid.innerHTML = `
                    <div class="eval-card">
                        <div class="val" style="color:var(--primary);">${evaluation.overall_score || 0}</div>
                        <div class="lbl">Overall Score</div>
                    </div>
                    <div class="eval-card">
                        <div class="val" style="color:#60a5fa;">${evaluation.technical_accuracy || 0}</div>
                        <div class="lbl">Technical</div>
                    </div>
                    <div class="eval-card">
                        <div class="val" style="color:#c084fc;">${evaluation.communication_clarity || 0}</div>
                        <div class="lbl">Communication</div>
                    </div>
                    <div class="eval-card">
                        <div class="val" style="color:#f97316;">${evaluation.role_fit || 0}</div>
                        <div class="lbl">Role Fit</div>
                    </div>
                `;
            }

            const strengths = evaluation.strengths || [];
            const evalStrengths = document.getElementById('eval-strengths');
            if (evalStrengths) {
                evalStrengths.innerHTML = strengths.length
                    ? strengths.map(s => `<div class="feedback-item strength">✓ ${s}</div>`).join('')
                    : '<p style="color:var(--text-muted);font-size:.875rem;">Complete more interviews to see strengths.</p>';
            }

            const weaknesses = evaluation.weaknesses || evaluation.areas_to_improve || [];
            const evalWeaknesses = document.getElementById('eval-weaknesses');
            if (evalWeaknesses) {
                evalWeaknesses.innerHTML = weaknesses.length
                    ? weaknesses.map(w => `<div class="feedback-item weakness">→ ${w}</div>`).join('')
                    : '<p style="color:var(--text-muted);font-size:.875rem;">No major weaknesses detected.</p>';
            }

            const evalSection = document.getElementById('eval-section');
            if (evalSection) {
                evalSection.style.display = 'block';
                evalSection.scrollIntoView({ behavior: 'smooth' });
            }

            API.showToast('Interview complete! See your results below.', 'success');
            this.stopCamera();

        } catch (error) {
            console.error('Show evaluation error:', error);
            API.showToast(error.message || 'Failed to load evaluation', 'error');
        }
    }

    updateProgress() {
        const qNum = document.getElementById('q-num');
        const qTotal = document.getElementById('q-total');
        if (qNum) qNum.textContent = this.currentQuestionIndex + 1;
        if (qTotal) qTotal.textContent = this.totalQuestions;

        const dotsContainer = document.getElementById('q-dots');
        if (!dotsContainer) return;
        dotsContainer.innerHTML = '';

        for (let i = 0; i < this.totalQuestions; i++) {
            const dot = document.createElement('div');
            dot.className = 'q-dot';
            if (i < this.currentQuestionIndex) dot.classList.add('done');
            else if (i === this.currentQuestionIndex) dot.classList.add('current');
            dotsContainer.appendChild(dot);
        }
    }

    toggleVoiceRecording() {
        if (!this.recognition) {
            API.showToast('Speech recognition not supported in this browser.', 'error');
            return;
        }
        if (this.isRecording) {
            this.recognition.stop();
            this.isRecording = false;
        } else {
            try {
                this.recognition.start();
                this.isRecording = true;
            } catch(e) {
                console.warn('Speech recognition start error:', e);
            }
        }
        this.updateVoiceButton();
    }

    updateVoiceButton() {
        const btn = document.getElementById('voice-btn');
        if (!btn) return;
        if (this.isRecording) {
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="6" width="12" height="12" rx="2"/></svg> Stop Recording`;
            btn.style.background = '#ef4444';
        } else {
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> Voice Input`;
            btn.style.background = '';
        }
    }

    stopCamera() {
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }
    }

    resetInterview() {
        this.cleanup();
        this.sessionId = null;
        this.currentQuestionIndex = 0;
        this.tabSwitchCount = 0;
        this.currentQuestionType = null;
        this.currentTextRequired = false;

        document.getElementById('eval-section').style.display = 'none';
        document.getElementById('setup-view').style.display = 'block';
        document.getElementById('interview-view').style.display = 'none';
        const input = document.getElementById('answer-input');
        if (input) {
            input.value = '';
            input.disabled = false;
            input.style.opacity = '1';
            input.style.cursor = 'text';
            input.style.borderColor = 'var(--border-color)';
            input.style.fontFamily = 'var(--font-family)';
        }
        // Remove type badge and hint
        document.getElementById('q-type-badge')?.remove();
        document.getElementById('q-input-hint')?.remove();

        const panel = document.getElementById('camera-panel');
        if (panel) panel.classList.remove('active');
        const cameraStatus = document.querySelector('.camera-status');
        if (cameraStatus) cameraStatus.textContent = 'Camera is off';
    }

    toggleCamera() {
        if (!this.mediaStream) {
            API.showToast('Camera not active. Start the interview first.', 'warning');
            return;
        }
        const track = this.mediaStream.getVideoTracks()[0];
        if (!track) return;
        track.enabled = !track.enabled;
        const panel = document.getElementById('camera-panel');
        const btn = document.getElementById('camera-toggle');
        if (track.enabled) {
            if (panel) panel.classList.add('active');
            if (btn) { btn.style.color = '#00b074'; btn.title = 'Camera on'; }
        } else {
            if (panel) panel.classList.remove('active');
            if (btn) { btn.style.color = '#ef4444'; btn.title = 'Camera off'; }
        }
    }

    toggleMicrophone() {
        if (!this.mediaStream) {
            API.showToast('Microphone not active. Start the interview first.', 'warning');
            return;
        }
        const track = this.mediaStream.getAudioTracks()[0];
        if (!track) return;
        track.enabled = !track.enabled;
        const btn = document.getElementById('mic-toggle');
        if (btn) {
            btn.style.color = track.enabled ? '#00b074' : '#ef4444';
            btn.title = track.enabled ? 'Microphone on' : 'Microphone off';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.interviewManager = new InterviewManager();
});
