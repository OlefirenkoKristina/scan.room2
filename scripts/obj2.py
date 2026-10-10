import sys, json, numpy as np
SC=r"C:/Users/II/AppData/Local/Temp/claude/C--Users-II-work-scan-room2/20838652-8a07-44d6-87fd-7ccc2bd27c02/scratchpad"
sys.path.insert(0,SC)
from icp import *
t1=json.load(open(SC+"/t1.json")); old=json.load(open(SC+"/objs.json"))
Pc=load(0); Sc=load(1)
Sc=Sc[(Sc[:,0]>-0.2)&(Sc[:,0]<3.0)&(Sc[:,1]>-2.7)&(Sc[:,1]<3.9)]
Sc=t1['s']*Sc@np.array(t1['R']).T+np.array(t1['t'])
sh=load(2); Rs=np.array(old['2']['R']); sh=sh@Rs.T+np.array(old['2']['t'])
T=np.vstack([sub(Pc,9000,1),sub(Sc,9000,2),sub(sh,3000,5)])
tree=kdtree.KDTree(len(T))
for i,p in enumerate(T): tree.insert(p,i)
tree.balance()
def score(X,r=0.06):
    d=np.array([tree.find(p)[2] for p in X]); return (d<r).mean()
regions={3:(-1.8,-0.9,1.3,2.8),4:(-1.8,1.3,1.0,2.8),5:(-0.2,1.4,-2.4,-1.0)}
res=dict(old)
for i,(x0,x1,y0,y1) in regions.items():
    O=sub(load(i),400,3); Of=sub(load(i),4000,4); c=O.mean(0); best=[]
    for yaw in range(0,360,15):
        a=np.radians(yaw); R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        for x in np.arange(x0,x1+.01,0.2):
            for y in np.arange(y0,y1+.01,0.2):
                t=np.array([x,y,0])-R@(c*np.array([1,1,0])); t[2]=-1.48-O[:,2].min()
                best.append((score(O@R.T+t),R,t))
    best.sort(key=lambda b:-b[0]); out=[]
    for b in best[:5]:
        s,R,t,rms,med=icp(Of,T,1.0,b[1],b[2],it=40,trim=0.5,scale=False)
        out.append((score((Of@R.T+t)[::8]),R,t,rms))
    out.sort(key=lambda o:-o[0]); o=out[0]
    print('OBJ',i,'score',round(o[0],2),'rms',round(o[3],3),'t',np.round(o[2],2),'yaw',round(np.degrees(np.arctan2(o[1][1,0],o[1][0,0]))),flush=True)
    res[str(i)]={'R':o[1].tolist(),'t':o[2].tolist(),'score':o[0],'rms':o[3]}
json.dump(res,open(SC+"/objs2.json",'w'))
