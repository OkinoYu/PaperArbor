(() => {
  const byId = id => document.getElementById(id);
  byId('print')?.addEventListener('click', () => window.print());
  const headings = [...document.querySelectorAll('main h2[id], main h3[id]')];
  const navLinks = [...document.querySelectorAll('.toc a, .mobile-toc nav a')];
  let owner = '';
  for (const heading of headings) {
    if (heading.tagName === 'H2') owner = heading.id;
    heading.dataset.section = owner;
  }
  for (const link of navLinks) {
    const heading = byId(decodeURIComponent(link.hash.slice(1)));
    if (heading) link.dataset.section = heading.dataset.section;
  }
  const update = () => {
    const distance = document.documentElement.scrollHeight - innerHeight;
    if (byId('progress')) byId('progress').style.width = `${distance > 0 ? Math.min(100, Math.max(0, scrollY / distance * 100)) : 0}%`;
    let current = headings[0];
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= 145) current = heading;
      else break;
    }
    for (const link of navLinks) {
      const active = link.hash === '#' + current?.id;
      link.classList.toggle('active', active);
      link.classList.toggle('section-active', link.dataset.section === current?.dataset.section);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
  };
  let scheduled = false;
  const schedule = () => {
    if (!scheduled) requestAnimationFrame(() => { scheduled = false; update(); });
    scheduled = true;
  };
  addEventListener('scroll', schedule, {passive:true}); addEventListener('resize', schedule); update();
  document.querySelectorAll('.mobile-toc a').forEach(link => link.addEventListener('click', () => {
    link.closest('details').open = false;
    const target = byId(decodeURIComponent(link.hash.slice(1)));
    if (target) { target.setAttribute('tabindex', '-1'); target.focus({preventScroll:true}); }
  }));
  for (const heading of document.querySelectorAll('main h2[id], main h3[id], main h4[id]')) {
    const link = document.createElement('a'); link.href = '#' + heading.id;
    link.className = 'permalink'; link.textContent = '§';
    link.setAttribute('aria-label', '定位：' + heading.textContent); heading.append(link);
  }
  document.querySelectorAll('.table-wrap, .viz-scroll, .equation').forEach((box, index) => {
    box.tabIndex = 0; box.setAttribute('role', 'region');
    const title = box.querySelector('title')?.textContent || box.querySelector('caption')?.textContent || box.querySelector('math')?.getAttribute('aria-label');
    box.setAttribute('aria-label', title || `可横向滚动的图表 ${index + 1}`);
    if (box.scrollWidth > box.clientWidth + 1) {
      const hint = document.createElement('p'); hint.className = 'scroll-hint'; hint.textContent = '↔ 横向滚动查看完整内容，也可聚焦后使用方向键';
      box.before(hint);
    }
  });
  document.querySelectorAll('.generation-switch').forEach(widget => {
    const buttons = [...widget.querySelectorAll('button[data-panel]')];
    const panels = [...widget.querySelectorAll('.generation-panel')];
    if (!buttons.length || buttons.some(button => !panels.some(panel => panel.id === button.dataset.panel))) return;
    const select = button => {
      buttons.forEach(item => { item.setAttribute('aria-pressed', String(item === button)); item.setAttribute('aria-controls', item.dataset.panel); });
      panels.forEach(panel => { panel.hidden = panel.id !== button.dataset.panel; });
    };
    buttons.forEach(button => button.addEventListener('click', () => select(button)));
    select(buttons[0]); widget.classList.add('enhanced');
  });

  // The article keeps its complete fitted image without JS. The viewer reuses
  // that embedded source, so enlargement works without a download or network.
  const figures = [...document.querySelectorAll('main figure img')];
  if (figures.length && typeof HTMLDialogElement !== 'undefined') {
    const viewer = document.createElement('dialog'); viewer.id = 'figure-dialog';
    viewer.setAttribute('aria-labelledby', 'figure-dialog-title');
    viewer.innerHTML = '<div class="dialog-head"><h2 id="figure-dialog-title">原图细节</h2><button type="button" class="figure-close" aria-label="关闭图像窗口">关闭 ×</button></div><div class="figure-controls"><button type="button" data-size="fit">完整显示</button><button type="button" data-size="actual">原始尺寸</button><span class="source" role="status" aria-live="polite"></span></div><div class="figure-viewport" tabindex="0" role="region" aria-label="放大的原图，可滚动查看"><img alt=""/></div><p class="figure-caption"></p>';
    document.body.append(viewer);
    const image = viewer.querySelector('img');
    const viewport = viewer.querySelector('.figure-viewport');
    const status = viewer.querySelector('[role="status"]');
    let original = null, imageOpener = null, mode = 'fit';
    const resizeImage = () => {
      if (!original?.naturalWidth) return;
      const available = Math.max(1, viewport.clientWidth - 16);
      const width = mode === 'actual' ? original.naturalWidth : Math.min(original.naturalWidth, available);
      image.style.width = `${width}px`;
      viewer.querySelectorAll('[data-size]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.size === mode)));
      status.textContent = `${Math.round(width / original.naturalWidth * 100)}% · ${mode === 'actual' ? '可横向、纵向滚动查看' : '完整图像'}`;
    };
    image.addEventListener('load', resizeImage);
    addEventListener('resize', () => { if (viewer.open) resizeImage(); });
    viewer.querySelector('.figure-close').addEventListener('click', () => viewer.close());
    viewer.addEventListener('close', () => imageOpener?.focus({preventScroll:true}));
    viewer.querySelectorAll('[data-size]').forEach(button => button.addEventListener('click', () => {
      mode = button.dataset.size; resizeImage(); viewport.scrollTo(0, 0);
    }));
    for (const sourceImage of figures) {
      if (!sourceImage.getAttribute('src')?.startsWith('data:image/')) continue;
      const actions = document.createElement('div'); actions.className = 'figure-actions';
      const button = document.createElement('button'); button.type = 'button'; button.textContent = '放大图像';
      button.setAttribute('aria-haspopup', 'dialog'); button.setAttribute('aria-controls', viewer.id);
      button.setAttribute('aria-label', '放大图像：' + sourceImage.alt);
      const hint = document.createElement('span'); hint.textContent = '完整显示 / 原始尺寸';
      actions.append(button, hint); sourceImage.after(actions);
      button.addEventListener('click', () => {
        if (typeof viewer.showModal !== 'function') return;
        original = sourceImage; imageOpener = button; mode = 'fit';
        image.src = sourceImage.getAttribute('src'); image.alt = sourceImage.alt;
        viewer.querySelector('.figure-caption').textContent = sourceImage.closest('figure').querySelector('figcaption')?.textContent || '';
        viewer.showModal(); resizeImage(); viewport.scrollTo(0, 0); viewport.focus();
      });
    }
  }

  const payload = byId('evidence-data');
  if (!payload) return;
  let data;
  try { data = JSON.parse(payload.textContent); } catch { return; }
  const sources = new Map(data.sources.map(source => [source.id, source]));
  const claims = data.ledger.claims;
  const kinds = {'paper-fact':'原文事实', 'explanatory-derivation':'说明式 / 推导', 'editorial-analysis':'分析判断', 'figure':'图形证据'};
  const dialog = document.createElement('dialog'); dialog.id = 'evidence-dialog'; dialog.setAttribute('aria-labelledby', 'evidence-dialog-title');
  // Static shell; all source and claim text below is assigned through textContent.
  dialog.innerHTML = '<div class="dialog-head"><h2 id="evidence-dialog-title">就地查证</h2><button type="button" class="dialog-close" aria-label="关闭证据窗口">关闭 ×</button></div><p class="source">保留原文定位；这些记录不能代替科学复核。</p><label for="evidence-search">搜索结论、来源或定位</label><input id="evidence-search" type="search" placeholder="例如：DeepStack、Table 12"><div class="evidence-filter"><p id="evidence-count" role="status" aria-live="polite"></p><button type="button" class="evidence-reset">全部证据</button></div><ol id="evidence-results" class="evidence-list"></ol>';
  document.body.append(dialog);
  let anchorFilter = '', sourceFilter = '', opener = null;
  const search = byId('evidence-search');
  const node = (tag, text, className) => {
    const element = document.createElement(tag); element.textContent = text;
    if (className) element.className = className;
    return element;
  };
  const refresh = () => {
    const query = search.value.trim().toLocaleLowerCase();
    const matches = claims.filter(claim => (!anchorFilter || claim.anchor === anchorFilter) && (!sourceFilter || claim.source === sourceFilter) &&
      (!query || [claim.statement, claim.locator, sources.get(claim.source)?.title, claim.source].join(' ').toLocaleLowerCase().includes(query)));
    byId('evidence-count').textContent = `${anchorFilter || sourceFilter ? '当前定位 · ' : '全部 · '}${matches.length} 条证据`;
    const list = byId('evidence-results'); list.replaceChildren();
    for (const claim of matches) {
      const source = sources.get(claim.source); if (!source) continue;
      const li = document.createElement('li');
      li.append(node('span', kinds[claim.kind] || '证据', 'label'), node('p', claim.statement), node('p', `${source.title} · ${source.version}\n${claim.locator}`, 'source'));
      const original = node('a', '打开原始来源 ↗'); original.href = source.url;
      const back = node('a', '返回对应正文 ↑'); back.href = '#' + claim.anchor; back.addEventListener('click', () => dialog.close());
      li.append(original, document.createTextNode(' · '), back); list.append(li);
    }
    if (!matches.length) list.append(node('li', '没有匹配的证据。可清空搜索，或切换到全部证据。', 'empty-evidence'));
  };
  const open = (anchor, source, trigger) => {
    if (typeof dialog.showModal !== 'function') { location.hash = 'evidence-heading'; byId('evidence-notes').open = true; return; }
    anchorFilter = anchor; sourceFilter = source; opener = trigger; search.value = ''; refresh();
    dialog.showModal(); search.focus();
  };
  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => opener?.focus({preventScroll:true}));
  search.addEventListener('input', refresh);
  dialog.querySelector('.evidence-reset').addEventListener('click', () => { anchorFilter = ''; sourceFilter = ''; search.value = ''; refresh(); search.focus(); });
  const plainClick = event => event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
  document.querySelectorAll('[data-evidence]').forEach(link => link.addEventListener('click', event => {
    if (!plainClick(event)) return; event.preventDefault(); open(link.dataset.evidence, '', link);
  }));
  for (const [anchor, count] of Object.entries(claims.reduce((result, claim) => { result[claim.anchor] = (result[claim.anchor] || 0) + 1; return result; }, {}))) {
    const target = byId(anchor); if (!target) continue;
    const button = node('button', `证据 ${count}`, 'evidence-trigger'); button.type = 'button';
    button.setAttribute('aria-haspopup', 'dialog'); button.setAttribute('aria-label', `查看 ${anchor} 对应的 ${count} 条证据`);
    button.addEventListener('click', () => open(anchor, '', button));
    // Evidence is an annotation, never a child of an authored grid, switch,
    // table or SVG. Adding a grid item would displace the scientific content.
    if (/^H[234]$/.test(target.tagName)) target.append(button);
    else if (target.tagName === 'FIGURE' && target.querySelector('figcaption')) target.querySelector('figcaption').append(button);
    else {
      const note = node('p', '', 'evidence-note');
      const content = target.closest('svg, math, table') || target;
      const layout = content.closest('.term-grid, .generation-switch, .table-wrap, .viz-scroll');
      note.append(button); (layout || content).after(note);
    }
  }
  document.querySelectorAll('a[data-source]').forEach(link => {
    link.setAttribute('aria-haspopup', 'dialog'); link.title = '就地查看证据；按住 Ctrl / Command 保留原链接';
    link.addEventListener('click', event => {
      if (!plainClick(event)) return;
      const source = link.dataset.source;
      // Prefer the nearest authored heading/claim container, then the chapter.
      let anchor = '', node = link;
      while (node && node !== byId('article')) {
        const ident = node.id || (/^SECTION$/.test(node.tagName) ? node.querySelector('h2[id]')?.id : '');
        if (ident && claims.some(claim => claim.source === source && claim.anchor === ident)) { anchor = ident; break; }
        let previous = node.previousElementSibling;
        while (previous) {
          if (/^H[234]$/.test(previous.tagName)) {
            if (claims.some(claim => claim.source === source && claim.anchor === previous.id)) anchor = previous.id;
            break;
          }
          previous = previous.previousElementSibling;
        }
        if (anchor) break;
        node = node.parentElement;
      }
      const hasLocal = claims.some(claim => claim.source === source && claim.anchor === anchor);
      event.preventDefault(); open(hasLocal ? anchor : '', source, link);
    });
  });
  let printOpen = [];
  addEventListener('beforeprint', () => {
    printOpen = [...document.querySelectorAll('details')].map(item => [item, item.open]);
    printOpen.forEach(([item]) => { item.open = true; });
  });
  addEventListener('afterprint', () => printOpen.forEach(([item, wasOpen]) => { item.open = wasOpen; }));
})();
