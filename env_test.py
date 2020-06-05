from pysc2.env import sc2_env, available_actions_printer
from pysc2.lib import actions, features, units
import sys

import random
import time
import math
import statistics
import numpy as np

from absl import flags
FLAGS = flags.FLAGS
FLAGS(sys.argv)

map_name = 'Simple64'
players = [sc2_env.Agent(sc2_env.Race['terran']), 
           sc2_env.Bot(sc2_env.Race['protoss'], sc2_env.Difficulty.very_easy)]
feature_screen_size = 84
feature_minimap_size = 64
rgb_screen_size = None
rgb_minimap_size = None
action_space = None
use_feature_units = True
step_mul = 8
game_steps_per_episode = None
disable_fog = True
visualize = True

env = sc2_env.SC2Env(
      map_name=map_name,
      players=players,
      agent_interface_format=sc2_env.parse_agent_interface_format(
          feature_screen=feature_screen_size,
          feature_minimap=feature_minimap_size,
          rgb_screen=rgb_screen_size,
          rgb_minimap=rgb_minimap_size,
          action_space=action_space,
          use_feature_units=use_feature_units),
      step_mul=step_mul,
      game_steps_per_episode=game_steps_per_episode,
      disable_fog=disable_fog,
      visualize=visualize)

_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_PLAYER_RELATIVE_SCALE = features.SCREEN_FEATURES.player_relative.scale
_PLAYER_SELF = features.PlayerRelative.SELF
_PLAYER_NEUTRAL = features.PlayerRelative.NEUTRAL  # beacon/minerals
_PLAYER_ENEMY = features.PlayerRelative.ENEMY

_NO_OP = actions.FUNCTIONS.no_op.id

_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_SELECT_ALL = [0]

_MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
_NOT_QUEUED = [0]
_QUEUED = [1]
_SELECT_ALL = [2]

_SELECT_POINT = actions.FUNCTIONS.select_point.id
_ATTACK_SCREEN = actions.FUNCTIONS.Attack_screen.id
_ATTACK_MINIMAP = actions.FUNCTIONS.Attack_minimap.id
_SELECT_CONTROL_GROUP = actions.FUNCTIONS.select_control_group.id

_BUILD_SUPPLY_DEPOT = actions.FUNCTIONS.Build_SupplyDepot_screen.id
_BUILD_BARRACKS = actions.FUNCTIONS.Build_Barracks_screen.id
_BUILD_REFINERY = actions.FUNCTIONS.Build_Refinery_screen.id
_BUILD_TECHLAB = actions.FUNCTIONS.Build_TechLab_screen.id

_TRAIN_MARINE = actions.FUNCTIONS.Train_Marine_quick.id
_TRAIN_MARAUDER = actions.FUNCTIONS.Train_Marauder_quick.id
_TRAIN_SCV = actions.FUNCTIONS.Train_SCV_quick.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_SELECT_IDLE_WORKER = actions.FUNCTIONS.select_idle_worker.id

_RETURN_SCV = actions.FUNCTIONS.Harvest_Return_SCV_quick.id
_HARVEST_GATHER = actions.FUNCTIONS.Harvest_Gather_screen.id
_HARVEST_GATHER_SCV = actions.FUNCTIONS.Harvest_Gather_SCV_screen.id

#print("_BUILD_SUPPLY_DEPOT :" + str(_BUILD_SUPPLY_DEPOT))

supply_depot_built = False

scv_selected = False
scv_return = False

marine_selected = False
marauder_selected = False
army_selected = False

first_attack = False
second_attack = False

