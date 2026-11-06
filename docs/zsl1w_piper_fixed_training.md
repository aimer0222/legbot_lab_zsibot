# ZSL1W 固定机械臂轮足训练

任务名：`RobotLab-ZSL1W-Piper-Fixed-v0`。沿用项目的训练入口和 MoE-CTS 算法，单独注册任务、资产和实验目录。原来的 `RobotLab-Legbot-v0` 配置保持原样。

## 原任务的训练链路

1. `scripts/rsl_rl/train.py` 启动 Isaac Sim，通过 Gym 注册信息和 Hydra 加载环境、算法配置；命令行覆盖并行环境数、迭代数、运行名。
2. `tasks/legbot/env_cfg.py` 定义 ManagerBased 场景、地形、速度指令、观测、动作、奖励、随机化和课程。物理步长 0.005 秒，动作降采样 4，因此策略运行频率为 50 Hz；单局最长 25 秒。
3. `tasks/legbot/env/legbot_env.py` 使用 `ActionManagerLegbot`，将 16 维策略输出按每条腿的“三个位置动作 + 一个轮速动作”拆分。四腿顺序为 FL、FR、RL、RR。
4. `LegbotObservationManager` 保证策略历史最后一帧与 CTS 单帧观测一致，并将轮子位置观测连同噪声清零。单帧 57 维，四帧历史 228 维；critic 295 维，额外使用机身线速度、关节加速度、力矩、轮接触力和地形高度。
5. `tasks/legbot/rsl_rl_cfg.py` 选择 `OnPolicyRunnerCTS`、`ActorCriticMoECTS` 和 `MoECTS`；8 个专家，32 维潜变量，teacher 环境比例 0.75。每次迭代每环境采样 24 个策略步，PPO 更新 5 个 epoch、4 个 minibatch。`max_iterations` 是训练迭代数；2048 个环境每迭代产生 49152 个样本。

原资产使用 W1W 的小写关节名、左右不同符号的默认腿姿、最高 120/175.38 Nm 的腿部力矩、20 倍轮速动作和 0.49 m 高度目标。这些参数不能直接用于 ZSL1W。

## 模型与机械臂固定方法

源装配：`resources/zsl1w/urdf/zsl1w_inspection_piper.urdf`。

训练资产：`resources/zsl1w/urdf/zsl1w_inspection_piper_fixed.urdf`。

将 `piper_joint1`～`piper_joint6`、`piper_gripper` 和两指从动关节改为 fixed，固定于原模型的零位、夹爪闭合。删除这些关节的运动轴、限位和 mimic 描述；所有连杆的惯量、质量、视觉和碰撞几何保留。`fix_base=False`，底盘仍然浮动，机械臂随底盘运动。

启用 `merge_fixed_joints=True`，将固定上装、机械臂和传感器并入对应刚体；这不会丢弃机械臂的负载。源 URDF 声明总质量 **26.329130015 kg**，其中机械臂含夹爪 **4.7 kg**。随机化前的导入质量由检查脚本核对；训练期间继承原任务的质量和重心随机化。

源 URDF 的 `../../../piper/meshes/` 在本项目内没有对应文件。已从本机 `WMP_Payload/legged_lab/source/legged_lab/legged_lab/data/Robots/piper/meshes/` 复制其实际引用的 22 个网格到 `resources/zsl1w/meshes/piper/`。生成的训练 URDF 使用项目内相对路径，不依赖该外部目录；源装配文件保持原样。

重新生成固定臂模型：

```bash
python3 scripts/tools/prepare_zsl1w_piper_fixed.py
```

该脚本只依赖 Python 标准库，会检查网格文件、固定轴完整性和剩余 16 个活动关节。若改变固定臂姿态，应将对应关节变换先烘焙到 URDF origin，再固定；当前脚本仅生成零位。

## 关节及配置适配

