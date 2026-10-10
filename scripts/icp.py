import bpy, os, sys, json, numpy as np
from mathutils import kdtree
src=r"C:\Users\II\work\scan.room2"
files=sorted(f for f in os.listdir(src) if f.endswith('.glb'))
def load(i):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(src,files[i]))
    P=[]
    for o in bpy.context.scene.objects:
        if o.type=='MESH':
            M=np.array(o.matrix_world)
            v=np.array([tuple(x.co) for x in o.data.vertices])
            P.append(v@M[:3,:3].T+M[:3,3])
    return np.vstack(P)
def umeyama(A,B,scale=True):
    ma,mb=A.mean(0),B.mean(0); a,b=A-ma,B-mb
    U,S,Vt=np.linalg.svd(b.T@a/len(A)); d=np.ones(3); 
    if np.linalg.det(U)*np.linalg.det(Vt)<0: d[2]=-1
    R=U@np.diag(d)@Vt; s=(S*d).sum()/a.var(0).sum() if scale else 1.0
    t=mb-s*R@ma; return s,R,t
def icp(A,B,s,R,t,it=60,trim=0.7,scale=True):
    tree=kdtree.KDTree(len(B)); 
    for i,p in enumerate(B): tree.insert(p,i)
    tree.balance()
    for _ in range(it):
        X=s*A@R.T+t
        idx=[];dist=[]
        for p in X:
            _,j,d=tree.find(p); idx.append(j); dist.append(d)
        dist=np.array(dist); k=dist<np.quantile(dist,trim)
        s,R,t=umeyama(A[k],B[np.array(idx)[k]],scale)
    return s,R,t,np.sqrt((dist[k]**2).mean()),np.median(dist)
def sub(P,n,seed=0):
    r=np.random.RandomState(seed); return P[r.choice(len(P),min(n,len(P)),replace=False)]
if __name__=='__main__':
    target=sub(load(0),6000)
    S=load(1); S=S[(S[:,0]>-0.2)&(S[:,0]<3.0)&(S[:,1]>-2.7)&(S[:,1]<3.9)]
    Ss=sub(S,4000)
    best=None
    for yaw in [0]:
        s0=1.0; t0=target.mean(0)-Ss.mean(0)
        r=icp(Ss,target,1.0,np.eye(3),t0,it=40)
        print('RES',r[0],r[3],r[4]); print(r[1],r[2])
        json.dump({'s':float(r[0]),'R':r[1].tolist(),'t':r[2].tolist()},open(sys.argv[-1],'w'))
