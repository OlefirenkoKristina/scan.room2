import sys, json, numpy as np
SC=r"C:/Users/II/AppData/Local/Temp/claude/C--Users-II-work-scan-room2/20838652-8a07-44d6-87fd-7ccc2bd27c02/scratchpad"
sys.path.insert(0,SC)
from icp import *
old=json.load(open(SC+"/objs.json"))
sh=load(2); sh=sh@np.array(old['2']['R']).T+np.array(old['2']['t'])
print('SH bounds',sh.min(0),sh.max(0))
T=sub(sh,4000,5); tree=kdtree.KDTree(len(T))
for i,p in enumerate(T): tree.insert(p,i)
tree.balance()
def score(X,r=0.05): return np.mean([tree.find(p)[2]<r for p in X])
O=sub(load(5),500,3); Of=sub(load(5),5000,4); print('O5 bounds',O.min(0),O.max(0))
best=[]
for yaw in range(0,360,15):
    a=np.radians(yaw); R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    Oc=O@R.T
    for x in np.arange(-0.5,2.6,0.25):
        for y in np.arange(-3.2,-0.4,0.25):
            for z in np.arange(-1.5,0.6,0.25):
                best.append((score(Oc+np.array([x,y,z])),R,np.array([x,y,z])))
best.sort(key=lambda b:-b[0]); out=[]
for b in best[:6]:
    s,R,t,rms,_=icp(Of,T,1.0,b[1],b[2],it=40,trim=0.35,scale=False)
    out.append((score((Of@R.T+t)[::10]),R,t,rms)); print('C',round(b[0],2),round(out[-1][0],2),np.round(t,2),round(rms,3),flush=True)
out.sort(key=lambda o:-o[0]); o=out[0]
res=json.load(open(SC+"/objs2.json")); res['5']={'R':o[1].tolist(),'t':o[2].tolist(),'score':o[0],'rms':o[3]}
json.dump(res,open(SC+"/objs3.json",'w'))
