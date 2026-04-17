/**
 * Skill Gap Analysis — Fixed & Production-Ready
 * Fixes: empty current_skills, wrong error structure check, learning path validation
 */

class SkillGapManager {
    constructor() {
        this.currentAnalysis = null;
        this.selectedLevel = 'Entry';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkPrerequisites();
    }

    setupEventListeners() {
        document.querySelectorAll('.exp-pill').forEach(pill => {
            pill.addEventListener('click', (e) => {
                document.querySelectorAll('.exp-pill').forEach(p => p.classList.remove('active'));
                e.target.classList.add('active');
                this.selectedLevel = e.target.dataset.level;
            });
        });

        document.getElementById('analyze-btn')?.addEventListener('click', () => this.analyzeSkills());
        document.getElementById('generate-path-btn')?.addEventListener('click', () => this.generateLearningPath());
        document.getElementById('new-analysis-btn')?.addEventListener('click', () => this.resetAnalysis());
    }

    async checkPrerequisites() {
        try {
            const [dashRes, ivRes] = await Promise.all([
                API.dashboard.get(),
                API.interview.history()
            ]);

            const hasResume = dashRes.success && (dashRes.data?.user?.resumeCount > 0 || dashRes.data?.resumeCount > 0);
            const hasInterview = ivRes.success && ((ivRes.data?.stats?.completed_interviews || ivRes.data?.stats?.total_interviews || 0) > 0);

            if (!hasResume || !hasInterview) {
                this.showPrerequisiteMessage(!hasResume, !hasInterview);
            }
        } catch (e) {
            console.warn('Could not check prerequisites:', e);
        }
    }

    showPrerequisiteMessage(needsResume, needsInterview) {
        const setupCard = document.querySelector('.setup-card');
        if (!setupCard) return;

        const existing = document.getElementById('prereq-message');
        if (existing) existing.remove();

        const div = document.createElement('div');
        div.id = 'prereq-message';
        div.style.cssText = `
            background:rgba(96,165,250,0.08);
            border:1px solid rgba(96,165,250,0.3);
            border-radius:8px; padding:1rem; margin-bottom:1.5rem;
        `;

        let steps = '';
        if (needsResume) steps += `<div style="margin-bottom:.5rem;"><strong style="color:var(--primary);">Step 1:</strong> <a href="resume.html" style="color:#60a5fa;">Upload your resume →</a></div>`;
        if (needsInterview) steps += `<div><strong style="color:var(--primary);">${needsResume ? 'Step 2' : 'Step 1'}:</strong> <a href="interview.html" style="color:#60a5fa;">Complete a mock interview →</a></div>`;

        div.innerHTML = `
            <p style="margin:0 0 .75rem 0;font-size:.875rem;color:var(--text-main);">
                <strong>Before analyzing skill gaps</strong>, please complete:
            </p>
            ${steps}
        `;

        setupCard.insertBefore(div, setupCard.firstChild);
    }

    async analyzeSkills() {
        const btn = document.getElementById('analyze-btn');
        const roleInput = document.getElementById('target-role');
        const role = roleInput?.value?.trim();

        if (!role) {
            API.showToast('Please enter a target role.', 'warning');
            return;
        }

        const level = this.selectedLevel;
        API.setLoading(btn, true, 'Analyzing...');

        try {
            // Use the skill-gap endpoint that combines resume + interview data
            const response = await fetch(`${API.getBaseUrl()}/api/skill-gap/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${API.getToken()}`
                },
                body: JSON.stringify({ role, level })
            });

            const data = await response.json();

            if (!data.success) {
                // Show missing data requirements
                if (data.required_actions) {
                    this.showPrerequisiteMessage(data.required_actions.resume, data.required_actions.interview);
                }
                throw new Error(data.message || data.error || 'Analysis failed');
            }

            this.currentAnalysis = data.analysis;
            this.displayAnalysis(data.analysis);

            document.getElementById('setup-section').style.display = 'none';
            document.getElementById('results-section').style.display = 'block';

