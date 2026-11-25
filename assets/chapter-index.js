// Enhancement only: the index and its fragment links work without JavaScript.
(() => {
  const index = document.querySelector('.chapter-toc');
  const track = index.querySelector('.chapter-toc-track');
  const prose = document.querySelector('.prose');
  const entry = track.querySelector('[aria-current="page"]');
  const chapter = {link: entry, label: entry.querySelector('.chapter-toc-label')};
  const sections = [...track.querySelectorAll('a[href^="#"]')].map(link => ({
    link, label: link.querySelector('.chapter-toc-label'),
    heading: document.getElementById(decodeURIComponent(link.hash.slice(1))),
  })).filter(({heading}) => heading);

  const mobile = matchMedia('(width < 920px)');
  const toggle = document.createElement('button');
  toggle.className = 'chapter-toc-toggle';
  toggle.type = 'button';
  toggle.textContent = chapter.label.textContent;
  const panel = document.createElement('div');
  panel.className = 'chapter-toc-panel';
  panel.id = 'chapter-toc-panel';
  toggle.setAttribute('aria-controls', panel.id);
  track.before(toggle, panel);
  panel.append(track);

  function setOpen(open, returnFocus = false) {
    toggle.setAttribute('aria-expanded', String(open));
    if (open) {
      if (frame) cancelAnimationFrame(frame);
      update();
      const row = (current || chapter).link.getBoundingClientRect();
      panel.scrollTop += row.top - panel.getBoundingClientRect().top - 12;
    } else if (returnFocus) {
      toggle.focus({preventScroll: true});
    }
    schedule();
  }

  const isOpen = () => mobile.matches && toggle.getAttribute('aria-expanded') === 'true';
  toggle.addEventListener('click', () => setOpen(!isOpen()));
  index.addEventListener('keydown', event => {
    if (event.key === 'Escape' && isOpen()) {
      event.preventDefault();
      setOpen(false, true);
    }
  });
  document.addEventListener('click', event => {
    if (isOpen() && !index.contains(event.target)) setOpen(false);
  });
  index.addEventListener('focusout', event => {
    if (isOpen() && event.relatedTarget && !index.contains(event.relatedTarget)) setOpen(false);
  });
  track.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!isOpen() || !link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const section = sections.find(({link: source}) => source === link);
    setOpen(false);
    if (section) {
      section.heading.tabIndex = -1;
      section.heading.focus({preventScroll: true});
    }
  });
  mobile.addEventListener('change', () => setOpen(false));

  const dot = document.createElement('span');
  dot.className = 'chapter-toc-dot';
  dot.setAttribute('aria-hidden', 'true');
  track.append(dot);
  const motion = matchMedia('(prefers-reduced-motion: no-preference)');
  let current, frame, markerX, markerY;
  function openContentsLink() {
    if (mobile.matches && location.hash === '#contents') setOpen(true);
  }
  setOpen(false);
  window.addEventListener('hashchange', openContentsLink);
  openContentsLink();

  function update() {
    frame = 0;
    let readingLine = Math.min(window.innerHeight * .22, 160);
    if (mobile.matches && sections.length) {
      const padding = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
      const margin = parseFloat(getComputedStyle(sections[0].heading).scrollMarginTop) || 0;
      readingLine = Math.max(readingLine, padding + margin + 1);
    }
    let active = chapter;
    // A short last section can be readable before its heading reaches the line.
    if (sections.length && prose.getBoundingClientRect().bottom <= window.innerHeight) {
      active = sections.at(-1);
    } else {
      for (const section of sections) {
        if (section.heading.getBoundingClientRect().top > readingLine) break;
        active = section;
      }
    }
    const changed = current !== active;
    if (changed) {
      if (current?.heading) current.link.removeAttribute('aria-current');
      if (active.heading) active.link.setAttribute('aria-current', 'location');
      current = active;
    }
    if (!track.getClientRects().length) return;

    const line = active.label.getClientRects()[0];
    if (!line) return;
    const trackBounds = track.getBoundingClientRect();
    const x = line.left - trackBounds.left;
    const y = line.top + line.height / 2 - trackBounds.top;
    if (markerX !== x || markerY !== y) {
      const glide = changed && markerY !== undefined && motion.matches;
      dot.toggleAttribute('data-glide', glide);
      dot.style.setProperty('--marker-x', `${x}px`);
      dot.style.setProperty('--marker-y', `${y}px`);
      dot.setAttribute('data-placed', '');
      markerX = x;
      markerY = y;
    }

    if (!mobile.matches && changed && index.clientHeight < index.scrollHeight) {
      const row = active.link.getBoundingClientRect();
      const bounds = index.getBoundingClientRect();
      if (row.top < bounds.top) index.scrollTop += row.top - bounds.top;
      if (row.bottom > bounds.bottom) index.scrollTop += row.bottom - bounds.bottom;
    }
  }

  function schedule() {
    if (!frame) frame = requestAnimationFrame(update);
  }
  for (const event of ['scroll', 'resize', 'hashchange', 'pageshow']) {
    window.addEventListener(event, schedule, {passive: true});
  }

  document.fonts.ready.then(schedule);
  schedule();
})();
