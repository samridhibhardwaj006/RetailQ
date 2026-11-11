'use strict';

const $ = (id) => document.getElementById(id);
const money = (value) => '£' + Number(value || 0).toLocaleString('en-GB', {minimumFractionDigits: 0, maximumFractionDigits: 0});
const number = (value) => Number(value || 0).toLocaleString('en-GB');
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

function queryString() {
  const query = new URLSearchParams();
  ['country', 'start', 'end', 'search'].forEach((key) => {
    const element = $(key);
    const value = element ? element.value.trim() : '';
    if (value && value !== 'All') query.set(key, value);
  });
  return query.toString();
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const message = payload && payload.detail ? payload.detail : (payload && payload.error ? payload.error : `Request failed (${response.status})`);
    throw new Error(message);
  }
  return payload;
}

async function api(path) {
  const query = queryString();
  return request(path + (query ? `?${query}` : ''));
}

function showNotice(message, type = 'error') {
  let notice = $('appNotice');
  if (!notice) {
    notice = document.createElement('div');
    notice.id = 'appNotice';
    notice.setAttribute('role', 'status');
    notice.style.cssText = 'margin:12px 0;padding:12px 14px;border-radius:10px;font-size:13px;line-height:1.5';
    const main = document.querySelector('.main');
    main.insertBefore(notice, main.children[1] || null);
  }
  notice.style.background = type === 'success' ? 'rgba(48,190,150,.12)' : 'rgba(230,95,95,.12)';
  notice.style.border = type === 'success' ? '1px solid rgba(48,190,150,.35)' : '1px solid rgba(230,95,95,.35)';
  notice.style.color = type === 'success' ? '#8ce0c8' : '#ffb4b4';
  notice.textContent = message;
}

function setText(id, value) {
  const element = $(id);
  if (element) element.textContent = value;
}

async function init() {
  try {
    const filters = await request('/api/filters');
    setText('source', filters.source || 'Dataset source unavailable');
    setText('sourceSide', filters.source || 'Dataset source unavailable');
    if ($('start')) $('start').value = filters.start || '';
    if ($('end')) $('end').value = filters.end || '';
    setText('dateRange', `${filters.start || '—'} — ${filters.end || '—'}`);
    const countrySelect = $('country');
    if (countrySelect) {
      countrySelect.replaceChildren(new Option('All', 'All'));
      (filters.countries || []).forEach((country) => countrySelect.add(new Option(country, country)));
    }
    await loadAll();
  } catch (error) {
    showNotice(`RetailIQ could not initialise: ${error.message}. Check that the FastAPI server is running, then refresh.`, 'error');
    console.error('RetailIQ initialisation failed:', error);
  }
}

async function loadAll() {
  const jobs = [
    ['overview', '/api/overview'], ['trends', '/api/trends'], ['products', '/api/products'],
    ['countries', '/api/countries'], ['segments', '/api/segments'], ['forecast', '/api/forecast'],
    ['anomalies', '/api/anomalies']
  ];
  const results = await Promise.allSettled(jobs.map(([, path]) => api(path)));
  const values = {};
  const failures = [];
  results.forEach((result, index) => {
    const key = jobs[index][0];
    if (result.status === 'fulfilled') values[key] = result.value;
    else failures.push(`${key}: ${result.reason.message}`);
  });

  if (values.overview) renderOverview(values.overview);
  else showNotice(`Overview could not load: ${failures.join(' · ')}`);
  if (values.trends) drawTrend(values.trends); else setText('trend', 'Monthly revenue could not be loaded.');
  if (values.countries) drawBars(values.countries.map((row) => ({name: row.country, value: row.revenue}))); else setText('markets', 'Market data could not be loaded.');
  if (values.products) drawProducts(values.products); else setText('productTable', 'Product data could not be loaded.');
  if (values.segments) drawSegments(values.segments); else setText('segments', 'Customer segments could not be loaded.');
  if (values.forecast) drawForecast(values.forecast); else setText('forecast', 'Forecast baseline could not be loaded.');
  if (values.anomalies) drawAnomalies(values.anomalies); else setText('anomalies', 'Anomaly analysis could not be loaded.');
  try { await loadDocs(); } catch (error) { setText('docs', `Knowledge desk unavailable: ${error.message}`); }

  if (failures.length) {
    showNotice(`Some dashboard modules could not load: ${failures.join(' · ')}`, 'error');
  } else {
    const notice = $('appNotice');
    if (notice) notice.remove();
  }
}

function renderOverview(data) {
  setText('revenue', money(data.revenue));
  setText('orders', number(data.orders));
  setText('customers', number(data.customers));
  setText('aov', money(data.aov));
  setText('units', number(data.units));
  setText('returns', `${Number(data.return_rate || 0).toFixed(1)}%`);
  setText('returnLines', `${number(data.return_lines)} flagged lines`);
  setText('source', data.source || 'Dataset source unavailable');
  setText('sourceSide', `${number(data.rows)} transaction lines`);
  setText('dateRange', `${data.date_min || '—'} — ${data.date_max || '—'}`);
}

