# -*- coding: utf-8 -*-
bl_info = {
    "name": "装甲碰撞分析模拟系统",
    "author": "AI Assistant",
    "version": (10, 5),
    "blender": (3, 6, 0),
    "location": "3D View > N面板 > 装甲模拟",
    "description": "极高拟真装甲穿透、弹头与弹孔绝对同步、军火库扩充版",
    "category": "Physics",
}

import bpy
import math
import random
import platform
from bpy.props import FloatProperty, EnumProperty, PointerProperty, CollectionProperty, StringProperty, BoolProperty
from bpy.types import Panel, Operator, PropertyGroup

# ================================================================
#  【数据库】
# ================================================================
MATERIAL_KEYS = [
    ("RHA", "RHA 均质装甲钢", ""),
    ("DU", "贫铀复合装甲", ""),
    ("Tungsten", "钨合金装甲", ""),
    ("Al2O3", "氧化铝陶瓷", ""),
    ("SiC", "碳化硅陶瓷", ""),
    ("Kevlar", "芳纶凯夫拉", ""),
    ("UHMWPE", "超高分子量聚乙烯", ""),
    ("BulletproofGlass", "夹层防弹玻璃", ""),
    ("PMMA", "亚克力板", ""),
    ("Birch", "桦木板", ""),
    ("Concrete", "钢筋混凝土", ""),
    ("Granite", "花岗岩", ""),
    ("Sandbag", "沙袋", ""),
    ("Water", "水层", ""),
]

ARMOR_MATERIALS = {
    "RHA": dict(K=86, rico=70, color="#5c6670", metal=0.9, rough=0.3, trans=0.0, gap_pen=0.8),
    "DU": dict(K=50, rico=65, color="#3a3a2a", metal=0.95,rough=0.4,  trans=0.0, gap_pen=0.6),
    "Tungsten": dict(K=70, rico=68, color="#4a4d52", metal=1.0, rough=0.2,  trans=0.0, gap_pen=0.7),
    "Al2O3": dict(K=60, rico=60, color="#f0e8d8", metal=0.0, rough=0.8,  trans=0.0, gap_pen=1.5),
    "SiC": dict(K=45, rico=58, color="#3a3a3a", metal=0.0, rough=0.7,  trans=0.0, gap_pen=1.8),
    "Kevlar": dict(K=21, rico=80, color="#c4a35a", metal=0.0, rough=0.9,  trans=0.0, gap_pen=0.3),
    "UHMWPE": dict(K=18, rico=83, color="#e8e8e8", metal=0.0, rough=0.85, trans=0.0, gap_pen=0.2),
    "BulletproofGlass": dict(K=28, rico=74, color="#a8d0e0", metal=0.0, rough=0.1,  trans=0.5, gap_pen=0.4),
    "PMMA": dict(K=25, rico=78, color="#b8e0f0", metal=0.0, rough=0.05, trans=0.7, gap_pen=0.2),
    "Birch": dict(K=10, rico=82, color="#d2b48c", metal=0.0, rough=0.9,  trans=0.0, gap_pen=0.1),
    "Concrete": dict(K=21, rico=78, color="#b0b0b0", metal=0.0, rough=0.95, trans=0.0, gap_pen=0.5),
    "Granite": dict(K=15, rico=75, color="#a08070", metal=0.0, rough=0.9,  trans=0.0, gap_pen=0.6),
    "Sandbag": dict(K=3,  rico=84, color="#c8b898", metal=0.0, rough=1.0,  trans=0.0, gap_pen=2.0),
    "Water": dict(K=1.5,rico=88, color="#6090c0", metal=0.0, rough=0.0,  trans=0.9, gap_pen=1.0),
}

PROJECTILE_KEYS = [
    ("125mm_APFSDS", "125mm 尾翼稳定脱壳穿甲弹", ""),
    ("120mm_APFSDS", "120mm 尾翼稳定脱壳穿甲弹", ""),
    ("125mm_HEAT", "125mm 破甲弹 (HEAT)", ""),
    ("105mm_HESH", "105mm 碎甲弹 (HESH)", ""),
    ("155mm_HE", "155mm 高爆榴弹 (HE)", ""),
    ("76mm_AP", "76mm 舰炮穿甲弹", ""),
    ("40mm_HE", "40mm 高爆榴弹", ""),
    ("30mm_AP", "30mm 机炮穿甲弹", ""),
    ("RPG7", "RPG-7 破甲弹", ""),
    ("50_BMG", ".50 BMG (12.7mm 重机枪)", ""),
    ("338_Lapua", ".338 Lapua (8.6mm 狙击弹)", ""),
    ("762x51", "7.62×51 NATO", ""),
    ("762x39", "7.62×39mm (AK-47)", ""),
    ("556x45", "5.56×45 NATO (M16)", ""),
    ("45_ACP", ".45 ACP (11.43mm 手枪弹)", ""),
    ("22_LR", ".22 LR (5.6mm 小口径)", ""),
    ("Meteor", "陨石", ""),
    ("Ice", "冰块", ""),
    ("Hail", "冰雹", ""),
    ("Dart", "金属飞镖", ""),
    ("SteelBall", "弹弓钢珠", ""),
    ("YarnBall", "毛线球", ""),
    ("Marble", "玻璃弹珠", ""),
    ("Raindrop", "雨滴", ""),
    ("Baseball", "棒球", ""),
    ("Nuke", "核弹 (战术级)", ""),
]

