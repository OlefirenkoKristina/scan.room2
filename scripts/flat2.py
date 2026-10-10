import bpy, numpy as np, bmesh
from mathutils import Matrix, Vector
sc=bpy.context.scene; bpy.context.view_layer.update()
XL,XR,YB,YT,ZF,ZC=-1.34,1.25,-2.17,2.11,0.02,2.53
room=[o for o in sc.objects if o.type=='MESH' and any(c.name=="Room_Polycam" for c in o.users_collection)]
tol=0.06; moved=0
for o in room:
    M=np.array(o.matrix_world); Mi=np.linalg.inv(M); n=len(o.data.vertices)
    v=np.empty(n*3,np.float32); o.data.vertices.foreach_get('co',v); v=v.reshape(-1,3)
    w=v@M[:3,:3].T+M[:3,3]; w0=w.copy()
    inx=(w[:,0]>XL-.15)&(w[:,0]<XR+.15); iny=(w[:,1]>YB-.15)&(w[:,1]<YT+.15); inz=(w[:,2]>ZF-.15)&(w[:,2]<ZC+.15)
    for ax,pl,ok in [(0,XL,iny&inz),(0,XR,iny&inz),(1,YB,inx&inz),(1,YT,inx&inz),(2,ZF,inx&iny),(2,ZC,inx&iny)]:
        t=tol if ax<2 else (0.05 if pl==ZF else 0.07)
        s=ok&(abs(w[:,ax]-pl)<t); w[s,ax]=pl
    moved+=int((np.abs(w-w0).sum(1)>0).sum())
    v2=(w-M[:3,3])@np.linalg.inv(M[:3,:3]).T
    o.data.vertices.foreach_set('co',v2.astype(np.float32).ravel()); o.data.update()
print('MOVED',moved)
# --- textured shell ---
root=bpy.data.objects['ROOM']
coll=bpy.data.collections.new("Room_shell"); sc.collection.children.link(coll)
def mk(name,col,rough,builder):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.use_backface_culling=True; m.diffuse_color=(*col,1)
    nt=m.node_tree; bsdf=nt.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value=rough
    builder(nt,bsdf,col); return m
def wall_b(nt,b,col):
    tc=nt.nodes.new('ShaderNodeTexCoord'); no=nt.nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value=60; no.inputs['Detail'].default_value=8
    mp=nt.nodes.new('ShaderNodeMapping'); nt.links.new(tc.outputs['Object'],mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'],no.inputs['Vector'])
    bu=nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value=0.15; nt.links.new(no.outputs['Fac'],bu.inputs['Height']); nt.links.new(bu.outputs['Normal'],b.inputs['Normal'])
    ramp=nt.nodes.new('ShaderNodeMix'); ramp.data_type='RGBA'; ramp.inputs['Factor'].default_value=0.12
    ramp.inputs['A'].default_value=(*col,1); ramp.inputs['B'].default_value=(col[0]*.8,col[1]*.8,col[2]*.8,1)
    nt.links.new(no.outputs['Fac'],ramp.inputs['Factor']); nt.links.new(ramp.outputs['Result'],b.inputs['Base Color'])
def floor_b(nt,b,col):
    tc=nt.nodes.new('ShaderNodeTexCoord'); br=nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value=1; br.inputs['Brick Width'].default_value=2.0; br.inputs['Row Height'].default_value=0.14
    br.inputs['Mortar Size'].default_value=0.004; br.inputs['Color1'].default_value=(0.42,0.15,0.06,1); br.inputs['Color2'].default_value=(0.33,0.11,0.04,1); br.inputs['Mortar'].default_value=(0.05,0.02,0.01,1)
    br.offset=0.3
    mp=nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value=(0,0,np.pi/2); nt.links.new(tc.outputs['Object'],mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'],br.inputs['Vector'])
    nt.links.new(br.outputs['Color'],b.inputs['Base Color'])
    no=nt.nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value=40; nt.links.new(tc.outputs['Object'],no.inputs['Vector'])
    bu=nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value=0.1; nt.links.new(no.outputs['Fac'],bu.inputs['Height']); nt.links.new(bu.outputs['Normal'],b.inputs['Normal'])
def ceil_b(nt,b,col):
    tc=nt.nodes.new('ShaderNodeTexCoord'); br=nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Brick Width'].default_value=0.5; br.inputs['Row Height'].default_value=0.5; br.inputs['Mortar Size'].default_value=0.004
    br.inputs['Color1'].default_value=(0.9,0.88,0.82,1); br.inputs['Color2'].default_value=(0.86,0.84,0.78,1); br.inputs['Mortar'].default_value=(0.6,0.58,0.52,1); br.offset=0
    nt.links.new(tc.outputs['Object'],br.inputs['Vector']); nt.links.new(br.outputs['Color'],b.inputs['Base Color'])
mw=mk("Wall_plaster",(0.86,0.79,0.58),0.9,wall_b); mf=mk("Floor_boards",(0.4,0.14,0.05),0.35,floor_b); mc=mk("Ceiling_tiles",(0.9,0.88,0.82),0.95,ceil_b)
o=0.015
def plane(name,pts,mat):
    me=bpy.data.meshes.new(name); me.from_pydata([Vector(p) for p in pts],[],[(0,1,2,3)]); me.update()
    ob=bpy.data.objects.new(name,me); coll.objects.link(ob); me.materials.append(mat)
    c=sum((Vector(p) for p in pts),Vector())/4; ctr=Vector(((XL+XR)/2,(YB+YT)/2,(ZF+ZC)/2))
    if me.polygons[0].normal.dot(ctr-c)<0: me.polygons[0].flip(); me.update()
    ob.visible_shadow=False; ob.parent=root; ob.matrix_parent_inverse=root.matrix_world.inverted(); return ob
x0,x1,y0,y1,z0,z1=XL-o,XR+o,YB-o,YT+o,ZF-o,ZC+o
plane("Wall_L",[(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)],mw); plane("Wall_R",[(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],mw)
plane("Wall_B",[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],mw); plane("Wall_T",[(x0,y1+0.40,z0),(x1,y1+0.40,z0),(x1,y1+0.40,z1),(x0,y1+0.40,z1)],mw)
plane("Floor",[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],mf); plane("Ceiling",[(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],mc)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\II\work\scan.room2\room_v3.blend")
# check renders
from mathutils import Vector
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=14; cam.data.clip_start=0.05
try: sc.render.engine='BLENDER_EEVEE'
except: sc.render.engine='BLENDER_EEVEE_NEXT'
sc.render.resolution_x=900; sc.render.resolution_y=700
w=bpy.data.worlds['w']; w.use_nodes=True; w.node_tree.nodes['Background'].inputs['Strength'].default_value=3.0
sc.eevee.taa_render_samples=16
for k,tgt in enumerate([(-0.05,3,1.4),(3,-1.0,1.4),(-0.05,-3,1.4)]):
    cam.location=(-0.05,0,1.4); cam.rotation_euler=(Vector(tgt)-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=rf"C:\Users\II\work\scan.room2\_work\v3_{k}.png"; bpy.ops.render.render(write_still=True)