| 物理位置 | URDF 前缀 | 三个腿部位置关节 | 轮速关节 |
| --- | --- | --- | --- |
| FL 左前 | FBL | FBL_ABAD/HIP/KNEE_JOINT | FBL_FOOT_JOINT |
| FR 右前 | FAR | FAR_ABAD/HIP/KNEE_JOINT | FAR_FOOT_JOINT |
| RL 左后 | RBL | RBL_ABAD/HIP/KNEE_JOINT | RBL_FOOT_JOINT |
| RR 右后 | RAR | RAR_ABAD/HIP/KNEE_JOINT | RAR_FOOT_JOINT |

上游列表先 FAR、再 FBL；本任务按照本项目动作管理器的顺序，统一使用 **FBL、FAR、RBL、RAR**，动作和观测每腿四维交错。每条腿的顺序为 ABAD、HIP、KNEE、FOOT。机械臂没有策略动作或关节观测。

| 项目 | 新任务配置 |
| --- | --- |
| 初始位置 | base 高度 0.40 m |
| 默认腿姿 | ABAD=0，HIP=0.8，KNEE=-1.5 rad；四腿同号 |
| 腿部执行器 | DCMotor，力矩/饱和力矩 28 Nm，速度 28 rad/s，P=20，D=0.7 |
| 轮子执行器 | Implicit 速度驱动，P=0，D=0.7，力矩 28 Nm，速度 28 rad/s |
| 位置动作幅度 | ABAD=0.125，其余腿关节=0.25 rad |
| 轮速动作幅度/目标限幅 | 5.0 / ±28 rad/s |
| 高度奖励目标 | 0.38 m；默认姿态轮底约在机身下方 0.373 m |
| 线速度/角速度跟踪奖励权重 | 3.0 / 1.5 |
| 腿部力矩/加速度惩罚权重 | -2.5e-5 / -2.5e-7 |
| 初始指令范围 | x ±0.5 m/s，y ±0.3 m/s，yaw ±0.8 rad/s |
| 20000 次迭代后 | x ±1.0，y ±0.4，yaw ±1.0 |
| 50000 次迭代后 | x ±1.5，y ±0.5，yaw ±1.5；复杂地形 x 限制在 ±1.0 |
| 初始地形等级 | 0～2；台阶/障碍范围降低为 0.03～0.18 m |

所有奖励、终止、随机化和观测中的实体名称均同步映射到 ZSL1W。接触轮体为 `.*_FOOT_LINK`，机身为 `BASE_LINK`，两组高度扫描器跟随 `BASE_LINK`。原有站立、轮轴对齐、动作平滑、接触终止和地形课程继续使用。

自碰撞按上游 ZSL1W 配置关闭，保留与地面的碰撞。这个设置不约束机器人自身连杆之间的穿透；需要训练避免自碰撞时，应先检查上装碰撞几何，再增加过滤规则。当前是固定零位负载的运动任务，不训练机械臂控制。

