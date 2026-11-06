from isaaclab.utils import configclass

from robot_lab.tasks.legbot.rsl_rl_cfg import LegbotMoECTSRunnerCfg


@configclass
class ZSL1WPiperFixedRunnerCfg(LegbotMoECTSRunnerCfg):
    experiment_name = "zsl1w_piper_fixed_moe_cts"
