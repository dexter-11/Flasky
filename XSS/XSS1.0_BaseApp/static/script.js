// compact vulnerable comment loader + renderer
function loadComments(path){
  fetch(path).then(r=>r.json()).then(comments=>{
    const container = document.getElementById('user-comments');
    comments.forEach(c=>{
      const sec = document.createElement('section');
      sec.className = 'comment';
      const meta = document.createElement('p');
      if(c.author) meta.innerHTML = (meta.innerHTML || '') + c.author;
      if(c.date){
        const d = new Date(c.date);
        const ds = [String(d.getDate()).padStart(2,'0'), String(d.getMonth()+1).padStart(2,'0'), d.getFullYear()].join('-');
        meta.innerHTML += ' | ' + ds;
      }
      sec.appendChild(meta);
      if(c.body){
        const p = document.createElement('p');
        // VULNERABLE: direct innerHTML from server-stored body
        p.innerHTML = c.body;
        sec.appendChild(p);
      }
      sec.appendChild(document.createElement('p'));
      container.appendChild(sec);
    });
  }).catch(()=>{});
}
