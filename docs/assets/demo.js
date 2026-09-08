(function () {
  var links = [].slice.call(document.querySelectorAll('.toc a[href^="#"]'));
  var secs = links.map(function (a) {
    return document.querySelector(a.getAttribute('href'));
  });
  function upd() {
    var y = window.scrollY + 120, idx = 0;
    secs.forEach(function (s, i) { if (s && s.offsetTop <= y) idx = i; });
    links.forEach(function (a, i) { a.classList.toggle('on', i === idx); });
  }
  window.addEventListener('scroll', upd, { passive: true });
  upd();
  var toc = document.getElementById('toc'), tb = document.getElementById('toc-btn');
  function narrow() { return window.matchMedia('(max-width:1400px)').matches; }
  function sync() { if (narrow()) toc.hidden = true; else toc.hidden = false; }
  sync();
  window.addEventListener('resize', sync);
  if (tb) tb.addEventListener('click', function () { toc.hidden = !toc.hidden; });
  document.querySelectorAll('.toc a').forEach(function (a) {
    a.addEventListener('click', function () { if (narrow()) toc.hidden = true; });
  });
})();
