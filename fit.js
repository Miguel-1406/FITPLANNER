const API = 'http://localhost:5000';
let treinosData = [];
let metasData = [];
let agendaData = [];
let googleConnected = false;
let selectedTreinoId = null;
let selectedMetaId = null;

// NAVIGATION
function goPage(p){
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.nav-links a').forEach(x=>x.classList.remove('active'));
  document.getElementById('page-'+p).classList.add('active');
  const link = document.querySelector(`.nav-links a[data-page="${p}"]`);
  if(link) link.classList.add('active');
  if(p==='home') loadHome();
  if(p==='status') loadStatus();
  if(p==='planos') loadPlanos();
  if(p==='treinos') loadTreinos();
  if(p==='calendario') loadCalendario();
}

//  TOAST 
function toast(msg, dur=2800){
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'), dur);
}

//  MODAL 
function openModal(id){
  document.getElementById(id).classList.add('open');
  if(id==='modal-agendar') preencherSelectTreinos();
}
function closeModal(id){document.getElementById(id).classList.remove('open')}
document.querySelectorAll('.modal-overlay').forEach(el=>{
  el.addEventListener('click',e=>{if(e.target===el) el.classList.remove('open')});
});

//  API HELPERS 
async function apiFetch(path, opts={}){
  try{
    const r=await fetch(API+path,{headers:{'Content-Type':'application/json'},...opts});
    return await r.json();
  }catch(e){
    console.error(e);
    return null;
  }
}

//  HOME 
function buildCalendar(){
  const strip=document.getElementById('cal-strip');
  strip.innerHTML='';
  const days=['DOM','SEG','TER','QUA','QUI','SEX','SAB'];
  const today=new Date();
  for(let i=0;i<7;i++){
    const d=new Date(today); d.setDate(today.getDate()+i);
    const isToday=i===0;
    const div=document.createElement('div');
    div.className='cal-day'+(isToday?' today':'');
    div.innerHTML=`<div class="day-name">${days[d.getDay()]}</div><div class="day-num">${String(d.getDate()).padStart(2,'0')}</div>`;
    strip.appendChild(div);
  }
}

async function loadHome(){
  buildCalendar();
  const res=await apiFetch('/treinos');
  if(!res) return;
  treinosData = res.dados || res;
  const grid=document.getElementById('home-treinos');
  grid.innerHTML='';
  if(!treinosData.length){grid.innerHTML='<div class="empty" style="grid-column:1/-1">Nenhum treino cadastrado.</div>';return;}
  treinosData.slice(0,3).forEach(t=>{
    const card=document.createElement('div');
    card.className='treino-card-home';
    card.innerHTML=`
      <div>
        <div class="t-name">${t.nome}</div>
        <div class="t-tipo">${t.tipo||'—'}, ${t.objetivo||'—'}</div>
      </div>
      <div class="t-footer">
        <span class="t-dur">45 min</span>
        <button class="btn-yellow" onclick="iniciarTreino(${t.id})">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg> Start
        </button>
      </div>`;
    grid.appendChild(card);
  });
}

function iniciarTreino(id){
  toast('🏋️ Treino iniciado!');
}

//  STATUS 
async function loadStatus(){
  const res=await apiFetch('/metas');
  if(!res) return;
  metasData = res.dados || res;

  const pg=document.getElementById('status-progress');
  pg.innerHTML='';
  if(!metasData.length){pg.innerHTML='<div class="empty" style="grid-column:1/-1">Nenhuma meta cadastrada.</div>';}
  else{
    metasData.forEach(m=>{
      const pct=Math.min(100, m.tipo_meta==='perder'
        ? ((m.valor_inicial-m.valor_atual)/(m.valor_inicial-m.valor_meta)*100)||0
        : ((m.valor_atual/m.valor_meta)*100)||0);
      const card=document.createElement('div');
      card.className='progress-card';
      card.innerHTML=`
        <div class="p-title">${m.titulo}</div>
        <div class="p-label">Progresso</div>
        <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:${pct.toFixed(0)}%"></div></div>`;
      pg.appendChild(card);
    });
  }

  const mg=document.getElementById('status-metas');
  mg.innerHTML='';
  if(!metasData.length){mg.innerHTML='<div class="empty" style="grid-column:1/-1">Nenhuma meta cadastrada.</div>';}
  else{
    metasData.forEach(m=>{
      const card=document.createElement('div');
      card.className='meta-card';
      card.innerHTML=`
        <div class="m-info">
          <div class="m-title">${m.titulo}</div>
          <div style="font-size:12px;color:var(--text3);margin:4px 0">${m.valor_atual} / ${m.valor_meta} ${m.unidade||''}</div>
          <span class="m-action" onclick="openProgress(${m.id},'${m.titulo}')">Atualizar progresso</span>
          &nbsp;·&nbsp;
          <span class="m-action" style="color:#e55" onclick="deletarMeta(${m.id})">Excluir</span>
        </div>
        <div class="m-check ${m.concluida?'':'pending'}">
          ${m.concluida?'<svg viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>':''}
        </div>`;
      mg.appendChild(card);
    });
  }
}