PROJECTILES = {
    "125mm_APFSDS": dict(mass=5300, velocity=1750, diameter=26, shape=2.0, norm=18.0, kind="apfsds", ptype="kinetic", color=(0.75, 0.78, 0.8)),
    "120mm_APFSDS": dict(mass=5000, velocity=1700, diameter=25, shape=2.0, norm=18.0, kind="apfsds", ptype="kinetic", color=(0.75, 0.78, 0.8)),
    "125mm_HEAT": dict(mass=19000,velocity=850,  diameter=125, shape=1.5, norm=0.0,  kind="rpg",    ptype="heat",    color=(0.5, 0.6, 0.4)),
    "105mm_HESH": dict(mass=11000,velocity=730,  diameter=105, shape=0.7, norm=0.0,  kind="he",     ptype="he",      color=(0.4, 0.45, 0.2)),
    "155mm_HE": dict(mass=43000,velocity=800,  diameter=155, shape=0.6, norm=0.0,  kind="he",     ptype="he",      color=(0.4, 0.45, 0.2)),
    "76mm_AP": dict(mass=5000, velocity=900,  diameter=76,  shape=0.9, norm=10.0, kind="ap",     ptype="kinetic", color=(0.85, 0.55, 0.2)),
    "40mm_HE": dict(mass=900,  velocity=240,  diameter=40,  shape=0.7, norm=0.0,  kind="he",     ptype="he",      color=(0.4, 0.45, 0.2)),
    "30mm_AP": dict(mass=240,  velocity=1080, diameter=30,  shape=1.0, norm=8.0,  kind="ap",     ptype="kinetic", color=(0.85, 0.55, 0.2)),
    "RPG7": dict(mass=2000, velocity=300,  diameter=85,  shape=1.5, norm=0.0,  kind="rpg",    ptype="heat",    color=(0.5, 0.6, 0.4)),
    "50_BMG": dict(mass=42.0, velocity=860,  diameter=12.7, shape=1.05, norm=10.0, kind="ap",     ptype="kinetic", color=(0.8, 0.6, 0.2)),
    "338_Lapua": dict(mass=16.2, velocity=900,  diameter=8.6,  shape=1.05, norm=10.0, kind="rifle",  ptype="kinetic", color=(0.9, 0.7, 0.3)),
    "762x51": dict(mass=9.5,  velocity=830,  diameter=7.8,  shape=1.0,  norm=8.0,  kind="rifle",  ptype="kinetic", color=(0.9, 0.7, 0.3)),
    "762x39": dict(mass=8.0,  velocity=715,  diameter=7.9,  shape=0.98, norm=7.0,  kind="rifle",  ptype="kinetic", color=(0.85, 0.65, 0.25)),
    "556x45": dict(mass=4.0,  velocity=940,  diameter=5.7,  shape=1.0,  norm=8.0,  kind="rifle",  ptype="kinetic", color=(0.9, 0.7, 0.3)),
    "45_ACP": dict(mass=14.9, velocity=253,  diameter=11.4, shape=0.88, norm=3.0,  kind="pistol", ptype="kinetic", color=(0.9, 0.75, 0.3)),
    "22_LR": dict(mass=2.6,  velocity=340,  diameter=5.7,  shape=0.85, norm=4.0,  kind="rifle",  ptype="kinetic", color=(0.8, 0.7, 0.4)),
    "Meteor": dict(mass=5000, velocity=15000, diameter=100, shape=0.8, norm=0.0,  kind="meteor", ptype="kinetic", color=(0.3, 0.2, 0.15)),
    "Ice": dict(mass=100,  velocity=30,   diameter=50,  shape=0.5, norm=0.0,  kind="ice",    ptype="kinetic", color=(0.8, 0.9, 1.0)),
    "Hail": dict(mass=15,   velocity=25,   diameter=30,  shape=0.6, norm=0.0,  kind="ice",    ptype="kinetic", color=(0.7, 0.85, 1.0)),
    "Dart": dict(mass=30,   velocity=15,   diameter=8,   shape=1.5, norm=0.0,  kind="ap",     ptype="kinetic", color=(0.2, 0.2, 0.2)),
    "SteelBall": dict(mass=8,    velocity=30,   diameter=10,  shape=0.8, norm=0.0,  kind="marble", ptype="kinetic", color=(0.6, 0.6, 0.6)),
    "YarnBall": dict(mass=30,   velocity=8,    diameter=80,  shape=0.2, norm=0.0,  kind="soft",   ptype="kinetic", color=(0.8, 0.4, 0.6)),
    "Marble": dict(mass=5,    velocity=12,   diameter=16,  shape=0.7, norm=0.0,  kind="marble", ptype="kinetic", color=(0.6, 0.9, 1.0)),
    "Raindrop": dict(mass=0.05, velocity=9,    diameter=4,   shape=0.2, norm=0.0,  kind="liquid", ptype="kinetic", color=(0.4, 0.7, 1.0)),
    "Baseball": dict(mass=145,  velocity=42,   diameter=74,  shape=0.4, norm=0.0,  kind="baseball", ptype="kinetic", color=(0.95, 0.95, 0.95)),
    "Nuke": dict(mass=1e6, velocity=400,  diameter=300, shape=0.5, norm=0.0,  kind="nuke",   ptype="nuke", color=(1, 1, 1)),
}

