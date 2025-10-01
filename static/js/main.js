/**
 * DeepMindCheck - Main JavaScript File
 * Professional Mental Health Analysis Platform
 */

// Global configuration
const CONFIG = {
    API_BASE_URL: '/api',
    MIN_TEXT_LENGTH: 10,
    MAX_TEXT_LENGTH: 2000,
    ANIMATION_DURATION: 300,
    DEBOUNCE_DELAY: 500
};

// Utility functions
const Utils = {
    // Debounce function for input events
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Get CSRF token for Django
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    // Format confidence percentage
    formatConfidence(confidence) {
        return `${(confidence * 100).toFixed(1)}%`;
    },

    // Get confidence level
    getConfidenceLevel(confidence) {
        if (confidence >= 0.8) return 'high';
        if (confidence >= 0.6) return 'medium';
        return 'low';
    },

    // Animate number counting
    animateCounter(element, start, end, duration = 1000) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 16);
    },

    // Show toast notification
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3 fade-in`;
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${this.getToastIcon(type)} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, duration);
    },

    getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            danger: 'fa-times-circle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
};

// Text Analysis Module
const TextAnalysis = {
    currentAnalysisId: null,
    isAnalyzing: false,

    init() {
        this.bindEvents();
        this.initializeCharacterCounter();
    },

    bindEvents() {
        const form = document.getElementById('analysisForm');
        const textInput = document.getElementById('textInput');
        
        if (form) {
            form.addEventListener('submit', this.handleSubmit.bind(this));
        }
        
        if (textInput) {
            textInput.addEventListener('input', Utils.debounce(this.updateCharacterCount.bind(this), CONFIG.DEBOUNCE_DELAY));
            textInput.addEventListener('paste', () => {
                setTimeout(() => this.updateCharacterCount(), 100);
            });
        }
    },

    initializeCharacterCounter() {
        const textInput = document.getElementById('textInput');
        if (textInput) {
            this.updateCharacterCount();
        }
    },

    updateCharacterCount() {
        const textInput = document.getElementById('textInput');
        const charCountElement = document.getElementById('charCount');
        
        if (!textInput || !charCountElement) return;
        
        const length = textInput.value.length;
        const remaining = CONFIG.MAX_TEXT_LENGTH - length;
        
        let status, message, className;
        
        if (length < CONFIG.MIN_TEXT_LENGTH) {
            const needed = CONFIG.MIN_TEXT_LENGTH - length;
            status = 'warning';
            message = `${needed} more characters needed (${length}/${CONFIG.MIN_TEXT_LENGTH}+)`;
            className = 'text-warning';
        } else if (length > CONFIG.MAX_TEXT_LENGTH) {
            status = 'danger';
            message = `Text too long! Remove ${-remaining} characters (${length}/${CONFIG.MAX_TEXT_LENGTH})`;
            className = 'text-danger';
        } else {
            status = 'success';
            message = `Ready for analysis! (${length} characters, ${remaining} remaining)`;
            className = 'text-success';
        }
        
        charCountElement.innerHTML = `
            <i class="fas ${Utils.getToastIcon(status)} me-1"></i>
            ${message}
        `;
        charCountElement.className = `form-text ${className}`;
    },

    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isAnalyzing) {
            Utils.showToast('Analysis already in progress...', 'warning');
            return;
        }
        
        const textInput = document.getElementById('textInput');
        const text = textInput.value.trim();
        
        if (!this.validateInput(text)) return;
        
        this.isAnalyzing = true;
        this.showLoading(true);
        
        try {
            const result = await this.analyzeText(text);
            this.displayResults(result);
            this.currentAnalysisId = result.id;
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.isAnalyzing = false;
            this.showLoading(false);
        }
    },

    validateInput(text) {
        if (!text) {
            Utils.showToast('Please enter some text to analyze', 'warning');
            return false;
        }
        
        if (text.length < CONFIG.MIN_TEXT_LENGTH) {
            Utils.showToast(`Text must be at least ${CONFIG.MIN_TEXT_LENGTH} characters long`, 'warning');
            return false;
        }
        
        if (text.length > CONFIG.MAX_TEXT_LENGTH) {
            Utils.showToast(`Text must be less than ${CONFIG.MAX_TEXT_LENGTH} characters`, 'warning');
            return false;
        }
        
        return true;
    },

    async analyzeText(text) {
        const modelChoice = document.getElementById('modelSelect')?.value || 'baseline';
        const includeExplanation = document.getElementById('includeExplanation')?.checked || false;
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Utils.getCookie('csrftoken'),
            },
            body: JSON.stringify({
                text: text,
                model: modelChoice,
                explain: includeExplanation
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Analysis failed');
        }
        
        return await response.json();
    },

    displayResults(data) {
        const resultsContainer = document.getElementById('results');
        if (!resultsContainer) return;
        
        const resultHtml = this.generateResultsHTML(data);
        resultsContainer.innerHTML = resultHtml;
        resultsContainer.style.display = 'block';
        
        // Animate confidence bar
        setTimeout(() => {
            this.animateConfidenceBar(data.confidence);
            this.animateProbabilityBars(data.probabilities);
        }, 300);
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        Utils.showToast('Analysis completed successfully!', 'success');
    },

    generateResultsHTML(data) {
        const confidenceLevel = Utils.getConfidenceLevel(data.confidence);
        const predictionClass = `result-${data.prediction}`;
        
        return `
            <div class="card ${predictionClass} result-card fade-in">
                <div class="card-body">
                    <!-- Header -->
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <h4 class="card-title mb-3">
                                <i class="fas fa-clipboard-check text-primary me-2"></i>
                                Analysis Results
                            </h4>
                            
                            <div class="row">
                                <div class="col-sm-6">
                                    <div class="d-flex align-items-center mb-3">
                                        <div class="feature-icon icon-${data.prediction} me-3" style="width: 60px; height: 60px; font-size: 1.5rem;">
                                            <i class="fas ${this.getPredictionIcon(data.prediction)}"></i>
                                        </div>
                                        <div>
                                            <h5 class="mb-0 text-capitalize">${data.prediction}</h5>
                                            <small class="text-muted">Primary Classification</small>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-sm-6">
                                    <div class="mb-2">
                                        <div class="d-flex justify-content-between mb-1">
                                            <span class="fw-semibold">Confidence</span>
                                            <span class="fw-bold">${Utils.formatConfidence(data.confidence)}</span>
                                        </div>
                                        <div class="confidence-bar">
                                            <div class="confidence-fill ${confidenceLevel}" 
                                                 id="confidenceBar" style="width: 0%"></div>
                                        </div>
                                        <small class="text-muted">Model certainty level</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-4">
                            <div class="text-center">
                                <div class="bg-light rounded p-3 mb-2">
                                    <div class="text-muted small">Model Used</div>
                                    <div class="fw-bold text-primary text-capitalize">${data.model_used}</div>
                                </div>
                                <div class="bg-light rounded p-3 mb-2">
                                    <div class="text-muted small">Response Time</div>
                                    <div class="fw-bold text-success">${data.response_time || 0.5}s</div>
                                </div>
                                <div class="bg-light rounded p-3">
                                    <div class="text-muted small">Text Length</div>
                                    <div class="fw-bold text-info">${data.text_length || 0} chars</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Main Message -->
                    <div class="alert alert-info border-0 mb-4">
                        <i class="fas fa-info-circle me-2"></i>
                        ${data.message}
                    </div>
                    
                    <!-- Probability Breakdown -->
                    ${this.generateProbabilityHTML(data.probabilities)}
                    
                    <!-- Recommendations -->
                    ${this.generateRecommendationsHTML(data.recommendations)}
                    
                    <!-- Explanation (if available) -->
                    ${data.explanation ? this.generateExplanationHTML(data.explanation) : ''}
                    
                    <!-- Feedback Section -->
                    ${this.generateFeedbackHTML(data.id)}
                </div>
            </div>
        `;
    },

    getPredictionIcon(prediction) {
        const icons = {
            neutral: 'fa-smile',
            depression: 'fa-frown',
            anxiety: 'fa-exclamation-triangle',
            stress: 'fa-bolt'
        };
        return icons[prediction] || 'fa-question-circle';
    },

    generateProbabilityHTML(probabilities) {
        if (!probabilities) return '';
        
        const items = Object.entries(probabilities).map(([label, prob]) => `
            <div class="col-md-4 mb-3">
                <div class="text-center">
                    <div class="fw-semibold text-capitalize mb-1">${label}</div>
                    <div class="progress mb-1" style="height: 10px;">
                        <div class="progress-bar bg-primary probability-bar" 
                             data-percentage="${(prob * 100).toFixed(1)}"
                             style="width: 0%"></div>
                    </div>
                    <small class="text-muted">${Utils.formatConfidence(prob)}</small>
                </div>
            </div>
        `).join('');
        
        return `
            <div class="mt-4">
                <h6 class="fw-bold mb-3">
                    <i class="fas fa-chart-bar text-info me-2"></i>Detailed Probabilities
                </h6>
                <div class="row">
                    ${items}
                </div>
            </div>
        `;
    },

    generateRecommendationsHTML(recommendations) {
        if (!recommendations || recommendations.length === 0) return '';
        
        const items = recommendations.map(rec => `
            <div class="d-flex align-items-start mb-2">
                <i class="fas fa-arrow-right text-primary me-2 mt-1"></i>
                <span>${rec}</span>
            </div>
        `).join('');
        
        return `
            <div class="mt-4">
                <h6 class="fw-bold mb-3">
                    <i class="fas fa-heart text-danger me-2"></i>Recommendations
                </h6>
                <div class="bg-light rounded p-3">
                    ${items}
                </div>
            </div>
        `;
    },

    generateExplanationHTML(explanation) {
        return `
            <div class="mt-4">
                <h6 class="fw-bold mb-3">
                    <i class="fas fa-lightbulb text-warning me-2"></i>Detailed Explanation
                </h6>
                <div class="bg-light rounded p-3">
                    <div class="mb-2">
                        <strong>Analysis Reasoning:</strong>
                        <p class="mb-2">${explanation.reasoning}</p>
                    </div>
                    <div class="mb-2">
                        <strong>Confidence Details:</strong>
                        <p class="mb-2">${explanation.confidence_explanation}</p>
                    </div>
                    <small class="text-muted">${explanation.disclaimer}</small>
                </div>
            </div>
        `;
    },

    generateFeedbackHTML(analysisId) {
        return `
            <div class="mt-4 pt-4 border-top">
                <h6 class="fw-bold mb-3">
                    <i class="fas fa-thumbs-up text-success me-2"></i>Rate This Analysis
                </h6>
                <div class="text-center">
                    <div class="rating-stars mb-3" data-analysis-id="${analysisId}">
                        ${[1, 2, 3, 4, 5].map(rating => 
                            `<span class="star" data-rating="${rating}">⭐</span>`
                        ).join('')}
                    </div>
                    <p class="text-muted small">Your feedback helps improve our AI models</p>
                </div>
            </div>
        `;
    },

    animateConfidenceBar(confidence) {
        const bar = document.getElementById('confidenceBar');
        if (bar) {
            setTimeout(() => {
                bar.style.width = `${confidence * 100}%`;
            }, 100);
        }
    },

    animateProbabilityBars(probabilities) {
        if (!probabilities) return;
        
        document.querySelectorAll('.probability-bar').forEach((bar, index) => {
            const percentage = bar.dataset.percentage;
            setTimeout(() => {
                bar.style.width = `${percentage}%`;
            }, 200 + (index * 100));
        });
    },

    showLoading(show) {
        const loadingElement = document.getElementById('loadingSpinner');
        const resultsElement = document.getElementById('results');
        
        if (loadingElement) {
            loadingElement.style.display = show ? 'block' : 'none';
        }
        
        if (resultsElement && show) {
            resultsElement.style.display = 'none';
        }
        
        // Scroll to loading area if showing
        if (show && loadingElement) {
            loadingElement.scrollIntoView({ behavior: 'smooth' });
        }
    },

   showError(message) {
        const resultsContainer = document.getElementById('results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger border-0 fade-in">
                    <div class="d-flex">
                        <i class="fas fa-exclamation-triangle fa-2x text-danger me-3"></i>
                        <div>
                            <h5 class="alert-heading">Analysis Error</h5>
                            <p class="mb-0">${message}</p>
                            <hr>
                            <div class="small">
                                <i class="fas fa-lightbulb me-1"></i>
                                Try checking your internet connection or simplifying your text.
                            </div>
                        </div>
                    </div>
                </div>
            `;
            resultsContainer.style.display = 'block';
            resultsContainer.scrollIntoView({ behavior: 'smooth' });
        }
        
        Utils.showToast(`Analysis failed: ${message}`, 'danger');
    }
};

