import pandas as pd
import glob
import os
import math
import re


def evaluateError(detectedFlowPath: str, outputFilePath: str):
    """
    Function for calculating RMSE and MAPE values of flow, velocity and density
    Args:
        :param detectedFlowPath: path of the file to get flow, speed and density attribute
        :param outputFilePath: path of the file to save error data
    """
    error_data = []
    detector_df = pd.read_csv(detectedFlowPath, sep=';', decimal=',')
    # Initialise variables for RMSE and MAPE
    speed_squared_errors = 0
    speed_absolute_percentage_errors = 0
    speed_absolute_errors = 0
    speed_total_variance = 0

    density_squared_errors = 0
    density_absolute_percentage_errors = 0
    density_absolute_errors = 0
    density_total_variance = 0

    flow_squared_errors = 0
    flow_absolute_percentage_errors = 0
    flow_absolute_errors = 0
    flow_total_variance = 0
    n = 0  # Count valid data

    # Lists to store true values for calculating the range
    speed_true_values = []
    density_true_values = []
    flow_true_values = []

    count_true = 0
    count_pred = 0
    flow_gehs = []  # List to store GEH values

    # Iterate on traffic loops shared by model and SUMO data
    for id, row in detector_df.iterrows():
        speed_true = float(row["real_speed"])
        speed_pred = float(row["detected_speed"])
        density_true = float(row["real_density"])
        density_pred = float(row["detected_density"])
        flow_true = float(row["real_flow"])
        flow_pred = float(row["detected_flow"])
        count_true += int(row["real_count"])
        count_pred += int(row["detected_count"])
        if speed_pred != 0 and speed_true != 0:
            speed_squared_errors += (speed_pred - speed_true) ** 2
            speed_absolute_percentage_errors += abs((speed_true - speed_pred) / speed_true)
            speed_absolute_errors += abs((speed_true - speed_pred))
            speed_true_values.append(speed_true)
        if density_pred != 0 and density_true != 0:
            density_squared_errors += (density_pred - density_true) ** 2
            density_absolute_percentage_errors += abs((density_true - density_pred) / density_true)
            density_absolute_errors += abs((density_true - density_pred))
            density_true_values.append(density_true)
        if flow_pred != 0 and flow_true != 0:
            flow_squared_errors += (flow_pred - flow_true) ** 2
            flow_absolute_percentage_errors += abs((flow_true - flow_pred) / flow_true)
            flow_absolute_errors += abs((flow_true - flow_pred))
            flow_true_values.append(flow_true)
            # Calculate GEH for flow
        if count_true != 0:  # GEH is undefined when true flow is 0
            geh = math.sqrt((count_pred - count_true) ** 2 / (0.5 * (count_pred + count_true)))
        else:
            geh = 0
        flow_gehs.append(geh)
        if speed_pred == 0 or density_pred == 0 or flow_pred == 0:
            break
        n += 1
    # Get RMSE e MAPE
    if n > 0:
        print(n)
        print("Speed Squared errors" + str(speed_squared_errors))
        print("Density Squared errors" + str(density_squared_errors))
        print("Flow Squared errors" + str(flow_squared_errors))
        speed_mean_true = sum(speed_true_values) / n
        density_mean_true = sum(density_true_values) / n
        flow_mean_true = sum(flow_true_values) / n
        speed_total_variance = sum((val - speed_mean_true) ** 2 for val in speed_true_values)
        print("Speed total variance" + str(speed_total_variance))
        density_total_variance = sum((val - density_mean_true) ** 2 for val in density_true_values)
        print("Density total variance" + str(density_total_variance))
        flow_total_variance = sum((val - flow_mean_true) ** 2 for val in flow_true_values)
        print("Flow total variance" + str(flow_total_variance))

        speed_rmse = math.sqrt(speed_squared_errors / n)
        speed_mape = (speed_absolute_percentage_errors / n) * 100
        speed_mae = speed_absolute_errors / n
        speed_r2 = 1 - (speed_squared_errors / speed_total_variance) if speed_total_variance != 0 else 0

        density_rmse = math.sqrt(density_squared_errors / n)
        density_mape = (density_absolute_percentage_errors / n) * 100
        density_mae = density_absolute_errors / n
        density_r2 = 1 - (density_squared_errors / density_total_variance) if density_total_variance != 0 else 0

        flow_rmse = math.sqrt(flow_squared_errors / n)
        flow_mape = (flow_absolute_percentage_errors / n) * 100
        flow_mae = flow_absolute_errors / n
        flow_r2 = 1 - (flow_squared_errors / flow_total_variance) if flow_total_variance != 0 else 0

        # Calculate GEH average
        average_geh = sum(flow_gehs) / n

        # Calculate NRMSE
        speed_range = 0
        density_range = 0
        flow_range = 0
        if len(speed_true_values) != 0:
            speed_range = max(speed_true_values) - min(speed_true_values)
        if len(density_true_values) != 0:
            density_range = max(density_true_values) - min(density_true_values)
        if len(flow_true_values) != 0:
            flow_range = max(flow_true_values) - min(flow_true_values)
        speed_nrmse = speed_rmse / speed_range if speed_range != 0 else 0
        density_nrmse = density_rmse / density_range if density_range != 0 else 0

        speed_nmae = speed_mae / speed_range if speed_range != 0 else 0
        density_nmae = density_mae / density_range if density_range != 0 else 0
        flow_nmae = flow_mae / flow_range if flow_range != 0 else 0

        # print(f"Speed RMSE: {speed_rmse:.4f}")
        # print(f"Speed MAPE: {speed_mape:.2f}%")
        # print(f"Speed R^2: {speed_r2:.4f}")
        # print(f"Speed NRMSE: {speed_nrmse:.4f}")
        # print(f"Density RMSE: {density_rmse:.4f}")
        # print(f"Density MAPE: {density_mape:.2f}%")
        # print(f"Density R^2: {density_r2:.4f}")
        # print(f"Density NRMSE: {density_nrmse:.4f}")
        # print(f"Flow RMSE: {flow_rmse:.4f}")
        # print(f"Flow MAPE: {flow_pred:.2f}%")
        # print(f"Flow R^2: {flow_r2}")
        # print(f"Flow GEH: {average_geh:.4f}")
        error_data.append({
            'speed_rmse': speed_rmse,
            'speed_nrmse': speed_nrmse,
            'speed_mape': speed_mape,
            'speed_mae': speed_mae,
            'speed_nmae': speed_nmae,
            'speed_r2': speed_r2,
            'density_rmse': density_rmse,
            'density_nrmse': density_nrmse,
            'density_mape': density_mape,
            'density_mae': density_mae,
            'density_nmae': density_nmae,
            'density_r2': density_r2,
            'flow_rmse': flow_rmse,
            'flow_mape': flow_mape,
            'flow_mae': flow_mae,
            'flow_nmae': flow_nmae,
            'flow_r2': flow_r2,
            'flow_geh': average_geh
        })
        error_df = pd.DataFrame(error_data)
        error_df.to_csv(outputFilePath, sep=';', decimal=',')
        return error_data[0]  # Restituisce il dizionario

    else:
        print("No valid data for comparison.")