function openProgress(id, titulo){
  selectedMetaId=id;
  document.getElementById('prog-meta-nome').textContent=titulo;
  document.getElementById('prog-valor').value='';
  openModal('modal-progresso');
}

async function atualizarProgresso(){
  const val=document.getElementById('prog-valor').value;
  if(!val){toast('Digite um valor');return;}
  const r=await apiFetch(`/metas/${selectedMetaId}`,{method:'PUT',body:JSON.stringify({valor_atual:parseFloat(val)})});
  if(r){toast('✅ Progresso atualizado!');closeModal('modal-progresso');loadStatus();}
}

async function deletarMeta(id){
  if(!confirm('Deletar esta meta?')) return;
  await apiFetch(`/metas/${id}`,{method:'DELETE'});
  toast('🗑️ Meta removida');loadStatus();
}

//  PLANOS 
async function loadPlanos(){
  const res=await apiFetch('/treinos');
  if(!res) return;
  treinosData = res.dados || res;

  const musc=treinosData.filter(t=>(t.tipo||'').toLowerCase().includes('musculação')||(t.tipo||'').toLowerCase().includes('musculacao'));
  const card=treinosData.filter(t=>(t.tipo||'').toLowerCase().includes('cardio'));
  const outros=treinosData.filter(t=>!musc.includes(t)&&!card.includes(t));
  const todos=[...musc,...outros];

  renderPlanoGrid('grid-musculacao', todos.length?todos:treinosData.slice(0,3));
  renderPlanoGrid('grid-cardio', card.length?card:treinosData.slice(0,3));
}

function renderPlanoGrid(gridId, items){
  const g=document.getElementById(gridId);
  g.innerHTML='';
  if(!items.length){g.innerHTML='<div class="empty" style="grid-column:1/-1">—</div>';return;}
  items.forEach(t=>{
    const card=document.createElement('div');
    card.className='plano-card';
    card.innerHTML=`
      <div class="pc-header">
        <span class="pc-name">${t.nome}</span>
        <button class="pc-dots" onclick="event.stopPropagation()">···</button>
      </div>
      <div class="pc-treinos">${t.objetivo||'Treino A, Treino B,\nTreino C'}</div>
      <div class="pc-footer">
        <span class="pc-dur">${t.tipo||'—'}</span>
        <button class="btn-yellow" onclick="verPlano(${t.id})">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/></svg>
          Ver plano
        </button>
      </div>`;
    g.appendChild(card);
  });
}

async function verPlano(id){
  selectedTreinoId=id;
  const t=treinosData.find(x=>x.id===id);
  document.getElementById('modal-ex-title').textContent=`EXERCÍCIOS — ${t?t.nome:''}`;
  await loadExercicios();
  openModal('modal-exercicio');
}

//  TREINOS 
async function loadTreinos(){
  const res=await apiFetch('/treinos');
  if(!res) return;
  treinosData = res.dados || res;
  const list=document.getElementById('treinos-list');
  list.innerHTML='';
  if(!treinosData.length){list.innerHTML='<div class="empty">Nenhum treino cadastrado.</div>';return;}
  treinosData.forEach(t=>{
    const card=document.createElement('div');
    card.className='card';
    card.style.marginBottom='12px';
    card.innerHTML=`
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div>
          <div style="font-size:14px;font-weight:700;letter-spacing:1px">${t.nome}</div>
          <div style="font-size:12px;color:var(--text3);margin-top:2px">${t.tipo||'—'} · ${t.objetivo||'—'}</div>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn-dark" onclick="abrirExercicios(${t.id},'${t.nome}')">Exercícios</button>
          <button class="btn-icon" onclick="deletarTreino(${t.id})" title="Deletar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
          </button>
        </div>
      </div>`;
    list.appendChild(card);
  });
}

