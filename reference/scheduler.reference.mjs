/**
 * @scheduler 참조 구현 (포팅 시작점)
 * ------------------------------------------------------------------
 * 현재 단일 HTML 대시보드의 계산 엔진을 전역 상태 없이 '순수 함수'로 추출한 것.
 * Claude Code가 packages/scheduler(TS)로 이식할 때 이 파일을 정본 참조로 사용.
 * 규칙: 역산(ALAP) + ASAP + slack + 크리티컬 패스 + M/M 집계. 주말/공휴일 근무일 계산.
 * 골든값(현재 데이터): off 목표 2026-09-23, on 목표 2026-09-04, 총 124MD, CP 12개.
 */
const pad = n => String(n).padStart(2, "0");
export const D = s => { const [y,m,d] = s.split("-").map(Number); return new Date(y, m-1, d); };
export const iso = dt => dt.getFullYear()+"-"+pad(dt.getMonth()+1)+"-"+pad(dt.getDate());
const addDays = (dt,n)=>{ const x=new Date(dt); x.setDate(x.getDate()+n); return x; };
const maxD = a => new Date(Math.max.apply(null, a.map(x=>+x)));
const minD = a => new Date(Math.min.apply(null, a.map(x=>+x)));
const dayn = (a,b) => Math.round((b-a)/86400000);

export function hasCycle(tasks){
  const byId={}; tasks.forEach(t=>byId[t.id]=t); const st={};
  const dfs=n=>{ if(st[n]===1)return true; if(st[n]===2)return false; st[n]=1;
    const v=byId[n]; if(v) for(const d of v.deps){ if(byId[d]&&dfs(d)) return true; } st[n]=2; return false; };
  for(const t of tasks) if(dfs(t.id)) return true; return false;
}

/** @param {Model} model @param {'off'|'on'} mode */
export function computeSchedule(model, mode){
  const hol = new Set(model.holidays.map(h=>h.date));
  const today = D(model.settings.today);
  const isWork = dt => { if(hol.has(iso(dt))) return false;
    if(mode==="off" && (dt.getDay()===0||dt.getDay()===6)) return false; return true; };
  const addWd = (dt,n)=>{ let s=n>=0?1:-1,c=0,x=new Date(dt);
    while(c<Math.abs(n)){ x=addDays(x,s); if(isWork(x))c++; } return x; };
  const normF = dt=>{ let x=new Date(dt); while(!isWork(x)) x=addDays(x,1); return x; };
  const normB = dt=>{ let x=new Date(dt); while(!isWork(x)) x=addDays(x,-1); return x; };
  const wdBetween = (a,b)=>{ if(b<a)return 0; let c=0,x=new Date(a);
    while(x<=b){ if(isWork(x))c++; x=addDays(x,1); } return c; };

  const tasks = model.tasks, byId={}; tasks.forEach(t=>byId[t.id]=t);
  const succ={}; tasks.forEach(t=>succ[t.id]=[]);
  tasks.forEach(t=>t.deps.forEach(dp=>{ if(succ[dp]) succ[dp].push(t.id); }));
  const order=[], seen={};
  const vis=n=>{ if(seen[n]||!byId[n])return; byId[n].deps.forEach(vis); seen[n]=1; order.push(n); };
  tasks.forEach(t=>vis(t.id));

  const es={}, ef={}, doneAnchor=normB(addDays(today,-1));
  order.forEach(n=>{ const v=byId[n];
    if(v.status==="완료"){ es[n]=null; ef[n]=doneAnchor; return; }
    const df=v.deps.map(dp=>ef[dp]).filter(Boolean);
    let start = df.length ? maxD([addWd(maxD(df),1), today]) : today;
    start=normF(start); es[n]=start; ef[n]=addWd(start, v.dur-1); });
  const nonDone = tasks.filter(t=>t.status!=="완료");
  const asap = nonDone.length ? maxD(nonDone.map(t=>ef[t.id])) : doneAnchor;
  const target = addWd(asap, model.settings.buffer_wd);

  const ls={}, lf={}, end=normB(target);
  order.slice().reverse().forEach(n=>{ const v=byId[n];
    let f = succ[n].length ? addWd(minD(succ[n].map(s=>ls[s])),-1) : end;
    f=normB(f); lf[n]=f; ls[n]=addWd(f, -(v.dur-1)); });

  const task={};
  tasks.forEach(t=>{ const n=t.id;
    if(t.status==="완료") task[n]={es:null, ef:iso(ef[n]), ls:iso(ls[n]), lf:iso(lf[n]), slack:null, critical:false};
    else { const sl = ls[n]>=es[n] ? wdBetween(es[n],ls[n])-1 : 0;
      task[n]={es:iso(es[n]), ef:iso(ef[n]), ls:iso(ls[n]), lf:iso(lf[n]), slack:Math.max(sl,0)}; } });
  const remSl = nonDone.map(t=>task[t.id].slack);
  const minSlack = remSl.length ? Math.min.apply(null, remSl) : 0;
  const critical=[];
  tasks.forEach(t=>{ if(t.status!=="완료"){ task[t.id].critical = task[t.id].slack===minSlack;
    if(task[t.id].critical) critical.push(t.id); } });

  return { target: iso(target), asap: iso(asap), dday: dayn(today,target), minSlack, critical, task };
}

export function rollupMM(model){
  const byPhase={}, byRole={}; let total=0, done=0; const mm=model.settings.md_per_mm;
  model.tasks.forEach(t=>{ byPhase[t.phase]=(byPhase[t.phase]||0)+t.md;
    byRole[t.role]=(byRole[t.role]||0)+t.md; total+=t.md; if(t.status==="완료") done+=t.md; });
  return { total, done, remain: total-done, progress: total?Math.round(done/total*100):0,
    totalMM: +(total/mm).toFixed(2), byPhase, byRole };
}
