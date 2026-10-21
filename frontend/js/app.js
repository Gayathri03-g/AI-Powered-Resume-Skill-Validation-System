/**
 * Main Application Logic
 * Upload handling, API integration, modal controls
 */

const API_BASE_URL = 'http://localhost:19440/api/v1';

// Modal Controls
const modal = document.getElementById('assessment-modal');
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const closeModalBtn = document.getElementById('close-modal');
const uploadResumeBtn = document.getElementById('upload-resume-btn');
const startAssessmentBtn = document.getElementById('start-assessment-btn');
const uploadProgress = document.getElementById('upload-progress');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

function setModalWide(isWide) {
    const modalContent = document.querySelector('.modal-content');
    if (!modalContent) return;
    modalContent.classList.toggle('modal-wide', isWide);
}

// Open modal
function openModal() {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    setModalWide(false);
}

// Close modal
function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
    resetUploadArea();
    setModalWide(false);
}

// Reset upload area
function resetUploadArea() {
    uploadArea.classList.remove('hidden');
    uploadProgress.classList.add('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';
}

// Event listeners for modal
uploadResumeBtn?.addEventListener('click', openModal);
startAssessmentBtn?.addEventListener('click', openModal);
closeModalBtn?.addEventListener('click', closeModal);

modal?.addEventListener('click', (e) => {
    if (e.target === modal || e.target.classList.contains('modal-backdrop')) {
        closeModal();
    }
});

// Upload area click
uploadArea?.addEventListener('click', () => {
    fileInput.click();
});

// Drag and drop
uploadArea?.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea?.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea?.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// File input change
fileInput?.addEventListener('change', (e) => {
    const files = e.target.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// Handle file upload
async function handleFileUpload(file) {
    // Validate file
    const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
        showError('Invalid file type. Please upload PDF or DOCX.');
        return;
    }

    if (file.size > maxSize) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        showError(`File too large (${sizeMB}MB). Maximum size is 10MB.`);
        return;
    }

    // Show progress
    uploadArea.classList.add('hidden');
    uploadProgress.classList.remove('hidden');

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        // Simulate initial progress
        progressFill.style.width = '10%';
        progressText.textContent = 'Uploading... 10%';

        // Upload file with progress simulation
        const uploadPromise = fetch(`${API_BASE_URL}/upload-resume`, {
            method: 'POST',
            body: formData
        });

        // Simulate progress while uploading
        const progressInterval = setInterval(() => {
            const currentWidth = parseFloat(progressFill.style.width) || 10;
            if (currentWidth < 90) {
                const newWidth = currentWidth + Math.random() * 15;
                progressFill.style.width = `${Math.min(newWidth, 90)}%`;
                progressText.textContent = `Uploading... ${Math.round(Math.min(newWidth, 90))}%`;
            }
        }, 200);

        const response = await uploadPromise;
        clearInterval(progressInterval);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();

        // Complete progress
        progressFill.style.width = '100%';
        progressText.textContent = 'Upload complete!';
        progressText.style.color = 'var(--accent-cyan)';

        // Wait a moment then process
        setTimeout(() => {
            handleUploadSuccess(data);
        }, 1000);

    } catch (error) {
        console.error('Upload error:', error);
        showError(error.message || 'Upload failed. Please try again.');
        resetUploadArea();
    }
}

// Simulate upload progress
function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 90) {
            clearInterval(interval);
            progress = 90;
        }
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `Uploading... ${Math.round(progress)}%`;
    }, 200);
}

// Handle upload success
function handleUploadSuccess(data) {
    console.log('Upload successful:', data);

    // Store session ID
    if (data.session_id) {
        localStorage.setItem('session_id', data.session_id);
    }
    // Store uploaded filename for later API calls
    if (data.file_info && data.file_info.filename) {
        localStorage.setItem('uploaded_filename', data.file_info.filename);
    }

    // Show detailed success info
    if (data.file_info) {
        const { original_filename, size_mb, file_type } = data.file_info;
        progressText.textContent = `✓ ${original_filename} (${size_mb}MB ${file_type}) uploaded successfully!`;
    } else {
        progressText.textContent = data.message || 'Resume uploaded successfully!';
    }

    progressText.style.color = 'var(--accent-cyan)';

    // Show success notification
    showSuccess(data.message || 'Resume uploaded successfully!');

    // Trigger Analysis (CHUNK 2.3)
    if (data.file_info && data.file_info.filename) {
        setTimeout(() => {
            analyzeResume(data.file_info.filename);
        }, 1000);
    } else {
        console.error("No filename returned from upload");
        showError("Upload succeeded but filename is missing.");
    }
}

// Show success message
function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 242, 254, 0.4);
        z-index: 1000;
        animation: fadeInDown 0.3s ease;
        max-width: 400px;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeInUp 0.3s ease reverse';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 4000);
}

// Show error message
function showError(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        animation: fadeInDown 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeInUp 0.3s ease reverse';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Health check with retry logic
let connectionAttempts = 0;
const MAX_CONNECTION_ATTEMPTS = 3;

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✅ API is healthy:', data);
            showConnectionStatus(true, data);
            connectionAttempts = 0;
            return true;
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.warn('⚠️ API connection failed:', error);
        connectionAttempts++;

        if (connectionAttempts < MAX_CONNECTION_ATTEMPTS) {
            console.log(`Retrying... (${connectionAttempts}/${MAX_CONNECTION_ATTEMPTS})`);
            setTimeout(checkApiHealth, 2000);
        } else {
            showConnectionStatus(false, error);
        }
        return false;
    }
}

