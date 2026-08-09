// AI 求职助手前端逻辑（原生 JavaScript，无框架）

// === 通用提示 ===
function showError(msg) {
  const el = document.getElementById('errBox');
  el.textContent = msg || '出错了，请重试';
  el.classList.add('show');
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
function hideError() {
  document.getElementById('errBox').classList.remove('show');
}

function friendlyDetail(status, detail) {
  const d = (detail || '').toString();
  if (status === 400) {
    if (d.includes('请输入岗位描述')) return '请先填写岗位描述';
    if (d.includes('PDF 解析失败')) return '简历解析失败：文件可能已损坏，请确认后重新上传';
    if (d.includes('无法从 PDF 中提取文字')) return '未能从简历中提取到文字，请改用文字版 PDF 简历';
    if (d.includes('请上传 PDF')) return '请选择 PDF 格式的简历文件';
    if (d.includes('文件类型不是 PDF')) return '文件类型不是 PDF，请上传 PDF 格式的简历';
    return d || '请求有误，请检查输入后重试';
  }
  if (status === 413) return '内容超出长度限制（简历 PDF 最大 10MB，JD 最多 15000 字），请精简后重试';
  if (status === 429) return '请求太频繁，请稍后再试';
  if (status === 503) return '服务暂时不可用，请稍后再试或联系管理员';
  if (status === 502) {
    if (d.includes('事实一致性校验')) return 'AI 改写结果未通过事实一致性校验，建议重试或补充更明确的原始简历信息。';
    if (d.includes('空内容')) return 'AI 没有返回有效内容，请重试';
    if (d.includes('格式异常')) return 'AI 返回格式异常，请重试';
    return 'AI 服务暂时不可用，请稍后重试';
  }
  return d || '操作失败，请重试';
}

async function readError(res) {
  let detail = '';
  try {
    const e = await res.json();
    detail = (e && e.detail) || '';
  } catch (_) { /* 非 JSON 响应，保留空 detail */ }
  return { status: res.status, detail };
}

function retryAfterMessage(res) {
  const ra = res.headers.get('Retry-After');
  return ra ? '请求太频繁，请约 ' + ra + ' 秒后重试' : '请求太频繁，请稍后再试';
}

// === PDF 上传 ===
const pz = document.getElementById('pdfZone');
const pi = document.getElementById('pdfInput');
const pn = document.getElementById('pdfName');

pz.addEventListener('click', () => pi.click());
pz.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pi.click(); } });
pz.addEventListener('dragover', e => { e.preventDefault(); pz.classList.add('dragover'); });
pz.addEventListener('dragleave', () => pz.classList.remove('dragover'));
pz.addEventListener('drop', e => {
  e.preventDefault();
  pz.classList.remove('dragover');
  if (e.dataTransfer.files.length) loadPDF(e.dataTransfer.files[0]);
});
pi.addEventListener('change', e => { if (e.target.files.length) loadPDF(e.target.files[0]); });

function loadPDF(f) {
  if (!f) return;
  if (f.size === 0) { alert('检测到空文件，请选择有效的 PDF 简历'); return; }
  if (f.type !== 'application/pdf') { alert('请选择 PDF 格式的简历文件'); return; }
  if (f.size > 10 * 1024 * 1024) { alert('简历文件不能超过 10MB，请压缩后再上传'); return; }
  pz.classList.add('has-file');
  pn.textContent = '✓ ' + f.name + ' · ' + (f.size / 1024).toFixed(1) + ' KB';
  pn.classList.add('show');
  pz._f = f;
  updateReadiness();
}

// === OCR 截图识别 ===
const iz = document.getElementById('imgZone');
const ii = document.getElementById('imgInput');
const inm = document.getElementById('imgName');
const opb = document.getElementById('ocrProg');
const ofl = document.getElementById('ocrFill');
const otx = document.getElementById('ocrText');
const ost = document.getElementById('ocrStatus');
let busy = false;
let totalImg = 0;
let allTxt = [];

