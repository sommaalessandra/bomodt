import typing
from libraries.constants import SHADOWS_PATH, SHADOW_TYPE_FILE_PATH
import pandas as pd
import os
import shutil

class Shadow:
    name: str

    def __init__(self, name: str, **attributes):
        self.name = name
        for key, value in attributes.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"Shadow(name={self.name}, attributes={self.__dict__})"

    def get(self, attribute: str) -> typing.Any:
        # get an attribute
        return getattr(self, attribute, None)

    def set(self, attribute: str, value: typing.Any) -> None:
        # set an attribute to value
        setattr(self, attribute, value)

    def getAllAttributes(self) -> typing.Dict[str, typing.Any]:
        # retrieve all attributes
        return self.__dict__


class ShadowDataProcessor:
    """
    The ShadowDataProcessor class processes data related to traffic loops and roads using geographical coordinates.
    It provides methods to search for roads and traffic loops based on coordinates, device IDs, and directions.

    """

    def __init__(self, datapath):
        self.df = pd.read_csv(datapath, sep=';')
        self.df.columns = [
            'StartingPoint', 'EndPoint', 'RoadName', 'Direction', 'Longitude',
            'Latitude', 'Geopoint', 'TrafficLoopID', 'EdgeID', 'TrafficLoopCode',
            'TrafficLoopLevel'
        ]

    def searchRoad(self, coordinates, direction: str, deviceID: str) -> typing.Tuple[str, str, str, str]:
        if self.df.empty:
            raise ValueError("The DataFrame is empty or not loaded correctly.")

        coordinatestr = f"{coordinates[0]}, {coordinates[1]}"
        loopID = deviceID.split('TL')[-1]

        self.df['Geopoint'] = self.df['Geopoint'].astype(str).str.strip()
        self.df['TrafficLoopID'] = self.df['TrafficLoopID'].astype(str).str.strip()
        self.df['Direction'] = self.df['Direction'].str.strip().str.lower()

        matchingRow = self.df[
            (self.df['Geopoint'] == coordinatestr) &
            (self.df['TrafficLoopID'] == loopID) &
            (self.df['Direction'] == direction.lower())
            ]

        if matchingRow.empty:
            raise ValueError(
                f"No matching rows found for the given coordinates {coordinates} and direction {direction}.")
        if len(matchingRow) > 1:
            raise ValueError("Multiple matching rows found; expected a single match.")
        roadName = matchingRow.iloc[0]['RoadName']
        edgeID = matchingRow.iloc[0]['EdgeID']
        startPoint = matchingRow.iloc[0]['StartingPoint']
        endPoint = matchingRow.iloc[0]['EndPoint']
        return roadName, edgeID, startPoint, endPoint

    def searchTrafficLoop(self, deviceID: str, coordinates, direction: str) -> typing.Tuple[str, int]:
        if self.df.empty:
            raise ValueError("The DataFrame is empty or not loaded correctly.")

        coordinatestr = f"{coordinates[0]}, {coordinates[1]}"
        loopID = deviceID.split('TL')[-1]

        self.df['Geopoint'] = self.df['Geopoint'].astype(str).str.strip()
        self.df['TrafficLoopID'] = self.df['TrafficLoopID'].astype(str).str.strip()
        self.df['Direction'] = self.df['Direction'].str.strip().str.lower()

        # Filter based on coordinates, unique ID, and direction
        matchingRow = self.df[
            (self.df['Geopoint'] == coordinatestr) &
            (self.df['TrafficLoopID'] == loopID) &
            (self.df['Direction'] == direction.lower())
            ]

        if matchingRow.empty:
            raise ValueError(
                f"No matching rows found for the given coordinates {coordinates}, direction {direction} and unique TL ID {loopID}.")
        if len(matchingRow) > 1:
            raise ValueError("Multiple matching rows found; expected a single match.")
        loopCode = str(matchingRow.iloc[0]['TrafficLoopCode'])
        loopLevel = int(matchingRow.iloc[0]['TrafficLoopLevel'])
        return loopCode, loopLevel



