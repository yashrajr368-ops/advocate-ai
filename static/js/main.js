/**
 * AI ADVOCATE - Interactive Client & Dashboard Scripts
 */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initFlashAlerts();
    initCaseSearch();
});

// ==========================================
// Theme (Light / Dark Mode) Management
// ==========================================
function initTheme() {
    const savedTheme = localStorage.getItem("ai_advocate_theme") || "light";
    setTheme(savedTheme);

    const themeToggleBtn = document.getElementById("themeToggleBtn");
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-bs-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            setTheme(newTheme);
            localStorage.setItem("ai_advocate_theme", newTheme);
        });
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
    const icon = document.getElementById("themeIcon");
    if (icon) {
        if (theme === "dark") {
            icon.classList.remove("bi-moon-stars-fill");
            icon.classList.add("bi-sun-fill");
        } else {
            icon.classList.remove("bi-sun-fill");
            icon.classList.add("bi-moon-stars-fill");
        }
    }
}

// ==========================================
// Auto-dismiss Flash Alerts
// ==========================================
function initFlashAlerts() {
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ==========================================
// Table Search & Filter
// ==========================================
function initCaseSearch() {
    const searchInput = document.getElementById("clientTableSearch");
    if (!searchInput) return;

    searchInput.addEventListener("keyup", function() {
        const query = this.value.toLowerCase().trim();
        const rows = document.querySelectorAll("#caseTableBody tr");

        rows.forEach(row => {
            const text = row.innerText.toLowerCase();
            if (text.includes(query)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    });
}

// ==========================================
// Simple Markdown to HTML formatter for Chatbot
// ==========================================
function formatMarkdown(text) {
    if (!text) return "";
    let html = text
        .replace(/### (.*?)\n/g, '<h4 class="fw-bold mt-3 mb-2 text-primary">$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\n\n/g, '<p class="mb-2"></p>')
        .replace(/\n/g, '<br>');

    // Wrap list items
    html = html.replace(/(<li>.*?<\/li>)/gs, '<ul class="ps-3 mb-2">$1</ul>');
    return html;
}

// ==========================================
// AI Legal Assistant Chatbot AJAX
// ==========================================
async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const container = document.getElementById("chatMessages");
    if (!input || !container) return;

    const query = input.value.trim();
    if (!query) return;

    // Append User Message
    const userDiv = document.createElement("div");
    userDiv.className = "chat-bubble user fade-in-up";
    userDiv.innerText = query;
    container.appendChild(userDiv);

    input.value = "";
    container.scrollTop = container.scrollHeight;

    // Append Typing Indicator
    const typingDiv = document.createElement("div");
    typingDiv.className = "chat-bubble assistant fade-in-up";
    typingDiv.id = "typingIndicator";
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="small text-muted ms-2">AI Advocate analyzing legal provisions...</span>
        </div>
    `;
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;

    try {
        const res = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: query })
        });
        const data = await res.json();

        // Remove indicator
        const indicator = document.getElementById("typingIndicator");
        if (indicator) indicator.remove();

        // Append Assistant Message
        const assistantDiv = document.createElement("div");
        assistantDiv.className = "chat-bubble assistant fade-in-up";
        assistantDiv.innerHTML = formatMarkdown(data.answer);
        container.appendChild(assistantDiv);
        container.scrollTop = container.scrollHeight;
    } catch (err) {
        const indicator = document.getElementById("typingIndicator");
        if (indicator) indicator.remove();

        const errDiv = document.createElement("div");
        errDiv.className = "chat-bubble assistant text-danger";
        errDiv.innerText = "Error connecting to AI legal server. Please check your internet connection.";
        container.appendChild(errDiv);
    }
}

function sendSamplePrompt(element) {
    const text = element.getAttribute("data-prompt") || element.innerText;
    const input = document.getElementById("chatInput");
    if (input) {
        input.value = text;
        sendChatMessage();
    }
}

// ==========================================
// Quick AI Consultation from Homepage
// ==========================================
async function submitHomeAskAI() {
    const textarea = document.getElementById("homeAskInput");
    const resultBox = document.getElementById("homeAskResult");
    const spinner = document.getElementById("homeAskSpinner");
    const submitBtn = document.getElementById("homeAskBtn");

    if (!textarea || !resultBox) return;

    const query = textarea.value.trim();
    if (!query) {
        alert("Please describe your legal situation.");
        return;
    }

    if (spinner) spinner.classList.remove("d-none");
    if (submitBtn) submitBtn.disabled = true;

    try {
        const res = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: query })
        });
        const data = await res.json();
        resultBox.innerHTML = formatMarkdown(data.answer);
        resultBox.classList.remove("d-none");
        resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (e) {
        resultBox.innerHTML = '<div class="alert alert-danger">Error retrieving legal response.</div>';
        resultBox.classList.remove("d-none");
    } finally {
        if (spinner) spinner.classList.add("d-none");
        if (submitBtn) submitBtn.disabled = false;
    }
}

// ==========================================
// Form Submission Loading Indicator
// ==========================================
function showSubmitLoading(btnId, spinnerId, loadingText = "Analyzing with Gemini AI...") {
    const btn = document.getElementById(btnId);
    const spinner = document.getElementById(spinnerId);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${loadingText}`;
    }
    if (spinner) {
        spinner.classList.remove("d-none");
    }
}