iz.addEventListener('click', () => { if (!busy) ii.click(); });
iz.addEventListener('keydown', e => { if ((e.key === 'Enter' || e.key === ' ') && !busy) { e.preventDefault(); ii.click(); } });
iz.addEventListener('dragover', e => { e.preventDefault(); e.stopPropagation(); iz.classList.add('dragover'); });
iz.addEventListener('dragleave', e => { e.preventDefault(); e.stopPropagation(); iz.classList.remove('dragover'); });
iz.addEventListener('drop', e => {
  e.preventDefault();
  e.stopPropagation();
  iz.classList.remove('dragover');
  const fs = Array.from(e.dataTransfer.files).filter(x => x.type.startsWith('image/'));
  if (fs.length) addImgs(fs);
});
ii.addEventListener('change', e => {
  if (e.target.files.length) {
    addImgs(Array.from(e.target.files).filter(x => x.type.startsWith('image/')));
    ii.value = '';
  }
});

function addImgs(fs) {
  if (!fs.length) return;
  iz.classList.add('has-file');
  inm.classList.add('show');
  ost.style.display = 'none';
  opb.style.display = 'block';
  runOCR(fs);
}

async function runOCR(fs, idx) {
  if (idx === undefined) idx = 0;
  if (!fs[idx]) { ocrDone(); return; }
  busy = true;
  updateReadiness();
  const f = fs[idx];
  const seq = totalImg + 1;
  inm.textContent = '[' + seq + '] ' + f.name;
  ofl.style.width = ((idx / fs.length) * 80) + '%';
  otx.textContent = '识别中 (' + seq + ')...';
  ost.style.display = 'none';
  try {
    const du = await new Promise((ok, no) => {
      const r = new FileReader();
      r.onload = () => ok(r.result);
      r.onerror = no;
      r.readAsDataURL(f);
    });
    ofl.style.width = (((idx + 0.1) / fs.length) * 80) + '%';
    otx.textContent = '第 ' + seq + ' 张：识别中...';
    const res = await Tesseract.recognize(du, 'chi_sim+eng', {
      logger: m => {
        if (m.status === 'recognizing text') {
          ofl.style.width = Math.min((idx / fs.length) * 80 + (m.progress * 15 / fs.length), 85) + '%';
        }
      }
    });
    const t = res.data.text.trim();
    if (t) {
      allTxt.push(t);
      totalImg++;
      ofl.style.width = (((idx + 0.9) / fs.length) * 80) + '%';
      otx.textContent = '完成 (' + seq + ') ' + t.length + ' 字';
    } else {
      otx.textContent = '跳过 (' + seq + ') 未识别到文字';
    }
  } catch (e) {
    otx.textContent = '失败 (' + seq + ') ' + e.message.substring(0, 30);
  }
  document.getElementById('jdInput').value = allTxt.join('\n\n---\n\n');
  updateReadiness();
  await new Promise(r => setTimeout(r, 100));
  if (idx + 1 < fs.length) await runOCR(fs, idx + 1); else ocrDone();
}

function ocrDone() {
  const v = document.getElementById('jdInput').value;
  const tc = v.length;
  ofl.style.width = '100%';
  otx.textContent = '完成！共 ' + totalImg + ' 张，' + tc + ' 字';
  if (tc < 20) {
    ost.style.display = 'block';
    ost.style.background = '#fffbeb';
    ost.style.color = '#d97706';
    ost.style.border = '1px solid #fde68a';
    ost.textContent = '识别文字较少，请检查截图是否清晰';
  } else {
    ost.style.display = 'block';
    ost.style.background = '#f0fdf4';
    ost.style.color = '#16a34a';
    ost.style.border = '1px solid #bbf7d0';
    ost.textContent = totalImg + ' 张截图，' + tc + ' 字。可继续添加';
  }
  busy = false;
  updateReadiness();
  document.getElementById('jdInput').focus();
  setTimeout(() => {
    opb.style.display = 'none';
    inm.textContent = '已识别 ' + totalImg + ' 张，可继续添加';
  }, 4000);
}

// === 分析 ===
const jdInput = document.getElementById('jdInput');
const charCount = document.getElementById('charCount');
const analyzeBtn = document.getElementById('btnAnalyze');

document.getElementById('btnAnalyze').addEventListener('click', analyze);

function updateReadiness() {
  const n = jdInput.value.length;
  charCount.textContent = n.toLocaleString() + ' 字';
  analyzeBtn.disabled = !(pz._f && jdInput.value.trim()) || busy;
}
jdInput.addEventListener('input', updateReadiness);
updateReadiness();

