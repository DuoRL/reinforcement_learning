import gym
import numpy as np
import tensorflow as tf
import dqn_cnn2
import os

# from pycallgraph import PyCallGraph
# from pycallgraph.output import GraphvizOutput

# import matplotlib.pyplot as plt

# ACTIONS = {0:1, 1:4, 2:5}
NUM_EPISODES = 100
FAIL_PENALTY = -1
EPSILON = 1
EPSILON_DECAY = 0.01
END_EPSILON = 0.1
LEARNING_RATE = 1e-4
DISCOUNT_FACTOR = 0.99
BATCH_SIZE = 256
MEM_SIZE = 1e5
ENV_NAME = 'Breakout-v0'
STEP_PER_EPOCH = 100
RECORD = False
KTH_FRAME = 4
TRAIN_EVERY_NUM_EPISODES = 1

BATCH_SIZE = 64
IMAGE_SIZE = [84, 84]

DISPLAY = False

MODEL_DIR = '/tmp/breakout-experiment-1'
MODEL_PATH = '/tmp/breakout-experiment-1/model'



class StateProcessor():


  def __init__(self):
    # Build the Tensorflow graph
    with tf.variable_scope("state_processor"):
      self.input_state = tf.placeholder(shape=[210, 160, 3], dtype=tf.uint8)
      self.output = tf.image.rgb_to_grayscale(self.input_state)
      self.output = tf.image.crop_to_bounding_box(self.output, 34, 0, 160, 160)
      self.output = tf.image.resize_images(self.output, [84, 84], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
      self.output = tf.squeeze(self.output)


  def process(self, sess, state):
    """
    Args:
        sess: A Tensorflow session object
        state: A [210, 160, 3] Atari RGB State

    Returns:
        A processed [84, 84, 1] state representing grayscale values.
    """
    return sess.run(self.output, { self.input_state: state })



def train(agent, env, history, sess, num_episodes=NUM_EPISODES):
  for i in xrange(NUM_EPISODES):
    obs = env.reset()
    cur_state = sp.process(sess, obs)

    action = 0
    episode = []
    done = False
    t = 0
    last_life = 5
    cum_reward = 0
    while not done:
      t = t + 1
      # action = env.action_space.sample()
      action = agent.get_action(cur_state,sess)
      if DISPLAY:
        print agent.get_action_dist(cur_state,sess), agent.get_optimal_action(cur_state, sess)
        env.render()
        # if action != 0:
          # print '~0'
        # while action==0:
          # action = env.action_space.sample()
      # else:
        # action = agent.get_action(cur_state,sess)
      # print len(cur_state), len(cur_state[0]), cur_state[15:-15][15:-15], action
      obs, reward, done, info = env.step(action)
      cum_reward = cum_reward + reward
      # next_state = sp.process(sess, obs)
      if reward == 0:
        reward = info['ale.lives'] - last_life
        last_life = info['ale.lives']

      if reward > 0:
        reward = 1
      elif reward < 0:
        reward = -1

      if done:
        reward = FAIL_PENALTY
        episode.append([cur_state, action, sp.process(sess, obs), reward, done])
        print("Episode finished after {} timesteps, cumulated reward: {}".format(t+1, cum_reward))
        history.append(t + 1)
        break
      if t % KTH_FRAME == 0:
        next_state = sp.process(sess, obs)
        episode.append([cur_state, action, next_state, reward, done])
        cur_state = next_state

    # print len(episode)
    print agent.get_action_dist(cur_state,sess), agent.get_optimal_action(cur_state, sess)
    agent.add_episode(episode)
    if i % TRAIN_EVERY_NUM_EPISODES == 0:
      print 'train at episode {}'.format(i)
      agent.learn(STEP_PER_EPOCH, sess)
  return agent, history


env = gym.envs.make(ENV_NAME)

tf.reset_default_graph()
sp = StateProcessor()


with tf.Session() as sess:
  with tf.device('/cpu:0'):
    agent = dqn_cnn2.DQNAgent_CNN(epsilon=EPSILON, epsilon_anneal=EPSILON_DECAY, end_epsilon=END_EPSILON, 
      lr=LEARNING_RATE, gamma=DISCOUNT_FACTOR, batch_size=BATCH_SIZE, state_size=IMAGE_SIZE, 
      action_size=6, mem_size=MEM_SIZE)
  sess.run(tf.global_variables_initializer())
  saver = tf.train.Saver()
  if os.path.isdir(MODEL_DIR):
    saver.restore(sess, MODEL_PATH)
    print 'restored model'
  else:
    os.makedirs(MODEL_DIR)
      
  history = []
  agent, history = train(agent, env, history, sess)
  print history

  saver.save(sess, MODEL_PATH)
  print 'saved model'




# # plt.ion()
# plt.figure()
# im = plt.imshow(np.zeros(IMAGE_SIZE), cmap='gist_gray_r', vmin=0, vmax=1)



# graphviz = GraphvizOutput(output_file='filter_none.png')
# with PyCallGraph(output=graphviz):
#   # while True:
#   with tf.Session() as sess:
#     sess.run(tf.global_variables_initializer())

#     done = False
#     observation = env.reset()
#     t = 0
#     cum_reward = 0
#     while not done:
#       t = t + 1
#       env.render()
#       observation_p = sp.process(sess, observation)
#       im.set_data(observation_p)

#       action = env.action_space.sample()
#       observation, reward, done, info = env.step(action)
#       cum_reward = cum_reward + reward
#       if done:
#         print("Episode finished after {} timesteps, cumulated reward: {}".format(t+1, cum_reward))