async function abrirExercicios(id, nome){
  selectedTreinoId=id;
  document.getElementById('modal-ex-title').textContent=`EXERCÍCIOS — ${nome}`;
  await loadExercicios();
  openModal('modal-exercicio');
}

async function loadExercicios(){
  const data=await apiFetch(`/exercicios/treino/${selectedTreinoId}`);
  const list=document.getElementById('exercicios-modal-list');
  list.innerHTML='';
  if(!data||!data.length){list.innerHTML='<div class="empty" style="padding:16px 0">Nenhum exercício ainda.</div>';return;}
  data.forEach(ex=>{
    const item=document.createElement('div');
    item.className='exercicio-item';
    item.innerHTML=`
      <div class="ex-info">
        <div class="ex-name">${ex.nome_exercicio}</div>
        <div class="ex-detail">${ex.series||'—'} séries · ${ex.repeticoes||'—'} reps</div>
      </div>
      <button class="btn-icon" onclick="deletarExercicio(${ex.id})" title="Remover">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>`;
    list.appendChild(item);
  });
}

async function salvarExercicio(){
  const nome=document.getElementById('ex-nome').value.trim();
  const series=document.getElementById('ex-series').value.trim();
  const reps=document.getElementById('ex-reps').value.trim();
  if(!nome){toast('Digite o nome do exercício');return;}
  const r=await apiFetch('/exercicios',{method:'POST',body:JSON.stringify({id_treino:selectedTreinoId,nome_exercicio:nome,series,repeticoes:reps})});
  if(r&&r.mensagem&&!r.mensagem.includes('obrigatório')){
    toast('✅ Exercício adicionado!');
    document.getElementById('ex-nome').value='';
    document.getElementById('ex-series').value='';
    document.getElementById('ex-reps').value='';
    await loadExercicios();
  }else{toast(r?.mensagem||'Erro');}
}

async function deletarExercicio(id){
  await apiFetch(`/exercicios/${id}`,{method:'DELETE'});
  await loadExercicios();
  toast('Exercício removido');
}

async function salvarTreino(){
  const nome=document.getElementById('t-nome').value.trim();
  const tipo=document.getElementById('t-tipo').value.trim();
  const obj=document.getElementById('t-obj').value.trim();
  if(!nome){toast('Nome obrigatório');return;}
  const lbl=document.getElementById('btn-treino-label');
  lbl.innerHTML='<span class="spinner"></span>';
  const r=await apiFetch('/treinos',{method:'POST',body:JSON.stringify({nome,tipo,objetivo:obj})});
  lbl.textContent='Salvar';
  if(r){
    if(r.mensagem&&r.mensagem.includes('sucesso')){
      toast('✅ Treino criado!');
      closeModal('modal-treino');
      document.getElementById('t-nome').value='';
      document.getElementById('t-tipo').value='';
      document.getElementById('t-obj').value='';
      loadHome(); loadTreinos();
    }else{toast(r.mensagem||'Erro');}
  }
}

async function deletarTreino(id){
  if(!confirm('Deletar este treino e todos os exercícios?')) return;
  await apiFetch(`/treinos/${id}`,{method:'DELETE'});
  toast('🗑️ Treino removido');loadTreinos();loadHome();
}

//  METAS 
async function salvarMeta(){
  const titulo=document.getElementById('m-titulo').value.trim();
  const atual=document.getElementById('m-atual').value;
  const meta=document.getElementById('m-meta').value;
  const unidade=document.getElementById('m-unidade').value.trim();
  const tipo=document.getElementById('m-tipo').value;
  if(!titulo||!meta){toast('Título e valor meta obrigatórios');return;}
  const r=await apiFetch('/metas',{method:'POST',body:JSON.stringify({titulo,valor_atual:parseFloat(atual)||0,valor_meta:parseFloat(meta),unidade,tipo_meta:tipo})});
  if(r&&r.mensagem&&r.mensagem.includes('sucesso')){
    toast('✅ Meta criada!');closeModal('modal-meta');
    document.getElementById('m-titulo').value='';
    document.getElementById('m-atual').value='';
    document.getElementById('m-meta').value='';
    document.getElementById('m-unidade').value='';
    loadStatus();
  }else{toast(r?.mensagem||'Erro');}
}

//  CALENDARIO 
async function loadCalendario(){
  await checkGoogleStatus();
}

