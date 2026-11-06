
FROM isaac-lab-base-sim510-lab230:latest

WORKDIR /workspace/legbot_lab

COPY . .

# 1. 安装 robot_lab 扩展
RUN /workspace/isaaclab/isaaclab.sh -p -m pip install \
    --no-build-isolation --no-deps -e source/robot_lab

# 2. 兼容现有 setuptools，不升级 packaging
# 仅修改镜像内的 RSL-RL 包元数据格式
RUN sed -i 's/^license = "BSD-3-Clause"$/license = {text = "BSD-3-Clause"}/' \
    source/rsl_rl/pyproject.toml \
    && grep -q '^license = {text = "BSD-3-Clause"}$' \
    source/rsl_rl/pyproject.toml

# 3. 安装项目自带的 MoE-CTS RSL-RL
RUN /workspace/isaaclab/isaaclab.sh -p -m pip uninstall -y rsl-rl-lib \
    && /workspace/isaaclab/isaaclab.sh -p -m pip install \
    --no-build-isolation --no-deps -e source/rsl_rl

CMD ["/bin/bash"]

