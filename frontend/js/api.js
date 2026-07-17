/**
 * API 客户端 - 封装后端接口调用
 */
const API_BASE = "http://localhost:8000";

class ApiClient {
    constructor() {
        this.token = localStorage.getItem("token");
    }

    _headers() {
        const headers = { "Content-Type": "application/json" };
        if (this.token) {
            headers["Authorization"] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async _request(method, path, body = null) {
        const opts = {
            method,
            headers: this._headers(),
        };
        if (body && !(body instanceof FormData)) {
            opts.body = JSON.stringify(body);
        } else if (body instanceof FormData) {
            // FormData: 删除 Content-Type 让浏览器自动设置 boundary
            delete opts.headers["Content-Type"];
            opts.body = body;
        }
        const res = await fetch(`${API_BASE}${path}`, opts);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "请求失败");
        return data;
    }

    // === 认证 ===
    async register(username, email, password) {
        return this._request("POST", "/api/auth/register", { username, email, password });
    }

    async login(username, password) {
        const data = await this._request("POST", "/api/auth/login", { username, password });
        this.token = data.access_token;
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("username", data.username);
        localStorage.setItem("userId", data.user_id);
        return data;
    }

    async getMe() {
        return this._request("GET", "/api/auth/me");
    }

    // === 简历 ===
    async uploadResume(file, userId, title = "我的简历") {
        const form = new FormData();
        form.append("file", file);
        form.append("user_id", String(userId));
        form.append("title", title);
        const res = await fetch(`${API_BASE}/api/resumes/upload`, {
            method: "POST",
            headers: this.token ? { Authorization: `Bearer ${this.token}` } : {},
            body: form,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "上传失败");
        return data;
    }

    async getResume(resumeId) {
        return this._request("GET", `/api/resumes/${resumeId}`);
    }

    async listUserResumes(userId) {
        return this._request("GET", `/api/resumes/user/${userId}`);
    }

    async analyzeResume(resumeId, jobDescription = "") {
        return this._request("POST", `/api/resumes/${resumeId}/analyze`, { job_description: jobDescription });
    }

    async optimizeResume(resumeId, jobDescription = "") {
        return this._request("PUT", `/api/resumes/${resumeId}/optimize`, { job_description: jobDescription });
    }

    // === 职位 ===
    async searchJobs(keyword = "", location = "", jobType = "", page = 1, pageSize = 20) {
        const params = new URLSearchParams({ keyword, location, job_type: jobType, page, page_size: pageSize });
        return this._request("GET", `/api/jobs/?${params}`);
    }

    async getJob(jobId) {
        return this._request("GET", `/api/jobs/${jobId}`);
    }

    async matchJob(jobId, resumeId) {
        return this._request("POST", `/api/jobs/${jobId}/match/${resumeId}`);
    }

    async getRecommendations(resumeId) {
        return this._request("GET", `/api/jobs/recommendations/${resumeId}`);
    }
}

// 全局 API 实例
const api = new ApiClient();