async function checkGoogleStatus(){
  try{
    const r = await fetch(API+'/agenda/treinos');
    const d = await r.json();
    if(Array.isArray(d)){
      setGoogleConnected(true);
      agendaData=d;
      renderAgenda();
    }else{
      setGoogleConnected(false);
    }
  }catch(e){
    setGoogleConnected(false);
  }
}

function setGoogleConnected(v){
  googleConnected=v;
  const btn=document.getElementById('google-connect-btn');
  const status=document.getElementById('google-status');
  const label=document.getElementById('google-connect-label');
  const notice=document.getElementById('auth-notice');
  if(v){
    btn.classList.add('connected');
    status.textContent='✓ Conectado';
    label.textContent='Google Agenda';
    notice.style.display='none';
  }else{
    btn.classList.remove('connected');
    status.textContent='Desconectado';
    label.textContent='Conectar Google Agenda';
    notice.style.display='flex';
  }
}

async function conectarGoogle(){
  const r=await apiFetch('/auth/google');
  if(r&&r.url){
    toast('Abrindo Google...');
    const popup = window.open(r.url,'_blank','width=500,height=600');
    // Verifica status a cada 2s por até 30s
    let tentativas = 0;
    const intervalo = setInterval(async ()=>{
      tentativas++;
      await checkGoogleStatus();
      if(googleConnected || tentativas >= 15) clearInterval(intervalo);
    }, 2000);
  }else{toast('API não disponível');}
}

async function loadAgenda(){
  if(!googleConnected) return;
  const data=await apiFetch('/agenda/treinos');
  if(!Array.isArray(data)) return;
  agendaData=data;
  renderAgenda();
}

function renderAgenda(){
  const list=document.getElementById('agenda-list');
  list.innerHTML='';
  if(!agendaData.length){list.innerHTML='<div class="empty">Nenhum evento agendado.</div>';return;}
  agendaData.forEach(ev=>{
    const start=ev.start?.dateTime||ev.start?.date||'';
    const dt=start?new Date(start):null;
    const timeStr=dt?dt.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}):'';
    const dateStr=dt?dt.toLocaleDateString('pt-BR',{day:'2-digit',month:'short'}):'';
    const item=document.createElement('div');
    item.className='agenda-item';
    item.innerHTML=`
      <div class="agenda-time">${dateStr}<br/>${timeStr}</div>
      <div class="agenda-dot"></div>
      <div class="agenda-info">
        <div class="ag-name">${ev.summary||'Treino'}</div>
        <div class="ag-sub">${ev.description||''}</div>
      </div>
      <button class="agenda-del" onclick="removerEvento('${ev.id}')" title="Remover">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>`;
    list.appendChild(item);
  });
}

async function removerEvento(id){
  if(!confirm('Remover da agenda?')) return;
  await apiFetch(`/agenda/treino/${id}`,{method:'DELETE'});
  toast('🗑️ Evento removido');
  await loadAgenda();
}

function preencherSelectTreinos(){
  const sel=document.getElementById('ag-treino-id');
  sel.innerHTML='';
  const hoje=new Date().toISOString().split('T')[0];
  document.getElementById('ag-data').min=hoje;
  document.getElementById('ag-data').value=hoje;
  if(!treinosData.length){sel.innerHTML='<option>Sem treinos</option>';return;}
  treinosData.forEach(t=>{
    const opt=document.createElement('option');
    opt.value=t.id; opt.textContent=t.nome;
    sel.appendChild(opt);
  });
}

async function agendarTreino(){
  if(!googleConnected){toast('Conecte o Google Agenda primeiro!');return;}
  const treinoId=document.getElementById('ag-treino-id').value;
  const data=document.getElementById('ag-data').value;
  const hora=document.getElementById('ag-hora').value;
  const dur=document.getElementById('ag-dur').value;
  if(!treinoId||!data||!hora){toast('Preencha todos os campos');return;}
  const r=await apiFetch('/agenda/treino',{method:'POST',body:JSON.stringify({treino_id:parseInt(treinoId),data,hora,duracao_min:parseInt(dur)||60})});
  if(r&&r.mensagem&&r.mensagem.includes('sucesso')){
    toast('📅 Treino agendado!');
    closeModal('modal-agendar');
    await loadAgenda();
  }else{toast(r?.mensagem||'Erro ao agendar');}
}

//  INIT 
async function init(){
  const res = await apiFetch('/treinos');
  if(res) treinosData = res.dados || res;
  loadHome();
}
init();