// Show connection status
function showConnectionStatus(connected, data) {
    return;
    // Remove any existing status badge
    const existingBadge = document.querySelector('.connection-badge');
    if (existingBadge) {
        existingBadge.remove();
    }

    // Create status badge
    const badge = document.createElement('div');
    badge.className = 'connection-badge';
    badge.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 600;
        z-index: 999;
        display: flex;
        align-items: center;
        gap: 8px;
        animation: fadeInDown 0.5s ease;
        cursor: pointer;
        transition: transform 0.2s;
    `;

    if (connected) {
        badge.style.background = 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)';
        badge.style.color = 'white';
        badge.style.boxShadow = '0 4px 15px rgba(0, 242, 254, 0.4)';
        badge.innerHTML = `
            <span style="width: 8px; height: 8px; background: white; border-radius: 50%; animation: pulse 2s infinite;"></span>
            Backend Connected
        `;
        badge.title = `Version: ${data.version}\nStatus: ${data.status}`;
    } else {
        badge.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        badge.style.color = 'white';
        badge.style.boxShadow = '0 4px 15px rgba(245, 87, 108, 0.4)';
        badge.innerHTML = `
            <span style="width: 8px; height: 8px; background: white; border-radius: 50%;"></span>
            Backend Disconnected
        `;
        badge.title = 'Backend connection failed. Click to retry.';
    }

    // Click to retry if disconnected
    badge.addEventListener('click', () => {
        if (!connected) {
            connectionAttempts = 0;
            checkApiHealth();
        } else {
            // Open connection test page
            window.open('/test-connection.html', '_blank');
        }
    });

    badge.addEventListener('mouseenter', () => {
        badge.style.transform = 'translateY(-2px)';
    });

    badge.addEventListener('mouseleave', () => {
        badge.style.transform = 'translateY(0)';
    });

    document.body.appendChild(badge);
}

// Test connection periodically
function startConnectionMonitoring() {
    return;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startConnectionMonitoring();
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape to close modal
    if (e.key === 'Escape' && modal.classList.contains('active')) {
        closeModal();
    }

    // Ctrl/Cmd + K to test connection
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        window.open('/test-connection.html', '_blank');
    }
});

// ==========================================
// CHUNK 3.2: Quiz Logic (Enhanced)
// ==========================================

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

let quizState = {
    currentQuestion: 0,
    answers: {},
    quizData: null,
    timer: null,
    timeLeft: 0,
    evaluationResult: null
};

async function startQuiz(filename) {
    if (!filename) { showError('Session lost. Please upload resume again.'); return; }
    setModalWide(true);
    const mc = document.querySelector('.modal-content');
    mc.innerHTML = `<div class="loader-container">
        <div class="pulse-loader">&#x26A1;</div>
        <h2>Generating Your Interview Questions...</h2>
        <p style="color:var(--text-secondary);margin-top:10px;">Gemini is crafting questions from your actual work experience &amp; projects.</p>
    </div>`;

    try {
        const body = { filename };
        if (window._forceRegenQuiz) { body.force_regenerate = true; window._forceRegenQuiz = false; }

        const response = await fetch(`${API_BASE_URL}/generate-quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Quiz generation failed' }));
            throw new Error(err.detail || 'Quiz generation failed');
        }
        const data = await response.json();

        quizState.quizData = data.quiz;
        quizState.currentQuestion = 0;
        quizState.answers = {};
        quizState.evaluationResult = null;
        quizState.timeLeft = (data.quiz.estimated_time_minutes || 45) * 60;
        startTimer();
        renderQuestion();
    } catch (error) {
        console.error('Quiz Error:', error);
        showError('Failed to generate quiz: ' + error.message);
        closeModal();
    }
}