obs = env.reset()
for i in range(0, 50000):
  #print("i: " + str(i))
  #time.sleep(0.1)

  target_0 = [random.randint(0,25),random.randint(0,25)]
  target_1 = [random.randint(0,25),random.randint(0,25)]

  action_0 = [actions.FUNCTIONS.no_op()]
  action_1 = [actions.FUNCTIONS.Move_screen("now", target_0)]
  action_2 = [actions.FUNCTIONS.select_point("select", target_0)]
  action_3 = [actions.FUNCTIONS.select_rect("select", target_0, target_1)]

  #print("obs[0][3]: " + str(obs[0][3]))
  feature_screen = obs[0][3]['feature_screen']
  feature_minimap = obs[0][3]['feature_minimap']
  feature_units = obs[0][3]['feature_units']
  feature_player = obs[0][3]['player']
  available_actions = obs[0][3]['available_actions']

  unit_type = feature_screen.unit_type
  empty_space = np.where(unit_type == 0)
  empty_space = np.vstack((empty_space[0], empty_space[1])).T
  #print("feature_minimap: " + str(feature_minimap))

  enermy = (feature_minimap.player_relative == _PLAYER_ENEMY).nonzero()
  enermy = np.vstack((enermy[0], enermy[1])).T

  self_CommandCenter = [unit for unit in feature_units if unit.unit_type == units.Terran.CommandCenter and unit.alliance == _PLAYER_SELF]
  self_SupplyDepot = [unit for unit in feature_units if unit.unit_type == units.Terran.SupplyDepot and unit.alliance == _PLAYER_SELF]
  self_Refinery = [unit for unit in feature_units if unit.unit_type == units.Terran.Refinery and unit.alliance == _PLAYER_SELF]
  self_BarracksTechLab = [unit for unit in feature_units if unit.unit_type == units.Terran.BarracksTechLab and unit.alliance == _PLAYER_SELF]
  self_SCVs = [unit for unit in feature_units if unit.unit_type == units.Terran.SCV and unit.alliance == _PLAYER_SELF]
  self_Marines = [unit for unit in feature_units if unit.unit_type == units.Terran.Marine and unit.alliance == _PLAYER_SELF]
  self_Marauder = [unit for unit in feature_units if unit.unit_type == units.Terran.Marauder and unit.alliance == _PLAYER_SELF]
  self_Barracks = [unit for unit in feature_units if unit.unit_type == units.Terran.Barracks and unit.alliance == _PLAYER_SELF]
  self_BarracksFlying = [unit for unit in feature_units if unit.unit_type == units.Terran.BarracksFlying and unit.alliance == _PLAYER_SELF]
  neutral_Minerals = [unit for unit in feature_units if unit.unit_type == units.Neutral.MineralField]
  neutral_VespeneGeysers = [unit for unit in feature_units if unit.unit_type == units.Neutral.VespeneGeyser]

  unselected_SCV_list = []
  for SCV in self_SCVs:
    if SCV.is_selected == 0:
      unselected_SCV_list.append(SCV)
  
  num_SCV = len(self_SCVs)
  num_Barracks = len(self_Barracks)
  num_BarracksFlying = len(self_BarracksFlying)
  num_Marines = len(self_Marines)
  num_Marauder= len(self_Marauder)
  num_Refinery = len(self_Refinery)
  num_BarracksTechLab = len(self_BarracksTechLab)

  total_Barracks = num_Barracks + num_BarracksFlying + num_BarracksTechLab
  #print("first_attack: " + str(first_attack))
  if num_Refinery != 0:
    assigned_scv = self_Refinery[0].assigned_harvesters

  x_list = []
  y_list = []
  for Mineral in neutral_Minerals:
    x_list.append(Mineral.x)
    y_list.append(Mineral.y)

  num_Minerals = len(x_list)
  if (num_Minerals != 0):
    mean_x_Minerals = statistics.mean(x_list)
    mean_y_Minerals = statistics.mean(y_list)
    dis_x = self_CommandCenter[0].x - mean_x_Minerals
    dis_y = self_CommandCenter[0].y - mean_y_Minerals
  
  self_minerals = feature_player.minerals
  self_vespene = feature_player.vespene
  self_food_used = feature_player.food_used
  self_food_cap = feature_player.food_cap

  #print("first_attack: " + str(first_attack))
  action = [actions.FUNCTIONS.no_op()]
  if (first_attack == False):
    if (self_food_cap - self_food_used <=3):
      if (scv_selected == False):
        scv_selected = True
        random_SCV = random.choice(unselected_SCV_list)
        target = [random_SCV.x, random_SCV.y]
        action = [actions.FUNCTIONS.select_point("select", target)]
      else:
        if ( (self_minerals >= 100) & (_BUILD_SUPPLY_DEPOT in available_actions) ):
          #target = [self_CommandCenter[0].x + dis_x, self_CommandCenter[0].y + dis_y]
          random_point = random.choice(empty_space)
          target = [random_point[0], random_point[1]]
          #print("target: " + str(target))
          action = [actions.FunctionCall(_BUILD_SUPPLY_DEPOT, [_NOT_QUEUED, target])]
    elif (num_Barracks <= 2):
      if ( (self_minerals >= 150) & (_BUILD_BARRACKS in available_actions) ):
          #target = [self_CommandCenter[0].x + dis_x, self_CommandCenter[0].y + dis_y]
          random_point = random.choice(empty_space)
          target = [random_point[0], random_point[1]]
          #print("target: " + str(target))
          action = [actions.FunctionCall(_BUILD_BARRACKS, [_NOT_QUEUED, target])]
    elif (num_Marines < 10):
      if (num_Barracks != 0):
        if ( (self_minerals >= 50) & (_TRAIN_MARINE in available_actions) ):
            action = [actions.FunctionCall(_TRAIN_MARINE, [_QUEUED])]
        else:
          scv_selected = False
          random_barrack = random.choice(self_Barracks)
          target = [random_barrack.x, random_barrack.y]
          action = [actions.FUNCTIONS.select_point("select", target)]
    elif (num_Marines >= 10):
        if ( (_SELECT_ARMY in available_actions) & (marine_selected == False) ) :
          marine_selected = True
          action = [actions.FunctionCall(_SELECT_ARMY, [_NOT_QUEUED])]
        elif (marine_selected == True):
          if (_ATTACK_MINIMAP in available_actions):
            first_attack = True
            random_point = random.choice(enermy)
            target = [random_point[0], random_point[1]]
            action = [actions.FunctionCall(_ATTACK_MINIMAP, [_NOT_QUEUED, target])]
    else:
      if (_HARVEST_GATHER in available_actions) :
        target = [neutral_Minerals[0].x, neutral_Minerals[0].y]
        action = [actions.FunctionCall(_HARVEST_GATHER, [_NOT_QUEUED, target])]
      else:
        if (_SELECT_IDLE_WORKER in available_actions):
          action = [actions.FunctionCall(_SELECT_IDLE_WORKER, [_NOT_QUEUED])]
  else:
    if (self_food_cap - self_food_used <=3):
      #print("scv_selected: " + str(scv_selected))

      if (scv_selected == False):
        scv_selected = True
        random_SCV = random.choice(unselected_SCV_list)
        target = [random_SCV.x, random_SCV.y]
        action = [actions.FUNCTIONS.select_point("select", target)]
      else:
        if ( (self_minerals >= 100) & (_BUILD_SUPPLY_DEPOT in available_actions) ):
          #target = [self_CommandCenter[0].x + dis_x, self_CommandCenter[0].y + dis_y]
          random_point = random.choice(empty_space)
          target = [random_point[0], random_point[1]]
          #print("target: " + str(target))
          action = [actions.FunctionCall(_BUILD_SUPPLY_DEPOT, [_NOT_QUEUED, target])]
    elif (num_Refinery == 0):
      if (_BUILD_REFINERY not in available_actions):
        random_SCV = random.choice(unselected_SCV_list)
        target = [random_SCV.x, random_SCV.y]
        action = [actions.FUNCTIONS.select_point("select", target)]
      elif ( (self_minerals >= 100) & (_BUILD_REFINERY in available_actions) ):
        #target = [random_point[0], random_point[1]]
        #print("target: " + str(target))
        if (len(neutral_VespeneGeysers) != 0):
          target = [neutral_VespeneGeysers[0].x, neutral_VespeneGeysers[0].y]
          action = [actions.FunctionCall(_BUILD_REFINERY, [_NOT_QUEUED, target])]
    elif (self_Refinery[0].assigned_harvesters <= 3):
      #print("self_Refinery[0].assigned_harvesters: " + str(self_Refinery[0].assigned_harvesters))
      #print("Refinery loop")
      if (scv_selected == False):
        #print("scv_selected command")
        scv_selected = True
        random_SCV = random.choice(unselected_SCV_list)
        target = [random_SCV.x, random_SCV.y]
        action = [actions.FUNCTIONS.select_point("select", target)]
        #print("select scv")
      elif ( (_HARVEST_GATHER in available_actions) & (scv_selected == True) ):
        #print("havest command")
        scv_selected = False
        target = [self_Refinery[0].x, self_Refinery[0].y]
        action = [actions.FunctionCall(_HARVEST_GATHER, [_NOT_QUEUED, target])]
    elif (num_SCV <= 14):
      if (_TRAIN_SCV not in available_actions):
        if (len(self_CommandCenter) != 0):
          target = [self_CommandCenter[0].x, self_CommandCenter[0].y]
          action = [actions.FUNCTIONS.select_point("select", target)]
          scv_selected = False
      else:
        action = [actions.FunctionCall(_TRAIN_SCV, [_QUEUED])]
    elif (num_Marines < 10):
      if (num_Barracks != 0):
        if ( (self_minerals >= 50) & (_TRAIN_MARINE in available_actions) ):
            action = [actions.FunctionCall(_TRAIN_MARINE, [_QUEUED])]
        else:
          target = [self_Barracks[0].x, self_Barracks[0].y]
          action = [actions.FUNCTIONS.select_point("select", target)]
    elif (total_Barracks <= 2):
      if ( (self_minerals >= 150) & (_BUILD_BARRACKS in available_actions) ):
        #target = [self_CommandCenter[0].x + dis_x, self_CommandCenter[0].y + dis_y]
        random_point = random.choice(empty_space)
        target = [random_point[0], random_point[1]]
        #print("target: " + str(target))
        action = [actions.FunctionCall(_BUILD_BARRACKS, [_NOT_QUEUED, target])]
      else:
        random_SCV = random.choice(unselected_SCV_list)
        target = [random_SCV.x, random_SCV.y]
        action = [actions.FUNCTIONS.select_point("select", target)]
    elif (num_BarracksTechLab == 0):
      #print("TechLab loop")
      #print("num_BarracksTechLab: " + str(num_BarracksTechLab))

      if (_BUILD_TECHLAB not in available_actions):
        #target = [self_Barracks[0].x, self_Barracks[0].y]
        #random_point = random.choice(empty_space)
        #target = [random_point[0], random_point[1]]
        target = [self_Barracks[0].x, self_Barracks[0].y]
        action = [actions.FUNCTIONS.select_point("select", target)]
      elif ( (self_minerals >= 100) & (self_vespene >= 25) & (_BUILD_TECHLAB in available_actions) ):
        #target = [self_Barracks[0].x, self_Barracks[0].y]
        random_point = random.choice(empty_space)
        target = [random_point[0], random_point[1]]
        action = [actions.FunctionCall(_BUILD_TECHLAB, [_NOT_QUEUED, target])]
    elif (num_Marauder < 5):
      #print("Marauder loop")
      if (num_Barracks != 0):
        if ( (self_minerals >= 100) & (self_vespene >= 25) & (_TRAIN_MARAUDER in available_actions) ):
            #print("_TRAIN_MARAUDER command")
            action = [actions.FunctionCall(_TRAIN_MARAUDER, [_QUEUED])]
        else:
          scv_selected = False
          target = [self_Barracks[1].x, self_Barracks[1].y]
          action = [actions.FUNCTIONS.select_point("select", target)]
    elif (num_Marauder >= 3):
      if ( (_SELECT_ARMY in available_actions) & (marauder_selected == False) ):
        marauder_selected = True
        scv_selected = False
        action = [actions.FunctionCall(_SELECT_ARMY, [_NOT_QUEUED])]
      elif ( (_SELECT_CONTROL_GROUP in available_actions) & (marauder_selected == True) ):
        #marauder_selected = False
        #random_point = random.choice(enermy)
        #target = [random_point[0], random_point[1]]
        action = [actions.FUNCTIONS.select_control_group("set", 1)]
        #action = [actions.FunctionCall(_ATTACK_MINIMAP, [_NOT_QUEUED, target])]
    else:
      if ( (_SELECT_CONTROL_GROUP in available_actions) & (army_selected == False) ):
        army_selected = True
        action = [actions.FUNCTIONS.select_control_group("recall", 1)]
      elif ( (_ATTACK_MINIMAP in available_actions) & (army_selected == True) ):
        random_point = random.choice(enermy)
        target = [random_point[0], random_point[1]]
        action = [actions.FunctionCall(_ATTACK_MINIMAP, [_NOT_QUEUED, target])]

  print("action: " + str(action))
  #print("num_Marauder: " + str(num_Marauder))
  obs = env.step(action)