"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import unittest

from opendbc.testing import parameterized

from opendbc.car import gen_empty_fingerprint
from opendbc.car.structs import CarParams
from opendbc.car.car_helpers import interfaces
from opendbc.car.honda.values import CAR

CarFw = CarParams.CarFw


class TestHondaEpsMod(unittest.TestCase):

  @parameterized("car_name, fw", [(CAR.HONDA_CIVIC, b'39990-TBA,A030\x00\x00'), (CAR.HONDA_CIVIC, b'39990-TBA-A030\x00\x00'),
                                  (CAR.HONDA_CLARITY, b'39990-TRW-A020\x00\x00'), (CAR.HONDA_CLARITY, b'39990,TRW,A020\x00\x00')])
  def test_eps_mod_fingerprint(self, car_name, fw):
    fingerprint = gen_empty_fingerprint()
    car_fw = [CarFw(ecu="eps", fwVersion=fw)]

    CarInterface = interfaces[car_name]
    CP = CarInterface.get_params(car_name, fingerprint, car_fw, False, False, False)
    _ = CarInterface.get_params_sp(CP, car_name, fingerprint, car_fw, False, False, False)

    self.assertFalse(CP.dashcamOnly)


class TestOdysseyModifiedEps(unittest.TestCase):
  def test_stock_and_modified_parameters(self):
    from opendbc.car.fingerprints import FW_VERSIONS
    from opendbc.car.fw_versions import match_fw_to_car_exact
    from opendbc.sunnypilot.car.honda.values_ext import HondaFlagsSP
    candidate = CAR.HONDA_ODYSSEY
    for modified, version, kp, ki in [(False, b"39990-THR-A020\x00\x00", 0.28, 0.08),
                                       (True, b"39990-THR,A020\x00\x00", 0.3, 0.1)]:
      with self.subTest(modified=modified):
        live = {(addr, subaddr): {versions[0]} for (_, addr, subaddr), versions in FW_VERSIONS[candidate].items()}
        live[(0x18da30f1, None)] = {version}
        self.assertEqual(match_fw_to_car_exact(live, match_brand="honda", log=False), {candidate})
        fp = gen_empty_fingerprint()
        fw = [CarFw(ecu="eps", fwVersion=version)]
        ci = interfaces[candidate]
        cp = ci.get_params(candidate, fp, fw, False, False, False)
        sp = ci.get_params_sp(cp, candidate, fp, fw, False, False, False)
        self.assertEqual(bool(sp.flags & HondaFlagsSP.EPS_MODIFIED), modified)
        self.assertAlmostEqual(cp.lateralTuning.pid.kpV[0], kp, places=6)
        self.assertAlmostEqual(cp.lateralTuning.pid.kiV[0], ki, places=6)
        self.assertEqual(list(cp.lateralParams.torqueBP), [0, 4096])
        self.assertEqual(list(cp.lateralParams.torqueV), [0, 4096])
        self.assertAlmostEqual(cp.lateralTuning.pid.kf, 0.00006, places=9)
        self.assertAlmostEqual(cp.steerActuatorDelay, 0.1, places=6)
        live[(0x18da30f1, None)] = {b"39990-THR,A999\x00\x00"}
        self.assertNotIn(candidate, match_fw_to_car_exact(live, match_brand="honda", log=False))
