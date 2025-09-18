import os
from pathlib import Path
from c3po.physicsDrivers.ICOCODriver import ICOCODriver
import c3po

import scivianna
from scivianna_example.c3po_coupling.fake_driver import DecreasingFieldProblem
import scivianna_example.c3po_coupling.visualizer as visualizer

def get_panel(_):
    # Building of objects driving codes
    fieldDriver = DecreasingFieldProblem(str(Path(scivianna.__file__).parent / "default_jdd" / "power.med"))
    fieldDriver.initialize()

    visualizer_data = visualizer.VisualizerData(
        grid=[
                # first line
                [
                    visualizer.FieldPanel(name="Field value", mesh=fieldDriver.getOutputMEDDoubleField("VALUE").getMesh()),
                    visualizer.ValuePanel(name="MAX"),
                ]
            ],
        title="C3PO coupling demo"
    )

    working_dir = Path("./results")
    os.makedirs(working_dir, exist_ok=True)
    visu_problem, visu_data_file = visualizer.get_problem(working_directory=working_dir,
                                                            data_to_view=visualizer_data)
    myVIZDriver = ICOCODriver(visu_problem)
    myVIZDriver.setDataFile(visu_data_file)
    myVIZDriver.init()

    LocalExchanger = c3po.tracer()(c3po.LocalExchanger)

    # 3. Exchanges between the codes and the visualizer
    Exchanger_to_Visualizer = LocalExchanger(
        method=c3po.DirectMatching(),
        # fieldsToGet=[],
        fieldsToGet=[
            (fieldDriver, "VALUE")
            ],
        # fieldsToSet=[],
        fieldsToSet=[
            (myVIZDriver, "Field value")
            ],
        valuesToGet=[(fieldDriver, "MAX"),],
        valuesToSet=[(myVIZDriver, "MAX"),])



    # Definition of a class defining what "doing an time-step" means.
    class ExplicitCoupler(c3po.Coupler):
        def __init__(self, physics, exchangers, dataManagers=[]):
            c3po.Coupler.__init__(self, physics, exchangers, dataManagers)
            self.maxPower = 0.

        def solveTimeStep(self):
            self._physicsDrivers["PHY"].solveTimeStep()
            self._exchangers["PHY_2_VIZ"].exchange()
            power = self._physicsDrivers["PHY"].getOutputDoubleValue("MAX")
            self._physicsDrivers["VISU"].solve()
            print("time =", self._physicsDrivers["VISU"].presentTime(), " power = ", power)
            if power > self.maxPower:
                self.maxPower = power
            return self.getSolveStatus()

        def computeTimeStep(self):
            return (5.E-4, False)  # This define time-step size


    # Building of a ExplicitCoupler object
    transientCoupler = ExplicitCoupler({"PHY": fieldDriver, "VISU": myVIZDriver},
                                        {
                                            "PHY_2_VIZ": Exchanger_to_Visualizer,
                                        })

    # Transient
    transientCoupler.maxPower = 0.
    transientCoupler.setStationaryMode(False)
    transientCoupler.solveTransient(0.03)

    myVIZDriver.term()

if __name__ == "__main__":
    get_panel(None)
    