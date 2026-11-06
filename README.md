# ZSL1_W 轮足机器人

ZSL1_W（代码中命名为 `zsl1w`）包含轮足底盘、Piper 六轴机械臂及夹爪、RealSense D435 深度/彩色相机、Livox MID-360 激光雷达和上装外壳。

当前训练任务为 **`RobotLab-ZSL1W-Piper-Fixed-v0`**，使用 MoE-CTS 训练轮足运动。机械臂和夹爪固定在零位，保留质量、惯量及碰撞；策略控制 12 个腿部关节和 4 个轮子关节。

## URDF 和传感器在哪里

宿主机项目目录：`/data/sdl/legbot_lab_zsibot`。以下路径均相对于项目根目录。

| 文件 | 用途 |
| --- | --- |
| [resources/zsl1w/urdf/zsl1w_inspection_piper.urdf](resources/zsl1w/urdf/zsl1w_inspection_piper.urdf) | **完整装配模型**：轮足底盘、可动 Piper 机械臂及夹爪、D435、MID-360、外壳 |
| [resources/zsl1w/urdf/zsl1w_inspection_piper_fixed.urdf](resources/zsl1w/urdf/zsl1w_inspection_piper_fixed.urdf) | **当前训练实际加载的模型**：相同装配，机械臂及夹爪固定，剩余 16 个活动关节 |
| [resources/zsl1w/urdf/zsl1w_inspection.urdf](resources/zsl1w/urdf/zsl1w_inspection.urdf) | 带 D435、MID-360 和外壳的轮足平台，不含机械臂 |
| [resources/zsl1w/meshes/](resources/zsl1w/meshes/) | 底盘、传感器和外壳网格；机械臂网格在 `piper/` 子目录 |
| [resources/zsl1w/configuration/payload_extrinsics.json](resources/zsl1w/configuration/payload_extrinsics.json) | 相机、雷达的名义安装外参 |
| [resources/zsl1w/configuration/piper_mount.json](resources/zsl1w/configuration/piper_mount.json) | 机械臂安装位姿记录 |

完整装配以 `BASE_LINK` 为根。机身坐标为 X 向前、Y 向左、Z 向上，距离单位为米。

| 部件 | URDF 连杆 / 坐标系 |
| --- | --- |
| Piper 机械臂和夹爪 | `piper_base_link`；六轴关节 `piper_joint1`～`piper_joint6`；夹爪驱动 `piper_gripper` |
| D435 深度相机 | 外观连杆 `D435_LINK`；深度光学坐标系 `D435_DEPTH_OPTICAL_FRAME`；彩色光学坐标系 `D435_COLOR_OPTICAL_FRAME` |
| MID-360 激光雷达 | 外观连杆 `MID360_LINK`；扫描坐标系 `MID360_SCAN` |
| 上装外壳 | `PAYLOAD_HOUSING` |

URDF 包含这些部件的几何、安装关系和坐标系。**当前轮足训练未启用 D435 图像或 MID-360 点云输出**；场景中的高度扫描器和接触传感器是训练使用的仿真传感器。需要相机或雷达数据时，应在对应坐标系配置仿真传感器；训练资产启用了固定关节合并，需要保留传感器坐标系时应另行配置导入。

## 训练 checkpoint 在哪里

本次上传的训练模型位于 [checkpoints/zsl1w_piper_fixed/](checkpoints/zsl1w_piper_fixed/)：

| 文件 | 内容 |
| --- | --- |
| [model_20000.pt](checkpoints/zsl1w_piper_fixed/model_20000.pt) | 本次上传的较新 checkpoint，保存的迭代编号为 20000；后续示例默认使用它 |
| [model_10000.pt](checkpoints/zsl1w_piper_fixed/model_10000.pt) | 迭代编号为 10000 的 checkpoint |
| [params/agent.yaml](checkpoints/zsl1w_piper_fixed/params/agent.yaml) | 该次训练的算法参数快照 |
| [params/env.yaml](checkpoints/zsl1w_piper_fixed/params/env.yaml) | 该次训练的环境参数快照（4096 个并行环境） |

