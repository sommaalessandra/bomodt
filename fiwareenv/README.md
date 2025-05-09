# FIWARE Platform Deployment

This ```docker-compose.yml``` setup file creates a FIWARE-powered smart city platform that integrates IoT devices, manages real-time context data, and enables historical analysis. Below is a detailed explanation of the core components and their interactions:
  -  **Orion-LD Context Broker**: Orion-LD is the core system of the platform. As an NGSI-LD compliant context broker, it manages digital representations of physical entities (e.g., roads, induction loop sensors, traffic light system). When a sensor sends new data (like vehicle counts), 
Orion-LD updates the corresponding entity's state and propagates these changes to subscribed components (e.g. QuantumLeap for managing historical data). It relies on **MongoDB** to persistently store entity data and exposes its API for CRUD operations and subscriptions.

  -  **IoT Agent-JSON**: This component serves as the bridge between physical IoT devices and the FIWARE ecosystem. When a device (e.g., traffic loop) registers with its API key, the IoT Agent translates raw device data into NGSI-LD format. It uses **MongoDB** to maintain a registry of connected devices and their metadata.

  -  **QuantumLeap + TimescaleDB**: QuantumLeap works as the platform's historic data manager. Whenever Orion-LD updates an entity, QuantumLeap captures the change and stores a timestamped record in **TimescaleDB** – a PostgreSQL extension optimized for time-series data. This enables powerful temporal queries, and it's capable
to speed up frequent queries, by leveraging **Redis** as an in-memory cache layer.

  -  **Grafana**: Grafana connects to TimescaleDB to create dynamic dashboards showing time-series trends, geographic distributions (using PostGIS coordinates), and real-time metrics. Pre-installed plugins enhance its capabilities for spatial and temporal data analysis. This component is embedded within the interfaces by the web application. 


### Key Interactions
Most of the interactions are explained by the data pipeline, in which the transmitted data is taken as input from the system and is modeled, stored, and routed among the various components. 
The pipeline can be summarized in this flow:

 ```beginSensor → Raw data → IoT Agent (JSON-to-NGSI conversion) → Orion-LD (entity update) → QuantumLeap (historical storage in TimescaleDB).```

1. **Device Onboarding**:  
   A traffic sensor registers via the IoT Agent, which in turn it creates an NGSI-LD entity in Orion-LD.

2. **Data Pipeline**:   
   Through its subscription mechanism, Orion-LD notifies QuantumLeap of data change in the registered entities. QuantumLeap add a timestamp to the data and archives the change into TimescaleDB.
   
3. **Monitoring**:  
   FlowTwin leverages Orion-LD's API for real-time status query, while Grafana pulls historical data from TimescaleDB for monitoring purposes.

### Key Dependencies
The following are the dependencies of the various containers in the docker-compose file:
  - Orion-LD → MongoDB
  - QuantumLeap → Orion-LD + TimescaleDB + Redis
  - IoT Agent → MongoDB + Orion-LD
   
### How to run
to start the service, you can simply run:
```
docker-compose up -d
```
