import os
import sys
import xml.etree.ElementTree as ET
import subprocess
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

from libraries.classes.DataManager import *
from libraries import constants
from libraries.classes.SumoSimulator import Simulator
from libraries.constants import SUMO_TOOLS_PATH, SUMO_NET_PATH


class ScenarioGenerator:
    """
    The ScenarioGenerator class handles traffic route scenarios, allowing them to be created and configured
    for sumoenv simulations. It generates route files and sets up these routes within the simulator.

    Class Attributes:
    - sumoConfiguration (str): Path to the sumoenv configuration file.
    - sim (Simulator): An instance of the Simulator class.

    Class Methods:
    - __init__: Constructor to initialize a new instance of the ScenarioGenerator class.
    - generateRoutes: Method to generate a route file for sumoenv simulation from an edgefile.
    - setScenario: Method to set the current scenario in the simulator using a generated or manual route file.
    """
    sumoConfiguration: str
    sim: Simulator

    def __init__(self, sumocfg: str, sim: Simulator):
        """
        Initializes the ScenarioGenerator with the sumoenv configuration file and the simulator instance.

        :param sumocfg: Path to the sumoenv configuration file.
        :param sim: An instance of the Simulator class.
        """
        self.sumoConfiguration = sumocfg
        self.sim = sim


    def defineScenarioFolder(self, congestioned: bool = False) -> str:
        """
        Defines and creates a folder for the scenario the planner wants to simulate.

        :param congestioned: Boolean flag indicating if the scenario should be congested.
        :return: The path to the folder created for the scenario.
        """
        date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        scenarioFolder = "congestioned" if congestioned else "basic"
        newPath = os.path.join(constants.SCENARIO_COLLECTION_PATH, f"{date}_{scenarioFolder}/")
        os.makedirs(newPath, exist_ok=True)
        return newPath


    def generateRoutes(self, edgefile: str, folderPath: str, totalVehicles: int, minLoops: int = 1, congestioned: bool= False) -> str:
        """
        Generates a route file for sumoenv simulation starting from an edgefile that contains vehicle counts.

        :param edgefile: The path to the edgefile containing traffic counts.
        :param totalVehicles: The total number of vehicles to be generated in the route file.
        :param minLoops: Minimum number of loops or counting locations covered by each vehicle route.
        :param congestioned: Boolean flag to indicate whether the generated scenario should be congested.
        :return: The absolute path to the generated route file.
        :raises FileNotFoundError: If the sumoenv tools path does not exist.
        """
        if not edgefile:
            raise ValueError("No edgefile provided.")
        if totalVehicles is None:
            raise ValueError("The total number of vehicles was not defined.")

        if not os.path.exists(constants.SUMO_TOOLS_PATH):
            raise FileNotFoundError("sumoenv tools path does not exist.")


        script1 = constants.SUMO_TOOLS_PATH + "/randomTrips.py"

        arg1 = ""
        if constants.SUMO_PATH.startswith("./"):
            arg1 = constants.SUMO_PATH[2:]
        else:
            arg1 = constants.SUMO_PATH
        arg1 = os.path.join(arg1, "static/joined_lanes.net.xml")
        arg1 = os.path.abspath(arg1)
        print(arg1)
        print(edgefile)

        subprocess.run(['python', script1, "-n", arg1, "-r", folderPath + "sampleRoutes.rou.xml",
                        "--fringe-factor", "10", "--random", "--min-distance", "100", "--random-factor", "200"])

        script2 = constants.SUMO_TOOLS_PATH + "/routeSampler.py"
        if congestioned:
            #TODO: here some actions has to be taken in order to generate a congestioned scenario. Note that using
            # the totalVehicles parameters and the minLoops can generate congestioned traffic even if this parameter
            # is not set.
            subprocess.run([sys.executable,  script2, "-r", folderPath + "sampleRoutes.rou.xml",
                        "--edgedata-files", edgefile, "-o", folderPath +
                        "generatedRoutes.rou.xml", "--total-count", str(totalVehicles), "--optimize",
                        "full", "--min-count", str(minLoops)])
        else:
            subprocess.run([sys.executable,  script2, "-r", folderPath + "sampleRoutes.rou.xml",
                        "--edgedata-files", edgefile, "-o", folderPath +
                        "generatedRoutes.rou.xml", "--total-count", str(totalVehicles), "--optimize",
                        "full", "--min-count", str(minLoops)])
        print("Routes Generated")
        # self.sim.changeRoutePath(newpath + "generatedRoutes.rou.xml")

        relativeRouteFile = folderPath # + "generatedRoutes.rou.xml"
        routeFilePath = os.path.abspath(relativeRouteFile)
        return routeFilePath

    def setScenario(self, routeFilePath=None, manual: bool = False, absolutePath: bool = False):
        """
        Sets the scenario in the simulator by selecting a route file.
        A manual file can also be selected using a file dialog.

        :param routeFilePath: The path to the route file (optional if manual=True).
        :param manual: If True, opens a file dialog for manual route file selection.
        :param absolutePath: Boolean indicating if the provided routeFilePath is an absolute path.
        :raises FileNotFoundError: If the chosen route file does not exist.
        """
        if manual:
            Tk().withdraw()
            routeFilePath = askopenfilename(title="Select a Route File",
                                            filetypes=(("route files", "*.rou.xml"), ("xml files", "*.xml")))
            if not routeFilePath:
                print("No route file was selected.")
                return
            print("The chosen file was " + routeFilePath)

        if routeFilePath:
            if not absolutePath:
                routeFilePath = os.path.abspath(routeFilePath)
            if not os.path.exists(routeFilePath):
                raise FileNotFoundError(f"The route file '{routeFilePath}' does not exist.")
            self.sim.changeRoutePath(routePath=routeFilePath)
        else:
            print("No route file path was provided or selected.")

    def generateRandomRoute(self, sumoNetPath: str, timeSlot: str):
        """
        the function generates a set of routes for the map that can be used during the sampling phase
        Args:
            :param sumoNetPath:
            :param timeSlot: the timeslot of the simulation. It is used as a folder name.

        Returns:

        """
        timeSlot = timeSlot.replace(':', '-')
        #folder_name = f"{date}_{modelType}_{carFollowingModelType}/{timeSlot}"
        #folder_path = os.path.join("sumoenv/", folder_name)
        folder_name = f"{timeSlot}"
        folder_path = os.path.join("sumoenv/routes", folder_name)
        os.makedirs(folder_path, exist_ok=True)
        script = SUMO_TOOLS_PATH + "/randomTrips.py"
        subprocess.run(['python', script, "-n", sumoNetPath, "-r", folder_path + "/randomTrips.rou.xml",
                        "--output-trip-file", folder_path + "/trips.rou.xml",
                        "--trip-attributes", "type='customModel'",
                        "--random-departpos", "--random-arrivalpos",
                        "--allow-fringe", "--random",
                        "--remove-loops",
                        "--fringe-factor", "10", "--min-distance", "100", "--max-distance", "2000",
                        "--random-routing-factor", "10", "--period", "0.1"])


    def generateRoute(self, inputEdgePath: str, timeSlot: str, withInitialRoute=True, vType: str = "customModelCar",
                      total_count=10000, output_path : str = None ):
        """
        Based on the input edgefile that contains the traffic counts detected by the specific traffic loops in the map,
        the function generates routes for the map (saved in :param sumoNetPath) that respect these crossing constraints
        Args:
            :param inputEdgePath: the file containing the traffic count linked to the edge_id to observe when sampling
            :param timeSlot: the timeslot of the simulation. It is used as a folder name.
            :param withInitialRoute: if true, this will call generateRandomRoute. Put it to false if you already have
            routes to sample.

        Returns:
        """
        timeSlot = timeSlot.replace(':', '-')
        if withInitialRoute:
            self.generateRandomRoute(sumoNetPath=SUMO_NET_PATH, timeSlot=timeSlot)
        #folder_name = f"{date}_{modelType}_{carFollowingModelType}/{timeSlot}"
        folder_name = f"{timeSlot}"
        #folder_path = os.path.join("sumoenv/", folder_name)
        folder_path = os.path.join("sumoenv/routes", folder_name)
        # folder_path = output_path
        os.makedirs(folder_path, exist_ok=True)
        random_route_path = folder_path
        outputRoutePath = folder_path + "/generatedRoutes.rou.xml"
        script = SUMO_TOOLS_PATH + "/routeSampler.py"
        type = "type='" + str(vType) + "'"
        # process = subprocess.run([sys.executable, script, "--r", random_route_path + "/randomTrips.rou.xml",
        #                           "--edgedata-files", inputEdgePath, "-o",
        #                           folder_path + "/generatedRoutes.rou.xml", "--edgedata-attribute", "qPKW",
        #                           "--write-flows", "number", "--attributes", type,
        #                           "--total-count", str(total_count), "--optimize", "full", "--minimize-vehicles", "1",
        #                           "--threads", "8", "--verbose"],
        #                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True,
        #                          env=os.environ.copy(), bufsize=1)
        process = subprocess.run([sys.executable, script, "--r", random_route_path + "/randomTrips.rou.xml",
                                  "--edgedata-files", inputEdgePath, "-o",
                                  output_path, "--edgedata-attribute", "qPKW",
                                  "--write-flows", "number", "--attributes", type,
                                  "--total-count", str(total_count), "--optimize", "full", "--minimize-vehicles", "1",
                                  "--threads", "8", "--verbose", "--prefix", vType, "--edgedata-attribute", vType + '_entered'],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True,
                                 env=os.environ.copy(), bufsize=1)

        # process.wait()

    def merge_route_files(self, file_paths, output_path):
        """
        Merges multiple SUMO .rou.xml files containing <flow> (or <vehicle>) elements,
        sorting them by 'begin' attribute.
        """
        all_flows = []

        for file in file_paths:
            tree = ET.parse(file)
            root = tree.getroot()

            for elem in root:
                if elem.tag == "flow":  # puoi aggiungere "vehicle" se ti serve
                    all_flows.append(elem)

        # Ordina i flow per tempo di inizio (begin)
        all_flows.sort(key=lambda x: float(x.attrib.get("begin", 0.0)))

        # Ricrea il root
        merged_root = ET.Element("routes")
        for flow in all_flows:
            merged_root.append(flow)

        # Salva su file
        tree = ET.ElementTree(merged_root)
        ET.indent(tree, "  ")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"[INFO] Merged route file written to: {output_path}")

    def generateRoutesFromVTypes(self, routes_xml_path: str, inputEdgePath: str, timeSlot: str, total_count: int = 10000):
        """
        For each vType in a vTypeDistribution XML, it generates a route file proportional to its probability,
        and then merges all the results into a single generatedRoutes.rou.xml
        """

        timeSlot = timeSlot.replace(':', '-')
        folder_path = os.path.join("sumoenv/routes", timeSlot)
        os.makedirs(folder_path, exist_ok=True)
        vtypes_xml_path = routes_xml_path + "/vtype.add.xml"
        tree = ET.parse(vtypes_xml_path)
        root = tree.getroot()
        vtype_dist = root.find("vTypeDistribution")

        partial_files = []

        for vtype in vtype_dist.findall("vType"):
            vtype_id = vtype.attrib["id"]
            probability = float(vtype.attrib.get("probability", 0))
            n_vehicles = int(probability * total_count)

            print(f"Generating {n_vehicles} vehicles for {vtype_id}...")

            partial_output = os.path.join(routes_xml_path, f"partial_{vtype_id}.rou.xml")
            self.generateRoute(inputEdgePath=inputEdgePath,
                               timeSlot=timeSlot,
                               withInitialRoute=True,
                               vType=vtype_id,
                               total_count=n_vehicles,
                               output_path=partial_output)
            partial_files.append(partial_output)

        # Merge all partial route files into a single one
        final_output = os.path.join(folder_path, "generatedRoutes.rou.xml")
        self.merge_route_files(file_paths=partial_files, output_path=final_output)
        print(f"Final route file created at: {final_output}")


