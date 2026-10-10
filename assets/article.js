(() => {
  document.getElementById('print').addEventListener('click', () => window.print());
  const progress = document.getElementById('progress');
  const update = () => { const distance = document.documentElement.scrollHeight - innerHeight; progress.style.width = `${distance > 0 ? Math.min(100, scrollY / distance * 100) : 0}%`; };
  addEventListener('scroll', update, {passive:true}); addEventListener('resize', update); update();
  if ('IntersectionObserver' in window) {
    const links = [...document.querySelectorAll('.toc a')];
    const observer = new IntersectionObserver(entries => { const visible=entries.filter(e=>e.isIntersecting); if (visible.length) { const id=visible[0].target.id; links.forEach(a=>{const active=a.hash==='#'+id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');}); } },{rootMargin:'-80px 0px -65% 0px'});
    document.querySelectorAll('h2[id]').forEach(h=>observer.observe(h));
  }
})();