执行器参数、默认站姿和动作幅度参考 [上游资产配置](https://github.com/fan-ziqi/robot_lab/blob/main/source/robot_lab/robot_lab/assets/zsibot.py) 和 [ZSL1W rough 配置](https://github.com/fan-ziqi/robot_lab/blob/main/source/robot_lab/robot_lab/tasks/manager_based/locomotion/velocity/config/wheeled/zsibot_zsl1w/rough_env_cfg.py)。上游 main 已使用较新的 PhysX/Newton API，本项目运行 Isaac Lab 2.3 / Isaac Sim 5.1，因此只迁移物理参数，按当前版本实现。带臂后的保守速度、地形和课程参数为本任务的初始训练选择，仍需根据长期训练结果调优。

## 训练和验证

当前机器已运行 `legbot-dev` 容器，绑定宿主机项目到 `/workspace/legbot_lab`。在宿主机直接执行：

```bash
docker exec -it legbot-dev /bin/bash -lc '
  cd /workspace/legbot_lab &&
  /workspace/isaaclab/isaaclab.sh -p scripts/rsl_rl/train.py \
    --task RobotLab-ZSL1W-Piper-Fixed-v0 \
    --headless \
    --num_envs 2048 \
    --max_iterations 300000 \
    --run_name v1
'
```

若已进入可运行原训练命令的 Isaac Lab Python 环境：

```bash
python scripts/rsl_rl/train.py \
  --task RobotLab-ZSL1W-Piper-Fixed-v0 \
  --headless \
  --num_envs 2048 \
  --max_iterations 300000 \
  --run_name v1
```

训练输出目录：`logs/rsl_rl/zsl1w_piper_fixed_moe_cts/<时间戳>_v1/`，每 50 次迭代保存。时间戳沿用现有训练入口的进程时区；当前容器默认 UTC。旧 W1W 检查点虽然维数相同，但关节语义和物理参数不同，新任务默认从头训练。

播放时使用以下命令：

```bash
/workspace/isaaclab/isaaclab.sh -p scripts/rsl_rl/play.py \
  --task RobotLab-ZSL1W-Piper-Fixed-v0 \
  --load_run 2026-11-05_11-41-01_zsl1w_v1 \
  --num_envs 16 \
  --device cuda:2
```

该任务的自动播放独立设置速度分布：40% 概率纯前进 `+1.5 m/s`，40% 概率纯后退 `-1.5 m/s`，两者侧移和转向均为零；剩余 20% 为混合指令，范围为 x `±1.5 m/s`、y `±0.6 m/s`、yaw `±1.5 rad/s`，每 5 秒重新采样。播放不再由检查点的训练进度、训练地形限速或静止课程压低指令。这些是目标速度，训练配置本身不受影响。加 `--fix_commands` 时仍使用原来的固定向前 `1.0 m/s` 模式。

按用户指定，播放默认将所有机器人固定在地形第 **6 级**（索引从 0 开始），保留各自的地形类型。重置时不再升降级，地形生成仍保持训练中的难度行排列。可通过 `--terrain_level 6` 显式指定，或用该参数选择 0～9 中的其他等级。这里的 6 是播放选择；训练日志记录的是平均等级，旧检查点没有保存各环境最高通关等级。

检查导入质量、自由度、实体名称、动作映射、轮位置清零、观测维数和重置后的有限数值：

```bash
docker exec legbot-dev /bin/bash -lc '
  cd /workspace/legbot_lab &&
  /workspace/isaaclab/isaaclab.sh -p scripts/tools/check_zsl1w_piper_fixed.py --headless
'
```

2026-11-05 已完成以下实际验证（Isaac Sim 5.1 / Isaac Lab 2.3，RTX 4090，cuda:0）：

- 32 个环境运行 2 次 MoE-CTS 迭代，保存 `model_0.pt`、`model_1.pt`。
- 2048 个环境运行 2 次 MoE-CTS 迭代，完成采样和参数更新并保存检查点；两次迭代分别约 5.57 秒和 3.87 秒，不含启动时间。日志位于 `logs/rsl_rl/zsl1w_piper_fixed_moe_cts/2026-11-05_11-12-25_fixed_arm_2048_smoke/train.log`。
- 16 个环境专项检查 100 步并在中途重置：16 DOF，导入总质量 `26.329128265 kg`，policy `(16, 228)`，critic `(16, 295)`，single_obs `(16, 57)`；关节集合、动作分发、轮速目标、轮位置观测清零、有限数值和旧配置独立性均通过。报告为 `/tmp/zsl1w_piper_physics_check.log`，检查成功标志为 `ZSL1W_CHECK_PASSED`。
- Python 语法、全部网格路径，以及生成前后所有连杆惯量描述不变均通过检查。

短程验证用于确认训练链路可运行，不代表策略已经学会稳定运动或完成收敛；没有启动 300000 次迭代的正式长训。