class Planner:
    """
    The Planner class manages traffic simulations by interacting with the sumoenv simulator and integrating it with a database.
    It also manages the scenario generation based on collected data.

    Class Attributes:
    - simulator (Simulator): An instance of the Simulator class.
    - scenarioGenerator (ScenarioGenerator): An instance of the ScenarioGenerator class.

    Class Methods:
    - __init__: Initializes a new instance of the Planner class.
    - planBasicScenarioForOneHourSlot: Plans a one-hour traffic simulation scenario based on collected data.
    """
    simulator: Simulator
    scenarioGenerator: ScenarioGenerator

    def __init__(self, simulator: Simulator):
        """
        Initializes the Planner with the given simulator instance.

        :param simulator: An instance of the Simulator class.
        """
        self.simulator = simulator
        self.scenarioGenerator = ScenarioGenerator(sumocfg="run.sumocfg",sim=self.simulator)

    def planBasicScenarioForOneHourSlot(self, collectedData: pd.DataFrame, entityType: str, totalVehicles: int, minLoops: int, congestioned: bool, activeGui: bool=False):
        """
        Plans a basic traffic simulation scenario for a one-hour timeslot based on the collected data.

        :param collectedData: A pandas DataFrame containing the collected traffic data with 'edgeid' and 'trafficflow' columns.
        :param entityType: The type of entity (e.g., "roadsegment").
        :param totalVehicles: The total number of vehicles to simulate.
        :param minLoops: Minimum number of loops or counting locations covered by each vehicle route.
        :param congestioned: Boolean flag to indicate whether the generated scenario should be congested.
        :return: A path to the generated scenario folder.
        :raises ValueError: If edge ID is missing or entity type is invalid.
        """
        if entityType.lower() not in ["road segment", "roadsegment"]:
            raise ValueError(f"Invalid entity type: {entityType}. Simulation requires edge IDs to generate a scenario.")

        root = ET.Element('data')
        interval = ET.SubElement(root, 'interval', begin='0', end='3600')
        scenarioFolder = self.scenarioGenerator.defineScenarioFolder(congestioned=congestioned)
        for _, row in collectedData.iterrows():
            edgeID = row.get('edgeid')
            trafficFlow = row.get('trafficflow')
            if edgeID is None:
                raise ValueError("Edge ID is missing for one of the rows in the collected data.")
            ET.SubElement(interval, 'edge', id=edgeID, entered=str(trafficFlow))


        tree = ET.ElementTree(root)
        ET.indent(tree, '  ')
        edgeFilePath = os.path.join(scenarioFolder, "edgefile.xml")
        tree.write(edgeFilePath, "UTF-8")
        routeFilePath = self.scenarioGenerator.generateRoutes(edgefile=edgeFilePath, folderPath=scenarioFolder, totalVehicles=totalVehicles, minLoops=minLoops, congestioned=congestioned)
        self.scenarioGenerator.setScenario(routeFilePath=routeFilePath, manual=False, absolutePath=True)
        logFilePath = os.path.join(scenarioFolder, "sumo_log.txt")
        self.simulator.start(activeGui=activeGui,logFilePath=logFilePath)

        return scenarioFolder



