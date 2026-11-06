"""Fixed-arm ZSL1W locomotion tasks using the project's MoE-CTS pipeline."""
import gymnasium as gym

gym.register(
    id="RobotLab-ZSL1W-Piper-Fixed-v0",
    entry_point="robot_lab.tasks.legbot.env.legbot_env:LegbotEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.env_cfg:ZSL1WPiperFixedEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.rsl_rl_cfg:ZSL1WPiperFixedRunnerCfg",
    },
)