function startTimer() {
    if (quizState.timer) clearInterval(quizState.timer);
    quizState.timer = setInterval(() => {
        quizState.timeLeft--;
        const mins = Math.floor(quizState.timeLeft / 60);
        const secs = quizState.timeLeft % 60;
        const timerEl = document.getElementById('quiz-timer');
        if (timerEl) {
            timerEl.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>${mins}:${String(secs).padStart(2, '0')}`;
            if (quizState.timeLeft < 60) timerEl.style.color = '#ff4757';
        }
        if (quizState.timeLeft <= 0) finishQuiz(true);
    }, 1000);
}

function getQTypeBadgeHtml(qtype) {
    const slug = (qtype || 'Technical').toLowerCase().replace(/[\s/]+/g, '-');
    return `<span class="qtype-badge qtype-${slug}">${escapeHtml(qtype || 'Technical')}</span>`;
}

function renderQuestion() {
    setModalWide(true);
    const question = quizState.quizData.questions[quizState.currentQuestion];
    const total = quizState.quizData.questions.length;
    const mc = document.querySelector('.modal-content');
    const progressPct = Math.round((quizState.currentQuestion / total) * 100);
    const isLast = quizState.currentQuestion === total - 1;
    const qId = String(question.id);
    const savedAnswer = quizState.answers[qId] || '';
    const hasSaved = savedAnswer.trim() !== '';

    mc.innerHTML = `
        <div class="qz-progress-track"><div class="qz-progress-fill" style="width:${progressPct}%"></div></div>
        <div class="qz-header">
            <div class="qz-meta">
                <span class="qz-badge">${quizState.currentQuestion + 1}<span class="qz-badge-sep">/</span>${total}</span>
                <span class="qz-label">${escapeHtml(question.topic || 'Interview')}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <button class="regen-btn" id="skip-quiz-btn" title="Skip this question (0 marks)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="11" height="11"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    Skip Question
                </button>
                <div class="qz-timer" id="quiz-timer">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    <span>--:--</span>
                </div>
                <button class="qz-exit-btn" id="exit-quiz-btn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    Exit
                </button>
            </div>
        </div>

        <div class="qz-question-card">
            ${getQTypeBadgeHtml(question.question_type)}
            <div class="qz-q-number">Q${quizState.currentQuestion + 1}&nbsp;&middot;&nbsp;${escapeHtml(question.difficulty || 'Medium')}</div>
            <p class="qz-q-text">${escapeHtml(question.text)}</p>
        </div>

        <div class="qz-answer-zone">
            <div class="qz-answer-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                Your Answer
            </div>
            <textarea id="answer-text" class="qz-textarea" placeholder="Type your detailed answer. Specific examples from your real experience score higher..." rows="7">${escapeHtml(savedAnswer)}</textarea>
            <div class="qz-char-row">
                <span class="qz-char-count" id="char-count">${savedAnswer.length} character${savedAnswer.length !== 1 ? 's' : ''}</span>
                <span class="qz-hint">Specific examples score higher</span>
            </div>
        </div>

        <div class="qz-footer">
            <div class="qz-step-dots">
                ${Array.from({ length: total }, (_, i) => `<span class="qz-dot ${i < quizState.currentQuestion ? 'done' : i === quizState.currentQuestion ? 'active' : ''}"></span>`).join('')}
            </div>
            ${isLast
            ? `<button class="btn btn-primary qz-action-btn" id="finish-btn" ${hasSaved ? '' : 'disabled'}>
                       <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><polyline points="20 6 9 17 4 12"/></svg>
                       Finish &amp; Get AI Score
                   </button>`
            : `<button class="btn btn-primary qz-action-btn" id="next-btn" ${hasSaved ? '' : 'disabled'}>
                       Next Question
                       <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                   </button>`
        }
        </div>`;

    document.getElementById('next-btn')?.addEventListener('click', () => { quizState.currentQuestion++; renderQuestion(); });
    document.getElementById('finish-btn')?.addEventListener('click', () => finishQuiz(false));
    document.getElementById('exit-quiz-btn')?.addEventListener('click', exitQuiz);
    document.getElementById('skip-quiz-btn')?.addEventListener('click', () => {
        quizState.answers[qId] = "[SKIPPED]";
        if (isLast) {
            finishQuiz(false);
        } else {
            quizState.currentQuestion++;
            renderQuestion();
        }
    });

    const textarea = document.getElementById('answer-text');
    const charCount = document.getElementById('char-count');
    textarea.focus();
    textarea.addEventListener('input', () => {
        const val = textarea.value;
        quizState.answers[qId] = val;
        const len = val.length;
        charCount.textContent = len + ' character' + (len !== 1 ? 's' : '');
        const btn = document.getElementById('next-btn') || document.getElementById('finish-btn');
        if (btn) btn.disabled = val.trim() === '';
    });
}

function exitQuiz() {
    if (quizState.timer) clearInterval(quizState.timer);
    setModalWide(false);
    const total = quizState.quizData ? quizState.quizData.questions.length : 0;
    const answered = Object.keys(quizState.answers).length;
    const mc = document.querySelector('.modal-content');
    mc.innerHTML = `
        <button class="modal-close" id="close-exit-modal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div style="text-align:center;padding:20px 0;">
            <div style="font-size:52px;margin-bottom:16px;">&#x1F6AB;</div>
            <h2 style="font-size:1.6rem;font-weight:700;margin-bottom:8px;">Assessment Not Completed</h2>
            <p style="color:var(--text-secondary);margin-bottom:24px;line-height:1.6;">You exited before finishing.<br>
                <span style="color:var(--accent-cyan);font-weight:600;">${answered} of ${total}</span> questions were answered.
            </p>
            <div style="background:rgba(245,87,108,0.08);border:1px solid rgba(245,87,108,0.2);border-radius:12px;padding:16px 20px;margin-bottom:28px;text-align:left;">
                <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:#f5576c;font-weight:700;margin-bottom:8px;">Status</div>
                <div style="font-weight:600;color:var(--text-primary);">Incomplete — No score recorded</div>
                <div style="font-size:0.85rem;color:var(--text-secondary);margin-top:4px;">Re-upload your resume to restart.</div>
            </div>
            <div style="display:flex;gap:12px;justify-content:center;">
                <button class="btn btn-secondary" id="close-exit-final">Close</button>
            </div>
        </div>`;
    document.getElementById('close-exit-modal').addEventListener('click', closeModal);
    document.getElementById('close-exit-final').addEventListener('click', closeModal);
}

async function finishQuiz(autoSubmit = false) {
    setModalWide(false);
    if (quizState.timer) clearInterval(quizState.timer);

    const mc = document.querySelector('.modal-content');
    mc.innerHTML = `<div class="loader-container">
        <div class="pulse-loader">&#x1F9E0;</div>
        <h2>AI is Scoring Your Answers...</h2>
        <p style="color:var(--text-secondary);margin-top:10px;">Evaluating against industry standards. Moving to coding round next.</p>
    </div>`;

    const filename = localStorage.getItem('uploaded_filename');
    let evaluation = null;
    let quizScore = 0;

    try {
        const resp = await fetch(`${API_BASE_URL}/evaluate-quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quiz_id: filename, answers: quizState.answers })
        });
        if (resp.ok) {
            const evalData = await resp.json();
            evaluation = evalData.evaluation;
            quizScore = evaluation ? (evaluation.total_score || 0) : 0;
            quizState.evaluationResult = evaluation;
        }
    } catch (e) { console.warn('Quiz evaluation error:', e); }

    // Store quiz results for the final unified report
    localStorage.setItem('quiz_score', String(quizScore));
    localStorage.setItem('quiz_feedback', evaluation ? (evaluation.overall_feedback || '') : '');
    // Persist the full evaluation object for the final report
    try { localStorage.setItem('quiz_evaluation_json', JSON.stringify(evaluation)); } catch (e) { }
    // Persist Q&A answers for the report
    try { localStorage.setItem('quiz_answers_json', JSON.stringify(quizState.answers)); } catch (e) { }
    try { localStorage.setItem('quiz_questions_json', JSON.stringify(quizState.quizData ? quizState.quizData.questions : [])); } catch (e) { }

    // Show transition screen then launch coding
    mc.innerHTML = `<div class="loader-container">
        <div class="pulse-loader">&#x2705;</div>
        <h2>Quiz Complete! Score: ${quizScore}/100</h2>
        <p style="color:var(--text-secondary);margin-top:10px;">Your results are saved. Starting the coding round now...</p>
    </div>`;
    setTimeout(() => startCodingChallenge(), 1800);
}

function buildScoreRingSvg(score) {
    const r = 50, circumference = 2 * Math.PI * r;
    const offset = circumference - (score / 100) * circumference;
    const color = score >= 75 ? '#00e676' : score >= 50 ? '#ffc107' : '#ff4757';
    return `<svg width="120" height="120" viewBox="0 0 120 120">
        <circle fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8" cx="60" cy="60" r="${r}"/>
        <circle fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round" cx="60" cy="60" r="${r}"
            stroke-dasharray="${circumference}" style="stroke-dashoffset:${offset};transform:rotate(-90deg);transform-origin:60px 60px;transition:stroke-dashoffset 1s ease;"/>
    </svg>`;
}

