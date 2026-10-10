import sys, json, numpy as np
sys.path.insert(0,r"C:/Users/II/AppData/Local/Temp/claude/C--Users-II-work-scan-room2/20838652-8a07-44d6-87fd-7ccc2bd27c02/scratchpad"); 
from icp import *
SC=r"C:/Users/II/AppData/Local/Temp/claude/C--Users-II-work-scan-room2/20838652-8a07-44d6-87fd-7ccc2bd27c02/scratchpad"
t1=json.load(open(SC+"/t1.json"))
Pc=load(0); Sc=load(1)
Sc=Sc[(Sc[:,0]>-0.2)&(Sc[:,0]<3.0)&(Sc[:,1]>-2.7)&(Sc[:,1]<3.9)]
Sc=t1['s']*Sc@np.array(t1['R']).T+np.array(t1['t'])
T=np.vstack([sub(Pc,8000,1),sub(Sc,8000,2)])
tree=kdtree.KDTree(len(T))
for i,p in enumerate(T): tree.insert(p,i)
tree.balance()
def score(X):
    d=np.array([tree.find(p)[2] for p in X]); return (d<0.08).mean()
res={}
for i in [2,3,4,5]:
    O=sub(load(i),350,3); Of=sub(load(i),4000,4)
    c=O.mean(0); best=[]
    zs=[-1.5,-0.9,-0.3,0.3,0.9] if i==2 else [-1.48-O[:,2].min()]
    for yaw in range(0,360,45):
        a=np.radians(yaw); R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        for x in np.arange(-1.8,1.4,0.5):
            for y in np.arange(-2.2,2.8,0.5):
                for z in zs:
                    t=np.array([x,y,z])-R@c*0 -R@(c*np.array([1,1,0]))
                    t[2]=z
                    best.append((score(O@R.T+t),yaw,x,y,z,R,t))
    best.sort(key=lambda b:-b[0])
    out=[]
    for b in best[:4]:
        s,R,t,rms,med=icp(Of,T,1.0,b[5],b[6],it=40,trim=0.6,scale=False)
        X=Of@R.T+t; sc=score(X[::10]); out.append((sc,R,t,rms,med,b[0]))
        print('OBJ',i,'init',round(b[0],2),'final score',round(sc,2),'rms',round(rms,3),'t',np.round(t,2),flush=True)
    out.sort(key=lambda o:-o[0]); o=out[0]
    res[i]={'R':o[1].tolist(),'t':o[2].tolist(),'score':o[0],'rms':o[3]}
json.dump(res,open(SC+"/objs.json",'w'))
