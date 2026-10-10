/* Search works from file:// too: catalog JSON is embedded at build time. */
(() => {
  const records = JSON.parse(document.getElementById('papers-data').textContent);
  const search = document.getElementById('search');
  const type = document.getElementById('content-type');
  const tag = document.getElementById('tag');
  const sort = document.getElementById('sort');
  const grid = document.getElementById('paper-grid');
  const cards = new Map([...grid.children].map(c => [c.dataset.id, c]));
  const buttons = [...document.querySelectorAll('[data-category]')];
  let category = '';
  [...new Set(records.flatMap(r => r.tags))].sort().forEach(t => {
    const o = document.createElement('option'); o.value = t; o.textContent = t; tag.append(o);
  });
  const fold = s => s.normalize('NFKC').toLocaleLowerCase();
  function update() {
    const words = fold(search.value).trim().split(/\s+/).filter(Boolean);
    const selected = records.filter(r => {
      const haystack = fold([r.title, r.summary, r.category, r.type, ...r.tags, ...r.sources.flatMap(s => [s.title, s.authors])].join(' '));
      return (!category || r.category === category) && (!type.value || r.type === type.value) && (!tag.value || r.tags.includes(tag.value)) && words.every(w => haystack.includes(w));
    }).sort((a,b) => sort.value === 'title' ? a.title.localeCompare(b.title, 'zh-CN') : b[sort.value].localeCompare(a[sort.value]) || a.id.localeCompare(b.id));
    cards.forEach(c => { c.hidden = true; });
    selected.forEach(r => { const c = cards.get(r.id); c.hidden = false; grid.append(c); });
    document.getElementById('result-count').textContent = `${selected.length} 篇解读 · ${sort.options[sort.selectedIndex].text}`;
    document.getElementById('empty-state').hidden = selected.length > 0;
    buttons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.category === category)));
  }
  buttons.forEach(b => b.addEventListener('click', () => { category = b.dataset.category; update(); }));
  search.addEventListener('input', update); [type, tag, sort].forEach(s => s.addEventListener('change', update));
  function reset() { search.value = ''; type.value = ''; tag.value = ''; sort.value = 'added'; category = ''; update(); }
  ['reset','empty-reset'].forEach(id => document.getElementById(id).addEventListener('click', reset));
  document.addEventListener('keydown', e => { if (e.key === '/' && !e.ctrlKey && !e.metaKey && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) { e.preventDefault(); search.focus(); } });
  update();
})();