# ================================================================
#  【UI 实时回调控制】
# ================================================================
def update_section(self, context):
    cutter = bpy.data.objects.get("SectionCutter")
    if cutter:
        armor_size_dm = self.armor_size / 10.0
        if self.show_section:
            cutter.location.y = armor_size_dm / 2.0 + 0.05 # 偏移防闪烁
        else:
            cutter.location.y = -9999.0
        context.view_layer.update()

def update_tracer(self, context):
    traj = bpy.data.objects.get("Trajectory")
    if traj:
        traj.hide_viewport = not self.show_tracer
        traj.hide_render = not self.show_tracer
        context.view_layer.update()

# ================================================================
#  【属性】
# ================================================================
class ArmorLayerProperty(PropertyGroup):
    material: EnumProperty(name="材质", items=MATERIAL_KEYS)
    thickness: FloatProperty(name="厚度(mm)", default=30.0, min=0.1)
    gap: FloatProperty(name="间隙(mm)", default=0.0, min=0.0)

class ArmorSimProperties(PropertyGroup):
    layers: CollectionProperty(type=ArmorLayerProperty, name="装甲层")
    angle: FloatProperty(name="装甲倾角", default=30.0, min=0.0, max=360.0)
    armor_size: FloatProperty(name="装甲尺寸(mm)", default=500.0, min=50.0, max=5000.0, description="装甲板的高度和宽度")
    projectile: EnumProperty(name="弹种", items=PROJECTILE_KEYS, default="125mm_APFSDS")
    
    show_section: BoolProperty(name="开启剖面", default=True, update=update_section)
    show_tracer: BoolProperty(name="显示弹道轨迹", default=True, update=update_tracer)
    
    res_outcome: StringProperty(default="等待模拟...")
    res_layers: StringProperty(default="-")
    res_depth: StringProperty(default="-")
    res_angle: StringProperty(default="-")
    res_speed: StringProperty(default="-")
    res_equiv: StringProperty(default="-")

