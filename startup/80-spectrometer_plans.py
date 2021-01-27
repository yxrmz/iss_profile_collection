from xas.spectrometer import Crystal, analyze_many_elastic_scans
import copy


# from ophyd import (PseudoPositioner, PseudoSingle)
# from ophyd import (Component as Cpt)
#
# class SpectrometerEnergy(PseudoPositioner):
#     # pseudo motor
#     energy = Cpt(PseudoSingle)
#
#     # real motors
#     crystal_x = auxxy.x
#     crystal_y = auxxy.y
#     det_y0 = huber_stage.z




class EmissionEnergyMotor:

    def __init__(self, energy0, cr_x0, cr_y0, det_y0, kind, hkl):
        self.energy0 = energy0
        self.cr_x0 = cr_x0
        self.cr_y0 = cr_y0
        self.det_y0 = det_y0

        self.crystal = Crystal(1000, 50, hkl, kind)
        self.crystal.place_E(energy0)
        self.cr_x0_nom = copy.copy(self.crystal.x)
        self.cry_0_nom = copy.copy(self.crystal.y)
        self.det_y0_nom = copy.copy(self.crystal.d_y)


    def _get_postion_for_energy(self, energy):

        # print(self.cr_x0_nom, self.crystal.x)
        self.crystal.place_E(energy)
        # print(self.cr_x0_nom, self.crystal.x)
        dcr_x = self.crystal.x - self.cr_x0_nom
        dcr_y = self.crystal.y - self.cry_0_nom
        ddet_y = self.crystal.d_y - self.det_y0_nom
        return (self.cr_x0 - dcr_x), (self.cr_y0 + dcr_y), (self.det_y0 - ddet_y)

    def get_positions_for_energies(self, energy_list):
        crystal_x_list = []
        crystal_y_list = []
        detector_y_list = []
        for energy in energy_list:
            crystal_x, crystal_y, detector_y = self._get_postion_for_energy(energy)
            crystal_x_list.append(crystal_x)
            crystal_y_list.append(crystal_y)
            detector_y_list.append(detector_y)
        return crystal_x_list, crystal_y_list, detector_y_list


def define_spectrometer_motor(kind, hkl):
    energy = hhm.energy.user_readback.get()
    cr_x0 = auxxy.x.user_readback.get()
    cr_y0 = auxxy.y.user_readback.get()
    det_y0 = huber_stage.z.user_readback.get()
    eem = EmissionEnergyMotor(energy, cr_x0, cr_y0, det_y0, kind, hkl)
    return eem

# eem_calculator = define_spectrometer_motor('Ge', [4, 4, 4])


def move_emission_energy_plan(energy):
    cr_x, cr_y, det_y = eem_calculator._get_postion_for_energy(energy)
    # print(cr_x, cr_y, det_y)

    yield from bps.mv(auxxy.x, cr_x)
    yield from bps.mv(auxxy.y, cr_y)
    yield from bps.mv(huber_stage.z, det_y)


# energies = np.linspace(7625, 7730, npt)
#RE(emission_scan_plan(energies))

def emission_scan_plan(energies):
    crystal_x_list, crystal_y_list, detector_y_list = eem_calculator.get_positions_for_energies(energies)
    yield from bp.list_scan([pil100k, apb_ave],
                            auxxy.x, crystal_x_list,
                            auxxy.y, crystal_y_list,
                            huber_stage.z, detector_y_list)
    # return energies


def elastic_scan_plan(DE=5, dE=0.1):
    npt = np.round(DE/dE + 1)
    name = 'elastic spectrometer scan'
    plan = bp.relative_scan([pil100k, apb_ave], hhm.energy, -DE/2, DE/2, npt, md={'plan_name': 'elastic_scan ' + motor.name, 'name' : name})
    yield from plan


def calibration_scan_plan(energies):
    uids = []
    for energy in energies:
        yield from bps.mv(hhm.energy, energy)
        yield from move_emission_energy_plan(energy)
        yield from elastic_scan_plan()
        # uid = (yield from elastic_scan_plan())
    #     if type(uid) == tuple:
    #         uid = uid[0]
    #     uids.append(uid)
    #
    # energy_converter = analyze_many_elastic_scans(db, uids, energies, plotting=True)
    # return energy_converter









# def test():
#     eem = define_spectrometer_motor('Ge', [4,4,4])
#     print(eem._get_postion_for_energy(7649))
#     print(eem._get_postion_for_energy(7639))
#     print(eem._get_postion_for_energy(7629))
#
#
# test()

######


spectrometer_calibration_dict = {}

# Energy      CrX         CrY         DetY
# 7749.2     -129.570     16.285       331.731
# 7739.2     -132.144


#######