async function analyze() {
  const f = pz._f;
  const jd = jdInput.value.trim();
  if (!f) { alert('请先上传 PDF 简历'); return; }
  if (!jd) { alert('请先填写岗位描述'); return; }
  hideError();
  document.getElementById('results').classList.remove('show');
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = '正在分析…';
  document.getElementById('loading').classList.add('show');
  document.getElementById('s1').className = 'on';
  const fd = new FormData();
  fd.append('resume', f);
  fd.append('jd_text', jd);
  try {
    document.getElementById('s1').className = 'ok';
    document.getElementById('s2').className = 'on';
    const res = await fetch('/analyze', { method: 'POST', body: fd });
    document.getElementById('s2').className = 'ok';
    document.getElementById('s3').className = 'on';
    if (!res.ok) {
      const { status, detail } = await readError(res);
      const msg = status === 429 ? retryAfterMessage(res) : friendlyDetail(status, detail);
      throw new Error(msg);
    }
    const d = await res.json();
    document.getElementById('s3').className = 'ok';
    showRes(d);
  } catch (e) {
    document.getElementById('s3').className = 'on';
    showError(e.message || '分析失败，请重试');
  } finally {
    analyzeBtn.textContent = '重新分析';
    document.getElementById('loading').classList.remove('show');
    updateReadiness();
  }
}

