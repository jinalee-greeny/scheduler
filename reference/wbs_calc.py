import json, datetime as dt
from collections import defaultdict

TODAY=dt.date(2026,7,15); MD_PER_MM=20; BUFFER_WD=5

# 2026 대한민국 공휴일 (프로젝트 기간 및 이후, 출처: trip.com 2026 달력)
HOLIDAYS={
 dt.date(2026,8,15):"광복절", dt.date(2026,8,17):"광복절 대체",
 dt.date(2026,9,24):"추석연휴", dt.date(2026,9,25):"추석", dt.date(2026,9,26):"추석연휴",
 dt.date(2026,10,3):"개천절", dt.date(2026,10,5):"개천절 대체", dt.date(2026,10,9):"한글날",
}

T=[
 ("1.1","킥오프 & 요구사항 정의","기획/PM",3,2,[],"완료"),
 ("1.2","필요항목·데이터 정의(기획서)","기획/PM",4,3,["1.1"],"완료"),
 ("1.3","벤치마킹·데스크리서치","UX",4,3,["1.1"],"완료"),
 ("2.1","IA & 유저플로우","UX",4,3,["1.2","1.3"],"완료"),
 ("2.2","화면설계(와이어프레임)","UX",8,5,["2.1"],"완료"),
 ("2.3","프로토타입 & 사용성 점검","UX",5,3,["2.2"],"완료"),
 ("3.1","디자인 컨셉·무드","UI",3,2,["2.2","2.3"],"진행중"),
 ("3.2","디자인 시스템(컴포넌트·토큰)","UI",6,4,["3.1"],"예정"),
 ("3.3","본 화면 UI 디자인","UI",10,6,["3.2"],"예정"),
 ("3.4","디자인 QA·핸드오프","UI",3,2,["3.3"],"예정"),
 ("4.1","마크업·스타일 퍼블리싱","퍼블",8,5,["3.4"],"예정"),
 ("4.2","프론트 기능개발(캘린더·목록·등록)","FE",12,7,["4.1"],"예정"),
 ("4.3","상태관리·유효성","FE",5,3,["4.2"],"예정"),
 ("5.1","데이터 모델·DB 설계","BE",4,3,["2.1"],"예정"),
 ("5.2","API 개발(CRUD·일정)","BE",10,6,["5.1","3.4"],"예정"),
 ("5.3","알림·반복일정 로직","BE",6,4,["5.2"],"예정"),
 ("5.4","인증·권한","BE",5,3,["5.2"],"예정"),
 ("6.1","FE/BE 통합","FE/BE",5,3,["4.3","5.3","5.4"],"예정"),
 ("6.2","통합 QA·버그픽스","QA",8,5,["6.1"],"예정"),
 ("6.3","UAT(사용자 검수)","기획/QA",4,3,["6.2"],"예정"),
 ("7.1","배포 준비·릴리즈","BE",3,2,["6.3"],"예정"),
 ("7.2","오픈 & 안정화 모니터링","전체",4,3,["7.1"],"예정"),
]
tasks={t[0]:{"id":t[0],"name":t[1],"role":t[2],"md":t[3],"dur":t[4],"deps":t[5],"status":t[6]} for t in T}

def is_work(d,mode):
    if d in HOLIDAYS: return False
    if mode=="off" and d.weekday()>=5: return False
    return True
def add_wd(d,n,mode):
    step=1 if n>=0 else -1;c=0
    while c<abs(n):
        d+=dt.timedelta(days=step)
        if is_work(d,mode):c+=1
    return d
def norm_f(d,mode):
    while not is_work(d,mode): d+=dt.timedelta(days=1)
    return d
def norm_b(d,mode):
    while not is_work(d,mode): d-=dt.timedelta(days=1)
    return d
def wd_between(a,b,mode):
    if b<a:return 0
    c=0;d=a
    while d<=b:
        if is_work(d,mode):c+=1
        d+=dt.timedelta(days=1)
    return c

succ=defaultdict(list)
for k,v in tasks.items():
    for dp in v["deps"]: succ[dp].append(k)
def topo():
    o=[];s=set()
    def vis(n):
        if n in s:return
        for dp in tasks[n]["deps"]:vis(dp)
        s.add(n);o.append(n)
    for k in tasks:vis(k)
    return o
order=topo()

