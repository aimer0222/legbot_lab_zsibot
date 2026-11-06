"""Generate the self-contained, zero-pose fixed-arm locomotion URDF.

Run from any directory with Python's standard library. The assembly source is
left untouched. All six arm axes and three gripper axes are locked at zero;
fixed-joint merging in Isaac Lab retains their mass, inertia and geometry.
"""
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "resources/zsl1w/urdf/zsl1w_inspection_piper.urdf"
OUTPUT = SOURCE.with_name("zsl1w_inspection_piper_fixed.urdf")
ARM_JOINTS = {f"piper_joint{i}" for i in range(1, 7)} | {
    "piper_gripper", "piper_gripper_joint1", "piper_gripper_joint2",
}


def build():
    tree = ET.parse(SOURCE)
    root = tree.getroot()
    root.set("name", "zsl1w_inspection_piper_fixed")
    locked = set()
    for joint in root.findall("joint"):
        if joint.get("name") in ARM_JOINTS:
            limits = joint.find("limit")
            if not float(limits.get("lower")) <= 0.0 <= float(limits.get("upper")):
                raise ValueError(f"Zero pose outside limits: {joint.get('name')}")
            joint.set("type", "fixed")
            for child in list(joint):
                if child.tag in {"axis", "limit", "mimic", "dynamics", "safety_controller"}:
                    joint.remove(child)
            locked.add(joint.get("name"))
    if locked != ARM_JOINTS:
        raise ValueError(f"Missing arm joints: {ARM_JOINTS - locked}")
    for mesh in root.iter("mesh"):
        name = mesh.get("filename").replace("../../../piper/meshes/", "../meshes/piper/")
        if not (OUTPUT.parent / name).is_file():
            raise FileNotFoundError(f"Missing mesh: {name}")
        mesh.set("filename", name)
    active = [j for j in root.findall("joint") if j.get("type") != "fixed"]
    if len(active) != 16:
        raise ValueError(f"Expected 16 locomotion joints, got {len(active)}")
    if list(root.iter("mimic")):
        raise ValueError("Fixed-arm model must not contain mimic joints")
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
    mass = sum(float(m.get("value")) for m in root.findall("link/inertial/mass"))
    print(f"Generated {OUTPUT}: {len(active)} active joints, {len(locked)} locked axes, {mass:.9f} kg")


if __name__ == "__main__":
    build()
