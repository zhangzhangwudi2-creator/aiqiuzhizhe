/**
 * AI求职助手 - 前端应用逻辑
 */

// ===== 认证相关 =====
function showLogin() {
    document.getElementById("loginModal").classList.add("show");
    document.getElementById("registerModal").classList.remove("show");
}

function showRegister() {
    document.getElementById("loginModal").classList.remove("show");
    document.getElementById("registerModal").classList.add("show");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("show");
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;
    const errEl = document.getElementById("loginError");

    try {
        await api.login(username, password);
        closeModal("loginModal");
        updateAuthUI();
        location.reload();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = "block";
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById("regUsername").value;
    const email = document.getElementById("regEmail").value;
    const password = document.getElementById("regPassword").value;
    const errEl = document.getElementById("registerError");

    try {
        await api.register(username, email, password);
        closeModal("registerModal");
        showLogin();
        alert("注册成功，请登录");
    } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = "block";
    }
}

function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("userId");
    api.token = null;
    updateAuthUI();
    location.href = "/";
}

function updateAuthUI() {
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");
    const loginBtn = document.getElementById("loginBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const userInfo = document.getElementById("userInfo");

    if (token && username) {
        if (loginBtn) loginBtn.style.display = "none";
        if (logoutBtn) logoutBtn.style.display = "inline-flex";
        if (userInfo) {
            userInfo.textContent = username;
            userInfo.style.display = "inline";
        }
    } else {
        if (loginBtn) loginBtn.style.display = "inline-flex";
        if (logoutBtn) logoutBtn.style.display = "none";
        if (userInfo) userInfo.style.display = "none";
    }
}

// ===== 拖拽上传 =====
function initUploadZone() {
    const zone = document.getElementById("uploadZone");
    const input = document.getElementById("resumeUpload");
    if (!zone) return;

    // 点击上传区域触发文件选择
    zone.addEventListener("click", function(e) {
        if (e.target.closest(".upload-link") || e.target.closest(".upload-zone-content")) {
            const userId = currentUser();
            if (!userId) {
                alert("请先登录");
                return;
            }
            input.click();
        }
    });

    // 拖拽事件
    zone.addEventListener("dragover", function(e) {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add("drag-over");
    });

    zone.addEventListener("dragleave", function(e) {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove("drag-over");
    });

    zone.addEventListener("drop", function(e) {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove("drag-over");

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const userId = currentUser();
            if (!userId) {
                alert("请先登录");
                return;
            }
            uploadFile(files[0]);
        }
    });
}

// ===== 简历相关 =====
const currentUser = () => parseInt(localStorage.getItem("userId") || "0");

function showUploadProgress(show) {
    const content = document.getElementById("uploadZoneContent");
    const progress = document.getElementById("uploadProgress");
    if (!content || !progress) return;
    content.style.display = show ? "none" : "block";
    progress.style.display = show ? "block" : "none";
}

function setProgress(pct, text) {
    const fill = document.getElementById("progressFill");
    const label = document.getElementById("progressText");
    if (fill) fill.style.width = pct + "%";
    if (label) label.textContent = text;
}

async function handleResumeUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    await uploadFile(file);
}

async function uploadFile(file) {
    // 验证文件类型
    const allowedExts = [".pdf", ".doc", ".docx"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!allowedExts.includes(ext)) {
        alert("仅支持 PDF 和 Word（.doc/.docx）格式");
        return;
    }

    // 验证文件大小（10MB）
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        alert("文件大小超过限制（最大 10MB）");
        return;
    }

    const userId = currentUser();
    if (!userId) {
        alert("请先登录");
        return;
    }

    showUploadProgress(true);
    setProgress(10, "正在上传...");

    try {
        // 模拟进度（实际 fetch 不支持进度，用模拟保持体验）
        setProgress(40, "正在解析简历...");
        const resume = await api.uploadResume(file, userId);
        setProgress(90, "解析完成...");
        await new Promise(r => setTimeout(r, 300));
        setProgress(100, "上传成功！");
        await new Promise(r => setTimeout(r, 500));

        showUploadProgress(false);
        loadResumes();
        showResumeDetail(resume);
    } catch (err) {
        showUploadProgress(false);
        alert("上传失败: " + err.message);
    }
}

