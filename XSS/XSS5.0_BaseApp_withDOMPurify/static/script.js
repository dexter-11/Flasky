// static/script.js — merged loader + submitter with DOMPurify toggle
(() => {
  // helper: sanitize if DomPurify available & toggle is on
  function maybeSanitize(html) {
    try {
      if (window.__useDomPurify && window.DOMPurify && typeof DOMPurify.sanitize === 'function') {
        // Use DOMPurify with default safe profile (can tune config)
        return DOMPurify.sanitize(html, {USE_PROFILES: {html: true}});
      }
    } catch (e) {
      console.warn('DOMPurify error', e);
    }
    // fallback: return original (vulnerable)
    return html;
  }

  // helper: load & render comments (vulnerable unless sanitized)
  async function loadComments(path) {
    try {
      const r = await fetch(path, { credentials: 'same-origin' });
      const comments = await r.json();
      const container = document.getElementById('user-comments');
      container.innerHTML = '<h4>Comments</h4>';
      comments.forEach(c => {
        const sec = document.createElement('section');
        sec.className = 'comment';
        const meta = document.createElement('div');
        if (c.author) meta.innerHTML = (meta.innerHTML || '') + maybeSanitize(c.author);
        if (c.date) {
          const d = new Date(c.date);
          const ds = [String(d.getDate()).padStart(2,'0'),
                      String(d.getMonth()+1).padStart(2,'0'),
                      d.getFullYear()].join('-');
          meta.innerHTML += ' | ' + ds;
        }
        sec.appendChild(meta);
        if (c.body) {
          const p = document.createElement('div');
          // previously vulnerable sink: p.innerHTML = c.body;
          // now sanitize conditionally
          p.innerHTML = maybeSanitize(c.body);
          sec.appendChild(p);
        }
        sec.appendChild(document.createElement('div'));
        container.appendChild(sec);
      });
    } catch (e) { /* ignore */ }
  }

  // submit form via fetch, then reload comments (preserve redirect behavior)
  async function submitComment(form) {
    try {
      const body = new URLSearchParams(new FormData(form)).toString();
      const res = await fetch(form.action, {
        method: form.method || 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body
      });
      if (res.redirected) { window.location = res.url; return; }
      // non-redirect: refresh comments and clear form
      form.reset();
      const postId = form.postId ? form.postId.value : 'demo';
      await loadComments('/comments?post_id=' + encodeURIComponent(postId));
    } catch (err) {
      alert('Failed to post comment');
    }
  }

  // wire on DOM ready
  document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('commentForm');
    const postId = (typeof POST_ID !== 'undefined') ? POST_ID : (form ? form.postId.value : 'demo');

    // initial load
    loadComments('/comments?post_id=' + encodeURIComponent(postId));

    // intercept submit
    if (form) form.addEventListener('submit', e => {
      e.preventDefault();
      submitComment(e.target);
    });
  });
})();
