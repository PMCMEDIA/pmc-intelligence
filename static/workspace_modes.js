/* PMC Intelligence: one project, two views. No inline event-handler generation. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const copy = value => JSON.parse(JSON.stringify(value));
  const order = ['Production','Digital Media','SEO / AEO','Organic Social','Creative / Website','PR / Communications','Measurement'];
  const editable = ['workspace_mode','strategy','department_details','department_approvals','discovery_answers','investment_allocations','tactic_allocations','website_pricing','forecast_inputs','deck_outline','deck_branding','strategy_approved','investment_approved','tactics_approved','measurement_approved','workspace_locks','deck_needs_review','budget','goal','strategy_context','status'];
  const state = {project:null, base:null, revision:null, mode:'ai', screen:'strategy', dirty:false, busy:false, suggestion:null};
  const money = value => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(Number(value)||0);
  const node = (tag, text='', cls='') => { const e=document.createElement(tag); e.textContent=String(text??''); if(cls)e.className=cls; return e; };
  const add = (parent,tag,text,cls) => {const e=node(tag,text,cls);parent.append(e);return e;};
  function button(parent,text,action,cls='') {const e=add(parent,'button',text,cls);e.type='button';e.addEventListener('click',()=>run(action,e));return e;}
  function message(text,error=false) {const e=$('workspaceMessage');e.hidden=!text;e.textContent=text;e.classList.toggle('error',error);}
  async function request(url,body,method) {
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),110000);let response;try{response=await fetch(url,{signal:controller.signal,method:method||(body?'POST':'GET'),headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined,cache:'no-store'});}finally{clearTimeout(timer);}
    const data=await response.json().catch(()=>({error:'The server did not return a usable response. Please try again.'}));
    if(!response.ok)throw new Error(data.error||'Request failed.');
    return data;
  }
  async function run(action,control) {
    if(state.busy)return;
    state.busy=true;setBusy(true);if(control)control.disabled=true;
    try {await action();}catch(error){message(error.message||'Could not complete that action. Your edits have been kept.',true);}finally{state.busy=false;setBusy(false);if(control?.isConnected)control.disabled=false;}
  }
  function setBusy(value){for(const id of ['projectContent','intakeForm','screenNav','modeSwitch','projectActions','projectList'])if($(id))$(id).inert=value;$('workspace').setAttribute('aria-busy',String(value));}
  function projectUrl(suffix='') {return '/api/projects/'+encodeURIComponent(state.project.id)+'/workspace'+suffix;}
  function accept(data) {if(state.project?.id===data.project.id){for(const k of Object.keys(state.project))if(!(k in data.project))delete state.project[k];for(const [k,v] of Object.entries(data.project))if(JSON.stringify(v)!==JSON.stringify(state.project[k]))state.project[k]=v;}else state.project=data.project;state.base=copy(data.project);state.revision=data.revision;state.mode=data.project.workspace_mode==='advanced'?'advanced':'ai';state.dirty=false;updateSaveState();}
  function change({department,content=true}={}) {
    state.dirty=true;
    if(content){state.project.deck_needs_review=!!state.project.deck_outline;state.project.measurement_approved=false;}
    if(department){state.project.department_approvals??={};state.project.department_approvals[department]=false;state.project.strategy_approved=false;state.project.workspace_locks??={};state.project.workspace_locks[department]=true;}
    updateSaveState();
  }
  function updateSaveState(){if($('saveState'))$('saveState').textContent=state.dirty?'Unsaved changes':'Saved';}
  async function save() {
    if(!state.project)return;
    const patch={};for(const key of editable)if(JSON.stringify(state.project[key])!==JSON.stringify(state.base?.[key])&&state.project[key]!==undefined)patch[key]=state.project[key];
    if(!Object.keys(patch).length){state.dirty=false;updateSaveState();return;}
    const data=await request(projectUrl(),{revision:state.revision,patch});accept(data);message('Project saved. Both views use these same recommendations and prices.');
  }
  async function setMode(mode) {
    if(!['ai','advanced'].includes(mode)||mode===state.mode)return;
    if(state.project){await save();const data=await request(projectUrl(),{revision:state.revision,patch:{workspace_mode:mode}});accept(data);}else{state.mode=mode;}
    render();
  }
  async function openProject(id) {
    await save();
    const data=await request('/api/projects/'+encodeURIComponent(id)+'/workspace');
    accept(data);state.screen='strategy';$('projectsDrawer').open=false;render();
    $('projectHeader').scrollIntoView({block:'start'});
  }
  async function listProjects() {
    const items=await request('/api/projects');const host=$('projectList');host.replaceChildren();
    if(!items.length)add(host,'p','No saved projects yet. Start a strategy using the client brief.','muted');
    for(const p of items){const row=add(host,'div','','project-row'),info=add(row,'div');add(info,'h3',p.client||'Untitled client');add(info,'p',(p.owner||'PMC Team')+' · '+(p.status||'Draft'),'muted');button(row,'Open project',()=>openProject(p.id));}
  }
  async function createProject(event) {
    event.preventDefault();
    await run(async()=>{await save();const form=$('intakeForm');if(!form.reportValidity())return;const body=Object.fromEntries(new FormData(form));body.budget=body.budget||'TBD';body.industry=body.industry||'Other';body.workspace_mode=state.mode;message('Researching the client website and preparing the strategy draft…');const p=await request('/api/projects',body);await openProject(p.id);message('Strategy draft ready. No discovery answers or department approvals are required to preview it.');await listProjects();},event.submitter);
  }
  function card(host,title,subtitle) {const c=add(host,'section','','card');add(c,'h2',title);if(subtitle)add(c,'p',subtitle,'muted');return c;}
  function textField(host,label,value,onInput,{type='text',area=false,min,step}={}) {
    const wrap=add(host,'label',label);const input=document.createElement(area?'textarea':'input');if(!area)input.type=type;input.value=value??'';if(min!==undefined)input.min=String(min);if(step!==undefined)input.step=String(step);input.setAttribute('aria-label',label);input.addEventListener('input',()=>onInput(type==='number'?(input.value===''?null:Number(input.value)):input.value));wrap.append(input);return input;
  }
  function safeLink(host,label,url) {try{const u=new URL(url);if(!['http:','https:'].includes(u.protocol))return;const a=add(host,'a',label);a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';}catch(_){add(host,'span',label);}}
  function lines(host,items) {for(const item of items||[])add(host,'div',item,'list-item');}
  function departments(){return Object.keys(state.project.strategy?.departments||{}).sort((a,b)=>{const ai=order.indexOf(a),bi=order.indexOf(b);return (ai<0?99:ai)-(bi<0?99:bi);});}
  function details(name){const p=state.project,s=p.strategy?.department_sections?.[name]||{},d=p.department_details?.[name]||{};return {...s,objective:d.objective??s.objective,success:d.kpis??s.success};}
  function setDepartmentField(name,key,value) {
    const p=state.project;p.strategy.department_sections??={};p.strategy.department_sections[name]??={};p.department_details??={};p.department_details[name]??={};
    if(key==='recommendations'){const items=value.split('\n').map(x=>x.trim()).filter(Boolean);p.strategy.departments[name]=items;p.strategy.department_sections[name].tactics=items;p.strategy.department_sections[name].recommendations=items;}
    else if(['owner','timing','deliverables','dependencies','notes'].includes(key))p.department_details[name][key]=value;
    else {p.strategy.department_sections[name][key]=value;if(key==='objective')p.department_details[name].objective=value;if(key==='success')p.department_details[name].kpis=value;}
    change({department:name});
  }
  function render() {
    document.documentElement.dataset.workspaceMode=state.mode;
    for(const b of document.querySelectorAll('[data-mode]'))b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode));
    $('modeDescription').textContent=state.mode==='ai'?'Review the generated strategy. Open advanced controls only where you need to make a change.':'Edit the same project in detail: recommendations, deliverables, pricing, research and assumptions.';
    if(!state.project)return;
    $('projectHeader').hidden=false;$('projectActions').hidden=false;$('pageTitle').textContent=state.project.client||'Client strategy';$('projectMeta').textContent=[state.project.industry,state.project.status||'Strategy draft'].filter(Boolean).join(' · ');$('projectStatus').textContent='One saved project · '+(state.mode==='ai'?'AI Strategy':'Advanced Builder');
    for(const b of document.querySelectorAll('[data-screen]')){if(b.dataset.screen===state.screen)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');}
    const host=$('projectContent');host.replaceChildren();
    if(state.screen==='deck')renderDeck(host);else if(state.screen==='review')renderReview(host);else{renderResearch(host);renderExecutive(host);for(const name of departments())renderDepartment(host,name);renderInvestment(host);if(state.mode==='advanced'){renderWebsite(host);renderMeasurement(host);}else renderGaps(host);}
    updateSaveState();
  }
  function renderResearch(host) {
    const box=add(host,'details','','card');add(box,'summary','Research, source material & items to confirm');
    const p=state.project;add(box,'p','This preview uses the saved strategy and available public findings. The current generator is template-guided; unverified figures are not completed research.','muted small');
    for(const fact of p.strategy?.facts||[]){add(box,'h3',fact.label||'Source');add(box,'p',fact.value||'','long-copy');add(box,'p',fact.source||'Source not recorded','muted small');}
    if(p.research?.ok===false)add(box,'p','Website research was unavailable. The draft is still accessible; site findings need confirmation.','notice');
    const competitors=p.competitive_intelligence?.candidates||[];
    if(competitors.length){add(box,'h3','Competitor candidates · not yet verified');for(const c of competitors){const line=add(box,'p');safeLink(line,c.title||c.url,c.url);}}
    else add(box,'p','Competitor research has not been saved for this project.','muted');
    button(box,'Research competitor candidates',async()=>{await save();await request('/api/projects/'+encodeURIComponent(p.id)+'/competitive',{});accept(await request(projectUrl()));render();message('Competitor candidates saved. Validate them before including claims in a proposal.');});
  }
  function renderExecutive(host) {
    const p=state.project,c=card(host,'Executive Summary'),actions=add(c,'div','','actions');
    if(state.mode==='advanced')textField(c,'Executive summary',p.strategy?.executive||'',v=>{p.strategy??={};p.strategy.executive=v;p.workspace_locks??={};p.workspace_locks.executive=true;for(const d of departments())(p.department_approvals??={})[d]=false;p.strategy_approved=false;change();},{area:true});
    else {add(c,'p',p.strategy?.executive||'Executive summary needs confirmation.','long-copy');button(actions,'Edit section',()=>focusAdvanced('executive'));}
    c.id='section-executive';button(actions,'Regenerate suggestion',()=>suggest('executive'));
    for(const [key,title] of [['opportunity','The opportunity'],['challenge','The challenge'],['strategic_response','Our strategic response']]){const value=p.strategy?.narrative?.[key];if(value){add(c,'h3',title,'subheading');if(state.mode==='advanced')textField(c,title,value,v=>{p.strategy.narrative[key]=v;change();},{area:true});else add(c,'p',value,'long-copy');}}
  }
  function renderDepartment(host,name) {
    const p=state.project,c=add(host,'section','','card');c.id='department-'+encodeURIComponent(name);const head=add(c,'div','','section-heading');add(head,'h2',name);add(head,'span',p.department_approvals?.[name]?'Approved':'Draft · review available','badge');const d=details(name);
    if(state.mode==='ai'){
      for(const [key,title] of [['objective','Objective'],['opportunity','Opportunity'],['response','Recommended approach']])if(d[key]){add(c,'h3',title,'subheading');add(c,'p',d[key],'long-copy');}
      add(c,'h3','Recommended deliverables / tactics','subheading');lines(c,p.strategy.departments[name]);
      for(const [key,title] of [['rationale','Why this approach'],['outcome','Expected outcome']])if(d[key]){add(c,'h3',title,'subheading');add(c,'p',d[key],'long-copy');}
      const manual=p.department_details?.[name]||{};if(manual.deliverables){add(c,'h3','Scoped deliverables','subheading');add(c,'p',manual.deliverables,'long-copy');}
      if(d.success){add(c,'h3',name==='Digital Media'?'Performance KPIs':'Department success measures','subheading');add(c,'p',d.success,'long-copy');}
    }else{
      textField(c,'Recommendations · one per line',(p.strategy.departments[name]||[]).join('\n'),v=>setDepartmentField(name,'recommendations',v),{area:true});
      const grid=add(c,'div','','field-grid');
      for(const [key,label] of [['objective','Department objective'],['opportunity','Opportunity'],['response','Strategic response'],['rationale','Rationale'],['outcome','Expected outcome'],['success',name==='Digital Media'?'Performance KPIs':'Department success measures']])textField(grid,label,d[key]||'',v=>setDepartmentField(name,key,v),{area:true});
      for(const [key,label] of [['deliverables','Scoped deliverables'],['dependencies','Asset / team dependencies'],['notes','Internal notes'],['owner','Department owner'],['timing','Timing']])textField(grid,label,p.department_details?.[name]?.[key]||'',v=>setDepartmentField(name,key,v),{area:!['owner','timing'].includes(key)});
    }
    const actions=add(c,'div','','actions');if(state.mode==='ai')button(actions,'Advanced controls',()=>focusAdvanced(name));button(actions,'Regenerate suggestion',()=>suggest(name));button(actions,p.department_approvals?.[name]?'Reopen section':'Approve section',()=>approve(name));
    if(state.mode==='advanced')button(actions,'Remove department',async()=>{if(!confirm('Remove '+name+' from the proposed strategy? Existing pricing will remain for review.'))return;delete p.strategy.departments[name];delete p.strategy.department_sections?.[name];delete p.department_details?.[name];delete p.department_approvals?.[name];change();await save();render();},'danger');
    if(p.workspace_locks?.[name])add(c,'p','Manually edited. Regeneration shows a proposed replacement before changing this section.','muted small');
  }
  async function focusAdvanced(name){await setMode('advanced');const target=$(name==='executive'?'section-executive':'department-'+encodeURIComponent(name));target?.scrollIntoView({block:'start'});target?.querySelector('textarea,input')?.focus({preventScroll:true});}
  async function approve(name){await save();const p=state.project;p.department_approvals??={};p.department_approvals[name]=!p.department_approvals[name];p.strategy_approved=departments().length>0&&departments().every(n=>p.department_approvals[n]);p.status=p.strategy_approved?'Strategy Reviewed':'Department Review';change({content:false});await save();render();}
  async function suggest(section){await save();const result=await request(projectUrl('/suggestion'),{section});state.suggestion=result;$('suggestionTitle').textContent='Review replacement: '+(section==='executive'?'Executive Summary':section);$('suggestionNote').textContent=result.note;$('currentSuggestion').textContent=section==='executive'?state.project.strategy.executive:JSON.stringify({recommendations:state.project.strategy.departments[section],details:details(section)},null,2);$('newSuggestion').textContent=typeof result.candidate==='string'?result.candidate:JSON.stringify(result.candidate,null,2);$('suggestionDialog').showModal();}
  async function applySuggestion(){const s=state.suggestion;if(!s)return;if(s.revision!==state.revision)throw new Error('The project changed after this suggestion. Generate a fresh suggestion first.');if(s.section==='executive'){state.project.strategy.executive=s.candidate;for(const name of departments())(state.project.department_approvals??={})[name]=false;state.project.strategy_approved=false;change();}else{const n=s.section;state.project.strategy.department_sections??={};state.project.strategy.department_sections[n]=s.candidate.details;setDepartmentField(n,'recommendations',s.candidate.recommendations.join('\n'));for(const [k,v] of Object.entries(s.candidate.details))if(typeof v==='string')setDepartmentField(n,k,v);}await save();$('suggestionDialog').close();state.suggestion=null;render();}
  function renderGaps(host){const p=state.project,c=card(host,'Items to confirm','These do not block the strategy preview or a draft deck.');const items=[];if(!p.investment_allocations?.some(a=>Number(a.amount)>0))items.push('Investment amounts have not been scoped.');if(!p.website_analysis&&departments().some(n=>n.includes('Website')))items.push('Website analysis and billable page scope need review.');if(!p.campaign_outlook)items.push('No validated campaign forecast is saved yet.');if(!p.social_analysis&&departments().includes('Organic Social'))items.push('Automatic social account auditing and social pricing are not connected in this release.');if(departments().includes('Production'))items.push('Production quantities and rates need confirmation against downstream deliverables.');if(!items.length)items.push('Review remaining source assumptions and departmental recommendations.');lines(c,items);button(c,'Open detailed controls',()=>setMode('advanced'));}
  function renderInvestment(host) {
    const p=state.project,c=card(host,'Investment Framework','The same saved prices appear in both views. Unpriced work is not treated as a confirmed zero-cost deliverable.');c.id='investment-controls';
    if(state.mode==='advanced')textField(c,'Budget guidance',p.budget||'',v=>{p.budget=v;change();});else add(c,'p','Budget guidance: '+(p.budget||'Needs confirmation'));
    const rows=p.investment_allocations||[];
    if(rows.length){const wrap=add(c,'div','','table-scroll'),table=add(wrap,'table'),thead=add(table,'thead'),tr=add(thead,'tr');for(const title of ['Department','Allocation','Investment'])add(tr,'th',title);const body=add(table,'tbody');for(const row of rows){const r=add(body,'tr');add(r,'td',row.department);add(r,'td',(Number(row.percent)||0)+'%');const amount=add(r,'td');if(state.mode==='advanced')textField(amount,row.department+' investment',row.amount,v=>{row.amount=v;recalculateAllocationPercents();change();updateInvestmentSummary();},{type:'number',min:0,step:1});else add(amount,'span',money(row.amount));}add(c,'p','','mono').id='investment-total';}
    else add(c,'p','No department investment has been saved yet.','notice');
    if(state.mode==='advanced'){
      button(c,'Add department allocations',()=>{p.investment_allocations??=[];for(const name of departments())if(!p.investment_allocations.some(a=>a.department===name))p.investment_allocations.push({department:name,amount:0,percent:0});change();render();});
      for(const allocation of p.investment_allocations||[])renderTactics(c,allocation);
      button(c,'Add a department',()=>{const name=prompt('Department name');if(!name?.trim())return;const clean=name.trim();if(['__proto__','constructor','prototype'].includes(clean))throw new Error('Choose another department name.');if(p.strategy.departments[clean])throw new Error('That department already exists.');p.strategy.departments[clean]=[];change({department:clean});render();});
    }
    const w=p.website_pricing;if(w){add(c,'h3','Website estimator · separately scoped','subheading');add(c,'p',(w.pages??0)+' development pages × '+money(w.page_rate??850)+' per page');add(c,'p','Estimated website project: '+money(websiteTotal(w))+' · not automatically added again to department allocations.');}
    if(state.mode==='ai')button(c,'Edit investment & technical scope',async()=>{await setMode('advanced');$('investment-controls')?.scrollIntoView({block:'start'});});
    updateInvestmentSummary();
  }
  function recalculateAllocationPercents(){const rows=state.project.investment_allocations||[],total=rows.reduce((n,r)=>n+(Number(r.amount)||0),0);for(const r of rows)r.percent=total?Math.round(10000*(Number(r.amount)||0)/total)/100:0;}
  function updateInvestmentSummary(){const rows=state.project.investment_allocations||[],total=rows.reduce((n,r)=>n+(Number(r.amount)||0),0);if($('investment-total'))$('investment-total').textContent='Department allocation total: '+money(total)+' · confirm billing period before export.';}
  function renderTactics(host,allocation){const p=state.project,name=allocation.department,box=add(host,'details','','tactic-row');add(box,'summary',name+' · channel / tactic detail');const items=p.tactic_allocations?.[name]||[];
    for(const item of items){const row=add(box,'div','','tactic-row'),grid=add(row,'div','','tactic-fields');textField(grid,'Tactic / channel',item.name,v=>{item.name=v;change();});textField(grid,'Percent of department',item.percent,v=>{item.percent=v;change();budget.textContent=money((Number(allocation.amount)||0)*(Number(v)||0)/100);},{type:'number',min:0,step:1});const budget=add(grid,'p',money((Number(allocation.amount)||0)*(Number(item.percent)||0)/100),'mono');if(name==='Digital Media')textField(row,'Primary performance KPI',item.kpi||'',v=>{item.kpi=v;change();});}
    button(box,'Add tactic',()=>{((p.tactic_allocations??={})[name]??=[]).push({name:'New tactic',percent:0,kpi:'',notes:''});change();render();});
  }
  function websiteTotal(w){const n=k=>Math.max(0,Number(w[k])||0);return Math.max(0,n('pages')*n('page_rate')+n('discovery')+n('templates')*n('mockup_rate')+n('technical')-n('adjustment'));}
  function renderWebsite(host){const p=state.project;if(!departments().some(n=>n.toLowerCase().includes('website'))&&!p.website_pricing)return;const c=card(host,'Website Scope & Research','Development defaults to $850 per billable page. Public URLs are not automatically treated as billable pages.');const w=p.website_pricing||{url:p.url||'',pages:0,page_rate:850,discovery:0,templates:0,mockup_rate:0,technical:0,adjustment:0,notes:''};const total=add(c,'h3',money(websiteTotal(w))),grid=add(c,'div','','field-grid');for(const [k,title] of [['url','Client website'],['pages','Billable development pages'],['page_rate','Development rate per page ($)'],['discovery','Discovery & sitemap ($)'],['templates','Unique mockup templates'],['mockup_rate','Mockup / wireframe fee per template ($)'],['technical','Additional technical functionality ($)'],['adjustment','Discount / adjustment ($)']])textField(grid,title,w[k],v=>{p.website_pricing=w;w[k]=v;total.textContent=money(websiteTotal(w));change({department:'Creative / Website'});},{type:k==='url'?'text':'number',min:0,step:1});textField(c,'Website scope notes',w.notes,v=>{p.website_pricing=w;w.notes=v;change({department:'Creative / Website'});},{area:true});let competitorText=(p.website_analysis?.competitors||[]).map(x=>x.url).join('\n');textField(c,'Competitor URLs · up to 5, one per line',competitorText,v=>{competitorText=v;},{area:true});button(c,'Scan website & competitors',async()=>{await save();message('Scanning public website and supplied competitors…');await request('/api/projects/'+encodeURIComponent(p.id)+'/website-analysis',{url:state.project.website_pricing?.url||state.project.url,competitors:competitorText.split('\n').map(x=>x.trim()).filter(Boolean).slice(0,5)});accept(await request(projectUrl()));render();message('Website findings saved. Review page classifications before changing the estimate.');});if(p.website_analysis){const a=p.website_analysis;add(c,'h3','Saved website findings','subheading');add(c,'p',(a.url_count||0)+' public URLs identified'+(a.truncated?' · scan limit reached':''));lines(c,(a.observed_features||[]).map(x=>x.feature+' · '+(x.confidence||'Needs verification')));lines(c,(a.recommendations||[]).map(x=>x.feature+' · '+x.reason));for(const competitor of a.competitors||[])add(c,'p',(competitor.title||competitor.url)+' · '+competitor.status);if(a.urls?.length){const urls=add(c,'details');add(urls,'summary','Review discovered URLs');for(const url of a.urls){const line=add(urls,'p');safeLink(line,url,url);}}}}
  function renderMeasurement(host){const p=state.project,c=card(host,'Measurement & Forecast Assumptions','These inputs are optional. Missing economics are not invented, and projections remain planning estimates.');const f=p.forecast_inputs||{};for(const [k,title] of [['close_rate','Lead-to-customer rate (%)'],['customer_value','Customer value ($)'],['margin','Contribution margin (%)']])textField(c,title,f[k]??'',v=>{p.forecast_inputs=f;f[k]=v;change();},{type:'number',min:0,step:'any'});button(c,'Preview assumption-based forecast',async()=>{await save();await request('/api/projects/'+encodeURIComponent(p.id)+'/forecast',{});accept(await request(projectUrl()));render();message('Assumption-based forecast saved. Current benchmark defaults are placeholders, not independently sourced industry benchmarks.');});if(p.campaign_outlook){const detail=add(c,'details');add(detail,'summary','Inspect saved forecast');add(detail,'pre',JSON.stringify(p.campaign_outlook,null,2));}
    const gaps=add(c,'details');add(gaps,'summary','Optional client / discovery inputs');for(const q of p.questions||[]){const question=typeof q==='string'?q:q.question;textField(gaps,question,(p.discovery_answers||[]).find(x=>x.question===question)?.answer||'',v=>{p.discovery_answers??=[];let entry=p.discovery_answers.find(x=>x.question===question);if(!entry){entry={question,answer:''};p.discovery_answers.push(entry);}entry.answer=v;change({content:false});},{area:true});}add(gaps,'p','Saving these answers does not replace edited strategy sections. Use a section-level suggestion to review a revised recommendation.','muted small');}
  async function buildDeck(){await save();const data=await request(projectUrl('/deck'),{revision:state.revision});accept(data);state.screen='deck';render();$('projectHeader').scrollIntoView({block:'start'});}
  function renderDeck(host){const p=state.project,c=card(host,'Draft Strategy Deck','Both modes use the same slide outline and saved project. Department approval is not required to create this draft.');add(c,'p','Template status: this release still uses the existing PowerPoint renderer. Exact reproduction of the uploaded PMC master is a separate, unfinished integration.','notice small');if(p.deck_needs_review)add(c,'p','The strategy or scope changed after this deck was built. Existing slide edits have been preserved. Review them or explicitly rebuild from the saved strategy.','notice');if(!p.deck_outline?.length){button(c,'Build draft deck',buildDeck,'primary');return;}const actions=add(c,'div','','actions');button(actions,'Export draft PowerPoint',async()=>{await save();const response=await fetch('/api/projects/'+encodeURIComponent(p.id)+'/deck.pptx');if(!response.ok){const e=await response.json().catch(()=>({}));throw new Error(e.error||'PowerPoint export failed.');}const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=(p.client||'Client').replace(/[^\w -]/g,'')+'_PMC_Draft.pptx';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);},'primary');button(actions,'Rebuild from current strategy',async()=>{if(!confirm('Replace the current slide outline with a new draft? A copy of the previous outline will be kept for recovery.'))return;await save();accept(await request(projectUrl('/deck'),{revision:state.revision,rebuild:true}));render();});if(p.previous_deck_outline)button(actions,'Restore previous outline',async()=>{await save();accept(await request(projectUrl('/restore-deck'),{revision:state.revision}));render();});
    if(state.mode==='advanced'){const g=add(c,'div','','field-grid');textField(g,'Presentation subtitle',p.deck_branding?.subtitle||p.client,v=>{(p.deck_branding??={}).subtitle=v;change({content:false});});textField(g,'Deck accent',p.deck_branding?.accent_color||'#16b7c8',v=>{(p.deck_branding??={}).accent_color=v;change({content:false});},{type:'color'});}
    p.deck_outline.forEach((slide,index)=>{const box=card(host,(index+1)+'. '+slide.title);box.classList.toggle('deck-excluded',slide.include===false);if(state.mode==='advanced'){textField(box,'Slide '+(index+1)+' title',slide.title,v=>{slide.title=v;change({content:false});});textField(box,'Slide '+(index+1)+' copy',slide.body||'',v=>{slide.body=v;change({content:false});},{area:true}).classList.add('deck-body-editor');const controls=add(box,'div','','actions');button(controls,slide.include===false?'Include slide':'Exclude slide',()=>{slide.include=slide.include===false;change({content:false});render();});const up=button(controls,'Move up',()=>{[p.deck_outline[index-1],p.deck_outline[index]]=[slide,p.deck_outline[index-1]];change({content:false});render();});up.disabled=index===0;const down=button(controls,'Move down',()=>{[p.deck_outline[index+1],p.deck_outline[index]]=[slide,p.deck_outline[index+1]];change({content:false});render();});down.disabled=index===p.deck_outline.length-1;}else{add(box,'p',slide.body||'This data slide is populated from the saved project during export.','long-copy');if(slide.include===false)add(box,'span','Excluded','badge');button(box,'Edit slide',()=>setMode('advanced'));}});
  }
  function renderReview(host){const p=state.project,c=card(host,'Review the proposed strategy','Approvals follow a complete strategy preview. They do not block creating or reading the draft deck.');add(c,'p',p.deck_outline?.length?'Draft deck available for review.':'No draft deck yet. You can build one before requesting approvals.');button(c,'Open draft deck',buildDeck,'primary');for(const name of departments()){const row=add(c,'div','','project-row');add(row,'h3',name);add(row,'span',p.department_approvals?.[name]?'Approved':'Pending review','badge');button(row,p.department_approvals?.[name]?'Reopen':'Approve',()=>approve(name));}if(p.deck_needs_review)add(c,'p','The deck needs review against the latest strategy edits.','notice');}
  for(const b of document.querySelectorAll('[data-mode]'))b.addEventListener('click',()=>run(()=>setMode(b.dataset.mode),b));
  for(const b of document.querySelectorAll('[data-screen]'))b.addEventListener('click',()=>run(async()=>{if(!state.project)return;await save();state.screen=b.dataset.screen;if(state.screen==='deck'&&!state.project.deck_outline)await buildDeck();else render();},b));
  $('intakeForm').addEventListener('submit',createProject);
  $('saveProject').addEventListener('click',()=>run(async()=>{await save();render();},$('saveProject')));
  $('buildDeck').addEventListener('click',()=>run(buildDeck,$('buildDeck')));
  $('keepCurrent').addEventListener('click',()=>{$('suggestionDialog').close();state.suggestion=null;});
  $('applySuggestion').addEventListener('click',()=>run(applySuggestion,$('applySuggestion')));
  window.addEventListener('beforeunload',event=>{if(state.dirty){event.preventDefault();event.returnValue='';}});
  for(const a of document.querySelectorAll('a[href="/"],a[href="/logout"]'))a.addEventListener('click',event=>{if(state.dirty&&!confirm('Leave with unsaved changes? Use Save project to keep your latest edits.'))event.preventDefault();});
  render();run(listProjects);
})();