function renderQuizResults(autoSubmit, evaluation) {
    setModalWide(true);
    const mc = document.querySelector('.modal-content');
    const questions = quizState.quizData.questions;
    const score = evaluation ? (evaluation.total_score || 0) : 0;

    const answerCards = questions.map(q => {
        const qId = String(q.id);
        const rawAns = quizState.answers[qId];
        const ans = rawAns === "[SKIPPED]" ? "(Question Skipped)" : (rawAns || "(No answer provided)");
        let evalData = null;
        if (evaluation && evaluation.answers) {
            evalData = evaluation.answers.find(a => a.question_id === q.id);
        }
        const cardScore = evalData ? evalData.score : null;
        const cardClass = cardScore !== null ? (cardScore >= 70 ? 'passed' : cardScore >= 40 ? 'partial' : 'failed') : '';
        const matchedKw = evalData ? (evalData.matched_keywords || []) : [];
        const missingKw = evalData ? (evalData.missing_keywords || []) : [];
        const kwHtml = (matchedKw.length || missingKw.length) ? `<div class="keyword-tags">
            ${matchedKw.map(k => `<span class="keyword-tag matched">&#x2713; ${escapeHtml(k)}</span>`).join('')}
            ${missingKw.map(k => `<span class="keyword-tag missing">${escapeHtml(k)}</span>`).join('')}
        </div>` : '';
        const scoreColor = cardScore !== null ? (cardScore >= 70 ? '#00e676' : cardScore >= 40 ? '#ffc107' : '#ff4757') : 'transparent';
        return `<div class="qa-review-card ${cardClass}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                <div>${getQTypeBadgeHtml(q.question_type)}</div>
                ${cardScore !== null ? `<span style="font-size:0.8rem;font-weight:700;color:${scoreColor};">${cardScore}/100</span>` : ''}
            </div>
            <div class="qa-q-text">${escapeHtml(q.text)}</div>
            <div class="qa-answer-text">${escapeHtml(ans)}</div>
            ${evalData ? `<div class="qa-feedback">&#x1F4A1; ${escapeHtml(evalData.feedback)}</div>` : `<div class="qa-feedback" style="color:var(--text-secondary);">Guide: ${escapeHtml(q.correct_answer_guide)}</div>`}
            ${kwHtml}
        </div>`;
    }).join('');

    const strengthHtml = (evaluation && evaluation.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');
    const weaknessHtml = (evaluation && evaluation.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');

    mc.innerHTML = `
        <button class="modal-close" onclick="closeModal()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div class="modal-header">
            <h2>${autoSubmit ? "&#x23F0; Time's Up!" : '&#x1F389; Assessment Complete'}</h2>
            <p>${autoSubmit ? 'Submitted automatically. Here are your AI-scored results.' : 'Your answers have been scored by AI.'}</p>
        </div>

        ${evaluation ? `<div style="display:flex;gap:20px;justify-content:center;margin-bottom:20px;flex-wrap:wrap;">
            <div class="quiz-score-ring" style="flex-shrink:0;">
                ${buildScoreRingSvg(score)}
                <div class="quiz-score-center">
                    <div class="quiz-score-num">${score}</div>
                    <div class="quiz-score-lbl">/ 100</div>
                </div>
            </div>
            <div style="flex:1;min-width:200px;">
                ${strengthHtml ? `<div style="margin-bottom:10px;"><div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:#00e676;margin-bottom:6px;font-weight:700;">&#x2705; Strengths</div><ul style="color:var(--text-secondary);font-size:0.8rem;line-height:1.7;padding-left:16px;">${strengthHtml}</ul></div>` : ''}
                ${weaknessHtml ? `<div><div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:#ff4757;margin-bottom:6px;font-weight:700;">&#x26A0;&#xFE0F; Areas to Improve</div><ul style="color:var(--text-secondary);font-size:0.8rem;line-height:1.7;padding-left:16px;">${weaknessHtml}</ul></div>` : ''}
                ${evaluation.overall_feedback ? `<div style="margin-top:10px;font-size:0.82rem;color:var(--text-secondary);line-height:1.6;font-style:italic;">"${escapeHtml(evaluation.overall_feedback)}"</div>` : ''}
            </div>
        </div>` : `<p style="text-align:center;color:var(--text-secondary);margin-bottom:20px;">Questions answered: ${Object.keys(quizState.answers).length} / ${questions.length}</p>`}

        <div style="max-height:45vh;overflow-y:auto;padding-right:6px;margin-bottom:20px;">
            ${answerCards}
        </div>

        <div style="text-align:center;">
            <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
                <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                <button class="btn btn-primary" onclick="startCodingChallenge()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                    Start Coding Round
                </button>
            </div>
        </div>`;
}


// ==========================================
// CHUNK 2.3: Analysis Integration
// ==========================================

async function analyzeResume(filename) {
    const modalContent = document.querySelector('.modal-content');
    modalContent.innerHTML = `
        <div class="loader-container">
            <div class="pulse-loader">&#x1F9E0;</div>
            <h2>Analyzing Resume...</h2>
            <p style="color:var(--text-secondary);margin-top:10px;">Extracting skills, experience &amp; projects.</p>
        </div>`;

    try {
        const response = await fetch(`${API_BASE_URL}/analyze-resume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`);
        }
        const data = await response.json();
        if (data.success && data.profile) {
            showAnalysisResults(data.profile);
        } else {
            throw new Error(data.message || 'Analysis succeeded but returned no profile.');
        }
    } catch (error) {
        console.error('Analysis Error:', error);
        showError(`AI Analysis Failed: ${error.message}`);
        setTimeout(() => {
            modalContent.innerHTML = `
                <button class="modal-close" id="close-modal-err">
                   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
                <div class="modal-header">
                    <h2>Analysis Error</h2>
                    <p>${escapeHtml(error.message) || "We couldn't parse your resume. Please try again."}</p>
                </div>
                <div style="text-align:center;">
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>`;
            document.getElementById('close-modal-err').addEventListener('click', closeModal);
        }, 2000);
    }
}

function showAnalysisResults(profile) {
    setModalWide(false);
    const modalContent = document.querySelector('.modal-content');
    const techSkills = (profile.technical_skills || []).map(s => `<span class="skill-chip tech">${escapeHtml(s)}</span>`).join('');
    const softSkills = (profile.soft_skills || []).map(s => `<span class="skill-chip soft">${escapeHtml(s)}</span>`).join('');

    modalContent.innerHTML = `
        <button class="modal-close" id="close-modal-res">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div class="modal-header">
            <div style="font-size:40px;margin-bottom:10px;">&#x2728;</div>
            <h2>Profile Analyzed</h2>
            <p>Here's what our AI found in your resume.</p>
        </div>

        <div class="analysis-results">
            <div class="result-section">
                <div class="profile-name">${escapeHtml(profile.full_name || 'Candidate')}</div>
                <div class="profile-summary">${escapeHtml(profile.summary || 'No summary available.')}</div>
            </div>
            <div class="result-section">
                <div class="section-label">Experience Level</div>
                <div style="font-weight:bold;color:var(--accent-cyan);">${escapeHtml(profile.experience_level || 'Unknown')} (${escapeHtml(String(profile.years_of_experience || 'N/A'))})</div>
            </div>
            <div class="result-section">
                <div class="section-label">Technical Skills</div>
                <div class="skill-tags">${techSkills || '<span style="color:var(--text-secondary)">None detected</span>'}</div>
            </div>
            <div class="result-section">
                <div class="section-label">Soft Skills</div>
                <div class="skill-tags">${softSkills || '<span style="color:var(--text-secondary)">None detected</span>'}</div>
            </div>
            <div style="margin-top:30px;text-align:center;">
                <button class="btn btn-primary btn-large" id="confirm-skills-btn">
                    Confirm &amp; Start Assessment
                    <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </button>
            </div>
        </div>`;

    document.getElementById('close-modal-res').addEventListener('click', closeModal);
    document.getElementById('confirm-skills-btn').addEventListener('click', () => {
        const filename = localStorage.getItem('uploaded_filename');
        if (!filename) { showError('Session lost. Please upload resume again.'); return; }
        startQuiz(filename);
    });
}

// ==========================================
// CHUNK 4.2: Coding Logic (Enhanced)
// ==========================================

const LANGUAGE_CONFIG = {
    python: { label: 'Python 3', ext: '.py' },
    javascript: { label: 'JavaScript', ext: '.js' },
    java: { label: 'Java', ext: '.java' },
    cpp: { label: 'C++', ext: '.cpp' }
};

let codingState = {
    challenge: null,
    filename: null,
    language: 'python',
    currentHintIndex: -1
};

async function startCodingChallenge() {
    const filename = localStorage.getItem('uploaded_filename');
    codingState.filename = filename;
    if (!filename) { showError('Session lost.'); return; }

    setModalWide(true);
    const mc = document.querySelector('.modal-content');
    mc.innerHTML = `<div class="loader-container">
        <div class="pulse-loader">&#x1F4BB;</div>
        <h2>Preparing Your Coding Challenge...</h2>
        <p style="color:var(--text-secondary);margin-top:10px;">Generating a domain-relevant problem based on your skill profile.</p>
    </div>`;

    try {
        const body = { filename };
        if (window._forceRegenCoding) { body.force_regenerate = true; window._forceRegenCoding = false; }

        const response = await fetch(`${API_BASE_URL}/generate-challenge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Challenge generation failed' }));
            throw new Error(err.detail || 'Challenge generation failed');
        }
        const data = await response.json();
        codingState.challenge = data.challenge;
        codingState.language = 'python';
        codingState.currentHintIndex = -1;
        renderCodingChallenge();
    } catch (error) {
        console.error('Coding Error:', error);
        showError('Failed to start coding challenge: ' + error.message);
        closeModal();
    }
}

function renderCodingChallenge() {
    setModalWide(true);
    const ch = codingState.challenge;
    const mc = document.querySelector('.modal-content');
    const lang = codingState.language;

    const starterCode = (ch.starter_code_by_language && ch.starter_code_by_language[lang])
        || ch.function_signature
        || `# Write your solution here\npass`;

    const visibleTests = (ch.test_cases || []).filter(tc => !tc.is_hidden);
    const testCasesHtml = visibleTests.map((tc, idx) => `
        <div class="test-case-card">
            <div class="test-label">Example ${idx + 1}${tc.description ? ' — ' + escapeHtml(tc.description) : ''}</div>
            <div style="color:var(--text-secondary);"><b>In:</b> ${escapeHtml(tc.input)}</div>
            <div style="color:var(--accent-cyan);"><b>Out:</b> ${escapeHtml(tc.expected_output)}</div>
        </div>`).join('');

    const tagsHtml = (ch.tags || []).map(t => `<span style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:3px;padding:2px 7px;font-size:0.68rem;color:var(--text-secondary);font-family:var(--font-mono);">${escapeHtml(t)}</span>`).join(' ');
    const diffColor = ch.difficulty === 'Hard' ? '#ff4757' : ch.difficulty === 'Medium' ? '#ffc107' : '#00e676';

    const hintsHtml = ch.hints && ch.hints.length ? `
        <div class="hint-section">
            <button class="hint-btn" id="hint-btn">&#x1F4A1; Show Hint <span id="hint-count">(${ch.hints.length} available)</span></button>
            <div class="hint-reveal" id="hint-reveal"></div>
        </div>` : '';

    const langSelectorHtml = Object.entries(LANGUAGE_CONFIG).map(([slug, cfg]) =>
        `<button class="lang-btn ${slug === lang ? 'active' : ''}" data-lang="${slug}">${escapeHtml(cfg.label)}</button>`
    ).join('');

    mc.innerHTML = `
        <div class="modal-header" style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <h2 style="margin-bottom:4px;">${escapeHtml(ch.title)}</h2>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        <span style="color:${diffColor};font-weight:700;font-size:0.8rem;">${escapeHtml(ch.difficulty)}</span>
                        ${tagsHtml}
                    </div>
                </div>
                <div style="display:flex;gap:8px;">
                    <button class="regen-btn" id="regen-coding-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="11" height="11"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                        New Problem
                    </button>
                    <button class="btn btn-secondary" onclick="closeModal()" style="padding:5px 12px;font-size:12px;">Exit</button>
                </div>
            </div>
        </div>

        <div class="coding-container">
            <div class="problem-pane">
                <div class="problem-desc">${escapeHtml(ch.problem_statement).replace(/\n/g, '<br>')}</div>
                <h4 style="margin-bottom:8px;color:white;font-size:0.9rem;">Examples</h4>
                ${testCasesHtml}
                <h4 style="margin:16px 0 8px;color:white;font-size:0.9rem;">Constraints</h4>
                <ul style="color:var(--text-secondary);font-size:0.8rem;padding-left:18px;line-height:1.8;">
                    ${(ch.constraints || []).map(c => `<li>${escapeHtml(c)}</li>`).join('')}
                </ul>
                ${hintsHtml}
            </div>

            <div class="editor-pane">
                <div class="editor-header">
                    <div class="lang-selector" id="lang-selector">${langSelectorHtml}</div>
                    <span style="font-size:11px;color:var(--text-secondary);">Tab = 4 spaces</span>
                </div>
                <textarea id="code-editor" class="code-editor" spellcheck="false">${escapeHtml(starterCode)}</textarea>
                <div id="console-output" class="console-output"></div>
                <div class="run-actions">
                    <div class="complexity-badges" id="complexity-badges" style="display:none;">
                        <div class="complexity-badge">Time: <span id="time-cplx">—</span></div>
                        <div class="complexity-badge">Space: <span id="space-cplx">—</span></div>
                        <div class="complexity-badge">Quality: <span id="code-quality">—</span></div>
                    </div>
                    <button class="btn btn-primary" id="run-code-btn">
                        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                        Run &amp; Submit
                    </button>
                </div>
            </div>
        </div>`;

    // Tab support
    const textarea = document.getElementById('code-editor');
    textarea.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const s = this.selectionStart, end = this.selectionEnd;
            this.value = this.value.substring(0, s) + '    ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = s + 4;
        }
    });

    // Language selector
    document.getElementById('lang-selector').addEventListener('click', (e) => {
        const btn = e.target.closest('.lang-btn');
        if (!btn) return;
        const newLang = btn.dataset.lang;
        if (newLang === codingState.language) return;
        codingState.language = newLang;
        document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === newLang));
        const newStarter = (ch.starter_code_by_language && ch.starter_code_by_language[newLang]) || ch.function_signature || '';
        textarea.value = newStarter;
        const co = document.getElementById('console-output');
        co.style.display = 'none';
        co.innerHTML = '';
        document.getElementById('complexity-badges').style.display = 'none';
    });

    // Hint system
    const hintBtn = document.getElementById('hint-btn');
    const hintReveal = document.getElementById('hint-reveal');
    if (hintBtn && hintReveal) {
        hintBtn.addEventListener('click', () => {
            codingState.currentHintIndex++;
            const hints = ch.hints || [];
            if (codingState.currentHintIndex < hints.length) {
                hintReveal.innerHTML = `<strong>Hint ${codingState.currentHintIndex + 1}/${hints.length}:</strong> ${escapeHtml(hints[codingState.currentHintIndex])}`;
                hintReveal.classList.add('visible');
                const remaining = hints.length - codingState.currentHintIndex - 1;
                document.getElementById('hint-count').textContent = remaining > 0 ? `(${remaining} more)` : '(no more hints)';
                if (remaining === 0) hintBtn.disabled = true;
            }
        });
    }

    // Regenerate
    document.getElementById('regen-coding-btn').addEventListener('click', () => {
        if (confirm('Generate a new coding problem? Your current code will be lost.')) {
            window._forceRegenCoding = true;
            startCodingChallenge();
        }
    });

    document.getElementById('run-code-btn').addEventListener('click', submitCode);
}