def compute(mode):
    es={};ef={}
    done_anchor=norm_b(TODAY-dt.timedelta(days=1),mode)
    for n in order:
        v=tasks[n]
        if v["status"]=="완료": es[n]=None; ef[n]=done_anchor; continue
        dep_f=[ef[d] for d in v["deps"] if ef[d] is not None]
        start=TODAY if not dep_f else max(add_wd(max(dep_f),1,mode),TODAY)
        start=norm_f(start,mode)
        es[n]=start; ef[n]=add_wd(start,v["dur"]-1,mode)
    asap=max(ef[n] for n in tasks if tasks[n]["status"]!="완료")
    target=add_wd(asap,BUFFER_WD,mode)
    lf={};ls={};end=norm_b(target,mode)
    for n in reversed(order):
        if succ[n]:
            f=add_wd(min(ls[s] for s in succ[n]),-1,mode)
        else:
            f=end
        f=norm_b(f,mode); lf[n]=f; ls[n]=add_wd(f,-(tasks[n]["dur"]-1),mode)
    # slack
    tstate={}
    for n in tasks:
        if tasks[n]["status"]=="완료":
            tstate[n]={"es":None,"ef":str(ef[n]),"ls":str(ls[n]),"lf":str(lf[n]),"slack":None,"critical":False}
        else:
            sl=wd_between(es[n],ls[n],mode)-1 if ls[n]>=es[n] else 0
            tstate[n]={"es":str(es[n]),"ef":str(ef[n]),"ls":str(ls[n]),"lf":str(lf[n]),"slack":max(sl,0)}
    rem=[n for n in tasks if tasks[n]["status"]!="완료"]
    mn=min(tstate[n]["slack"] for n in rem)
    crit=[]
    for n in rem:
        tstate[n]["critical"]=(tstate[n]["slack"]==mn)
        if tstate[n]["critical"]:crit.append(n)
    crit=sorted(crit,key=lambda x:(int(x.split('.')[0]),int(x.split('.')[1])))
    dday=(target-TODAY).days
    return {"target_open":str(target),"asap_finish":str(asap),"dday":dday,
            "min_slack":mn,"critical":crit,"avail_wd":wd_between(TODAY,end,mode),
            "task":tstate}

phase_md=defaultdict(float);role_md=defaultdict(float)
for k,v in tasks.items():
    phase_md[k.split(".")[0]]+=v["md"]; role_md[v["role"]]+=v["md"]
total_md=sum(v["md"] for v in tasks.values())
done_md=sum(v["md"] for v in tasks.values() if v["status"]=="완료")
pn={"1":"준비·기획","2":"UX 설계","3":"UI 디자인","4":"퍼블·프론트","5":"백엔드·데이터","6":"통합·QA","7":"오픈·안정화"}

out={"today":str(TODAY),"md_per_mm":MD_PER_MM,"buffer_wd":BUFFER_WD,
     "holidays":{str(k):v for k,v in HOLIDAYS.items()},
     "total_md":total_md,"total_mm":round(total_md/MD_PER_MM,2),
     "done_md":done_md,"done_mm":round(done_md/MD_PER_MM,2),
     "remain_md":total_md-done_md,"remain_mm":round((total_md-done_md)/MD_PER_MM,2),
     "progress_pct":round(done_md/total_md*100),
     "phase":{p:{"name":pn[p],"md":phase_md[p],"mm":round(phase_md[p]/MD_PER_MM,2)} for p in sorted(phase_md)},
     "role":{r:{"md":role_md[r],"mm":round(role_md[r]/MD_PER_MM,2)} for r in sorted(role_md,key=lambda x:-role_md[x])},
     "tasks":[{"id":k,"name":tasks[k]["name"],"role":tasks[k]["role"],"md":tasks[k]["md"],
               "dur":tasks[k]["dur"],"deps":tasks[k]["deps"],"status":tasks[k]["status"],
               "phase":k.split('.')[0]} for k in sorted(tasks,key=lambda x:(int(x.split('.')[0]),int(x.split('.')[1])))],
     "scenarios":{"off":compute("off"),"on":compute("on")}}
json.dump(out,open("wbs_data.json","w"),ensure_ascii=False,indent=1)
for m in ("off","on"):
    s=out["scenarios"][m]
    print(f"[{'주말제외' if m=='off' else '주말포함'}] 목표오픈 {s['target_open']} (ASAP {s['asap_finish']}, D-{s['dday']}), 가용근무일 {s['avail_wd']}, CP {len(s['critical'])}개")
print("총 %d MD = %.2f M/M | 완료 %d%%"%(total_md,total_md/MD_PER_MM,out["progress_pct"]))
print("공휴일:", ", ".join(f"{k}({v})" for k,v in out["holidays"].items()))
