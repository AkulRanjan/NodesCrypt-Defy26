import gymnasium as gym
import numpy as np

class CheckpointEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.observation_space = gym.spaces.Box(
            low=0, high=1e6, shape=(5,), dtype=np.float32
        )

        self.action_space = gym.spaces.Discrete(4)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.array([
            np.random.randint(50, 150),   # mempool_tx_count
            np.random.random(),           # avg_fee_rate
            np.random.randint(100, 500),  # congestion_score
            np.random.random(),           # avg_spam_score
            np.random.random()            # spam_tx_ratio
        ], dtype=np.float32)

        return self.state, {}

    def step(self, action):
        mempool, fee, congestion, spam_score, spam_ratio = self.state

        # Simulate effect of actions
        if action == 1:  # raise fee
            spam_ratio *= 0.7
            congestion *= 0.85
        elif action == 2:  # deprioritize spam
            spam_ratio *= 0.5
        elif action == 3:  # defensive mode
            spam_ratio *= 0.3
            mempool *= 0.8

        # Random noise (realism)
        mempool += np.random.randint(-10, 10)
        mempool = max(mempool, 10)

        self.state = np.array([
            mempool,
            fee,
            congestion,
            spam_score,
            spam_ratio
        ], dtype=np.float32)

        reward = (
            -mempool * 0.01
            -spam_ratio * 10
        )

        terminated = False
        truncated = False
        return self.state, reward, terminated, truncated, {}
