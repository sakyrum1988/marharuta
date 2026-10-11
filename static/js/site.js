(function(){
  var nav = document.getElementById('rta-nav');
  var btn = document.getElementById('rta-burger');
  var triggers = nav ? nav.querySelectorAll('.rta-nav-trigger') : [];
  var compactLayout = window.matchMedia('(max-width: 980px)');

  function setMenuState(open) {
    if (!nav || !btn) return;
    nav.classList.toggle('rta-nav--open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.setAttribute('aria-label', open ? btn.dataset.closeLabel : btn.dataset.openLabel);
    document.documentElement.classList.toggle('rta-nav-lock', open && compactLayout.matches);
    if (!open) closeSubmenus();
  }

  function closeSubmenus(except) {
    triggers.forEach(function(trigger){
      var item = trigger.closest('.rta-nav-item');
      if (item !== except) {
        item.classList.remove('rta-nav-item--open');
        trigger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  triggers.forEach(function(trigger){
    trigger.addEventListener('click', function(e){
      if (!window.matchMedia('(max-width: 980px)').matches) return;
      e.preventDefault();
      var item = trigger.closest('.rta-nav-item');
      var opening = !item.classList.contains('rta-nav-item--open');
      closeSubmenus(item);
      item.classList.toggle('rta-nav-item--open', opening);
      trigger.setAttribute('aria-expanded', opening ? 'true' : 'false');
    });
  });

  if (btn) {
    btn.addEventListener('click', function(event){
      var open = !nav.classList.contains('rta-nav--open');
      setMenuState(open);
      if (open && event.detail === 0) {
        requestAnimationFrame(function(){
          var firstLink = nav.querySelector('.rta-nav-links a');
          if (firstLink) firstLink.focus();
        });
      }
    });
    document.addEventListener('click', function(e){
      if (!nav.contains(e.target)) {
        setMenuState(false);
      }
    });
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape') {
        var wasOpen = nav.classList.contains('rta-nav--open');
        setMenuState(false);
        if (wasOpen) btn.focus();
      }
    });
  }

  /* Long FAQ answers are progressive disclosure: questions stay scannable,
     while the original answer nodes and their links remain in the document. */
  document.querySelectorAll('.rta-reading-body .faq-item').forEach(function(item){
    var heading = item.querySelector('h3');
    if (!heading) return;

    var disclosure = document.createElement('details');
    disclosure.className = 'rta-faq-disclosure';
    var summary = document.createElement('summary');
    summary.textContent = heading.textContent.trim();
    var answer = document.createElement('div');
    answer.className = 'rta-faq-answer';

    Array.from(item.childNodes).forEach(function(node){
      if (node !== heading) answer.appendChild(node);
    });
    disclosure.appendChild(summary);
    disclosure.appendChild(answer);
    item.replaceWith(disclosure);
  });

  compactLayout.addEventListener('change', function(event){
    setMenuState(false);
  });

  /* Reading progress bar */
  var bar = document.getElementById('rta-progress');
  if (bar) {
    function updateProgress() {
      var scrollTop = window.scrollY || document.documentElement.scrollTop;
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var pct = docHeight > 0 ? Math.min(100, (scrollTop / docHeight) * 100) : 0;
      bar.style.width = pct + '%';
    }
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
  }
})();
