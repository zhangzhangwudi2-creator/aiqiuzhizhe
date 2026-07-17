"""
简历解析服务 - 解析 PDF/Word 格式简历
"""
import re
from typing import Optional
import io


class ResumeParser:
    """简历文件解析器，支持 PDF 和 Word 文档。"""

    async def parse(self, content: bytes, filename: str, content_type: str) -> dict:
        """解析简历文件，返回结构化数据"""
        raw_text = ""

        if "pdf" in content_type:
            raw_text = await self._parse_pdf(content)
        elif "word" in content_type or "document" in content_type:
            raw_text = await self._parse_word(content)
        else:
            raw_text = content.decode("utf-8", errors="ignore")

        return self._extract_structured_data(raw_text, filename)

    async def _parse_pdf(self, content: bytes) -> str:
        """解析 PDF 文件"""
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    text_parts.append(text.strip())
            return "\n".join(text_parts)
        except Exception as e:
            return f"[PDF 解析失败: {e}]"

    async def _parse_word(self, content: bytes) -> str:
        """解析 Word 文件"""
        try:
            import docx

            doc = docx.Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            return f"[Word 解析失败: {e}]"

    def _extract_structured_data(self, text: str, filename: str) -> dict:
        """从原始文本中提取结构化信息"""
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        result = {
            "full_name": self._extract_name(lines),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "summary": self._extract_summary(lines),
            "skills": self._extract_skills(lines),
            "education": self._extract_education(lines),
            "experience": self._extract_experience(lines),
            "projects": [],
            "raw_text": text,
        }
        return result

    def _extract_name(self, lines: list[str]) -> str:
        """提取姓名（第一行非空通常为姓名）"""
        for line in lines[:5]:
            line_clean = line.strip().strip("*#-")
            if line_clean and len(line_clean) <= 12:
                return line_clean
        return ""

    def _extract_email(self, text: str) -> str:
        """提取邮箱地址"""
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        match = re.search(pattern, text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        """提取手机号码"""
        # 中国手机号（支持 +86 前缀和分隔符）
        cleaned = text.replace(" ", "").replace("-", "").replace("+86", "")
        pattern = r"1[3-9]\d{9}"
        match = re.search(pattern, cleaned)
        return match.group(0) if match else ""

    def _extract_summary(self, lines: list[str]) -> str:
        """提取个人总结（通常出现在姓名/联系方式之后，技能之前）"""
        summary_keywords = ["总结", "简介", "about", "profile", "summary"]
        for keyword in summary_keywords:
            for i, line in enumerate(lines):
                if keyword in line.lower() and len(line) < 20:
                    for j in range(i + 1, min(i + 6, len(lines))):
                        if len(lines[j]) > 10:
                            return lines[j][:500]
        for line in lines[1:6]:
            if 20 < len(line) < 500:
                return line
        return ""

    def _extract_skills(self, lines: list[str]) -> list[str]:
        """提取技能列表"""
        skill_keywords = ["技能", "技术", "skill", "technology"]
        skill_section_idx = -1
        for keyword in skill_keywords:
            for i, line in enumerate(lines):
                if keyword in line.lower() and len(line) < 20:
                    skill_section_idx = i
                    break
            if skill_section_idx >= 0:
                break

        if skill_section_idx < 0:
            return self._fallback_skills(lines)

        skills: list[str] = []
        for i in range(skill_section_idx + 1, min(skill_section_idx + 15, len(lines))):
            line = lines[i]
            if any(kw in line.lower() for kw in ["教育", "经历", "项目", "工作", "experience", "education", "project"]):
                break
            parts = re.split(r"[，,、/|]", line)
            for part in parts:
                part = part.strip().strip("·•-")
                if part and len(part) <= 40:
                    skills.append(part)
        return skills[:30]

    def _fallback_skills(self, lines: list[str]) -> list[str]:
        """从全文通过关键词匹配提取技能"""
        tech_keywords = {
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask", "Spring",
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP",
            "Git", "Linux", "RESTful", "GraphQL",
        }
        found: set[str] = set()
        text_upper = " ".join(lines).upper()
        for kw in tech_keywords:
            if kw.upper() in text_upper:
                found.add(kw)
        return sorted(found)[:20]

    def _extract_education(self, lines: list[str]) -> list[dict]:
        """提取教育经历"""
        edu_section_idx = -1
        for keyword in ["教育", "education"]:
            for i, line in enumerate(lines):
                if keyword in line.lower() and len(line) < 20:
                    edu_section_idx = i
                    break
            if edu_section_idx >= 0:
                break

        if edu_section_idx < 0:
            return self._guess_education(lines)

        records: list[dict] = []
        school_pattern = re.compile(r"(.{2,8}(?:大学|学院|学校|University|College))", re.IGNORECASE)
        degree_pattern = re.compile(r"(博士|硕士|学士|本科|研究生|PhD|Master|Bachelor)")

        for i in range(edu_section_idx + 1, min(edu_section_idx + 10, len(lines))):
            line = lines[i]
            if any(kw in line.lower() for kw in ["经历", "项目", "技能", "experience", "project", "skill"]):
                break
            school_match = school_pattern.search(line)
            degree_match = degree_pattern.search(line)
            if school_match:
                records.append({
                    "school": school_match.group(1),
                    "major": line.replace(school_match.group(1), "").strip().strip("·-–—"),
                    "degree": degree_match.group(1) if degree_match else "",
                    "start_date": "",
                    "end_date": "",
                    "description": line,
                })
        return records[:5]

    def _guess_education(self, lines: list[str]) -> list[dict]:
        """通过高校名称关键词猜测教育经历"""
        records: list[dict] = []
        school_pattern = re.compile(r"(.{2,20}(?:大学|学院|学校|University|College))", re.IGNORECASE)
        for line in lines[:30]:
            match = school_pattern.search(line)
            if match:
                records.append({
                    "school": match.group(1),
                    "major": line.replace(match.group(1), "").strip().strip("·-–—"),
                    "degree": "",
                    "start_date": "",
                    "end_date": "",
                    "description": line,
                })
        return records[:3]

    def _extract_experience(self, lines: list[str]) -> list[dict]:
        """提取工作经历"""
        exp_section_idx = -1
        for keyword in ["工作经历", "工作经验", "经历", "experience"]:
            for i, line in enumerate(lines):
                if keyword in line.lower() and len(line) < 20:
                    exp_section_idx = i
                    break
            if exp_section_idx >= 0:
                break

        if exp_section_idx < 0:
            return []

        records: list[dict] = []
        current: Optional[dict] = None

        for i in range(exp_section_idx + 1, min(exp_section_idx + 30, len(lines))):
            line = lines[i]
            if any(kw in line.lower() for kw in ["教育", "项目", "技能", "education", "project", "skill"]):
                if current:
                    records.append(current)
                break

            if re.search(r"(公司|科技|有限|Group|Inc|Corp|Ltd)", line, re.IGNORECASE):
                if current:
                    records.append(current)
                current = {
                    "company": line,
                    "position": "",
                    "start_date": "",
                    "end_date": "",
                    "description": "",
                }
            elif current:
                if not current["position"] and len(line) < 30:
                    current["position"] = line
                else:
                    current["description"] = (current["description"] + "\n" + line).strip()

        if current:
            records.append(current)

        return records[:10]
