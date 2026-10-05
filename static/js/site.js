(function(){
  var nav = document.getElementById('rta-nav');
  var btn = document.getElementById('rta-burger');
  var triggers = nav ? nav.querySelectorAll('.rta-nav-trigger') : [];

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
    btn.addEventListener('click', function(){
      var open = nav.classList.toggle('rta-nav--open');
      btn.setAttribute('aria-expanded', open);
      if (!open) closeSubmenus();
    });
    document.addEventListener('click', function(e){
      if (!nav.contains(e.target)) {
        nav.classList.remove('rta-nav--open');
        btn.setAttribute('aria-expanded', 'false');
        closeSubmenus();
      }
    });
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape') {
        var wasOpen = nav.classList.contains('rta-nav--open');
        nav.classList.remove('rta-nav--open');
        btn.setAttribute('aria-expanded', 'false');
        closeSubmenus();
        if (wasOpen) btn.focus();
      }
    });
  }

  /* Keep long article contents within a disclosure on smaller screens.
     With JavaScript disabled the accessible native details remain open. */
  var readingContents = document.querySelector('.rta-reading-nav details');
  var compactLayout = window.matchMedia('(max-width: 980px)');
  if (readingContents) readingContents.open = !compactLayout.matches;
  compactLayout.addEventListener('change', function(event){
    if (readingContents) readingContents.open = !event.matches;
    if (nav) nav.classList.remove('rta-nav--open');
    if (btn) btn.setAttribute('aria-expanded', 'false');
    closeSubmenus();
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