def evaluateErrorEverywhere():
    # Cartella principale che contiene tutte le sottocartelle
    input_folder = "./../sumoenv/"

    # Regex per riconoscere una data all'inizio del nome cartella (formato YYYY-MM-DD)
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
    # Process all CSV files in the current directory that start with "detectedFlow"
    csv_files = glob.glob(os.path.join(input_folder, "*detectedFlow*.csv"))
    # Trova tutte le sottocartelle di primo livello
    subfolders = [f.path for f in os.scandir(input_folder) if f.is_dir()]
    mean_error_data = []  # Per raccogliere tutti gli errori individuali

    for subfolder in subfolders:
        detected_flow_path = os.path.join(subfolder, "detected_output")  # O detected_output se è quello corretto
        if not os.path.isdir(detected_flow_path):
            continue

        csv_files = [
            os.path.join(detected_flow_path, f)
            for f in os.listdir(detected_flow_path)
            if f.endswith(".csv") and "detectedFlow" in f
        ]

        for file in csv_files:
            filename = os.path.basename(file)
            suffix = filename.replace("detectedFlow", "")
            output_filename = f"error_summary{suffix}"
            output_folder = os.path.join("error_output", output_filename)
            output_path = os.path.join(subfolder, output_folder)

            print(f"Processing {file} -> {output_path}")
            error = evaluateError(file, output_path)
            if error:
                mean_error_data.append(error)  # Salva il dizionario per media finale

        # Calcola media finale e salva in mean_summary
        if mean_error_data:
            mean_df = pd.DataFrame(mean_error_data)
            mean_row = mean_df.mean().to_frame().T  # Media di ogni colonna
            output_filename = f"mean_errors.csv"
            output_path = os.path.join(subfolder, output_filename)
            mean_row.to_csv(output_path, sep=';', decimal=',', index=False)
            print("Saved mean_summary.csv")
        else:
            print("No error data collected to compute mean.")

def evaluateSimulationError(folderPath: str):
    input_folder = "./../sumoenv/"
    mean_error_data = []
    detected_flow_path = os.path.join(folderPath, "detected_output")  # O detected_output se è quello corretto
    if not os.path.isdir(detected_flow_path):
        print("The given path is not a dir!")
        return

    csv_files = [
        os.path.join(detected_flow_path, f)
        for f in os.listdir(detected_flow_path)
        if f.endswith(".csv") and "detectedFlow" in f
    ]

    for file in csv_files:
        filename = os.path.basename(file)
        suffix = filename.replace("detectedFlow", "")
        output_filename = f"error_summary{suffix}"
        output_folder = os.path.join("error_output", output_filename)
        output_path = os.path.join(folderPath, output_folder)

        print(f"Processing {file} -> {output_path}")
        error = evaluateError(file, output_path)
        if error:
            mean_error_data.append(error)  # Salva il dizionario per media finale

    # Compute final mean and save in mean_summary
    if mean_error_data:
        mean_df = pd.DataFrame(mean_error_data)
        mean_row = mean_df.mean().to_frame().T  # Media di ogni colonna
        output_filename = f"mean_errors.csv"
        output_path = os.path.join(folderPath, output_filename)
        mean_row.to_csv(output_path, sep=';', decimal=',', index=False)
        print("Saved mean_summary.csv")
    else:
        print("No error data collected to compute mean.")

