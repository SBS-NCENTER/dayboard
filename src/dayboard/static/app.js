// dayboard 프론트: /api/data 폴링 + 4-page 클릭드래그 스와이프.
function esc(s) {
  return String(s == null ? '' : s)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}
// 테마 (dark 기본 / light 토글, localStorage 지속)
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  document.getElementById('theme-btn').textContent = t === 'light' ? '☀' : '☾';
}
let theme = localStorage.getItem('theme') === 'light' ? 'light' : 'dark';
applyTheme(theme);
document.getElementById('theme-btn').onclick = () => {
  theme = theme === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', theme);
  applyTheme(theme);
};
const PAGES = 4, REFRESH_MS = 5 * 60 * 1000;
let idx = 0;
const track = document.getElementById('track');
const dotsBox = document.getElementById('dots');

for (let i = 0; i < PAGES; i++) {
  const d = document.createElement('div');
  d.className = 'dot' + (i === 0 ? ' on' : '');
  d.onclick = () => go(i);
  dotsBox.appendChild(d);
}
function go(i) {
  idx = Math.max(0, Math.min(PAGES - 1, i));
  track.style.transform = `translateX(-${idx * 25}%)`;
  [...dotsBox.children].forEach((d, k) => d.classList.toggle('on', k === idx));
}
document.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowLeft') go(idx - 1);
  if (e.key === 'ArrowRight') go(idx + 1);
});
// 클릭-드래그 / 터치 스와이프
let x0 = null;
const start = (x) => { x0 = x; track.style.transition = 'none'; };
const end = (x) => {
  track.style.transition = '';
  if (x0 === null) return;
  const dx = x - x0; x0 = null;
  if (Math.abs(dx) > 60) go(idx + (dx < 0 ? 1 : -1)); else go(idx);
};
track.addEventListener('mousedown', (e) => start(e.clientX));
window.addEventListener('mouseup', (e) => end(e.clientX));
track.addEventListener('touchstart', (e) => start(e.touches[0].clientX), { passive: true });
track.addEventListener('touchend', (e) => end(e.changedTouches[0].clientX));

const WD = ['월', '화', '수', '목', '금', '토', '일'];
function renderCalendar(c) {
  const el = document.getElementById('cal');
  if (!c) { el.innerHTML = '<div class="err">달력 로드 실패</div>'; return; }
  let h = '<div class="cal-grid">' + WD.map(w => `<div class="cal-h">${w}</div>`).join('');
  for (const wk of c.weeks) for (const cell of wk) {
    if (cell.day === null) { h += '<div class="cal-c empty"></div>'; continue; }
    const cls = 'cal-c' + (cell.is_today ? ' today' : '') + (cell.holiday ? ' holiday' : '');
    h += `<div class="${cls}">${cell.day}` +
         (cell.holiday ? `<span class="cal-hol-name">${esc(cell.holiday)}</span>` : '') + '</div>';
  }
  el.innerHTML = h + '</div>';
}
function renderWeather(w) {
  const el = document.getElementById('wx');
  if (!w) { el.innerHTML = '<div class="err">날씨 불러오기 실패</div>'; return; }
  el.innerHTML = `<div class="big">${Math.round(w.temp)}°</div>` +
    `<div class="sub">${esc(w.label)}</div>` +
    `<div class="row"><span>최고 ${Math.round(w.tmax)}°</span><span>최저 ${Math.round(w.tmin)}°</span>` +
    `<span>습도 ${Math.round(w.humidity)}%</span><span>바람 ${Math.round(w.wind)} m/s</span></div>`;
}
function renderSunMoon(s) {
  const el = document.getElementById('sm');
  if (!s) { el.innerHTML = '<div class="err">해/달 정보 로드 실패</div>'; return; }
  el.innerHTML =
    `<div class="row" style="font-size:2rem"><span>🌅 ${s.sunrise}</span><span>🌇 ${s.sunset}</span></div>` +
    `<div class="big" style="font-size:3rem;margin-top:3vh">${s.moon_phase}</div>` +
    `<div class="sub">달 나이 ${s.moon_age}일</div>`;
}
function renderSky(events) {
  const el = document.getElementById('sky');
  if (!events || !events.length) { el.innerHTML = '<div class="err">다가오는 천체 이벤트 없음</div>'; return; }
  el.innerHTML = events.map(e =>
    `<div class="ev"><span>${esc(e.name)}${e.note ? ` <small>(${esc(e.note)})</small>` : ''}</span><span class="d">${esc(e.date)}</span></div>`
  ).join('');
}
async function refresh() {
  try {
    const r = await fetch('/api/data');
    if (!r.ok) return;
    const d = await r.json();
    renderCalendar(d.calendar); renderWeather(d.weather);
    renderSunMoon(d.sun_moon); renderSky(d.events);
  } catch (e) { /* 네트워크 순간 실패 — 다음 폴링에서 복구 */ }
}
refresh();
setInterval(refresh, REFRESH_MS);
