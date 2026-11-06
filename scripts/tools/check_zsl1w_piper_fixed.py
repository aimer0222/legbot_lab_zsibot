"""Check fixed-arm physics, action routing, observations and resets in Isaac Lab.

Example: isaaclab.sh -p scripts/tools/check_zsl1w_piper_fixed.py --headless
"""
import argparse
import math
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(line_buffering=True)

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--num_envs", type=int, default=16)
parser.add_argument("--steps", type=int, default=100)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)

import gymnasium as gym
import torch
from pxr import Usd, UsdPhysics

import robot_lab.tasks  # noqa: F401
from robot_lab.assets.zsl1w_piper import ALL_JOINT_NAMES, LEG_JOINT_NAMES, WHEEL_JOINT_NAMES
from robot_lab.tasks.legbot.env_cfg import LegbotEnvCfg
from robot_lab.tasks.zsl1w_piper.env_cfg import ZSL1WPiperFixedEnvCfg


def main():
    cfg = ZSL1WPiperFixedEnvCfg()
    original = LegbotEnvCfg()
    assert original.scene.height_scanner.prim_path.endswith("/base")
    assert original.rewards.base_height_l2.params["target_height"] == 0.49
    assert original.actions.wheel_vel.scale == 20.0
    cfg.scene.num_envs = args.num_envs
    cfg.seed = 42
    cfg.sim.device = args.device
    # Measure nominal imported mass without domain randomization.
    cfg.events.randomize_rigid_body_mass_base = None
    cfg.events.randomize_rigid_body_mass_others = None
    cfg.scene.terrain.terrain_generator.num_rows = 3
    cfg.scene.terrain.terrain_generator.num_cols = 10
    env = gym.make("RobotLab-ZSL1W-Piper-Fixed-v0", cfg=cfg)
    try:
        base = env.unwrapped
        robot = base.scene["robot"]
        assert robot.num_joints == 16, robot.joint_names
        assert set(robot.joint_names) == set(ALL_JOINT_NAMES)
        assert base.action_manager.total_action_dim == 16
        assert "BASE_LINK" in robot.body_names
        assert all(name in robot.body_names for name in ("FL_FOOT_LINK", "FR_FOOT_LINK", "RL_FOOT_LINK", "RR_FOOT_LINK"))
        mass = float(robot.root_physx_view.get_masses()[0].sum())
        nominal = sum(float(m.get("value")) for m in ET.parse(cfg.scene.robot.spawn.asset_path).findall("link/inertial/mass"))
        assert math.isclose(mass, nominal, abs_tol=0.01), (mass, nominal)
        root = robot.root_physx_view.prim_paths[0]
        prim = base.scene.stage.GetPrimAtPath(root) if hasattr(base.scene, "stage") else None
        if prim is None:
            import isaaclab.sim as sim_utils
            prim = sim_utils.get_current_stage().GetPrimAtPath(root)
        assert not any(p.IsA(UsdPhysics.RevoluteJoint) and p.GetName().startswith("piper_") for p in Usd.PrimRange(prim))
        obs, _ = env.reset()
        assert obs["policy"].shape == (args.num_envs, 228)
        assert obs["single_obs"].shape == (args.num_envs, 57)
        leg_ids, _ = robot.find_joints(LEG_JOINT_NAMES, preserve_order=True)
        wheel_ids, _ = robot.find_joints(WHEEL_JOINT_NAMES, preserve_order=True)
        action = torch.zeros(args.num_envs, 16, device=base.device)
        action[:, 3::4] = 0.25
        for step in range(args.steps):
            if step == args.steps // 2:
                obs, _ = env.reset()
            obs, reward, terminated, truncated, _ = env.step(action)
            assert all(torch.isfinite(value).all() for value in obs.values())
            assert torch.isfinite(reward).all() and torch.isfinite(robot.data.joint_pos).all()
            assert torch.count_nonzero(obs["single_obs"][:, 12:25:4]) == 0
            assert torch.allclose(robot.data.joint_pos_target[:, leg_ids], base.action_manager.get_term("joint_pos").processed_actions)
            assert torch.allclose(robot.data.joint_vel_target[:, wheel_ids], torch.full_like(robot.data.joint_vel[:, wheel_ids], 1.25))
        print(f"ZSL1W_CHECK_PASSED: {robot.num_joints} DOF, mass={mass:.9f} kg, "
              f"policy={tuple(obs['policy'].shape)}, critic={tuple(obs['critic'].shape)}, "
              f"single_obs={tuple(obs['single_obs'].shape)}, steps={args.steps}; reset/action routing/finite checks passed")
    finally:
        env.close()


if __name__ == "__main__":
    main()
    launcher.app.close()