async function loadResumes() {
    const userId = currentUser();
    if (!userId) return;

    try {
        const data = await api.listUserResumes(userId);
        const list = document.getElementById("resumeList");
        if (!list) return;

        if (data.resumes.length === 0) {
            list.innerHTML = `\n                <div class="empty-state">\n                    <p>还没有上传简历</p>\n                    <p>支持 PDF、Word 格式</p>\n                </div>\n            `;
            return;
        }

        list.innerHTML = data.resumes.map(r => `\n                <div class="resume-item" onclick="showResumeDetailById(${r.id})">\n                    <div class="resume-item-info">\n                        <strong>${r.title || "未命名简历"}</strong>\n                        <span class="resume-item-meta">${r.full_name || "未填写姓名"}${r.original_filename ? " \u00B7 " + r.original_filename : ""}</span>\n                    </div>\n                    <div class="resume-item-right">\n                        <span class="skill-count">${r.skills?.length || 0} 项技能</span>\n                        <span class="resume-item-date">${new Date(r.created_at).toLocaleDateString()}</span>\n                    </div>\n                </div>\n        `).join("");
    } catch (err) {
        console.error("加载简历列表失败:", err);
    }
}

async function showResumeDetailById(id) {
    try {
        const resume = await api.getResume(id);
        showResumeDetail(resume);
    } catch (err) {
        console.error(err);
    }
}