# ================================================================
#  【材质与物理核心引擎】
# ================================================================
def hex_to_rgb(hex_str):
    return tuple(int(hex_str.lstrip("#")[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def make_material(name, mat_info):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf: return mat
    
    color_rgb = hex_to_rgb(mat_info["color"])
    mat.diffuse_color = (*color_rgb, 1.0)
    
    bsdf.inputs["Base Color"].default_value = (*color_rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = mat_info["metal"]
    bsdf.inputs["Roughness"].default_value = mat_info["rough"]
    
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = mat_info["trans"]
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = mat_info["trans"]
        
    if mat_info["trans"] > 0.1:
        mat.blend_method = 'HASHED'
        if hasattr(mat, 'shadow_method'): mat.shadow_method = 'HASHED'
        if hasattr(mat, 'use_screen_refraction'): mat.use_screen_refraction = True
        
    return mat

def compute_effective_angle(angle_deg):
    a = angle_deg % 360
    if a <= 90: return a, False
    if a <= 180: return 180 - a, False
    if a <= 270: return a - 180, True
    return 360 - a, True

def compute_simulation(layers, proj, angle_deg, armor_size_mm):
    inc, from_back = compute_effective_angle(angle_deg)
    m, v, d = proj["mass"], proj["velocity"], proj["diameter"]
    norm = proj["norm"] if inc > proj["norm"] else inc * 0.5
    eff_inc = max(0.0, inc - norm)
    cos_a = max(math.cos(math.radians(eff_inc)), 0.035)
    tan_a = math.tan(math.radians(eff_inc))

    max_x_dist = (armor_size_mm / 2.0) / tan_a if tan_a > 0.001 else 999999.0

    res = dict(outcome="stopped", penetrated_layers=0, total_depth_mm=0.0, total_phys_dist_mm=0.0,
               total_thickness_mm=sum(l.thickness for l in layers),
               v_init=v, v_final=v, incidence=inc, eff_incidence=eff_inc, layer_results=[], normalization=norm)

    if proj["ptype"] == "nuke":
        res.update(outcome="obliterated", penetrated_layers=len(layers), total_depth_mm=sum(l.thickness for l in layers), total_phys_dist_mm=max_x_dist, v_final=0.0)
        return res
    if proj["ptype"] == "he":
        res.update(outcome="penetrated", penetrated_layers=1, total_depth_mm=0.0, total_phys_dist_mm=0.0, v_final=0.0)
        return res

    calc_layers = list(reversed(layers)) if from_back else list(layers)
    cur_v = v

    for i, layer in enumerate(calc_layers):
        mat = ARMOR_MATERIALS[layer.material]
        layer_x_dist = (layer.thickness / 10.0) / cos_a
        t_eff = layer.thickness / cos_a
        
        if res["total_phys_dist_mm"] + layer_x_dist > max_x_dist:
            allowed_x = max_x_dist - res["total_phys_dist_mm"]
            actual_t = allowed_x * cos_a
            res["layer_results"].append({"status": "edge_out", "depth": actual_t, "x_dist": allowed_x})
            res["total_depth_mm"] += actual_t
            res["total_phys_dist_mm"] = max_x_dist
            res["outcome"] = "stopped" 
            break

        if proj["ptype"] == "kinetic":
            if i == 0 and proj["kind"] not in ("apfsds",) and inc > mat["rico"] + norm:
                res.update(outcome="ricochet", v_final=cur_v * 0.7)
                return res
            t_max = ((cur_v * proj["shape"] * math.sqrt(m)) / (mat["K"] * (d ** 0.75))) ** (1.333)
        elif proj["ptype"] == "heat":
            t_max = (d * 5.0) * (1.0 / mat["gap_pen"])

        if t_max >= t_eff:
            if proj["ptype"] == "kinetic":
                cur_v *= math.sqrt(max(0.0, 1.0 - t_eff / t_max))
            res["total_depth_mm"] += layer.thickness
            res["total_phys_dist_mm"] += layer_x_dist
            res["penetrated_layers"] += 1
            res["layer_results"].append({"status": "penetrated", "depth": layer.thickness, "x_dist": layer_x_dist})
        else:
            actual_t = t_max * cos_a
            actual_x = actual_t / cos_a
            res["total_depth_mm"] += actual_t
            res["total_phys_dist_mm"] += actual_x
            cur_v = 0.0
            res["layer_results"].append({"status": "stopped", "depth": actual_t, "x_dist": actual_x})
            break

        if i < len(calc_layers) - 1 and layer.gap > 0:
            gap_x_dist = (layer.gap / 10.0) / cos_a
            if res["total_phys_dist_mm"] + gap_x_dist > max_x_dist:
                res["total_phys_dist_mm"] = max_x_dist
                res["outcome"] = "stopped"
                break
            res["total_phys_dist_mm"] += gap_x_dist

    res["v_final"] = cur_v
    if res["penetrated_layers"] == len(layers): res["outcome"] = "penetrated"
    return res

# ================================================================
#  【高保真弹药生成】
# ================================================================
def build_projectile(proj):
    kind = proj["kind"]
    d = proj["diameter"] / 10.0
    r = d / 2.0
    parts = []

    if kind == "pistol":
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=r*2.5, vertices=32, location=(0, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, location=(r*1.25, 0, 0))
        head = bpy.context.active_object
        head.scale = (1.5, 1.0, 1.0)
        parts.append(head)

    elif kind == "rifle":
        body_len = r * 4.5
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=body_len, vertices=32, location=(body_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        nose_len = r * 3.5
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0, depth=nose_len, vertices=32, location=(body_len + nose_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)

    elif kind == "ap":
        body_len = r * 4.0
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=body_len, vertices=32, location=(body_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        nose_len = r * 3.0
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0, depth=nose_len, vertices=32, location=(body_len + nose_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)

    elif kind == "apfsds":
        rod_len = d * 5.0
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=rod_len, vertices=32, location=(rod_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        nose_len = r * 2.5
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0, depth=nose_len, vertices=32, location=(rod_len + nose_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        for i in range(4):
            bpy.ops.mesh.primitive_cube_add(size=1)
            fin = bpy.context.active_object
            fin.scale = (rod_len*0.3, r*1.5, 0.02)
            fin.location = (rod_len*0.15, 0, 0)
            fin.rotation_euler.x = math.radians(i * 90)
            parts.append(fin)

    elif kind == "rpg":
        body_len = d * 1.5
        bpy.ops.mesh.primitive_cylinder_add(radius=r*0.7, depth=body_len, vertices=32, location=(body_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        bpy.ops.mesh.primitive_cone_add(radius1=r*0.7, radius2=r*0.2, depth=r*1.5, vertices=32, location=(body_len + r*0.75, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        
    elif kind == "he":
        body_len = d * 2.0
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=body_len, vertices=32, location=(body_len/2, 0, 0), rotation=(0, math.pi/2, 0))
        parts.append(bpy.context.active_object)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, location=(body_len, 0, 0))
        head = bpy.context.active_object
        head.scale = (1.5, 1.0, 1.0)
        parts.append(head)

    elif kind == "liquid":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, location=(0,0,0))
        body = bpy.context.active_object
        body.scale = (2.0, 1.0, 1.0)
        parts.append(body)
    elif kind == "meteor":
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=2, location=(0,0,0))
        body = bpy.context.active_object
        for v in body.data.vertices:
            v.co += v.normal * random.uniform(-r*0.2, r*0.2)
        parts.append(body)

    else:
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=3, location=(0,0,0))
        parts.append(bpy.context.active_object)

    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = parts[0]
    obj.name = "Projectile"
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

    color_hex = f"#{int(proj['color'][0]*255):02x}{int(proj['color'][1]*255):02x}{int(proj['color'][2]*255):02x}"
    trans = 0.8 if kind in ("marble", "ice") else 0.0
    obj.data.materials.append(make_material("ProjMat", {"color": color_hex, "metal": 0.85, "rough": 0.25, "trans": trans}))
    
    return obj, obj.dimensions.x

# ================================================================
#  【关键帧插值与特效】
# ================================================================
def set_object_interpolation(obj, interp_type='BEZIER'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    fcurves = []
    if hasattr(action, "fcurves"):
        fcurves = action.fcurves
    elif hasattr(action, "layers") and action.layers:
        slot = obj.animation_data.action_slot
        if slot:
            for layer in action.layers:
                for strip in layer.strips:
                    if hasattr(strip, "channelbag"):
                        cb = strip.channelbag(slot)
                        if cb: fcurves.extend(cb.fcurves)
        else:
            for layer in action.layers:
                for strip in layer.strips:
                    if hasattr(strip, "channelbags"):
                        for cb in strip.channelbags: fcurves.extend(cb.fcurves)
    for fc in fcurves:
        for kf in fc.keyframe_points:
            kf.interpolation = interp_type
            kf.handle_left_type = 'AUTO_CLAMPED'
            kf.handle_right_type = 'AUTO_CLAMPED'

def create_spalling(loc, normal_dir, frame, count=30):
    mat = bpy.data.materials.new("SpallMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.05, 0.05, 1)
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.2, 0.0, 1)
        else:
            bsdf.inputs["Emission"].default_value = (1.0, 0.2, 0.0, 1)
        bsdf.inputs["Emission Strength"].default_value = 5.0

    nx, nz = normal_dir

    for i in range(count):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        s = bpy.context.active_object
        s.scale = (random.uniform(0.05, 0.2), random.uniform(0.05, 0.2), random.uniform(0.05, 0.2))
        s.rotation_euler = (random.random()*math.pi, random.random()*math.pi, random.random()*math.pi)
        s.data.materials.append(mat)
        
        s.scale = (0,0,0)
        s.keyframe_insert("scale", frame=frame-1)
        s.scale = (1,1,1)
        s.keyframe_insert("scale", frame=frame)
        
        speed = random.uniform(10, 30)
        vx = nx * speed + random.uniform(-8, 8)
        vy = random.uniform(-12, 12)
        vz = nz * speed + random.uniform(-8, 8)
        
        for f in range(1, 25):
            s.location = (loc[0] + vx * f/30, loc[1] + vy * f/30, loc[2] + vz * f/30 - 15*(f/30)**2)
            s.keyframe_insert("location", frame=frame+f)

def create_trajectory(points, color):
    curve_data = bpy.data.curves.new('TrajectoryCurve', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.15 
    curve_data.bevel_resolution = 6
    
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, p in enumerate(points):
        spline.points[i].co = (p[0], p[1], p[2], 1.0)
        
    obj = bpy.data.objects.new("Trajectory", curve_data)
    bpy.context.collection.objects.link(obj)
    
    obj.show_in_front = True
    
    mat = bpy.data.materials.new("TrajMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*color, 1)
        else:
            bsdf.inputs["Emission"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = 5.0
    obj.data.materials.append(mat)
    return obj

# ================================================================
#  【执行模拟】
# ================================================================
class OBJECT_OT_Run_Armor_Sim(Operator):
    bl_idname = "object.run_armor_sim"
    bl_label = "开始模拟"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.armor_sim_props
        proj = PROJECTILES[props.projectile]
        sim = compute_simulation(props.layers, proj, props.angle, props.armor_size)

        angle_rad = math.radians(props.angle)
        cos_a = abs(math.cos(angle_rad))
        sin_a = math.sin(angle_rad)
        
        o_map = {"penetrated": "[击穿]", "stopped": "[未击穿(边缘穿出/卡弹)]", "ricochet": "[跳弹]", "obliterated": "[毁灭]"}
        props.res_outcome = o_map.get(sim["outcome"], "未知")
        props.res_layers = f"{sim['penetrated_layers']} / {len(props.layers)}"
        props.res_depth = f"{sim['total_depth_mm']:.1f} / {sim['total_thickness_mm']:.1f} mm"
        
        real_flight_mm = sim["total_phys_dist_mm"] * 10.0
        props.res_equiv = f"{real_flight_mm:.1f} mm (含间隙及偏航)"
        
        props.res_angle = f"{sim['eff_incidence']:.1f}° (转正 {sim['normalization']:.1f}°)"
        props.res_speed = f"{sim['v_final']:.0f} m/s"

        # 【修复】彻底清理所有多余的场景残留物，只保留必要的相机、灯光、目标点
        keep_names = {"Camera", "CamTarget", "Ground", "KeyLight", "FillLight", "Light"}
        for obj in list(bpy.data.objects):
            if obj.name not in keep_names:
                bpy.data.objects.remove(obj, do_unlink=True)

        armor_size_dm = props.armor_size / 10.0
        total_solid = sum(l.thickness for l in props.layers)
        total_gap = sum(l.gap for l in props.layers[:-1]) if len(props.layers) > 1 else 0
        total_len = (total_solid + total_gap) / 10.0

        bpy.ops.object.empty_add(location=(0, 0, 0))
        root = bpy.context.active_object
        root.name = "ArmorRoot"

        armor_objs = []
        x_cursor = 0.0

        for i, L in enumerate(props.layers):
            t = L.thickness / 10.0
            g = L.gap / 10.0
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            obj = bpy.context.active_object
            obj.scale = (t, armor_size_dm, armor_size_dm)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            obj.location = (x_cursor + t / 2.0, 0, 0)
            m_info = ARMOR_MATERIALS[L.material]
            obj.data.materials.append(make_material(f"M_{i}_{L.material}", m_info))
            obj.parent = root
            armor_objs.append(obj)
            x_cursor += t + g

        root.rotation_euler = (0, angle_rad, 0)
        x_ent = 0.0

        proj_obj, proj_len = build_projectile(proj)
        
        proj_obj.rotation_euler = (0, 0, 0)
        proj_obj.keyframe_insert("rotation_euler", frame=1)
        proj_obj.keyframe_insert("rotation_euler", frame=25)
        
        start_tip = x_ent - 30.0
        start_center = start_tip - proj_len / 2.0
        hit_tip = x_ent
        hit_center = hit_tip - proj_len / 2.0
        
        proj_obj.location = (start_center, 0, 0)
        proj_obj.keyframe_insert("location", frame=1)
        proj_obj.location = (hit_center, 0, 0)
        proj_obj.keyframe_insert("location", frame=25)

        traj_points = [(start_tip, 0, 0), (hit_tip, 0, 0)]

        bpy.ops.mesh.primitive_cylinder_add(radius=proj["diameter"] / 20.0, depth=2000.0, vertices=32)
        drill = bpy.context.active_object
        drill.name = "DrillCutter"
        drill.rotation_euler = (0, math.pi / 2, 0)
        drill.hide_render = True
        drill.hide_viewport = True
        drill.hide_set(True) 
        
        mat_drill = bpy.data.materials.new("DrillMat")
        mat_drill.use_nodes = True
        mat_drill.node_tree.nodes.clear()
        trans_node = mat_drill.node_tree.nodes.new('ShaderNodeBsdfTransparent')
        out_node = mat_drill.node_tree.nodes.new('ShaderNodeOutputMaterial')
        mat_drill.node_tree.links.new(trans_node.outputs[0], out_node.inputs[0])
        drill.data.materials.append(mat_drill)

        from_back_flag = compute_effective_angle(props.angle)[1]
        for i, layer_res in enumerate(sim["layer_results"]):
            orig_idx = len(props.layers) - 1 - i if from_back_flag else i
            if orig_idx < 0 or orig_idx >= len(armor_objs): continue
            mod_damage = armor_objs[orig_idx].modifiers.new(name=f"Damage_{i}", type='BOOLEAN')
            mod_damage.operation = 'DIFFERENCE'
            mod_damage.object = drill
            mod_damage.solver = 'EXACT'
            if layer_res["status"] in ("stopped", "edge_out"): break

        drill.location = (start_tip - 1000.0, 0, 0)
        drill.keyframe_insert("location", frame=1)
        drill.location = (hit_tip - 1000.0, 0, 0)
        drill.keyframe_insert("location", frame=25)

        if sim["outcome"] == "penetrated":
            end_tip = x_ent + sim["total_phys_dist_mm"] + proj_len
            end_center = end_tip - proj_len / 2.0
            fly_tip = end_tip + 40.0
            fly_center = fly_tip - proj_len / 2.0
            
            proj_obj.location = (end_center, 0, 0)
            proj_obj.keyframe_insert("location", frame=45)
            proj_obj.location = (fly_center, 0, 0)
            proj_obj.keyframe_insert("location", frame=70)
            
            traj_points.extend([(end_tip, 0, 0), (fly_tip, 0, 0)])
            
            drill.location = (end_tip - 1000.0, 0, 0)
            drill.keyframe_insert("location", frame=45)
            drill.location = (fly_tip - 1000.0, 0, 0)
            drill.keyframe_insert("location", frame=70)
            
            back_x = sim["total_phys_dist_mm"] * cos_a
            back_z = -sim["total_phys_dist_mm"] * sin_a
            n_x = cos_a
            n_z = -sin_a
            create_spalling((back_x, 0, back_z), (n_x, n_z), 45)
            
        elif sim["outcome"] == "stopped":
            end_tip = x_ent + sim["total_phys_dist_mm"]
            end_center = end_tip - proj_len / 2.0
            
            proj_obj.location = (end_center, 0, 0)
            proj_obj.keyframe_insert("location", frame=45)
            traj_points.append((end_tip, 0, 0))
            
            drill.location = (end_tip - 1000.0, 0, 0)
            drill.keyframe_insert("location", frame=45)
            
        elif sim["outcome"] == "ricochet":
            drill.location = (hit_tip - 1000.0, 0, 0)
            drill.keyframe_insert("location", frame=70)
            
            hit_x = hit_tip
            n_x = -cos_a
            n_z = sin_a
            t_x = sin_a
            t_z = cos_a
            
            px, pz = hit_x + t_x * 6.0 + n_x * 1.0, t_z * 6.0 + n_z * 1.0
            proj_obj.location = (px, 0, pz); proj_obj.keyframe_insert("location", frame=30)
            traj_points.append((px, 0, pz))
            
            px, pz = hit_x + t_x * 14.0 + n_x * 4.0, t_z * 14.0 + n_z * 4.0
            proj_obj.location = (px, 0, pz); proj_obj.keyframe_insert("location", frame=38)
            traj_points.append((px, 0, pz))
            
            px, pz = hit_x + t_x * 25.0 + n_x * 12.0, t_z * 25.0 + n_z * 12.0
            proj_obj.location = (px, 0, pz); proj_obj.keyframe_insert("location", frame=50)
            traj_points.append((px, 0, pz))
            
            px, pz = hit_x + t_x * 40.0 + n_x * 25.0, t_z * 40.0 + n_z * 25.0
            proj_obj.location = (px, 0, pz); proj_obj.keyframe_insert("location", frame=70)
            traj_points.append((px, 0, pz))

            rot_y = -math.atan2(t_z, t_x)
            proj_obj.rotation_euler = (0, 0, 0)
            proj_obj.keyframe_insert("rotation_euler", frame=25)
            proj_obj.rotation_euler = (0, rot_y * 0.3, 0)
            proj_obj.keyframe_insert("rotation_euler", frame=30)
            proj_obj.rotation_euler = (0, rot_y * 0.8, 0)
            proj_obj.keyframe_insert("rotation_euler", frame=38)
            proj_obj.rotation_euler = (math.radians(20), rot_y, math.radians(15))
            proj_obj.keyframe_insert("rotation_euler", frame=50)
            proj_obj.rotation_euler = (math.radians(60), rot_y + math.radians(45), math.radians(45))
            proj_obj.keyframe_insert("rotation_euler", frame=70)

        traj_obj = create_trajectory(traj_points, proj["color"])
        traj_obj.hide_viewport = not props.show_tracer
        traj_obj.hide_render = not props.show_tracer

        set_object_interpolation(proj_obj, 'BEZIER')
        set_object_interpolation(drill, 'BEZIER')
        
        self.create_sparks((x_ent, 0, 0), 25, sim["outcome"], angle_rad)
        self.create_ui_text(sim, props, proj, total_len)

        bpy.ops.mesh.primitive_cube_add(size=2.0)
        cutter = bpy.context.active_object
        cutter.name = "SectionCutter"
        cutter.scale = (total_len + 10.0, armor_size_dm / 2, armor_size_dm / 2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        if props.show_section:
            cutter.location = (0, armor_size_dm / 2.0 + 0.05, 0) # 偏移防闪烁
        else:
            cutter.location = (0, -9999, 0)
            
        cutter.hide_viewport = True
        cutter.hide_render = True
        cutter.parent = root

        for obj in armor_objs:
            mod_section = obj.modifiers.new(name="Section", type='BOOLEAN')
            mod_section.operation = 'DIFFERENCE'
            mod_section.object = cutter
            mod_section.solver = 'EXACT'

        # 锁定第45帧：只固化剖面布尔（Section），弹孔布尔（Damage）保留为活动
        context.scene.frame_set(45)
        context.view_layer.update()
        for obj in armor_objs:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # 临时禁用 Damage 布尔，避免被连带 apply 掉
            for mod in obj.modifiers:
                if mod.name.startswith("Damage"):
                    mod.show_viewport = False

            # 只应用剖面布尔
            for mod in list(obj.modifiers):
                if mod.name == "Section":
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except Exception:
                        pass

            # 恢复弹孔布尔，保持活动，随炮弹动画实时切割
            for mod in obj.modifiers:
                if mod.name.startswith("Damage"):
                    mod.show_viewport = True

        bpy.data.objects.remove(cutter)
        # 注意：不删除 drill，让 Damage 布尔在动画播放中实时切割弹孔

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'

        cam = bpy.data.objects.get("Camera")
        if cam:
            cam.location = (-total_len*0.8 - 15, -40, 15)
            target = bpy.data.objects.get("CamTarget")
            if target: target.location = (total_len / 2.0, 0, 0)

        context.scene.frame_set(1)
        bpy.ops.screen.animation_play()
        return {'FINISHED'}

    def create_ui_text(self, sim, props, proj, total_len):
        if "UI_ResultPanel" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects["UI_ResultPanel"], do_unlink=True)

        loc = (-20, -10, 20)
        bpy.ops.object.text_add(location=loc)
        txt = bpy.context.active_object
        txt.name = "UI_ResultPanel"
        
        color_map = {
            "[击穿]": (1.0, 0.2, 0.2, 1),
            "[未击穿(边缘穿出/卡弹)]": (0.8, 0.8, 0.8, 1),
            "[跳弹]": (1.0, 0.8, 0.1, 1),
            "[毁灭]": (1.0, 0.1, 1.0, 1)
        }
        c = color_map.get(props.res_outcome, (1, 1, 1, 1))
        
        txt.data.body = (
            f"【实弹物理分析】\n"
            f"弹种：{props.projectile}\n"
            f"结果：{props.res_outcome}\n"
            f"击穿层数：{props.res_layers}\n"
            f"法向穿透：{props.res_depth}\n"
            f"真实飞行：{props.res_equiv}\n"
            f"有效入射角：{props.res_angle}\n"
            f"残余速度：{props.res_speed}"
        )
        txt.data.size = 0.8
        txt.data.align_x = 'LEFT'
        
        if platform.system() == "Windows":
            for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
                try:
                    txt.data.font = bpy.data.fonts.load(fp)
                    break
                except: pass
                
        mat = bpy.data.materials.new("TxtMat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = c
            else:
                bsdf.inputs["Emission"].default_value = c
            bsdf.inputs["Emission Strength"].default_value = 2.0
        txt.data.materials.append(mat)
        
        if bpy.context.scene.camera:
            txt.constraints.new('TRACK_TO').target = bpy.context.scene.camera

    def create_sparks(self, loc, frame, outcome, angle_rad):
        for i in range(30):
            bpy.ops.mesh.primitive_ico_sphere_add(radius=0.15, subdivisions=1, location=loc)
            s = bpy.context.active_object
            mat = bpy.data.materials.new(f"Spk_{i}")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                if "Emission Color" in bsdf.inputs:
                    bsdf.inputs["Emission Color"].default_value = (1.0, 0.6, 0.1, 1)
                else:
                    bsdf.inputs["Emission"].default_value = (1.0, 0.6, 0.1, 1)
                bsdf.inputs["Emission Strength"].default_value = 15.0
            s.data.materials.append(mat)
            s.scale = (0, 0, 0)
            s.keyframe_insert("scale", frame=frame - 1)
            s.scale = (1, 1, 1)
            s.keyframe_insert("scale", frame=frame)

            if outcome == "ricochet":
                vx = -random.uniform(10, 20)
                vz = random.uniform(10, 20)
            else:
                vx = random.uniform(-15, 5)
                vz = random.uniform(5, 20)
                
            vy = random.uniform(-10, 10) 
                
            for f in range(1, 15):
                s.location = (loc[0] + vx * f / 30, loc[1] + vy * f / 30, loc[2] + vz * f / 30 - 12 * (f / 30) ** 2)
                s.scale = (1 - f / 15, 1 - f / 15, 1 - f / 15)
                s.keyframe_insert("location", frame=frame + f)
                s.keyframe_insert("scale", frame=frame + f)

# ================================================================
#  【注册】
# ================================================================
class OBJECT_OT_Add_Layer(Operator):
    bl_idname = "object.add_armor_layer"
    bl_label = "添加装甲层"
    def execute(self, context):
        context.scene.armor_sim_props.layers.add()
        return {'FINISHED'}

class OBJECT_OT_Remove_Layer(Operator):
    bl_idname = "object.remove_armor_layer"
    bl_label = "删除末层"
    def execute(self, context):
        layers = context.scene.armor_sim_props.layers
        if len(layers) > 1:
            layers.remove(len(layers) - 1)
        return {'FINISHED'}

class VIEW3D_PT_ArmorSim(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = '装甲模拟'
    bl_label = "拟真弹道控制台"

    def draw(self, context):
        layout = self.layout
        props = context.scene.armor_sim_props
        box = layout.box()
        box.label(text="装甲堆叠与尺寸")
        box.prop(props, "armor_size", text="迎弹面积(mm)")
        
        for i, L in enumerate(props.layers):
            row = box.row(align=True)
            row.prop(L, "material", text=f"层 {i+1}")
            row2 = box.row(align=True)
            row2.prop(L, "thickness", text="厚度(mm)")
            row2.prop(L, "gap", text="间隙(mm)")
        row_btn = box.row(align=True)
        row_btn.operator("object.add_armor_layer", text="+ 添加")
        row_btn.operator("object.remove_armor_layer", text="- 删除")

        box = layout.box()
        box.label(text="弹道与视图")
        box.prop(props, "projectile", text="撞击物")
        box.prop(props, "angle", text="装甲倾角(0-360度)", slider=True)
        
        row_view = box.row(align=True)
        row_view.prop(props, "show_section", text="开启装甲剖面")
        row_view.prop(props, "show_tracer", text="显示曳光轨迹")

        layout.operator("object.run_armor_sim", text="开火模拟", icon='PLAY')

classes = (ArmorLayerProperty, ArmorSimProperties, OBJECT_OT_Run_Armor_Sim, OBJECT_OT_Add_Layer, OBJECT_OT_Remove_Layer, VIEW3D_PT_ArmorSim)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.armor_sim_props = PointerProperty(type=ArmorSimProperties)

    def init_defaults():
        props = bpy.context.scene.armor_sim_props
        if not props.layers:
            l1 = props.layers.add()
            l1.material = "RHA"
            l1.thickness = 200.0
            l2 = props.layers.add()
            l2.material = "Kevlar"
            l2.thickness = 200.0
            l2.gap = 100.0
    bpy.app.timers.register(init_defaults, first_interval=0.1)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.armor_sim_props

if __name__ == "__main__":
    register()