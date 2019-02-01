import collections
import numpy as np


Step = collections.namedtuple('Step', 'state, action, reward, done')
Experience = collections.namedtuple('Experience', 'state, action, reward, last_state')


class ExperienceSource:
    """Experience source using single environment"""

    def __init__(self, env, agent, gamma, steps_count=2):
        self.env = env
        self.agent = agent
        self.gamma = gamma
        self.steps_count = steps_count
        self.episode_reward = None

    def __iter__(self):
        state = self.env.reset()
        exp = collections.deque(maxlen=self.steps_count)
        total_reward = 0.0

        while True:
            action = self.agent(state)
            next_state, reward, is_done, _ = self.env.step(action)
            total_reward += reward
            step = Step(state=state, action=action,
                        reward=reward, done=is_done)
            exp.append(step)
            if len(exp) == self.steps_count:
                last_state = next_state if not is_done else None
                sum_reward = 0.0
                for e in reversed(exp):
                    sum_reward *= self.gamma
                    sum_reward += e.reward
                yield Experience(state=exp[0].state, action=exp[0].action,
                                 reward=sum_reward, last_state=last_state)
            state = next_state
            if is_done:
                self.episode_reward = total_reward
                total_reward = 0.0
                state = self.env.reset()
                exp.clear()

    def pop_episode_reward(self):
        res = self.episode_reward
        if res:
            self.episode_reward = None
        return res


class ExperienceBuffer:
    def __init__(self, source, capacity):
        self.buffer = collections.deque(maxlen=capacity)
        self.source = iter(source)

    def __len__(self):
        return len(self.buffer)

    def append(self, experience):
        self.buffer.append(experience)

    def sample(self, batch_size):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]

    def populate(self, exp_count):
        for _ in range(exp_count):
            entry = next(self.source)
            self.append(entry)