function backToResumeList() {
    const detail = document.getElementById("resumeDetail");
    const list = document.getElementById("resumeList");
    if (detail) detail.style.display = "none";
    if (list) list.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function showResumeDetail(resume) {
    const detail = document.getElementById("resumeDetail");
    const list = document.getElementById("resumeList");
    if (!detail) return;

    document.getElementById("detailTitle").textContent = resume.title || "简历详情";

    document.getElementById("detailBasic").innerHTML = `\n        <p><strong>姓名：</strong>${resume.full_name || "-"}</p>\n        <p><strong>邮箱：</strong>${resume.email || "-"}</p>\n        <p><strong>电话：</strong>${resume.phone || "-"}</p>\n        <p><strong>个人总结：</strong>${resume.summary || "-"}</p>\n        ${resume.original_filename ? `<p><strong>原始文件：</strong>${resume.original_filename}</p>` : ""}\n    `;

    document.getElementById("detailSkills").innerHTML =
        (resume.skills || []).length > 0
            ? (resume.skills || []).map(s => `<span class="skill-tag">${s}</span>`).join("")
            : "-";

    document.getElementById("detailExperience").innerHTML =
        (resume.experience || []).length > 0
            ? (resume.experience || []).map(exp => `\n                <div class="exp-item">\n                    <div class="exp-header">\n                        <strong>${exp.company || ""}</strong>\n                        ${exp.position ? `<span class="exp-position">${exp.position}</span>` : ""}\n                    </div>\n                    <div class="exp-date">${exp.start_date || ""} ~ ${exp.end_date || "至今"}</div>\n                    <p class="exp-desc">${exp.description || ""}</p>\n                </div>\n            `).join("")
            : "-";

    document.getElementById("detailEducation").innerHTML =
        (resume.education || []).length > 0
            ? (resume.education || []).map(edu => `\n                <div class="edu-item">\n                    <strong>${edu.school || ""}</strong>\n                    <span>${edu.major ? "- " + edu.major : ""}${edu.degree ? " (" + edu.degree + ")" : ""}</span>\n                    <div class="edu-date">${edu.start_date || ""} ${edu.end_date ? "~ " + edu.end_date : ""}</div>\n                </div>\n            `).join("")
            : "-";

    detail.style.display = "block";
    if (list) list.style.display = "none";

    // 保存当前简历 ID
    detail.dataset.resumeId = resume.id;

    // 隐藏旧的 AI 分析结果
    const analysisEl = document.getElementById("analysisResult");
    if (analysisEl) analysisEl.style.display = "none";

    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function analyzeResume() {
    const detail = document.getElementById("resumeDetail");
    const resumeId = detail?.dataset?.resumeId;
    if (!resumeId) return;

    const btn = event?.target?.closest?.("button");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "分析中...";
    }

    try {
        const result = await api.analyzeResume(parseInt(resumeId));
        const el = document.getElementById("analysisResult");
        const content = document.getElementById("analysisContent");

        content.innerHTML = `\n            <div class="analysis-scores">\n                <div class="score-item main-score">\n                    <span class="score-label">综合评分</span>\n                    <span class="score-value">${result.overall_score}</span>\n                </div>\n                <div class="score-item">\n                    <span class="score-label">内容评分</span>\n                    <span class="score-value">${result.content_score}</span>\n                </div>\n                <div class="score-item">\n                    <span class="score-label">格式评分</span>\n                    <span class="score-value">${result.format_score}</span>\n                </div>\n                <div class="score-item">\n                    <span class="score-label">相关度</span>\n                    <span class="score-value">${result.relevance_score}</span>\n                </div>\n            </div>\n\n            <div class="analysis-section">\n                <h4>优势</h4>\n                <ul class="analysis-good">${result.strengths.map(s => `<li>${s}</li>`).join("")}</ul>\n            </div>\n\n            <div class="analysis-section">\n                <h4>待改进</h4>\n                <ul class="analysis-warn">${result.weaknesses.map(w => `<li>${w}</li>`).join("")}</ul>\n            </div>\n\n            <div class="analysis-section">\n                <h4>改进建议</h4>\n                <ul class="analysis-suggest">${result.suggestions.map(s => `<li>${s}</li>`).join("")}</ul>\n            </div>\n        `;
        el.style.display = "block";
        el.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
        alert("分析失败: " + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "AI 分析";
        }
    }
}

async function optimizeResume() {
    const detail = document.getElementById("resumeDetail");
    const resumeId = detail?.dataset?.resumeId;
    if (!resumeId) return;

    const btn = event?.target?.closest?.("button");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "优化中...";
    }

    try {
        const result = await api.optimizeResume(parseInt(resumeId));
        alert("简历优化完成！建议已生成。");
        console.log("优化结果:", result);
    } catch (err) {
        alert("优化失败: " + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "AI 优化";
        }
    }
}

// ===== 职位相关 =====
async function searchJobs() {
    const keyword = document.getElementById("searchKeyword")?.value || "";
    const location = document.getElementById("searchLocation")?.value || "";
    const jobType = document.getElementById("searchType")?.value || "";

    try {
        const data = await api.searchJobs(keyword, location, jobType);
        const list = document.getElementById("jobsList");
        if (!list) return;

        if (data.jobs.length === 0) {
            list.innerHTML = `<div class="empty-state"><p>未找到匹配职位</p></div>`;
            return;
        }

        list.innerHTML = data.jobs.map(j => `\n            <div class="job-card" onclick="showJobDetail(${j.id})">\n                <h3>${j.title}</h3>\n                <div class="company">${j.company} \u00B7 ${j.location || "地点不限"}</div>\n                <div class="tags">\n                    ${j.job_type ? `<span class="tag">${j.job_type}</span>` : ""}\n                    ${j.salary_min ? `<span class="tag">${j.salary_min}-${j.salary_max}K</span>` : ""}\n                    ${j.experience_level ? `<span class="tag">${j.experience_level}</span>` : ""}\n                </div>\n            </div>\n        `).join("");

        const pagination = document.getElementById("pagination");
        if (pagination) {
            let pages = "";
            for (let i = 1; i <= data.total_pages && i <= 10; i++) {
                pages += `<button class="page-btn ${i === data.page ? "active" : ""}" onclick="searchJobsPage(${i})">${i}</button>`;
            }
            pagination.innerHTML = pages;
        }
    } catch (err) {
        console.error("搜索失败:", err);
    }
}