function drawTrend(rows) {
  const element = $('trend');
  if (!element) return;
  if (!Array.isArray(rows) || !rows.length) { element.textContent = 'No sales data for this filter.'; return; }
  const width = 650, height = 205, padding = 28;
  const values = rows.map((row) => Number(row.revenue) || 0);
  const max = Math.max(...values, 1) * 1.12;
  const points = values.map((value, index) => [padding + index * (width - 2 * padding) / Math.max(values.length - 1, 1), height - padding - value / max * (height - 2 * padding)]);
  const path = points.map((point, index) => `${index ? 'L' : 'M'}${point[0]},${point[1]}`).join(' ');
  const labels = rows.filter((_, index) => index % Math.max(1, Math.ceil(rows.length / 6)) === 0);
  element.innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Monthly revenue trend"><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#8587f5" stop-opacity=".32"/><stop offset="1" stop-color="#8587f5" stop-opacity="0"/></linearGradient></defs>${[.25,.5,.75].map((value) => `<line x1="${padding}" x2="${width-padding}" y1="${height-padding-value*(height-2*padding)}" y2="${height-padding-value*(height-2*padding)}" stroke="#263650" stroke-dasharray="3 5"/>`).join('')}<path d="${path} L${points[points.length-1][0]},${height-padding} L${points[0][0]},${height-padding} Z" fill="url(#area)"/><path d="${path}" fill="none" stroke="#9293ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>${points.filter((_, index) => index % Math.max(1, Math.ceil(points.length/8)) === 0).map((point) => `<circle cx="${point[0]}" cy="${point[1]}" r="3.5" fill="#62d7c6"/>`).join('')}</svg><div style="display:flex;justify-content:space-between;color:#71839f;font-size:9px">${labels.map((row) => `<span>${escapeHTML(row.month)}</span>`).join('')}</div>`;
}

function drawBars(rows) {
  const element = $('markets');
  if (!element) return;
  if (!rows.length) { element.textContent = 'No market data for this filter.'; return; }
  const max = Math.max(...rows.map((row) => Number(row.value) || 0), 1);
  element.innerHTML = rows.slice(0, 7).map((row) => `<div class="barrow"><span class="barname">${escapeHTML(row.name)}</span><div class="bartrack"><div class="barfill" style="width:${Math.max(0, Math.min(100, row.value/max*100))}%"></div></div><span class="barval">${money(row.value)}</span></div>`).join('');
}

function drawProducts(rows) {
  const element = $('productTable');
  if (!element) return;
  element.innerHTML = `<table class="table"><thead><tr><th>PRODUCT</th><th>UNITS</th><th>REVENUE</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${escapeHTML(row.product)}</td><td>${number(row.units)}</td><td>${money(row.revenue)}</td></tr>`).join('')}</tbody></table>`;
  if (!rows.length) element.textContent = 'No products found for this filter.';
}

function drawSegments(data) {
  const element = $('segments');
  if (!element) return;
  const rows = data.segments || [];
  element.innerHTML = rows.map((row) => `<div class="segment"><b>${escapeHTML(row.segment)}</b><span>${number(row.customers)} customers</span><small>${money(row.revenue)} revenue · ${Number(row.avg_recency).toFixed(1)} days average recency</small></div>`).join('') || 'No customer segments for this selection.';
}

function drawForecast(data) {
  const element = $('forecast');
  if (!element) return;
  const rows = data.baseline || [];
  element.innerHTML = rows.slice(-6).map((row) => `<div class="forecastrow"><span>${escapeHTML(row.month)}${row.actual === null ? ' · forecast' : ''}</span><b>${money(row.actual ?? row.baseline)}</b></div>`).join('') || escapeHTML(data.note || 'Not enough history to calculate a forecast.');
}

function drawAnomalies(rows) {
  const element = $('anomalies');
  if (!element) return;
  element.innerHTML = rows.slice(0, 7).map((row) => `<div class="anomaly"><b>Invoice ${escapeHTML(row.invoice)}</b><span>${money(row.total)}</span></div>`).join('') || '<small>No anomaly candidates for this selection.</small>';
}

function usePrompt(value) { $('question').value = value; ask(); }

async function ask() {
  const question = $('question').value.trim();
  if (!question) return;
  const answer = $('answer');
  answer.classList.remove('hidden');
  answer.textContent = 'Analysing…';
  try {
    const result = await request('/api/ask', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question})});
    answer.innerHTML = `<h3>WORKFLOW · ${escapeHTML(result.route || 'query')}</h3><div>${escapeHTML(result.answer || result.error || '')}</div><pre>${escapeHTML(JSON.stringify(result.evidence || result.retrieved_documents || [], null, 2).slice(0, 3500))}</pre>`;
  } catch (error) {
    answer.textContent = `Analysis failed: ${error.message}`;
  }
}

async function loadDocs() {
  const documents = await request('/api/documents');
  $('docs').innerHTML = documents.map((document) => `<div class="docitem">▧ &nbsp; ${escapeHTML(document.name)}<small>${number(document.characters)} characters · indexed for retrieval</small></div>`).join('');
}

async function uploadDoc() {
  const file = $('docfile').files[0];
  if (!file) { alert('Choose a PDF, TXT or MD file first.'); return; }
  const form = new FormData();
  form.append('file', file);
  try {
    await request('/api/documents', {method:'POST', body:form});
    alert('Document added to the knowledge desk.');
    await loadDocs();
    $('docfile').value = '';
  } catch (error) { alert(`Upload failed: ${error.message}`); }
}

window.loadAll = loadAll;
window.usePrompt = usePrompt;
window.ask = ask;
window.uploadDoc = uploadDoc;
document.addEventListener('DOMContentLoaded', init);