async function submitCode() {
    const code = document.getElementById('code-editor').value;
    const co = document.getElementById('console-output');
    const runBtn = document.getElementById('run-code-btn');

    if (!code || !code.trim()) {
        showError('Please write your solution before submitting.');
        return;
    }

    runBtn.disabled = true;
    runBtn.innerHTML = '<span>&#x2699;&#xFE0F;</span> Evaluating...';
    co.style.display = 'none';
    co.innerHTML = '';
    document.getElementById('complexity-badges').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/submit-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                challenge_id: codingState.filename,
                code,
                language: codingState.language
            })
        });
        const result = await response.json();

        if (result.time_complexity || result.space_complexity) {
            document.getElementById('complexity-badges').style.display = 'flex';
            document.getElementById('time-cplx').textContent = result.time_complexity || '—';
            document.getElementById('space-cplx').textContent = result.space_complexity || '—';
            document.getElementById('code-quality').textContent = result.code_quality || '—';
        }

        let testResultsHtml = '';
        if (result.test_results && result.test_results.length > 0) {
            testResultsHtml = `<table class="test-results-table">
                <thead><tr><th>#</th><th>Status</th><th>Input</th><th>Expected</th><th>Got</th></tr></thead>
                <tbody>${result.test_results.map(tr => {
                const cls = tr.passed ? 'tr-pass' : 'tr-fail';
                const icon = tr.passed ? '&#x2714;' : '&#x2718;';
                const hidden = tr.is_hidden ? '<span class="tr-hidden-badge">hidden</span>' : '';
                return `<tr>
                        <td class="${cls}">${icon} ${(tr.test_case_index || 0) + 1}${hidden}</td>
                        <td class="${cls}">${tr.passed ? 'Pass' : 'Fail'}</td>
                        <td>${escapeHtml(String(tr.input || '').substring(0, 40))}</td>
                        <td>${escapeHtml(String(tr.expected_output || '').substring(0, 30))}</td>
                        <td>${escapeHtml(String(tr.actual_output || '').substring(0, 30))}</td>
                    </tr>`;
            }).join('')}</tbody></table>`;
        }

        let bugsHtml = '';
        if (result.bugs_found && result.bugs_found.length > 0) {
            bugsHtml = `<div style="margin-top:8px;"><div style="font-size:0.7rem;text-transform:uppercase;color:#ff4757;margin-bottom:4px;font-weight:700;">&#x26A0; Issues Found</div>${result.bugs_found.map(b => `<div style="font-size:0.78rem;color:var(--text-secondary);margin:2px 0;">&bull; ${escapeHtml(b)}</div>`).join('')}</div>`;
        }

        const scoreColor = result.score >= 75 ? '#00e676' : result.score >= 50 ? '#ffc107' : '#ff4757';
        const outputHtml = `
            <div style="margin-bottom:8px;">
                <span style="color:${result.success ? '#00e676' : '#ff4757'};font-weight:700;font-size:1rem;">${result.success ? '&#x2705; Passed' : '&#x274C; Failed'}</span>
                <span style="margin-left:12px;color:${scoreColor};font-weight:700;">Score: ${result.score}/100</span>
                <span style="margin-left:12px;color:var(--text-secondary);font-size:0.8rem;">${result.passed_test_cases}/${result.total_test_cases} test cases</span>
            </div>
            ${testResultsHtml}
            <div style="margin-top:10px;font-size:0.82rem;color:${result.success ? '#00e676' : 'var(--text-secondary)'};line-height:1.6;">${escapeHtml(result.feedback)}</div>
            ${bugsHtml}
            ${result.suggestions && result.suggestions.length ? `<div style="margin-top:8px;"><div style="font-size:0.7rem;text-transform:uppercase;color:var(--accent-cyan);margin-bottom:4px;font-weight:700;">&#x1F4A1; Tips</div>${result.suggestions.map(s => `<div style="font-size:0.78rem;color:var(--text-secondary);margin:2px 0;">&bull; ${escapeHtml(s)}</div>`).join('')}</div>` : ''}`;

        co.style.display = 'block';
        co.className = `console-output visible${result.success ? '' : ' error'}`;
        co.innerHTML = outputHtml;

        if (result.success) {
            // Auto-generate the final unified report after a short delay
            runBtn.disabled = true;
            runBtn.innerHTML = `<span>&#x2699;&#xFE0F;</span> Generating Final Report...`;
            const quizScore = parseInt(localStorage.getItem('quiz_score') || '0', 10);
            const quizFeedback = localStorage.getItem('quiz_feedback') || '';
            // Store coding result for report
            localStorage.setItem('coding_result_json', JSON.stringify(result));
            setTimeout(() => {
                generateReport(codingState.filename, quizScore, result.score, result.feedback, quizFeedback);
            }, 1500);
        } else {
            runBtn.disabled = false;
            runBtn.innerHTML = `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Try Again`;
        }
    } catch (error) {
        console.error('Submission Error:', error);
        co.style.display = 'block';
        co.className = 'console-output visible error';
        co.innerHTML = 'Error submitting code. Please check your connection and try again.';
        runBtn.disabled = false;
        runBtn.innerHTML = `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run &amp; Submit`;
    }
}