let searchPage = 1;
function searchJobsPage(page) {
    searchPage = page;
    searchJobs();
}

async function showJobDetail(jobId) {
    try {
        const job = await api.getJob(jobId);
        const sidebar = document.getElementById("jobDetail");
        const content = document.getElementById("jobDetailContent");

        document.getElementById("jobDetailTitle").textContent = job.title;
        content.innerHTML = `\n            <p><strong>公司：</strong>${job.company}</p>\n            <p><strong>地点：</strong>${job.location || "-"}</p>\n            <p><strong>薪资：</strong>${job.salary_min ? `${job.salary_min}-${job.salary_max}K` : "面议"}</p>\n            <p><strong>类型：</strong>${job.job_type}</p>\n            <hr style="margin:12px 0">\n            <h4>职位描述</h4>\n            <p>${job.description || "暂无描述"}</p>\n            <hr style="margin:12px 0">\n            <h4>任职要求</h4>\n            <ul>${(job.requirements || []).map(r => `<li>${r}</li>`).join("") || "暂无"}</ul>\n        `;
        sidebar.style.display = "block";
        sidebar.dataset.jobId = jobId;
    } catch (err) {
        console.error(err);
    }
}

async function matchJob() {
    const sidebar = document.getElementById("jobDetail");
    const jobId = sidebar?.dataset?.jobId;
    const userId = currentUser();
    if (!jobId || !userId) {
        alert("请先登录并选择简历");
        return;
    }

    try {
        const data = await api.listUserResumes(userId);
        if (data.resumes.length === 0) {
            alert("请先上传简历");
            return;
        }
        const resumeId = data.resumes[0].id;
        const result = await api.matchJob(parseInt(jobId), resumeId);
        alert(`匹配度: ${result.match_score}%\n${result.ai_comment}`);
    } catch (err) {
        alert("匹配失败: " + err.message);
    }
}

// ===== 仪表盘加载 =====
async function loadDashboard() {
    const statResumes = document.getElementById("statResumes");
    const statJobs = document.getElementById("statJobs");
    const recentEl = document.getElementById("recentResumes");
    const recEl = document.getElementById("jobRecommendations");

    if (!statResumes) return;

    const userId = currentUser();
    if (!userId) return;

    try {
        const resumeData = await api.listUserResumes(userId);
        statResumes.textContent = resumeData.resumes.length;

        if (recentEl) {
            if (resumeData.resumes.length > 0) {
                recentEl.innerHTML = resumeData.resumes.slice(0, 5).map(r => `\n                    <div class="resume-item" onclick="showResumeDetailById(${r.id})">\n                        <strong>${r.title}</strong>\n                        <small>${new Date(r.created_at).toLocaleDateString()}</small>\n                    </div>\n                `).join("");
            }
        }

        if (resumeData.resumes.length > 0) {
            const recData = await api.getRecommendations(resumeData.resumes[0].id);
            statJobs.textContent = recData.total;
            if (recEl) {
                if (recData.recommendations.length > 0) {
                    recEl.innerHTML = recData.recommendations.slice(0, 5).map(r => `\n                        <div class="job-card" onclick="showJobDetail(${r.job.id})">\n                            <strong>${r.job.title}</strong>\n                            <div class="company">${r.job.company} \u00B7 匹配度 ${r.match_score}%</div>\n                        </div>\n                    `).join("");
                } else {
                    recEl.innerHTML = `<p class="empty-state">暂无推荐职位</p>`;
                }
            }
        }
    } catch (err) {
        console.error("加载仪表盘失败:", err);
    }
}

// ===== 初始化 =====
document.addEventListener("DOMContentLoaded", () => {
    updateAuthUI();
    initUploadZone();

    const path = window.location.pathname;

    if (path.includes("dashboard")) {
        loadDashboard();
    } else if (path.includes("resume")) {
        const userId = currentUser();
        if (userId) loadResumes();
    } else if (path.includes("jobs")) {
        searchJobs();
    }
});