def compute_mean_road_metrics(folderPath: str):
    '''
    Explores all the simulation folders present in folderPath and retrieves the edge data output.
    Calculates the average relative to the values of travel time, waiting time, loss time, and speed for each road and
    then averages it for each simulation present
    Args:
        folderPath: path in which simulation folders are stored

    Returns:
        a json file containing the averaged metrics
    '''
    metrics_to_extract = ['traveltime', 'waitingTime', 'timeLoss', 'speed']
    all_aggregated_metrics = []

    for subdir in os.listdir(folderPath):
        full_subdir_path = os.path.join(folderPath, subdir)
        if not os.path.isdir(full_subdir_path):
            continue

        output_path = os.path.join(full_subdir_path, 'output', 'edgedata-output.xml')
        if not os.path.isfile(output_path):
            continue

        try:
            tree = ET.parse(output_path)
            root = tree.getroot()

            edge_values = {key: [] for key in metrics_to_extract}
            for interval in root.findall('interval'):
                for edge in interval.findall('edge'):
                    for metric in metrics_to_extract:
                        value = edge.get(metric)
                        if value is not None:
                            edge_values[metric].append(float(value))

            mean_metrics = {}
            for metric, values in edge_values.items():
                if values:
                    mean_metrics[metric] = sum(values) / len(values)
                else:
                    mean_metrics[metric] = None

            all_aggregated_metrics.append(mean_metrics)

        except Exception as e:
            print(f"Error in the parsing of {output_path}: {e}")

    final_means = {}
    for metric in metrics_to_extract:
        values = [entry[metric] for entry in all_aggregated_metrics if entry[metric] is not None]
        if values:
            final_means[metric] = sum(values) / len(values)
        else:
            final_means[metric] = None

    output_path = os.path.join(folderPath, 'mean_metrics.json')
    with open(output_path, 'w') as f:
        json.dump(final_means, f, indent=4)

    print(f"Saved in: {output_path}")
    return final_means

import os
import xml.etree.ElementTree as ET
import json


def compute_mean_tripinfo_metrics(base_folder):
    '''
    Explores all the simulation folders present in folderPath and retrieves the trip info output.
    Calculates the average relative to the values of duration, waiting time, loss time, and route length for each trip
    (i.e., each car) and then averages it for each simulation present .
    Args:
        folderPath: path in which simulation folders are stored

    Returns:
        a json file containing the averaged metrics
    '''
    metrics_to_extract = ['duration', 'waitingTime', 'timeLoss', 'routeLength']
    all_metrics = []

    for subdir in os.listdir(base_folder):
        full_subdir_path = os.path.join(base_folder, subdir)
        if not os.path.isdir(full_subdir_path):
            continue

        file_path = os.path.join(full_subdir_path, 'output', 'tripinfos.xml')
        if not os.path.isfile(file_path):
            continue

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            values = {k: [] for k in metrics_to_extract}
            speeds = []

            for tripinfo in root.findall('tripinfo'):
                try:
                    duration = float(tripinfo.get('duration'))
                    waiting = float(tripinfo.get('waitingTime'))
                    time_loss = float(tripinfo.get('timeLoss'))
                    route_length = float(tripinfo.get('routeLength'))

                    if duration > 0:
                        speed = route_length / duration
                        speeds.append(speed)

                    values['duration'].append(duration)
                    values['waitingTime'].append(waiting)
                    values['timeLoss'].append(time_loss)
                    values['routeLength'].append(route_length)

                except (TypeError, ValueError):
                    continue

            mean_metrics = {}
            for metric, vals in values.items():
                mean_metrics[metric] = sum(vals) / len(vals) if vals else None

            mean_metrics['computedSpeed'] = (sum(speeds) / len(speeds)) if speeds else None

            all_metrics.append(mean_metrics)

        except Exception as e:
            print(f"Error in the parsing of {file_path}: {e}")

    # Final average over all folders
    final_result = {}
    for metric in metrics_to_extract + ['computedSpeed']:
        vals = [entry[metric] for entry in all_metrics if entry[metric] is not None]
        final_result[metric] = (sum(vals) / len(vals)) if vals else None

    output_path = os.path.join(base_folder, 'mean_tripinfo_metrics.json')
    with open(output_path, 'w') as f:
        json.dump(final_result, f, indent=4)

    print(f"Salvato in: {output_path}")
    return final_result