两个 `.pt` 均包含策略网络、优化器、学生编码器优化器和训练进度，可用于续训。参数快照用于核对原训练设置；运行脚本实际加载任务的 Python 配置。

本机原始 checkpoint 目录为：

```text
/data/sdl/legbot_lab_zsibot/logs/rsl_rl/zsl1w_piper_fixed_moe_cts/2026-11-05_11-41-01_zsl1w_v1/
├── model_10000.pt
├── model_20000.pt
└── params/
```

新训练及续训的输出均保存到 `logs/rsl_rl/zsl1w_piper_fixed_moe_cts/<时间戳>_<run_name>/`，默认每 50 次迭代保存 checkpoint。GitHub 中的 `checkpoints/` 是本次模型快照；后续训练不会自动更新 GitHub 上的模型。

## 执行环境

当前运行环境为 Isaac Sim 5.1 / Isaac Lab 2.3，已安装本项目的 `robot_lab` 和自带 MoE-CTS `rsl_rl`。在宿主机进入现有容器：

```bash
docker exec -it legbot-dev bash
cd /workspace/legbot_lab
```

**下面所有命令均在该容器的项目根目录执行。** 宿主机目录虽已重命名，当前容器内挂载点仍为 `/workspace/legbot_lab`；重建容器时将 `/data/sdl/legbot_lab_zsibot` 挂载到该路径。示例使用 `cuda:0`，可改为实际使用的 GPU。

## 从头训练

```bash
/workspace/isaaclab/isaaclab.sh -p scripts/rsl_rl/train.py \
  --task RobotLab-ZSL1W-Piper-Fixed-v0 \
  --headless \
  --device cuda:0 \
  --num_envs 4096 \
  --max_iterations 50000 \
  --run_name zsl1w_scratch
```

不加 `--resume` 即从头训练。显存不足时可降低 `--num_envs`。

## 从 checkpoint 继续训练

训练入口通过 `logs/` 下的运行目录查找 checkpoint。为使新克隆的仓库也能直接续训，先将上传的模型复制到单独的恢复目录：

```bash
mkdir -p logs/rsl_rl/zsl1w_piper_fixed_moe_cts/github_checkpoint
cp checkpoints/zsl1w_piper_fixed/model_*.pt \
  logs/rsl_rl/zsl1w_piper_fixed_moe_cts/github_checkpoint/
```

从 `model_20000.pt` 恢复，额外训练 30000 次更新：

```bash
/workspace/isaaclab/isaaclab.sh -p scripts/rsl_rl/train.py \
  --task RobotLab-ZSL1W-Piper-Fixed-v0 \
  --headless \
  --device cuda:0 \
  --num_envs 4096 \
  --resume \
  --load_run github_checkpoint \
  --checkpoint model_20000.pt \
  --max_iterations 30000 \
  --run_name zsl1w_resume
```

`--max_iterations` 在续训时表示**额外更新次数**，不是总迭代上限。续训恢复网络、优化器和课程进度，仿真场景重新初始化；输出写入新的时间戳目录。若直接使用本机原始训练目录，将 `--load_run` 改为 `2026-11-05_11-41-01_zsl1w_v1` 即可，无需复制。

## Play 可视化

在支持图形显示的会话中运行，直接加载上传的 checkpoint：

```bash
/workspace/isaaclab/isaaclab.sh -p scripts/rsl_rl/play.py \
  --task RobotLab-ZSL1W-Piper-Fixed-v0 \
  --checkpoint checkpoints/zsl1w_piper_fixed/model_20000.pt \
  --device cuda:0 \
  --num_envs 16 \
  --terrain_level 6 \
  --real-time
```

此命令不加 `--headless`，打开仿真窗口。默认在第 6 级地形上播放（从 0 开始计数），随机指令偏向前进和后退；增加 `--fix_commands` 可固定为向前 `1.0 m/s`。也可将 `--terrain_level` 改为 0～9 中的其他等级。

无图形界面时，可在同一命令末尾增加 `--headless --video --video_length 500` 录制视频。视频保存到所选 checkpoint 旁的 `videos/play/`；播放时导出的 `policy.pt`、`policy.onnx` 保存到旁边的 `exported/`，续训使用上面的 `model_*.pt`。