class DigitalShadowManager:

    def __init__(self):
        self.clearShadowData()
        self.shadowsByTypes: typing.Dict[str, typing.List[Shadow]] = {}
        self.dataProcessor = ShadowDataProcessor(SHADOW_TYPE_FILE_PATH)

    def clearShadowData(self):
        """
        Clears shadow data (directories and files) in the SHADOWS_PATH, but preserves the shadowFilePath file.
        """
        if os.path.exists(SHADOWS_PATH):
            for item in os.listdir(SHADOWS_PATH):
                itemPath = os.path.join(SHADOWS_PATH, item)
                if itemPath == SHADOW_TYPE_FILE_PATH:
                    continue
                if os.path.isdir(itemPath):
                    shutil.rmtree(itemPath)
                elif os.path.isfile(itemPath):
                    os.remove(itemPath)
            print(f"Cleared shadow data from {SHADOWS_PATH}, preserving {SHADOW_TYPE_FILE_PATH}.")

    def addShadow(self, shadowType: str, timeSlot: str, trafficFlow: int, coordinates: typing.List[float], direction: str, taz: str, deviceID: str) -> Shadow:
        try:
            if shadowType == "road":
                roadName, edgeID, startPoint, endPoint = self.dataProcessor.searchRoad(coordinates=coordinates,direction=direction, deviceID=deviceID)
                shadowAttributes = {
                    "startPoint": startPoint,
                    "endPoint": endPoint,
                    "coordinates": coordinates,
                    "direction": direction,
                    "taz": taz,
                    "timeSlot": timeSlot,
                    "trafficFlow": trafficFlow,
                    "edgeID": edgeID
                }

                newShadow = Shadow(name=roadName, **shadowAttributes)
                # adding the shadow to the shadow list w.r.t the appropriate type
                if shadowType not in self.shadowsByTypes:
                    self.shadowsByTypes[shadowType] = []
                self.shadowsByTypes[shadowType].append(newShadow)
                self.saveShadowToCSV(shadowType=shadowType, shadow=newShadow)
                return newShadow
            elif shadowType == "trafficLoop":
                loopCode, loopLevel = self.dataProcessor.searchTrafficLoop(coordinates=coordinates, direction=direction,
                                                                           deviceID=deviceID)
                shadowAttributes = {
                    "coordinates": coordinates,
                    "timeSlot": timeSlot,
                    "trafficFlow": trafficFlow,
                    "loopCode": loopCode,
                    "loopLevel": loopLevel
                }
                newShadow = Shadow(name=deviceID, **shadowAttributes)
                if shadowType not in self.shadowsByTypes:
                    self.shadowsByTypes[shadowType] = []
                self.shadowsByTypes[shadowType].append(newShadow)
                self.saveShadowToCSV(shadowType=shadowType, shadow=newShadow)
                return newShadow

        except ValueError as e:
            print(f"Error occurred: {e}")
            raise RuntimeError(f"Failed to create shadow: {e}")

    def searchShadow(self, shadowType: str, timeSlot: str, trafficFlow: int, coordinates: typing.List[float],
                     laneDirection: str, taz: str, deviceID: str) -> Shadow:
        if shadowType in self.shadowsByTypes and shadowType == "road":
            for shadow in self.shadowsByTypes[shadowType]:
                if (shadow.get("coordinates") == coordinates and
                        shadow.get("direction") == laneDirection and
                        shadow.get("trafficFlow") == trafficFlow and shadow.get("taz")):
                    return shadow
        elif shadowType in self.shadowsByTypes and shadowType == "trafficLoop":
            for shadow in self.shadowsByTypes[shadowType]:
                if (shadow.get("coordinates") == coordinates and
                        shadow.name == deviceID and
                        shadow.get("trafficFlow") == trafficFlow):
                    return shadow

        # if no matching shadow is found, it creates a new one
        try:
            if shadowType == "road":
                newShadow = self.addShadow(shadowType, timeSlot=timeSlot, trafficFlow=trafficFlow,
                                           coordinates=coordinates, direction=laneDirection, taz=taz, deviceID=deviceID)
                return newShadow
            elif shadowType == "trafficLoop":
                newShadow = self.addShadow(shadowType, timeSlot=timeSlot, trafficFlow=trafficFlow,
                                           coordinates=coordinates, direction=laneDirection, deviceID=deviceID)
                return newShadow

        except RuntimeError as e:
            print(f"Error in searchShadow: {e}")
            raise ValueError("Unable to create or find the shadow.")


    def saveShadowToCSV(self, shadowType: str, shadow: Shadow):
        """
        Save shadow data to a CSV file inside the folder SHADOWS_PATH+shadowType, using ';' as the separator.

        :param shadowType: Type of the shadow, which determines the folder within SHADOWS_PATH.
        :param shadow: Shadow object containing attributes and data to save.
        """
        # Create the directory path
        directoryPath = os.path.join(SHADOWS_PATH, shadowType)
        os.makedirs(directoryPath, exist_ok=True)

        # Set the file path and name
        fileName = shadow.name.replace(" ", "_") + ".csv"
        filePath = os.path.join(directoryPath, fileName)

        # Retrieve and prepare shadow attributes
        shadowAttributes = shadow.getAllAttributes()
        coordinates = shadowAttributes.get("coordinates", [None, None])

        # Add latitude and longitude columns from coordinates
        shadowAttributes["latitude"] = coordinates[0]
        shadowAttributes["longitude"] = coordinates[1]

        # Create a DataFrame from shadow attributes
        shadowData = pd.DataFrame([shadowAttributes])

        # Save to CSV with ';' as the separator
        if os.path.exists(filePath):
            shadowData.to_csv(filePath, sep=';', mode='a', header=False, index=False)
        else:
            shadowData.to_csv(filePath, sep=';', mode='w', header=True, index=False)
