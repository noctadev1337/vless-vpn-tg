from datetime import datetime


def _fmt_traffic(used_b: int, limit_b: int) -> tuple[str, str]:
    """Возвращает (строка трафика, html прогресс-бар)."""
    if limit_b > 0:
        used_gb = used_b / 1024 ** 3
        limit_gb = limit_b / 1024 ** 3
        tr_str = f"{used_gb:.1f} ГБ / {limit_gb:.0f} ГБ"
        pct = min(100, int(used_b / limit_b * 100))
        bar = (
            f'<div style="margin-top:20px;width:100%">'
            f'<div style="background:rgba(0,0,0,0.4);border-radius:8px;'
            f'height:6px;overflow:hidden;border:1px solid rgba(147,51,234,0.2)">'
            f'<div style="background:linear-gradient(90deg,#9333ea,#4f46e5);'
            f'height:100%;width:{pct}%;border-radius:8px;transition:width 1s ease">'
            f'</div></div></div>'
        )
    else:
        used_gb = used_b / 1024 ** 3
        tr_str = f"{used_gb:.1f} ГБ / ∞"
        bar = ""
    return tr_str, bar


def _fmt_news(news) -> str:
    if not news:
        return ""
    n_text, n_date = news
    n_text_esc = (
        n_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    try:
        from datetime import datetime as _dt
        n_dt = _dt.fromisoformat(str(n_date))
        n_date_fmt = n_dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        n_date_fmt = str(n_date)[:16]
    return (
        '<div class="news-block">'
        '<div class="news-label">📢 Новости</div>'
        f'<div class="news-text">{n_text_esc}</div>'
        f'<div class="news-date">{n_date_fmt}</div>'
        '</div>'
    )


def build_html(
        sub, used_b: int, limit_b: int, expires: datetime, key: str,
        tg_id=None, news=None
) -> str:
    from shared.config import DOMAIN, PLANS, VPN_NAME, BOT_LINK

    vpn_name = VPN_NAME
    bot_link = BOT_LINK
    plan = PLANS.get(sub["plan"], {})
    plan_name = plan.get("name", sub["plan"])
    days_left = max(0, (expires - datetime.now()).days)
    full_url = f"https://{DOMAIN}/{key}"
    tg_id_str = str(tg_id) if tg_id else "—"
    tr_str, bar = _fmt_traffic(used_b, limit_b)
    news_block = _fmt_news(news)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{vpn_name} - Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-main: #06030b;
  --bg-card: rgba(18,10,32,0.5);
  --border-glow: rgba(147,51,234,0.3);
  --primary: #9333ea;
  --secondary: #4f46e5;
  --accent: #d8b4fe;
  --text-light: #f8fafc;
  --text-muted: #94a3b8;
  --success: #10b981;
  --warning: #f59e0b;
}}
*,*::before,*::after {{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
body {{background-color:var(--bg-main);color:var(--text-light);font-family:'Inter',sans-serif;min-height:100vh;display:flex;justify-content:center;padding:24px 16px 40px;overflow-x:hidden;position:relative}}
.ambient-bg {{position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;overflow:hidden;background:radial-gradient(circle at 15% 50%,rgba(147,51,234,0.08),transparent 25%),radial-gradient(circle at 85% 30%,rgba(79,70,229,0.08),transparent 25%)}}
.orb {{position:absolute;border-radius:50%;filter:blur(80px);opacity:0.5;animation:pulseOrb 10s infinite alternate ease-in-out}}
.orb-1 {{width:300px;height:300px;background:var(--primary);top:-100px;right:-100px}}
.orb-2 {{width:250px;height:250px;background:var(--secondary);bottom:-50px;left:-50px;animation-delay:-5s}}
@keyframes pulseOrb {{0% {{transform:scale(1) translate(0,0)}} 100% {{transform:scale(1.2) translate(20px,30px)}}}}
.app-container {{width:100%;max-width:540px;z-index:1;display:flex;flex-direction:column;gap:20px}}
.header {{text-align:center;margin-bottom:10px;animation:fadeInDown 0.8s ease-out}}
.header h1 {{font-family:'Orbitron',sans-serif;font-size:2.2rem;font-weight:900;letter-spacing:2px;background:linear-gradient(to right,#fff,var(--accent),var(--primary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 30px rgba(147,51,234,0.4)}}
.glass-card {{background:var(--bg-card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border-glow);border-radius:24px;padding:24px;box-shadow:0 8px 32px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.05);position:relative;overflow:hidden;opacity:0;transform:translateY(20px);animation:fadeUp 0.6s forwards cubic-bezier(0.2,0.8,0.2,1)}}
.glass-card::before {{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--primary),transparent);opacity:0.5}}
.card-title {{display:flex;align-items:center;gap:10px;font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:20px;letter-spacing:1px}}
.card-title svg {{width:20px;height:20px;color:var(--accent);filter:drop-shadow(0 0 8px var(--primary))}}
.plan-badge {{background:rgba(147,51,234,0.15);border:1px solid rgba(147,51,234,0.5);color:var(--accent);padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-left:auto;box-shadow:0 0 15px rgba(147,51,234,0.2)}}
.stats-grid {{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.stat-box {{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.03);border-radius:16px;padding:16px;transition:transform 0.3s}}
.stat-box:hover {{transform:translateY(-2px);border-color:rgba(147,51,234,0.3)}}
.stat-label {{font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;display:block}}
.stat-value {{font-size:1.1rem;font-weight:600;color:var(--text-light)}}
.tg-id {{margin-top:16px;text-align:right;font-size:0.75rem;color:rgba(148,163,184,0.5);font-family:monospace}}
.terminal-box {{background:#000;border-radius:12px;border:1px solid rgba(255,255,255,0.1);overflow:hidden;margin-bottom:16px}}
.terminal-header {{background:rgba(255,255,255,0.05);padding:8px 12px;display:flex;gap:6px;border-bottom:1px solid rgba(255,255,255,0.05)}}
.term-dot {{width:10px;height:10px;border-radius:50%}}
.dot-r {{background:#ff5f56}}.dot-y {{background:#ffbd2e}}.dot-g {{background:#27c93f}}
.terminal-body {{padding:16px;font-family:'Courier New',Courier,monospace;font-size:0.85rem;color:var(--accent);word-break:break-all;line-height:1.5;max-height:120px;overflow-y:auto}}
.warning-msg {{display:flex;align-items:center;gap:10px;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.2);color:var(--warning);padding:12px;border-radius:12px;font-size:0.85rem;margin-bottom:20px}}
.btn {{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;padding:16px;border-radius:16px;border:none;font-family:'Inter',sans-serif;font-weight:600;font-size:1rem;cursor:pointer;transition:all 0.3s cubic-bezier(0.4,0,0.2,1);text-decoration:none;outline:none}}
.btn-glow {{background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff;box-shadow:0 4px 20px rgba(147,51,234,0.4);position:relative;overflow:hidden}}
.btn-glow::after {{content:'';position:absolute;top:0;left:-100%;width:50%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent);transform:skewX(-20deg);transition:0.5s}}
.btn-glow:hover {{transform:translateY(-2px);box-shadow:0 6px 30px rgba(147,51,234,0.6)}}
.btn-glow:hover::after {{left:150%}}
.btn-glow.success {{background:linear-gradient(135deg,var(--success),#059669);box-shadow:0 4px 20px rgba(16,185,129,0.4)}}
.btn-telegram {{background:linear-gradient(135deg,#2AABEE,#229ED9);color:#fff;box-shadow:0 4px 20px rgba(42,171,238,0.3);border:1px solid rgba(255,255,255,0.1)}}
.btn-telegram:hover {{background:linear-gradient(135deg,#32b5f8,#26a5e4);transform:translateY(-2px);box-shadow:0 6px 25px rgba(42,171,238,0.5)}}
.steps {{display:flex;flex-direction:column;gap:16px;margin-bottom:24px}}
.step-item {{display:flex;align-items:center;gap:16px;background:rgba(0,0,0,0.2);padding:14px 16px;border-radius:14px;border:1px solid rgba(255,255,255,0.02)}}
.step-num {{width:32px;height:32px;border-radius:10px;background:rgba(147,51,234,0.2);color:var(--accent);display:flex;align-items:center;justify-content:center;font-family:'Orbitron',sans-serif;font-weight:700;font-size:0.9rem;border:1px solid rgba(147,51,234,0.4);box-shadow:0 0 10px rgba(147,51,234,0.2);flex-shrink:0}}
.step-text {{font-size:0.9rem;color:var(--text-light);line-height:1.5}}
.step-text strong {{color:#fff;font-weight:600}}
.step-text a {{color:var(--accent);text-decoration:none;font-weight:600;border-bottom:1px solid rgba(216,180,254,0.3);transition:all 0.2s}}
.step-text a:hover {{color:#fff;border-bottom-color:var(--primary);text-shadow:0 0 8px var(--primary)}}
.apps-grid {{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.app-card {{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:14px 6px;text-align:center;text-decoration:none;display:flex;flex-direction:column;align-items:center;transition:0.3s}}
.app-card:hover {{border-color:var(--primary);background:rgba(147,51,234,0.1);box-shadow:0 0 15px rgba(147,51,234,0.2);transform:translateY(-3px)}}
.app-icon {{width:46px;height:46px;border-radius:12px;margin-bottom:10px;box-shadow:0 4px 10px rgba(0,0,0,0.5);object-fit:cover;background:#222}}
.app-name {{font-size:0.85rem;font-weight:600;color:var(--text-light)}}
@keyframes fadeUp {{to {{opacity:1;transform:translateY(0)}}}}
@keyframes fadeInDown {{from {{opacity:0;transform:translateY(-20px)}} to {{opacity:1;transform:translateY(0)}}}}
::-webkit-scrollbar {{width:6px}}
::-webkit-scrollbar-track {{background:rgba(0,0,0,0.2);border-radius:4px}}
::-webkit-scrollbar-thumb {{background:var(--primary);border-radius:4px}}
.news-block {{margin-top:16px;background:rgba(147,51,234,0.08);border:1px solid rgba(147,51,234,0.25);border-radius:12px;padding:12px 14px}}
.news-label {{font-size:0.7rem;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;color:var(--accent);margin-bottom:6px}}
.news-text {{font-size:0.88rem;color:var(--text-light);line-height:1.55}}
.news-date {{font-size:0.7rem;color:var(--text-muted);margin-top:6px}}
</style>
</head>
<body>
<div class="ambient-bg">
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
</div>
<div class="app-container">
  <div class="header"><h1>{vpn_name}</h1></div>
  <div class="glass-card" style="animation-delay:0.1s">
    <div class="card-title">
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
      СТАТИСТИКА
      <span class="plan-badge">{plan_name}</span>
    </div>
    <div class="stats-grid">
      <div class="stat-box">
        <span class="stat-label">Трафик</span>
        <span class="stat-value">{tr_str}</span>
      </div>
      <div class="stat-box">
        <span class="stat-label">Осталось</span>
        <span class="stat-value">{days_left} дн.</span>
      </div>
      <div class="stat-box" style="grid-column:1/-1;display:flex;justify-content:space-between;align-items:center">
        <span class="stat-label" style="margin:0">Истекает:</span>
        <span class="stat-value" style="font-size:0.95rem">{expires.strftime('%d.%m.%Y')}</span>
      </div>
    </div>
    {bar}
    <div class="tg-id">ID: {tg_id_str}</div>
    {news_block}
  </div>

  <div class="glass-card" style="animation-delay:0.2s">
    <div class="card-title">
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>
      КЛЮЧ ПОДКЛЮЧЕНИЯ
    </div>
    <div class="terminal-box">
      <div class="terminal-header">
        <div class="term-dot dot-r"></div>
        <div class="term-dot dot-y"></div>
        <div class="term-dot dot-g"></div>
      </div>
      <div class="terminal-body" id="vpn-key">{full_url}</div>
    </div>
    <div class="warning-msg">⚠ Личный ключ — не передавай эту ссылку другим</div>
    <button id="copy-btn" class="btn btn-glow" onclick="copyKey()">
      <span>⎘  Скопировать ключ</span>
    </button>
  </div>

  <div class="glass-card" style="animation-delay:0.3s">
    <div class="card-title">
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M4 15V9a2 2 0 012-2h12a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2z"/></svg>
      КАК ПОДКЛЮЧИТЬСЯ
    </div>
    <div class="steps">
      <div class="step-item">
        <div class="step-num">1</div>
        <div class="step-text">Скачай <a href="https://example.com/happ" target="_blank">Happ</a>, <a href="https://example.com/v2raytun" target="_blank">v2rayTUN</a> или <a href="https://example.com/v2box" target="_blank">v2Box</a></div>
      </div>
      <div class="step-item">
        <div class="step-num">2</div>
        <div class="step-text">Нажми <strong>«Скопировать ключ»</strong> выше</div>
      </div>
      <div class="step-item">
        <div class="step-num">3</div>
        <div class="step-text">В приложении нажми <strong>+</strong> → <strong>«Импорт из буфера»</strong></div>
      </div>
      <div class="step-item">
        <div class="step-num">4</div>
        <div class="step-text">Нажми кнопку подключения ✓</div>
      </div>
    </div>
    <div class="apps-grid">
      <a class="app-card" href="https://play.google.com/store/apps/details?id=com.happproxy" target="_blank">
        <img class="app-icon" src="https://play-lh.googleusercontent.com/6_GZclv7PToXy9vOisL4XfM6vY-5N275-J8E_UqZ_1YV0XoN-R0-x8J5k1N-L0Y" alt="Happ">
        <span class="app-name">Happ</span>
      </a>
      <a class="app-card" href="https://play.google.com/store/apps/details?id=com.v2raytun.android" target="_blank">
        <img class="app-icon" src="https://play-lh.googleusercontent.com/8-zB9E_5f8W-UuV7-R0_r-N0-x8J5k1N-L0Y_5N275-J8E_UqZ_1YV0XoN-R0" alt="v2rayTUN">
        <span class="app-name">v2rayTUN</span>
      </a>
      <a class="app-card" href="https://play.google.com/store/apps/details?id=dev.hexasoftware.v2box" target="_blank">
        <img class="app-icon" src="https://play-lh.googleusercontent.com/9-A-B9E_5f8W-UuV7-R0_r-N0-x8J5k1N-L0Y_5N275-J8E_UqZ_1YV0XoN-R0" alt="v2Box">
        <span class="app-name">v2Box</span>
      </a>
    </div>
  </div>

  <div style="animation-delay:0.4s;opacity:0;animation:fadeUp 0.6s forwards cubic-bezier(0.2,0.8,0.2,1)">
    <a href="{bot_link}" class="btn btn-telegram">
      <span>Вернуться в Telegram</span>
    </a>
  </div>
</div>
<script>
function copyKey() {{
  const keyText = document.getElementById('vpn-key').innerText.trim();
  const btn = document.getElementById('copy-btn');
  const btnText = btn.querySelector('span');
  const showSuccess = () => {{
    btn.classList.add('success');
    btnText.innerText = '✓ Скопировано';
    setTimeout(() => {{
      btn.classList.remove('success');
      btnText.innerText = '⎘  Скопировать ключ';
    }}, 2200);
  }};
  if (navigator.clipboard && window.isSecureContext) {{
    navigator.clipboard.writeText(keyText).then(showSuccess);
  }} else {{
    const ta = document.createElement('textarea');
    ta.value = keyText;
    document.body.appendChild(ta);
    ta.select();
    try {{ document.execCommand('Copy'); showSuccess(); }} catch(e) {{}}
    ta.remove();
  }}
}}
</script>
</body>
</html>"""