// Feedback System
const FeedbackSystem = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('star')) {
                this.handleStarRating(e.target);
            }
        });
    },

    handleStarRating(starElement) {
        const rating = parseInt(starElement.dataset.rating);
        const container = starElement.closest('.rating-stars');
        const analysisId = container.dataset.analysisId;
        
        this.updateStarDisplay(container, rating);
        this.submitRating(analysisId, rating);
    },

    updateStarDisplay(container, rating) {
        const stars = container.querySelectorAll('.star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('active');
                star.style.color = '#fbbf24';
            } else {
                star.classList.remove('active');
                star.style.color = '#ddd';
            }
        });
    },

    async submitRating(analysisId, rating) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/feedback/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': Utils.getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    analysis_id: analysisId,
                    rating: rating
                })
            });

            if (response.ok) {
                Utils.showToast('Thank you for your feedback!', 'success');
                this.showFeedbackSuccess();
            } else {
                throw new Error('Failed to submit feedback');
            }
        } catch (error) {
            Utils.showToast('Failed to submit feedback. Please try again.', 'danger');
        }
    },

    showFeedbackSuccess() {
        const feedbackSection = document.querySelector('.rating-stars')?.closest('.mt-4');
        if (feedbackSection) {
            feedbackSection.innerHTML = `
                <div class="alert alert-success border-0 text-center">
                    <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                    <h6>Thank you for your feedback!</h6>
                    <p class="mb-0 small">Your input helps us improve our AI models.</p>
                </div>
            `;
        }
    }
};

// Form Utilities
const FormUtils = {
    init() {
        this.bindFormEvents();
    },

    bindFormEvents() {
        document.querySelectorAll('[data-clear-form]').forEach(button => {
            button.addEventListener('click', (e) => {
                const formId = e.target.dataset.clearForm;
                const form = document.getElementById(formId);
                if (form) {
                    form.reset();
                    const charCount = document.getElementById('charCount');
                    if (charCount) {
                        charCount.innerHTML = '<i class="fas fa-info-circle text-info me-1"></i>Minimum 10 characters required.';
                        charCount.className = 'form-text text-muted';
                    }
                    document.getElementById('results')?.style.display = 'none';
                }
            });
        });
    }
};

// Application Initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('DeepMindCheck Application Initializing...');
    
    TextAnalysis.init();
    FeedbackSystem.init();
    FormUtils.init();
    
    console.log('DeepMindCheck Application Initialized Successfully!');
});

// Export for global access
window.DeepMindCheck = {
    TextAnalysis,
    FeedbackSystem,
    Utils,
    CONFIG
};