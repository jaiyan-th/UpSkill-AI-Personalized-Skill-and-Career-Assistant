/**
 * Resume Analysis - Production-Ready Integration
 * Uses api-v2.js with proper error handling and loading states
 */

class ResumeAnalyzer {
    constructor() {
        this.selectedFile = null;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        document.getElementById('select-file-btn')?.addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        
        document.getElementById('file-input')?.addEventListener('change', (e) => {
            this.handleFileSelect(e);
        });
        
        document.getElementById('analyze-btn')?.addEventListener('click', () => {
            this.analyzeResume();
        });
    }
    
    handleFileSelect(e) {
        this.selectedFile = e.target.files[0];
        
        if (!this.selectedFile) return;
        
        // Validate file type
        if (!this.selectedFile.type.includes('pdf')) {
            API.showToast('Please select a PDF file', 'error');
            this.selectedFile = null;
            return;
        }
        
        // Validate file size (5MB limit)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (this.selectedFile.size > maxSize) {
            API.showToast('File size must be less than 5MB', 'error');
            this.selectedFile = null;
            return;
        }
        
        // Show selected file
        const pickedEl = document.getElementById('file-picked');
        pickedEl.textContent = `✓ ${this.selectedFile.name} (${(this.selectedFile.size/1024/1024).toFixed(2)} MB)`;
        pickedEl.style.display = 'block';
    }
    
    async analyzeResume() {
        if (!this.selectedFile) {
            API.showToast('Please select a PDF file first', 'warning');
            return;
        }
        
        const btn = document.getElementById('analyze-btn');
        API.setLoading(btn, true, 'Analyzing...');
        
        try {
            const targetRole = document.getElementById('target-role').value.trim();
            
            if (!targetRole) {
                throw new Error('Please enter a target role');
            }
            
            console.log('[Resume] Uploading:', this.selectedFile.name);
            
            const response = await API.resume.upload(this.selectedFile, targetRole);
            
            if (!response.success) {
                throw new Error(response.error?.message || 'Analysis failed');
            }
            
            console.log('[Resume] Analysis complete:', response.data);
            
            this.displayResults(response.data);
            
            API.showToast('Resume analyzed successfully!', 'success');
            
        } catch (error) {
            console.error('[Resume] Analysis error:', error);
            
            // Handle specific error codes
            if (error.code === 'LLM_TIMEOUT') {
                API.showToast('Analysis is taking longer than expected. Please try again.', 'error');
            } else if (error.code === 'LLM_RATE_LIMIT') {
                API.showToast('Too many requests. Please wait a moment and try again.', 'error');
            } else {
                API.showToast(error.message || 'Analysis failed', 'error');
            }
        } finally {
            API.setLoading(btn, false);
        }
    }
    
    displayResults(data) {
        const analysis = data.analysis || {};
        const skills = data.skills || [];
        
        // Render scores
        const scoreGrid = document.getElementById('score-grid');
        scoreGrid.innerHTML = `
            <div class="score-box">
                <div class="val">${analysis.ats_score || analysis.overall_score || '—'}</div>
                <div class="lbl">ATS Score</div>
            </div>
            <div class="score-box">
                <div class="val">${analysis.tech_match || '—'}</div>
                <div class="lbl">Tech Match</div>
            </div>
            <div class="score-box">
                <div class="val">${analysis.improvements?.length || analysis.suggestions?.length || '—'}</div>
                <div class="lbl">Improvements</div>
            </div>
        `;
        
        // Render detected skills
        const skillNames = skills.map(s => typeof s === 'string' ? s : (s.name || s));
        const skillsFoundEl = document.getElementById('skills-found');
        
        if (skillNames.length > 0) {
            skillsFoundEl.innerHTML = skillNames.slice(0, 20).map(skill => 
                `<span class="chip">${skill}</span>`
            ).join('');
        } else {
            skillsFoundEl.innerHTML = '<span style="color:var(--text-muted);font-size:.85rem;">No skills detected. Try adding more technical details to your resume.</span>';
        }
        
        // Render missing skills
        const missingSkills = analysis.missing_skills || analysis.skill_gaps || [];
        const missingEl = document.getElementById('skills-missing');
        
        if (missingSkills.length > 0) {
            missingEl.innerHTML = missingSkills.slice(0, 20).map(skill => 
                `<span class="chip missing">${skill}</span>`
            ).join('');
        } else {
            missingEl.innerHTML = '<span style="color:var(--text-muted);font-size:.85rem;">None — great job!</span>';
        }
        
        // Render suggestions
        const suggestions = analysis.suggestions || analysis.improvements || [];
        const suggestionsEl = document.getElementById('suggestions-list');
        
        if (suggestions.length > 0) {
            suggestionsEl.innerHTML = suggestions.map(suggestion => 
                `<div class="suggestion-item">${suggestion}</div>`
            ).join('');
        } else {
            suggestionsEl.innerHTML = '<div class="suggestion-item">Resume looks good! Consider tailoring it further to the target role.</div>';
        }
        
        // Show results panel
        const resultsPanel = document.getElementById('results-panel');
        resultsPanel.style.display = 'block';
        resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.resumeAnalyzer = new ResumeAnalyzer();
});
