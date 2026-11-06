"""ZSL1W inspection quadruped with Piper and gripper rigidly fixed at zero."""
import isaaclab.sim as sim_utils
from isaaclab.actuators import DCMotorCfg, ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg

from robot_lab.assets import ISAACLAB_ASSETS_DATA_DIR

# Motor/observation order: FL, FR, RL, RR. URDF names use FBL/FAR/RBL/RAR.
LEG_PREFIXES = ("FBL", "FAR", "RBL", "RAR")
LEG_JOINT_NAMES = [f"{leg}_{axis}_JOINT" for leg in LEG_PREFIXES for axis in ("ABAD", "HIP", "KNEE")]
WHEEL_JOINT_NAMES = [f"{leg}_FOOT_JOINT" for leg in LEG_PREFIXES]
ALL_JOINT_NAMES = [
    f"{leg}_{axis}_JOINT" for leg in LEG_PREFIXES for axis in ("ABAD", "HIP", "KNEE", "FOOT")
]

ZSL1W_PIPER_FIXED_CFG = ArticulationCfg(
    spawn=sim_utils.UrdfFileCfg(
        asset_path=f"{ISAACLAB_ASSETS_DATA_DIR}/zsl1w/urdf/zsl1w_inspection_piper_fixed.urdf",
        fix_base=False,
        merge_fixed_joints=True,
        self_collision=False,
        replace_cylinders_with_capsules=False,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=4,
        ),
        joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
            gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=0.0, damping=0.0),
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.40),
        joint_pos={".*_ABAD_JOINT": 0.0, ".*_HIP_JOINT": 0.8, ".*_KNEE_JOINT": -1.5, ".*_FOOT_JOINT": 0.0},
        joint_vel={".*": 0.0},
    ),
    soft_joint_pos_limit_factor=0.9,
    actuators={
        "legs": DCMotorCfg(
            joint_names_expr=[".*_(ABAD|HIP|KNEE)_JOINT"],
            effort_limit=28.0,
            saturation_effort=28.0,
            velocity_limit=28.0,
            velocity_limit_sim=28.0,
            stiffness=20.0,
            damping=0.7,
            friction=0.0,
        ),
        "wheels": ImplicitActuatorCfg(
            joint_names_expr=WHEEL_JOINT_NAMES,
            effort_limit_sim=28.0,
            velocity_limit_sim=28.0,
            stiffness=0.0,
            damping=0.7,
            friction=0.0,
        ),
    },
)
