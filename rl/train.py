from stable_baselines3 import PPO
from env import CheckpointEnv

env = CheckpointEnv()

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    gamma=0.99
)

model.learn(total_timesteps=30_000)
model.save("checkpoint_rl_policy")

print("[CP4] RL policy trained")