// ==========================================
// CHUNK 5.1: Report Generation
// ==========================================

async function generateReport(filename, quizScore, codingScore, codingFeedback, quizFeedback) {
    setModalWide(true);
    const mc = document.querySelector('.modal-content');
    mc.innerHTML = `<div class="loader-container">
        <div class="pulse-loader">&#x1F4CA;</div>
        <h2>Generating Final Report...</h2>
        <p style="color:var(--text-secondary);margin-top:10px;">Analyzing resume claims vs. assessment reality.</p>
    </div>`;

    try {
        const response = await fetch(`${API_BASE_URL}/generate-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename,
                quiz_score: quizScore,
                coding_score: codingScore,
                coding_feedback: codingFeedback || null,
                quiz_feedback: quizFeedback || null
            })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Report generation failed' }));
            throw new Error(err.detail || 'Report generation failed');
        }
        const data = await response.json();
        renderReport(data.report);
    } catch (error) {
        console.error('Report Error:', error);
        showError('Failed to generate report: ' + error.message);
        closeModal();
    }
}

function renderReport(report) {
    setModalWide(true);
    const mc = document.querySelector('.modal-content');

    // ── Hiring decision data ──
    const skillRows = (report.skill_gaps || []).map(gap => `
        <tr>
            <td>${escapeHtml(gap.skill)}</td>
            <td class="status-${(gap.status || '').toLowerCase().replace(/\s+/g, '-')}">${escapeHtml(gap.status)}</td>
            <td style="color:var(--text-secondary)">${escapeHtml(gap.gap_analysis)}</td>
        </tr>`).join('');
    const roadmapItems = (report.recommendation?.learning_path || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
    const prosHtml = (report.recommendation?.pros || []).map(p => `<li>${escapeHtml(p)}</li>`).join('');
    const consHtml = (report.recommendation?.cons || []).map(c => `<li>${escapeHtml(c)}</li>`).join('');
    const credibilityColor = report.credibility_status === 'Authentic' ? '#00e676' : report.credibility_status === 'Hidden Gem' ? '#ffc107' : '#ff4757';
    const verdictColor = getVerdictColor(report.recommendation?.verdict || '');

    // ── Quiz results section ──
    let quizSection = '';
    try {
        const evaluation = JSON.parse(localStorage.getItem('quiz_evaluation_json') || 'null');
        const questions = JSON.parse(localStorage.getItem('quiz_questions_json') || '[]');
        const answers = JSON.parse(localStorage.getItem('quiz_answers_json') || '{}');
        const quizScore = parseInt(localStorage.getItem('quiz_score') || '0', 10);

        const scoreColor = quizScore >= 75 ? '#00e676' : quizScore >= 50 ? '#ffc107' : '#ff4757';
        const strengthHtml = (evaluation?.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');
        const weaknessHtml = (evaluation?.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');

        const answerCards = questions.map(q => {
            const qId = String(q.id);
            const ans = answers[qId] || '(No answer)';
            const evalData = evaluation?.answers?.find(a => a.question_id === q.id);
            const cardScore = evalData ? evalData.score : null;
            const cardClass = cardScore !== null ? (cardScore >= 70 ? 'passed' : cardScore >= 40 ? 'partial' : 'failed') : '';
            const sc = cardScore !== null ? (cardScore >= 70 ? '#00e676' : cardScore >= 40 ? '#ffc107' : '#ff4757') : 'transparent';
            const matchedKw = evalData?.matched_keywords || [];
            const missingKw = evalData?.missing_keywords || [];
            const kwHtml = (matchedKw.length || missingKw.length) ? `<div class="keyword-tags">
                ${matchedKw.map(k => `<span class="keyword-tag matched">&#x2713; ${escapeHtml(k)}</span>`).join('')}
                ${missingKw.map(k => `<span class="keyword-tag missing">${escapeHtml(k)}</span>`).join('')}
            </div>` : '';
            return `<div class="qa-review-card ${cardClass}">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                    <div>${getQTypeBadgeHtml(q.question_type)}</div>
                    ${cardScore !== null ? `<span style="font-size:0.8rem;font-weight:700;color:${sc};">${cardScore}/100</span>` : ''}
                </div>
                <div class="qa-q-text">${escapeHtml(q.text)}</div>
                <div class="qa-answer-text">${escapeHtml(ans)}</div>
                ${evalData ? `<div class="qa-feedback">&#x1F4A1; ${escapeHtml(evalData.feedback)}</div>` : ''}
                ${kwHtml}
            </div>`;
        }).join('');

        quizSection = `
        <div style="margin:24px 0;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.07);">
                <h3 style="margin:0;font-size:1rem;font-weight:700;">&#x1F9E0; Quiz Round Results</h3>
                <span style="font-size:1.1rem;font-weight:800;color:${scoreColor};">${quizScore}/100</span>
            </div>
            ${evaluation ? `<div style="display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap;">
                ${strengthHtml ? `<div style="flex:1;min-width:160px;"><div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#00e676;margin-bottom:5px;font-weight:700;">&#x2705; Strengths</div><ul style="color:var(--text-secondary);font-size:0.78rem;line-height:1.7;padding-left:16px;">${strengthHtml}</ul></div>` : ''}
                ${weaknessHtml ? `<div style="flex:1;min-width:160px;"><div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#ff4757;margin-bottom:5px;font-weight:700;">&#x26A0; To Improve</div><ul style="color:var(--text-secondary);font-size:0.78rem;line-height:1.7;padding-left:16px;">${weaknessHtml}</ul></div>` : ''}
            </div>` : ''}
            <div style="max-height:38vh;overflow-y:auto;padding-right:4px;">
                ${answerCards || '<p style="color:var(--text-secondary);font-size:0.85rem;">No quiz data available.</p>'}
            </div>
        </div>`;
    } catch (e) { console.warn('Could not render quiz section:', e); }

    // ── Coding results section ──
    let codingSection = '';
    try {
        const cr = JSON.parse(localStorage.getItem('coding_result_json') || 'null');
        if (cr) {
            const cs = cr.score >= 75 ? '#00e676' : cr.score >= 50 ? '#ffc107' : '#ff4757';
            codingSection = `
            <div style="margin:24px 0;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.07);">
                    <h3 style="margin:0;font-size:1rem;font-weight:700;">&#x1F4BB; Coding Round Results</h3>
                    <span style="font-size:1.1rem;font-weight:800;color:${cs};">${cr.score}/100</span>
                </div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px;">
                    <div><span style="color:${cr.success ? '#00e676' : '#ff4757'};font-weight:700;">${cr.success ? '&#x2705; Passed' : '&#x274C; Failed'}</span>
                        <span style="margin-left:14px;color:var(--text-secondary);font-size:0.82rem;">${cr.passed_test_cases}/${cr.total_test_cases} test cases</span>
                    </div>
                    ${cr.time_complexity ? `<div style="font-size:0.78rem;font-family:var(--font-mono);color:var(--accent-cyan);">Time: ${escapeHtml(cr.time_complexity)}</div>` : ''}
                    ${cr.space_complexity ? `<div style="font-size:0.78rem;font-family:var(--font-mono);color:var(--accent-cyan);">Space: ${escapeHtml(cr.space_complexity)}</div>` : ''}
                </div>
                <div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.6;">${escapeHtml(cr.feedback || '')}</div>
            </div>`;
        }
    } catch (e) { }

    mc.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.07);">
            <div>
                <h2 style="margin:0 0 4px;">&#x1F4CB; Final Assessment Report</h2>
                <div style="font-size:0.8rem;color:var(--text-secondary);">Complete evaluation — Quiz + Coding + Hiring Recommendation</div>
            </div>
            <button class="btn btn-secondary" onclick="closeModal()" style="padding:5px 12px;font-size:12px;flex-shrink:0;">Close</button>
        </div>

        <!-- Candidate identity strip -->
        <div style="background:linear-gradient(135deg,rgba(79,172,254,0.1),rgba(0,242,254,0.06));border:1px solid rgba(79,172,254,0.2);border-radius:12px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
            <div>
                <div style="font-size:1.15rem;font-weight:800;color:white;">${escapeHtml(report.candidate_name)}</div>
                <div style="color:var(--accent-cyan);font-size:0.85rem;">${escapeHtml(report.technical_rating)} Engineer &nbsp;&middot;&nbsp;
                    <span style="color:${credibilityColor};">${escapeHtml(report.credibility_status || 'Authentic')}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:2rem;font-weight:900;color:${verdictColor};line-height:1;">${escapeHtml(report.recommendation?.verdict || 'N/A')}</div>
                <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-secondary);">Final Verdict</div>
            </div>
        </div>

        <!-- Score summary row -->
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:22px;">
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.8rem;font-weight:900;color:${parseInt(localStorage.getItem('quiz_score') || '0') >= 75 ? '#00e676' : parseInt(localStorage.getItem('quiz_score') || '0') >= 50 ? '#ffc107' : '#ff4757'};">${localStorage.getItem('quiz_score') || '0'}</div>
                <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-secondary);margin-top:4px;">Quiz Score</div>
            </div>
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.8rem;font-weight:900;color:${(() => { try { const c = JSON.parse(localStorage.getItem('coding_result_json') || '{}'); return c.score >= 75 ? '#00e676' : c.score >= 50 ? '#ffc107' : '#ff4757'; } catch (e) { return 'white'; } })()}">${(() => { try { return JSON.parse(localStorage.getItem('coding_result_json') || '{}').score || '—'; } catch (e) { return '—'; } })()}</div>
                <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-secondary);margin-top:4px;">Coding Score</div>
            </div>
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.8rem;font-weight:900;color:${verdictColor};">${report.overall_score}</div>
                <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-secondary);margin-top:4px;">Overall Score</div>
            </div>
        </div>

        <!-- Quiz section -->
        ${quizSection}

        <!-- Coding section -->
        ${codingSection}

        <!-- Hiring recommendation -->
        <div style="margin:24px 0;">
            <div style="margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.07);">
                <h3 style="margin:0;font-size:1rem;font-weight:700;">&#x1F3AF; Hiring Recommendation</h3>
            </div>
            <div class="report-grid">
                <div class="verdict-card" style="grid-column:span 2;">
                    <div style="display:flex;gap:24px;width:100%;flex-wrap:wrap;">
                        ${prosHtml ? `<div style="flex:1;min-width:160px;text-align:left;"><div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#00e676;margin-bottom:5px;font-weight:700;">&#x2705; Strengths</div><ul style="color:var(--text-secondary);font-size:0.8rem;line-height:1.7;padding-left:16px;">${prosHtml}</ul></div>` : ''}
                        ${consHtml ? `<div style="flex:1;min-width:160px;text-align:left;"><div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#ff4757;margin-bottom:5px;font-weight:700;">&#x26A0; Concerns</div><ul style="color:var(--text-secondary);font-size:0.8rem;line-height:1.7;padding-left:16px;">${consHtml}</ul></div>` : ''}
                    </div>
                    ${report.recommendation?.summary ? `<div style="margin-top:12px;font-size:0.82rem;color:var(--text-secondary);line-height:1.6;font-style:italic;border-top:1px solid rgba(255,255,255,0.06);padding-top:10px;width:100%;">&ldquo;${escapeHtml(report.recommendation.summary)}&rdquo;</div>` : ''}
                </div>
                <div class="analysis-card" style="grid-column:span 1;">
                    <div class="card-title">Skill Verification</div>
                    <table class="skill-table">
                        <thead><tr style="text-align:left;color:var(--text-secondary);"><th>Skill</th><th>Status</th><th>Note</th></tr></thead>
                        <tbody>${skillRows}</tbody>
                    </table>
                </div>
                <div class="analysis-card" style="grid-column:span 1;">
                    <div class="card-title">&#x1F4D6; Learning Path</div>
                    <ul class="roadmap-list">${roadmapItems}</ul>
                </div>
            </div>
        </div>

        <div style="text-align:center;margin-top:24px;">
            <button class="btn btn-primary" onclick="closeModal()" style="padding:12px 36px;font-size:1rem;">&#x2714; Done</button>
        </div>`;
}

function getVerdictColor(verdict) {
    if (verdict.includes('Strong')) return '#00e676';
    if (verdict.includes('No')) return '#ff1744';
    if (verdict.includes('Weak')) return '#ff9100';
    return '#2979ff';
}