function showRes(d) {
  if (!d || typeof d !== 'object') {
    showError('分析结果为空，请重试');
    return;
  }
  const sc = Number.isFinite(d.overall_score) ? d.overall_score : 0;
  document.getElementById('scoreNum').textContent = sc;
  document.getElementById('scoreRing').style.setProperty('--pct', sc + '%');

  function rd(list, id) {
    const el = document.getElementById(id);
    if (!Array.isArray(list) || !list.length) {
      el.innerHTML = '<div class="emp">暂无数据</div>';
      return;
    }
    el.innerHTML = list.map(i => {
      let h = '<div class="ri">';
      if (i.point) h += '<div class="lb">' + esc(i.point) + '</div>';
      if (i.detail) h += '<div class="ds">' + esc(i.detail) + '</div>';
      if (i.skill) h += '<div class="lb">' + esc(i.skill) + '</div>';
      if (i.current_status) h += '<div class="ds">现状：' + esc(i.current_status) + '</div>';
      if (i.improvement_suggestion) h += '<div class="ds">建议：' + esc(i.improvement_suggestion) + '</div>';
      if (i.importance) {
        const c = { '高': 't1', '中': 't2', '低': 't3' }[i.importance];
        h += '<span class="tg ' + c + '">' + esc(i.importance) + ' 优先级</span>';
      }
      if (i.section) h += '<div class="lb">' + esc(i.section) + '</div>';
      if (i.issue) h += '<div class="ds">问题：' + esc(i.issue) + '</div>';
      if (i.rewrite_suggestion) h += '<div class="ds">建议：' + esc(i.rewrite_suggestion) + '</div>';
      if (i.question) h += '<div class="lb">' + esc(i.question) + '</div>';
      if (i.intent) h += '<div class="ds">考察点：' + esc(i.intent) + '</div>';
      if (i.difficulty) {
        const c = { '简单': 't4', '中等': 't5', '困难': 't6' }[i.difficulty];
        h += '<span class="tg ' + c + '">' + esc(i.difficulty) + '</span>';
      }
      return h + '</div>';
    }).join('');
  }

  rd(d.strengths, 'lc1');
  rd(d.skill_gaps, 'lc2');
  rd(d.resume_tips, 'lc3');
  rd(d.interview_questions, 'lc4');
  document.getElementById('sc1').textContent = (d.strengths || []).length;
  document.getElementById('sc2').textContent = (d.skill_gaps || []).length;
  document.getElementById('sc3').textContent = (d.resume_tips || []).length;
  document.getElementById('sc4').textContent = (d.interview_questions || []).length;
  document.getElementById('results').classList.add('show');
  document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function esc(t) {
  if (!t) return '';
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

function stripMD(t) {
  return t.replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/~~~[\s\S]*?~~~/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .trim();
}

// === 生成优化简历 ===
const rwOut = document.getElementById('rwOut');
const rwLoad = document.getElementById('rwLoad');
const btnRewrite = document.getElementById('btnRewrite');

btnRewrite.addEventListener('click', doRewrite);

function isNeutralRole(role) {
  return role === '目标岗位' || role === '未指定岗位';
}

async function doRewrite() {
  const f = pz._f;
  const jd = jdInput.value.trim();
  const role = document.getElementById('targetRole').value.trim();
  if (!f || !jd) { alert('请先上传简历并填写岗位描述'); return; }
  hideError();
  rwOut.style.display = 'none';
  rwLoad.style.display = 'block';
  btnRewrite.disabled = true;
  const fd = new FormData();
  fd.append('resume', f);
  fd.append('jd_text', jd);
  if (role) fd.append('target_role', role);
  try {
    const res = await fetch('/rewrite-resume', { method: 'POST', body: fd });
    if (!res.ok) {
      const { status, detail } = await readError(res);
      const msg = status === 429 ? retryAfterMessage(res) : friendlyDetail(status, detail);
      throw new Error(msg);
    }
    const d = await res.json();
    const resolvedRole = (d && d.target_role) || role || '目标岗位';
    const neutral = isNeutralRole(resolvedRole);
    if (!neutral) {
      document.getElementById('targetRole').value = resolvedRole;
    }
    document.getElementById('rwBody').textContent = stripMD((d && d.rewritten_resume) || '');
    document.getElementById('rwTitle').textContent = neutral
      ? '目标岗位待确认（可在上方手动填写后重试）'
      : '已自动针对「' + resolvedRole + '」重写';
    rwLoad.style.display = 'none';
    rwOut.style.display = 'block';
    document.getElementById('rwSec').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (e) {
    rwLoad.style.display = 'none';
    showError(e.message || '改写失败，请重试');
  } finally {
    btnRewrite.disabled = false;
  }
}

// === 复制优化简历 ===
function copyResume() {
  const t = document.getElementById('rwBody').textContent;
  navigator.clipboard.writeText(t).then(() => {
    const btns = document.querySelectorAll('.rhd button');
    const o = btns[0].textContent;
    btns[0].textContent = '已复制';
    setTimeout(() => { btns[0].textContent = o; }, 2000);
  });
}

// === 下载 PDF（保留照片）；后端必须提取到原简历照片才会生成 ===
async function dlPDF() {
  const t = document.getElementById('rwBody').textContent;
  if (!t || !t.trim()) { alert('请先生成优化简历'); return; }
  if (!pz._f) { alert('原简历文件已失效，请重新上传，以便保留照片'); return; }
  const role = document.getElementById('targetRole').value.trim() || '目标岗位';
  const fd = new FormData();
  fd.append('resume', pz._f);
  fd.append('rewritten_resume', t);
  fd.append('target_role', role);
  try {
    const res = await fetch('/export-resume-pdf', { method: 'POST', body: fd });
    if (!res.ok) {
      const { status, detail } = await readError(res);
      let msg = friendlyDetail(status, detail);
      if (status === 422 && detail.includes('未检测到')) {
        msg = '原简历中未检测到可提取的证件照，已停止导出；请上传带证件照的 PDF 简历。';
      }
      throw new Error(msg);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const safeRole = role.replace(/[\\/:*?"<>|]/g, '_');
    const a = document.createElement('a');
    a.href = url;
    a.download = safeRole + '_针对性简历.pdf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (e) {
    alert(e.message);
  }
}

// === 下载 Word（浏览器端生成草稿） ===
function dlWord() {
  const t = stripMD(document.getElementById('rwBody').textContent);
  if (!t || !t.trim()) { alert('请先生成优化简历'); return; }
  let body = '';
  for (const l of t.split('\n')) {
    const s = l.trim();
    if (!s) body += '<p>&nbsp;</p>';
    else if (s.startsWith('### ')) body += '<h3>' + esc(s.slice(4)) + '</h3>';
    else if (s.startsWith('## ')) body += '<h2>' + esc(s.slice(3)) + '</h2>';
    else if (s.startsWith('# ')) body += '<h1>' + esc(s.slice(2)) + '</h1>';
    else if (s.startsWith('- ') || s.startsWith('* ')) body += '<li>' + esc(s.slice(2)) + '</li>';
    else body += '<p>' + esc(s) + '</p>';
  }
  const html = '<html><head><meta charset=utf-8><style>body{font-family:Arial,SimSun;font-size:11pt;line-height:1.4;color:#000}h1,h2,h3,p,li{color:#000}</style></head><body>' + body + '</body></html>';
  const blob = new Blob([html], { type: 'application/msword' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '优化简历.doc';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
