import bpy, os, json, numpy as np
from mathutils import Matrix
SC=r"C:/Users/II/AppData/Local/Temp/claude/C--Users-II-work-scan-room2/20838652-8a07-44d6-87fd-7ccc2bd27c02/scratchpad"
src=r"C:\Users\II\work\scan.room2"
files=sorted(f for f in os.listdir(src) if f.endswith('.glb'))
t1=json.load(open(SC+"/t1.json")); ob=json.load(open(SC+"/objs.json"))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
def coll(n,hide=False):
    c=bpy.data.collections.new(n); sc.collection.children.link(c); return c
def bring(i,cname,name,M,hide=False):
    before=set(sc.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(src,files[i]))
    new=[o for o in sc.objects if o not in before]
    c=bpy.data.collections.get(cname) or coll(cname)
    roots=[o for o in new if o.parent is None]
    for o in new:
        for k in list(o.users_collection): k.objects.unlink(o)
        c.objects.link(o)
    for r in roots:
        r.matrix_world=Matrix(M)@r.matrix_world
        r.name=name
    for o in new:
        if o.type=='MESH' and hide: o.hide_viewport=o.hide_render=True
    return new
def mat(s,R,t):
    M=np.eye(4); M[:3,:3]=s*np.array(R); M[:3,3]=t; return M.tolist()
bring(0,"Room_Polycam","Room_Polycam",np.eye(4).tolist())
bring(1,"Room_Scaniverse_aligned_(hidden)","Room_Scaniverse",mat(t1['s'],t1['R'],t1['t']),hide=True)
names={2:"Shelf_Scaniverse",3:"Cabinet_books",4:"Cabinet_side",5:"Wall_pictures_shelf"}
for i,n in names.items():
    bring(i,"Objects",n,mat(1,ob[str(i)]['R'],ob[str(i)]['t']))
w=bpy.data.worlds.new('w'); w.color=(0.8,0.8,0.8); sc.world=w
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\II\work\scan.room2\room.blend")
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); cam.data.type='ORTHO'; cam.data.ortho_scale=5.5
cam.location=(-0.27,0.26,3); cam.data.clip_start=2.0; sc.camera=cam
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='FLAT'; sc.display.shading.color_type='TEXTURE'
sc.render.resolution_x=800; sc.render.resolution_y=800; sc.render.filepath=r"C:\Users\II\work\scan.room2\_work\final_top.png"; bpy.ops.render.render(write_still=True)
import mathutils
cam.data.type='PERSP'; cam.data.clip_start=0.1
for k,(loc,rot) in enumerate([((-1.2,-1.8,-0.2),(1.5,0,-0.55)),((0.9,2.3,-0.3),(1.55,0,3.3))]):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=rf"C:\Users\II\work\scan.room2\_work\final_in{k}.png"; bpy.ops.render.render(write_still=True)
