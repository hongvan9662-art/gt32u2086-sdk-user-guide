/* GT32U2086 docs — page behaviour
   1. "Copy" button on every code block
   2. Breadcrumb bar above the page title (GT32U2086 SDK › User Guide › Part n › Chapter n)
   3. Contents cards (home page: one card per PART; PART pages: one card per chapter)
      - more than 5 text lines: the list is cut at 5 lines and a chevron button shows the rest
      - "Read All" opens the PART / chapter page */
(function () {
  var CHEVRON = '<svg width="14" height="14" viewBox="0 0 12 12" aria-hidden="true">' +
    '<path d="M4 2l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var MAX_LINES = 5;

  /* current page file name; works with ".../ch01.html" and with hosts that drop ".html" (".../ch01") */
  function pageName() {
    var p = decodeURIComponent(location.pathname.split('/').pop() || '');
    if (!p) return 'index.html';
    if (!/\.html?$/i.test(p)) p += '.html';
    return p.replace(/\.htm$/i, '.html');
  }

  // ---------------------------------------------------------------- 1. copy buttons
  function copyButtons() {
    document.querySelectorAll('div.fragment').forEach(function (frag) {
      var btn = document.createElement('button');
      btn.className = 'gt32u2086-copy';
      btn.type = 'button';
      btn.textContent = 'Copy';
      btn.addEventListener('click', function () {
        var text = Array.prototype.map.call(frag.querySelectorAll('div.line'), function (l) {
          return l.textContent;
        }).join('\n');
        try {
          navigator.clipboard.writeText(text).then(function () {
            btn.textContent = 'Copied';
            setTimeout(function () { btn.textContent = 'Copy'; }, 1500);
          }, function () {});
        } catch (e) {}
      });
      frag.appendChild(btn);
    });
  }

  // ---------------------------------------------------------------- 2. breadcrumb
  function breadcrumb() {
    var header = document.querySelector('div.header');
    var data = (window.GT32U2086_CRUMBS || {})[pageName()];
    if (!header || !data) return;
    var trail = [['GT32U2086 SDK', 'index.html'], ['User Guide', 'index.html']].concat(data);
    var nav = document.createElement('nav');
    nav.className = 'gt32u2086-crumbs';
    nav.setAttribute('aria-label', 'Breadcrumb');
    var ol = document.createElement('ol');
    trail.forEach(function (c, i) {
      var li = document.createElement('li');
      var last = i === trail.length - 1;
      var el = document.createElement(last ? 'span' : 'a');
      if (!last) el.href = c[1]; else el.setAttribute('aria-current', 'page');
      el.className = last ? 'gt32u2086-crumb-current' : 'gt32u2086-crumb-link';
      el.textContent = c[0];
      li.appendChild(el);
      if (!last) {
        var sep = document.createElement('span');
        sep.className = 'gt32u2086-crumb-sep';
        sep.innerHTML = CHEVRON;
        li.appendChild(sep);
      }
      ol.appendChild(li);
    });
    nav.appendChild(ol);
    header.insertBefore(nav, header.firstChild);
  }

  // ---------------------------------------------------------------- 3. contents cards
  function splitTitle(t) {
    var i = t.indexOf(':');
    return i < 0 ? [t, ''] : [t.slice(0, i + 1), t.slice(i + 1).trim()];
  }

  function buildCards() {
    document.querySelectorAll('.gt32u2086-cards > ul').forEach(function (ul) {
      var grid = document.createElement('div');
      grid.className = 'gt32u2086-card-grid';
      Array.prototype.forEach.call(ul.children, function (li) {
        var link = li.querySelector(':scope > a');
        if (!link) return;
        var parts = splitTitle(link.textContent.trim());
        var card = document.createElement('section');
        card.className = 'gt32u2086-card';
        var inner = document.createElement('div');
        inner.className = 'gt32u2086-card-inner';
        var h = document.createElement('h3');
        h.className = 'gt32u2086-card-title';
        h.innerHTML = '<span class="gt32u2086-card-kicker"></span><span class="gt32u2086-card-name"></span>';
        h.firstChild.textContent = parts[0];
        h.lastChild.textContent = parts[1];
        inner.appendChild(h);
        var items = document.createElement('div');
        items.className = 'gt32u2086-card-items';
        li.querySelectorAll(':scope > ul > li > a').forEach(function (a) {
          var item = document.createElement('a');
          item.className = 'gt32u2086-card-item';
          item.href = a.getAttribute('href');
          item.textContent = a.textContent.trim();
          items.appendChild(item);
        });
        inner.appendChild(items);
        card.appendChild(inner);

        var foot = document.createElement('div');
        foot.className = 'gt32u2086-card-foot';
        var more = document.createElement('button');
        more.type = 'button';
        more.className = 'gt32u2086-card-more';
        more.setAttribute('aria-expanded', 'false');
        more.setAttribute('aria-label', 'Show all items');
        more.innerHTML = CHEVRON;
        more.hidden = true;
        more.addEventListener('click', function () {
          var open = card.classList.toggle('open');
          more.setAttribute('aria-expanded', open ? 'true' : 'false');
          more.setAttribute('aria-label', open ? 'Show fewer items' : 'Show all items');
          clip(card);
        });
        var read = document.createElement('a');
        read.className = 'gt32u2086-read-all';
        read.href = link.getAttribute('href');
        read.textContent = 'Read All';
        foot.appendChild(more);
        foot.appendChild(read);
        card.appendChild(foot);
        grid.appendChild(card);
      });
      ul.parentNode.insertBefore(grid, ul);
      ul.hidden = true;
    });
    clipAll();
    window.addEventListener('resize', clipAll);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(clipAll);
  }

  /* cut the list after MAX_LINES lines of text (a two-line item counts as two lines) */
  function clip(card) {
    var box = card.querySelector('.gt32u2086-card-items');
    var btn = card.querySelector('.gt32u2086-card-more');
    var items = box.children;
    box.style.maxHeight = 'none';
    if (!items.length) { btn.hidden = true; card.classList.remove('has-more'); return; }
    var lh = parseFloat(getComputedStyle(items[0]).lineHeight) || 18;
    var top0 = box.getBoundingClientRect().top;
    var used = 0, cut = null, total = 0;
    for (var i = 0; i < items.length; i++) {
      var r = items[i].getBoundingClientRect();
      var n = Math.max(1, Math.round(r.height / lh));
      total += n;
      if (cut === null && used + n > MAX_LINES) {
        cut = (r.top - top0) + (MAX_LINES - used) * lh;
      }
      used += n;
    }
    var hasMore = total > MAX_LINES;
    btn.hidden = !hasMore;
    card.classList.toggle('has-more', hasMore);
    if (hasMore && !card.classList.contains('open')) box.style.maxHeight = Math.round(cut) + 'px';
  }

  function clipAll() {
    document.querySelectorAll('.gt32u2086-card').forEach(clip);
  }

  // ---------------------------------------------------------------- 4. header lockup
  /* top of "GT32U2086 SDK" capitals on the top of the logo, baseline of "Document" on the bottom of the logo
     (measured in the browser, so it stays right on any screen size and whatever font metrics the viewer gets) */
  var CAP_HEIGHT = 0.727;   // Inter capital height, in em
  function baselineOf(el) {
    var probe = document.createElement('span');
    probe.style.cssText = 'display:inline-block;width:0;height:0;';
    el.appendChild(probe);
    var y = probe.getBoundingClientRect().top;
    el.removeChild(probe);
    return y;
  }
  function alignBrief() {
    var name = document.getElementById('projectname');
    var brief = document.getElementById('projectbrief');
    if (!name || !brief) return;
    name.style.transform = '';
    brief.style.transform = '';
    var logo = Array.prototype.filter.call(document.querySelectorAll('#projectlogo img'), function (im) {
      return im.getBoundingClientRect().height > 0;
    })[0];
    if (!logo || brief.getBoundingClientRect().height === 0) return;
    var lr = logo.getBoundingClientRect();
    var capTop = baselineOf(name) - CAP_HEIGHT * parseFloat(getComputedStyle(name).fontSize);
    var dn = lr.top - capTop;
    var db = lr.bottom - baselineOf(brief);
    if (Math.abs(dn) < 10) name.style.transform = 'translateY(' + dn.toFixed(2) + 'px)';
    if (Math.abs(db) < 10) brief.style.transform = 'translateY(' + db.toFixed(2) + 'px)';
  }

  // ---------------------------------------------------------------- 5. search on phones
  /* on small screens the search field is replaced by a magnifier button; tapping it opens the field */
  var MAGNIFIER = '<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.75" fill="none" ' +
    'stroke="currentColor" stroke-width="1.8"/><path d="M13 13l4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
  var CLOSE = '<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" stroke="currentColor" ' +
    'stroke-width="1.8" stroke-linecap="round"/></svg>';
  function mobileSearch() {
    var box = document.getElementById('MSearchBox');
    var field = document.getElementById('MSearchField');
    if (!box || !field) return;
    var root = document.documentElement;
    var open = document.createElement('button');
    open.type = 'button';
    open.className = 'gt32u2086-search-btn';
    open.setAttribute('aria-label', 'Search');
    open.innerHTML = MAGNIFIER;
    var cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'gt32u2086-search-cancel';
    cancel.setAttribute('aria-label', 'Close search');
    cancel.innerHTML = CLOSE;
    box.parentNode.insertBefore(open, box);
    box.parentNode.insertBefore(cancel, box.nextSibling);
    function close() {
      root.classList.remove('gt32u2086-search-open');
      try { if (window.searchBox) window.searchBox.CloseResultsWindow(); } catch (e) {}
      field.blur();
    }
    open.addEventListener('click', function () {
      root.classList.add('gt32u2086-search-open');
      setTimeout(function () { field.focus(); }, 0);
    });
    cancel.addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && root.classList.contains('gt32u2086-search-open')) close();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    mobileSearch();
    alignBrief();
    window.addEventListener('load', alignBrief);
    window.addEventListener('resize', alignBrief);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(alignBrief);
    copyButtons();
    breadcrumb();
    buildCards();
  });
})();