            API.showToast('Analysis complete! 🎯', 'success');

        } catch (error) {
            console.error('Analysis error:', error);
            API.showToast(error.message || 'Analysis failed. Please try again.', 'error');
        } finally {
            API.setLoading(btn, false);
        }
    }

    displayAnalysis(analysis) {
        // Scores
        const readinessEl = document.getElementById('readiness-score');
        const strongEl = document.getElementById('strong-count');
        const missingEl = document.getElementById('missing-count');
        const weakEl = document.getElementById('weak-count');

        if (readinessEl) readinessEl.textContent = analysis.readiness_score || 0;
        if (strongEl) strongEl.textContent = analysis.strong_skills?.length || 0;
        if (missingEl) missingEl.textContent = analysis.missing_skills?.length || 0;
        if (weakEl) weakEl.textContent = analysis.weak_skills?.length || 0;

        // Readiness circle
        const circle = document.getElementById('readiness-circle');
        if (circle) {
            const deg = ((analysis.readiness_score || 0) / 100) * 360;
            circle.style.background = `conic-gradient(var(--primary) 0deg, var(--primary) ${deg}deg, rgba(255,255,255,0.05) ${deg}deg)`;
        }

        // Summary
        const summaryEl = document.getElementById('analysis-summary');
        if (summaryEl) {
            summaryEl.innerHTML = `<p>${analysis.analysis_summary || 'Analysis complete.'}</p>`;
        }

        // Strong skills
        const strongSkillsEl = document.getElementById('strong-skills');
        if (strongSkillsEl) {
            const skills = analysis.strong_skills || [];
            strongSkillsEl.innerHTML = skills.length
                ? skills.map(s => `
                    <div class="skill-item">
                        <span>${typeof s === 'string' ? s : s.name || s}</span>
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                    </div>`).join('')
                : '<p style="color:var(--text-muted);font-size:.875rem;">Upload your resume and complete an interview for better insights.</p>';
        }

        // Missing skills
        const missingSkillsEl = document.getElementById('missing-skills');
        if (missingSkillsEl) {
            const missing = analysis.missing_skills || [];
            missingSkillsEl.innerHTML = missing.length
                ? missing.map(item => {
                    const name = typeof item === 'string' ? item : item.skill || item.name || item;
                    const priority = typeof item === 'object' ? (item.priority || 'Medium') : 'Medium';
                    return `<div class="skill-item"><span>${name}</span><span class="skill-badge badge-${priority.toLowerCase()}">${priority} Priority</span></div>`;
                }).join('')
                : '<p style="color:var(--text-muted);font-size:.875rem;">Great! You have all the required skills.</p>';
        }
    }

    async generateLearningPath() {
        const btn = document.getElementById('generate-path-btn');
        const roleInput = document.getElementById('target-role');
        const role = roleInput?.value?.trim();

        if (!role) {
            API.showToast('Please enter a target role first.', 'warning');
            return;
        }

        API.setLoading(btn, true, 'Generating...');

        try {
            const response = await API.learning.generatePath('', role, 10);

            if (!response.success) {
                throw new Error(response.error?.message || 'Failed to generate learning path');
            }

            this.displayLearningPath(response.data);
            API.showToast('Learning path generated! 📚', 'success');

        } catch (error) {
            console.error('Learning path error:', error);
            API.showToast(error.message || 'Failed to generate learning path', 'error');
        } finally {
            API.setLoading(btn, false);
        }
    }

    displayLearningPath(data) {
        const container = document.getElementById('learning-path-content');
        if (!container) return;

        // Handle both nested and flat response structures
        const path = data.learning_path || data;
        const phases = path.phases || [];

        if (!phases.length) {
            container.innerHTML = '<p style="color:var(--text-muted);">No learning path available.</p>';
            return;
        }

        let html = '';
        phases.forEach(phase => {
            const phaseNum = phase.phase_number || phase.phase || '';
            const title = phase.title || `Phase ${phaseNum}`;
            const weeks = phase.duration_weeks || '?';
            const skills = phase.skills_to_learn || phase.skills || [];
            const resources = phase.resources || [];
            const milestones = phase.milestones || phase.projects || [];

            html += `
                <div class="phase-card" style="background:var(--bg-panel);border:1px solid var(--border-color);border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
                        <div style="width:36px;height:36px;border-radius:50%;background:rgba(0,176,116,0.15);color:var(--primary);display:flex;align-items:center;justify-content:center;font-weight:600;">${phaseNum}</div>
                        <div>
                            <h4 style="margin:0;font-size:1rem;">${title}</h4>
                            <p style="margin:0;font-size:.8rem;color:var(--text-muted);">${weeks} weeks</p>
                        </div>
                    </div>
                    ${skills.length ? `
                        <div style="margin-bottom:.75rem;">
                            <p style="font-size:.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem;">Skills</p>
                            <div style="display:flex;flex-wrap:wrap;gap:.4rem;">
                                ${skills.map(s => `<span style="padding:.2rem .7rem;background:rgba(0,176,116,0.1);border:1px solid rgba(0,176,116,0.2);border-radius:12px;font-size:.75rem;color:var(--primary);">${s}</span>`).join('')}
                            </div>
                        </div>` : ''}
                    ${resources.length ? `
                        <div style="margin-bottom:.75rem;">
                            <p style="font-size:.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem;">Resources</p>
                            <ul style="margin:0;padding-left:1.25rem;font-size:.85rem;color:var(--text-muted);">
                                ${resources.map(r => `<li>${r}</li>`).join('')}
                            </ul>
                        </div>` : ''}
                    ${milestones.length ? `
                        <div>
                            <p style="font-size:.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem;">Milestones</p>
                            <ul style="margin:0;padding-left:1.25rem;font-size:.85rem;color:var(--text-muted);">
                                ${milestones.map(m => `<li>${m}</li>`).join('')}
                            </ul>
                        </div>` : ''}
                </div>`;
        });

        const totalWeeks = path.total_duration_weeks || '';
        const nextSteps = path.next_steps || [];

        if (totalWeeks || nextSteps.length) {
            html += `
                <div style="background:rgba(0,176,116,0.05);border:1px solid rgba(0,176,116,0.2);border-radius:var(--radius);padding:1.5rem;margin-top:.5rem;">
                    ${totalWeeks ? `<h4 style="margin:0 0 .75rem 0;color:var(--primary);">Total Duration: ${totalWeeks} weeks</h4>` : ''}
                    ${nextSteps.length ? `
                        <p style="font-size:.8rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem;">Next Steps</p>
                        <ul style="margin:0;padding-left:1.25rem;font-size:.875rem;color:var(--text-muted);">
                            ${nextSteps.map(s => `<li>${s}</li>`).join('')}
                        </ul>` : ''}
                </div>`;
        }

        container.innerHTML = html;
    }

    resetAnalysis() {
        this.currentAnalysis = null;
        const setup = document.getElementById('setup-section');
        const results = document.getElementById('results-section');
        const pathContent = document.getElementById('learning-path-content');
        if (setup) setup.style.display = 'block';
        if (results) results.style.display = 'none';
        if (pathContent) pathContent.innerHTML = '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.skillGapManager = new SkillGapManager();
});
