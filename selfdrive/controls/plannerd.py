#!/usr/bin/env python3
import gc

from cereal import car
from common.params import Params
from common.realtime import set_realtime_priority
from selfdrive.swaglog import cloudlog
from selfdrive.controls.lib.planner import Planner
from selfdrive.controls.lib.vehicle_model import VehicleModel
from selfdrive.controls.lib.pathplanner import PathPlanner
import cereal.messaging as messaging
import time

def dummy_plannerd_logger(msg):
  f = open("plannerd_log.txt", "a+")
  f.write(str(time.asctime()))
  f.write("\n")
  f.write(str(time.time()))
  f.write("\n")
  f.write("\n")
  f.write(msg)
  f.write("\n")

  f.close()

def plannerd_thread(sm=None, pm=None):
  gc.disable()

  # start the loop
  set_realtime_priority(2)

  cloudlog.info("plannerd is waiting for CarParams")
  dummy_plannerd_logger("plannerd is waiting for CarParams")
  CP = car.CarParams.from_bytes(Params().get("CarParams", block=True))
  cloudlog.info("plannerd got CarParams: %s", CP.carName)
  dummy_plannerd_logger("plannerd got CarParams: " + str(CP.carName))

  PL = Planner(CP)
  PP = PathPlanner(CP)

  VM = VehicleModel(CP)

  if sm is None:
    sm = messaging.SubMaster(['carState', 'controlsState', 'radarState', 'model', 'liveParameters'])

  if pm is None:
    pm = messaging.PubMaster(['plan', 'liveLongitudinalMpc', 'pathPlan', 'liveMpc'])

  sm['liveParameters'].valid = True
  sm['liveParameters'].sensorValid = True
  sm['liveParameters'].steerRatio = CP.steerRatio
  sm['liveParameters'].stiffnessFactor = 1.0

  dummy_plannerd_logger("initialized liveParameters service, entering main loop...")

  while True:
    sm.update()

    if sm.updated['model']:
      PP.update(sm, pm, CP, VM)
    if sm.updated['radarState']:
      PL.update(sm, pm, CP, VM, PP)


def main(sm=None, pm=None):
  plannerd_thread(sm, pm)


if __name__ == "__main__":
  main()
