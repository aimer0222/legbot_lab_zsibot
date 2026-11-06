"""Retarget Legbot's CTS task to the 16-DOF ZSL1W with fixed Piper payload.

Uses the Isaac Lab 2.3 API installed in this project. The upstream ZSL1W
configuration supplies the stance, actuator gains and action scales, but its
newer PhysX/Newton API and policy layout are intentionally not imported.
"""
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass

from robot_lab.assets.zsl1w_piper import ALL_JOINT_NAMES, LEG_JOINT_NAMES, WHEEL_JOINT_NAMES, ZSL1W_PIPER_FIXED_CFG
from robot_lab.tasks.legbot.env_cfg import ALL_JOINT_NAMES as LEGBOT_ALL_JOINT_NAMES
from robot_lab.tasks.legbot.env_cfg import LegbotEnvCfg


ENTITY_NAMES = dict(zip(LEGBOT_ALL_JOINT_NAMES, ALL_JOINT_NAMES)) | {
    "base": "BASE_LINK",
    "^(?!.*base).*": "^(?!BASE_LINK$).*",
    ".*_foot": ".*_FOOT_LINK",
    ".*_thigh|.*_calf": ".*_(HIP|KNEE)_LINK",
    ".*_hip_joint": ".*_ABAD_JOINT",
    ".*_(thigh|calf)_joint": ".*_(HIP|KNEE)_JOINT",
}


def _retarget(value):
    """Retarget every entity selector, including nested reward/observation params."""
    if isinstance(value, SceneEntityCfg):
        for field in ("joint_names", "body_names"):
            names = getattr(value, field)
            if isinstance(names, str):
                setattr(value, field, ENTITY_NAMES.get(names, names))
            elif names is not None:
                setattr(value, field, [ENTITY_NAMES.get(name, name) for name in names])
    elif isinstance(value, dict):
        for child in value.values():
            _retarget(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            _retarget(child)


@configclass
class ZSL1WPiperFixedEnvCfg(LegbotEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.robot = ZSL1W_PIPER_FIXED_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        self.scene.height_scanner.prim_path = "{ENV_REGEX_NS}/Robot/BASE_LINK"
        self.scene.height_scanner_small.prim_path = "{ENV_REGEX_NS}/Robot/BASE_LINK"

        for group in (self.observations.policy, self.observations.single_obs, self.observations.critic,
                      self.rewards, self.events, self.terminations):
            for term in vars(group).values():
                if hasattr(term, "params"):
                    _retarget(term.params)

        # Keep FL/FR/RL/RR interleaving required by ActionManagerLegbot and CTS.
        self.actions.joint_pos.joint_names = LEG_JOINT_NAMES.copy()
        self.actions.joint_pos.scale = {".*_ABAD_JOINT": 0.125, ".*_(HIP|KNEE)_JOINT": 0.25}
        self.actions.wheel_vel.joint_names = WHEEL_JOINT_NAMES.copy()
        self.actions.wheel_vel.scale = 5.0
        self.actions.wheel_vel.clip = {".*": (-28.0, 28.0)}

        # Stance wheel bottoms are about 0.38 m below BASE_LINK (0.8/-1.5 rad).
        self.rewards.base_height_l2.params["target_height"] = 0.38
        self.rewards.track_lin_vel_xy_exp.weight = 3.0
        self.rewards.track_ang_vel_z_exp.weight = 1.5
        self.rewards.joint_torques_l2.weight = -2.5e-5
        self.rewards.joint_torques_l2.params["asset_cfg"].joint_names = LEG_JOINT_NAMES.copy()
        self.rewards.joint_acc_l2.weight = -2.5e-7
        self.rewards.joint_acc_l2.params["asset_cfg"].joint_names = LEG_JOINT_NAMES.copy()

        # Wheel radius/speed and the 4.7 kg arm call for a gentler initial course.
        self.scene.terrain.max_init_terrain_level = 2
        terrain = self.scene.terrain.terrain_generator
        terrain.sub_terrains["stairs_up"].step_height_range = (0.03, 0.18)
        terrain.sub_terrains["stairs_down"].step_height_range = (0.03, 0.18)
        terrain.sub_terrains["obstacles"].obstacle_height_range = (0.03, 0.18)
        command = self.commands.base_velocity
        command.ranges.lin_vel_x = (-0.5, 0.5)
        command.ranges.lin_vel_y = (-0.3, 0.3)
        command.ranges.ang_vel_yaw = (-0.8, 0.8)
        command.command_range_curriculum = [
            {"iter": 20000, "lin_vel_x": [-1.0, 1.0], "lin_vel_y": [-0.4, 0.4], "ang_vel_yaw": [-1.0, 1.0]},
            {"iter": 50000, "lin_vel_x": [-1.5, 1.5], "lin_vel_y": [-0.5, 0.5], "ang_vel_yaw": [-1.5, 1.5]},
        ]
        command.terrain_max_command_ranges = {
            name: {"lin_vel_x": [-1.5, 1.5] if name == "flat" else [-1.0, 1.0],
                   "lin_vel_y": [-0.5, 0.5], "ang_vel_yaw": [-1.5, 1.5]}
            for name in terrain.sub_terrains
        }
