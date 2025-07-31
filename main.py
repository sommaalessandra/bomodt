import libraries.constants
from libraries.utils.generalUtils import *
from libraries.utils.preprocessingUtils import *
from libraries.classes.DataManager import *
from libraries.classes.Planner import Planner
from libraries.classes.DigitalTwinManager import DigitalTwinManager
from libraries.classes.Agent import *
from libraries.classes.SumoSimulator import Simulator
from libraries.classes.SubscriptionManager import QuantumLeapManager
from libraries.classes.Broker import Broker
from libraries.classes.TrafficModeler import TrafficModeler
from mobilityvenv.MobilityVirtualEnvironment import setupPhysicalSystem, startPhysicalSystem
from data.preprocessing import preprocessingSetup


if __name__ == "__main__":

    # 0. Pre-processing phase (to be run only once)
    # preprocessingSetup.run()

    # 1. Instantiate Orion CB, IoT Agent and create three types of subscriptions.
    envVar = loadEnvVar(CONTAINER_ENV_FILE_PATH)
    iotanorth = envVar.get("IOTA_NORTH_PORT")
    iotasouth = envVar.get("IOTA_SOUTH_PORT")
    cbport = envVar.get("ORIONLD_PORT")
    timescalePort = envVar.get("TIMESCALE_DB_PORT")
    quantumleapPort = envVar.get("QUANTUMLEAP_PORT")
    contextBroker = Broker(pn=cbport, pnt=None, host="localhost", fiwareservice="openiot")
    cbConnection = contextBroker.createConnection()
    IoTAgent = Agent(aid="01", hostname="localhost", cb_port=cbport, south_port=iotasouth, northport=iotanorth, fw_service="openiot", fw_path="/")
    quantumLeapManager = QuantumLeapManager(containerName="fiware-quantumleap", cbPort=cbport, quantumleapPort=quantumleapPort)

    quantumLeapManager.createQuantumLeapSubscription(cbConnection=cbConnection, entityType="RoadSegment", attribute="trafficFlow", description="Notify me of Traffic Flow")
    quantumLeapManager.createQuantumLeapSubscription(cbConnection=cbConnection, entityType="trafficflowobserved", attribute="trafficFlow", description="Notify me of Traffic Flow")
    quantumLeapManager.createQuantumLeapSubscription(cbConnection=cbConnection, entityType="Device", attribute="trafficFlow", description="Notify me of traffic Flow")


    #### Comment/decomment these two code lines to run the physical system.
    # TODO: thread-multiprocessing
    # roads, files = setupPhysicalSystem(IoTAgent)
    # startPhysicalSystem(roads)

    # 2. The DigitalTwinManager needs i) a DataManager for accessing data; ii) a SumoSimulator for running simulations
    #    iii) a Planner including a ScenarioGenerator for generating sumoenv scenarios.
    timescaleManager = TimescaleManager(
        host="localhost",
        port=timescalePort,
        dbname="quantumleap",
        username="postgres",
        password="postgres"
    )
    dataManager = DataManager("TwinDataManager")
    dataManager.addDBManager(timescaleManager)

    configurationPath = SUMO_PATH + "/standalone"
    logFile = SUMO_PATH + "/standalone/command_log.txt"

    detector_output = os.path.abspath(SUMO_PATH + "/output")
    os.makedirs(detector_output, exist_ok=True)

    sumoSimulator = Simulator(configurationPath=configurationPath, logFile=logFile)
    twinPlanner = Planner(simulator=sumoSimulator)
    twinManager = DigitalTwinManager(dataManager=dataManager, simulator=sumoSimulator, sumoConfigurationPath=configurationPath, sumoLogFile=logFile)

    # The date to simulate is set here.
    # TODO: ask for simulation date or start from a date on
    simulationDate = '2024-02-01'

    # 3. Route generation process. This will generate 24h traffic route for a specific date.
    # put generateRoutes to true/false if you want (or not) to generate traffic
    generateRoutes = False
    if generateRoutes:
        for hour in range(24):
            if hour < 9:
                timeSlotFolder = '0' + str(hour) + ':00-' + '0' + str(hour + 1) + ':00'
            elif hour == 9:
                timeSlotFolder = '0' + str(hour) + ':00-' + str(hour + 1) + ':00'
            else:
                timeSlotFolder = str(hour) + ':00-' + str(hour + 1) + ':00'
            generateEdgeDataFile(PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH, date=simulationDate, time_slot=timeSlotFolder)
            twinPlanner.scenarioGenerator.generateRoute(inputEdgePath=EDGE_DATA_FILE_PATH, timeSlot=timeSlotFolder)

    # 4. Simulation of one hour slot scenario. The function will open sumo gui. The play button must be pressed to run the simulation. When simulation ends, the function returns the folder path in which sumoenv files have been generated.
    # scenarioFolder = twinManager.simulateBasicScenarioForOneHourSlot(timeslot="00:00-01:00", date="2024/02/01", entityType='Road Segment', totalVehicles=100, minLoops=3, congestioned=False, activeGui=True, timecolumn="timeslot")
    # print(scenarioFolder)
    # twinManager.generateGraphs(scenarioFolder)
    # twinManager.showGraphs(scenarioFolder, saveSummary=False)


    # 5. Configuration of Macroscopic traffic model and car-following model with 24-hour simulation.
    # The output of simulation will be compared to the macroscopic data previously constructed.
    macroModelType = "greenshield"
    carFollowingModel = "Krauss"
    ### ADDITIONAL KRAUSS PARAMS additionalParam={"sigma": "0", "sigmaStep": "1"}
    ### ADDITIONAL IDM PARAMS additionalParam={"delta": "6","stepping": "0.1"})
    ### ADDITIONAL W99 PARAMS additionalParam={"cc1": "1.5", "cc2": "10.0"})

    # This loop is made for an automated testing of Krauss car-following model with all its combinations
    for i in range(18):
        # time.sleep(10)
        if i == 0:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH, carFollowingModel=carFollowingModel,
                                               macroModelType=macroModelType, tau="1", parameters={"sigma": "0.5", "sigmaStep": "1"},
                                               date=simulationDate, timeslot=[0,24])
        elif i == 1:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="Krauss",
                                                 macroModelType=macroModelType, tau="1",
                                                 parameters={"sigma": "1", "sigmaStep": "5"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 2:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="Krauss",
                                                 macroModelType=macroModelType, tau="1",
                                                 parameters={"sigma": "0", "sigmaStep": "1"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 3:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="Krauss",
                                                 macroModelType=macroModelType, tau="1.5",
                                                 parameters={"sigma": "0.5", "sigmaStep": "2"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 4:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="Krauss",
                                                 macroModelType=macroModelType, tau="1.5",
                                                 parameters={"sigma": "1", "sigmaStep": "5"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 5:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="Krauss",
                                                 macroModelType=macroModelType, tau="1.5",
                                                 parameters={"sigma": "0", "sigmaStep": "1"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 6:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH, carFollowingModel="IDM",
                                             macroModelType=macroModelType, tau="1", parameters={"delta": "4", "stepping": "0.25"},
                                             date=simulationDate, timeslot=[0, 24])
        elif i == 7:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="IDM",
                                                 macroModelType=macroModelType, tau="1",
                                                 parameters={"delta": "2", "stepping": "1"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 8:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="IDM",
                                                 macroModelType=macroModelType, tau="1",
                                                 parameters={"delta": "6", "stepping": "0.1"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 9:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH, carFollowingModel="IDM",
                                             macroModelType=macroModelType, tau="1.5", parameters={"delta": "4", "stepping": "0.25"},
                                             date=simulationDate, timeslot=[0,24])
        elif i == 10:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="IDM",
                                                 macroModelType=macroModelType, tau="1.5",
                                                 parameters={"delta": "2", "stepping": "1"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 11:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="IDM",
                                                 macroModelType=macroModelType, tau="1.5",
                                                 parameters={"delta": "6", "stepping": "0.1"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 12:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH, carFollowingModel="W99",
                                             macroModelType=macroModelType, tau="1", parameters={"cc1": "1.3", "cc2": "8"},
                                             date=simulationDate, timeslot=[0,24])
        elif i == 13:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="W99",
                                                 macroModelType=macroModelType, tau="1",
                                                 parameters={"cc1": "1.5", "cc2": "10"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 14:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="W99",
                                                 macroModelType=macroModelType, tau="1",
                                                 parameters={"cc1": "1", "cc2": "4"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 15:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH, carFollowingModel="W99",
                                             macroModelType=macroModelType, tau="1.5", parameters={"cc1": "1.3", "cc2": "8"},
                                             date=simulationDate, timeslot=[0,24])
        elif i == 16:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="W99",
                                                 macroModelType=macroModelType, tau="1.5",
                                                 parameters={"cc1": "1.5", "cc2": "10"},
                                                 date=simulationDate, timeslot=[0, 24])
        elif i == 17:
            twinManager.configureCalibrateAndRun(dataFilePath=PROCESSED_TRAFFIC_FLOW_EDGE_FILE_PATH,
                                                 carFollowingModel="W99",
                                                 macroModelType=macroModelType, tau="1.5",
                                                 parameters={"cc1": "1", "cc2": "4"},
                                                 date=simulationDate, timeslot=[0, 24])
