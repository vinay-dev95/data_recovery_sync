##############################################################################
#
# Module: iot_data_sync.py
#
# Description:
#     This script processes and synchronizes IoT data from two sources:
#     - InfluxDB Excel export (InfluxDB_2024.xlsx)
#     - SIM card data (Simcard_2024.xlsx)
#
#     Key functionalities include:
#     - Convert Excel files to CSV
#     - Print CSV headers
#     - Count specific column values
#     - Detect missing 6-minute intervals and insert synthetic rows
#     - Patch missing rows with sensor readings from SIM card data
#     - Write the final cleaned and patched dataset to `update.csv`
#     - Optionally plot data using matplotlib
#
# Author:
#     Vinay N
#
# Revision History:
#     V1.0.1  Mon June 2025  Vinay N
#         Added interactive graph plotting
#
##############################################################################

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from data_sync import convert_excel_to_csv
import matplotlib.dates as mdates

def print_csv_header(csv_path):
    try:
        df = pd.read_csv(csv_path, nrows=0)
        print(f"\nCSV Header ({csv_path}):")
        print(", ".join(df.columns))
    except Exception as e:
        print(f"Error reading header from {csv_path}: {e}")


def count_boot_column(csv_path):
    try:
        df = pd.read_csv(csv_path)
        boot_count = df['boot'].count()
        print(f"Total rows with 'boot' value in {csv_path}: {boot_count}")
    except Exception as e:
        print(f"Error counting 'boot' values: {e}")


def count_sno_column(csv_path):
    try:
        df = pd.read_csv(csv_path)
        sno_count = df['Sno'].count()
        print(f"Total rows with 'Sno' value in {csv_path}: {sno_count}")
    except Exception as e:
        print(f"Error counting 'Sno' values: {e}")


def detect_time_gaps_and_insert_missing_rows(csv_path, threshold_minutes=6, output_path="update.csv"):
    try:
        df = pd.read_csv(csv_path, parse_dates=['time'])
        df = df.sort_values('time').reset_index(drop=True)

        columns = df.columns.tolist()
        data = []

        for i in range(1, len(df)):
            prev_row = df.iloc[i - 1]
            curr_row = df.iloc[i]

            data.append(prev_row.to_dict())

            time_diff = curr_row['time'] - prev_row['time']
            if time_diff > timedelta(minutes=threshold_minutes):
                next_time = prev_row['time'] + timedelta(minutes=threshold_minutes)
                while next_time < curr_row['time']:
                    if not ((df['time'] == next_time).any()):
                        missing_row = {'time': next_time}
                        for col in columns:
                            if col in ['Sno', 'time']:
                                continue
                            elif col in ['applicationName', 'boot', 'devEUI']:
                                missing_row[col] = prev_row[col]
                            else:
                                missing_row[col] = 0
                        data.append(missing_row)
                        print(f"[MISSING INSERTED] {next_time}")
                    next_time += timedelta(minutes=threshold_minutes)

        data.append(df.iloc[-1].to_dict())

        for row in data:
            if 'time' in row and not pd.isnull(row['time']):
                try:
                    ts = pd.to_datetime(row['time'])
                    row['time'] = ts.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
                except Exception:
                    pass

        updated_df = pd.DataFrame(data)
        updated_df.insert(0, 'Sno', range(1, len(updated_df) + 1))
        updated_df.to_csv(output_path, index=False)
        print(f"[+] Missing data added and written to {output_path}")

    except Exception as e:
        print(f"[ERROR] Failed to process and write {output_path}: {e}")


def patch_missing_rows_with_simcard(update_csv, simcard_csv):
    try:
        update_df = pd.read_csv(update_csv)
        simcard_df = pd.read_csv(simcard_csv)

        cols_to_patch = ['p', 'rh', 'temp_soil', 'temp']
        patched_count = 0

        for i in range(len(update_df)):
            row = update_df.iloc[i]
            if all(row[col] == 0 or str(row[col]) == '0.0' for col in cols_to_patch):
                devEUI = row['devEUI']
                sno = row['Sno']
                match = simcard_df[(simcard_df['DevEUI'] == devEUI) & (simcard_df['Sno'] == sno)]
                if not match.empty:
                    match_row = match.iloc[0]
                    for col in cols_to_patch:
                        update_df.at[i, col] = match_row[col]
                    patched_count += 1
                    print(f"[PATCHED] Row Sno={sno} with Simcard data")

        update_df.to_csv(update_csv, index=False)
        print(f"[+] Patched {patched_count} rows in {update_csv}")

    except Exception as e:
        print(f"[ERROR] Failed to patch missing data: {e}")


def plot_update_csv(csv_path="update.csv"):
    try:
        df = pd.read_csv(csv_path, parse_dates=['time'])
        df = df.sort_values('time')

        # Format time column to include Z for display
        df['time_str'] = df['time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'

        plt.style.use('dark_background')
        fig, axs = plt.subplots(4, 1, figsize=(15, 12), sharex=True)
        fig.suptitle("Sensor Readings Over Time", fontsize=16, color='white')

        axs[0].plot(df['time_str'], df['p'], color='cyan', linewidth=1.5)
        axs[0].set_ylabel("Pressure (p)")
        axs[0].grid(True)

        axs[1].plot(df['time_str'], df['rh'], color='lime', linewidth=1.5)
        axs[1].set_ylabel("Humidity (rh)")
        axs[1].grid(True)

        axs[2].plot(df['time_str'], df['temp'], color='red', linewidth=1.5)
        axs[2].set_ylabel("Air Temp (temp)")
        axs[2].grid(True)

        axs[3].plot(df['time_str'], df['temp_soil'], color='orange', linewidth=1.5)
        axs[3].set_ylabel("Soil Temp (temp_soil)")
        axs[3].set_xlabel("Time (UTC ISO Format)")
        axs[3].grid(True)

        # Improve x-axis labels
        for ax in axs:
            ax.tick_params(axis='x', rotation=45, labelsize=8)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()

    except Exception as e:
        print(f"[ERROR] Failed to plot: {e}")


def main():
    print("Running...")
    files_to_convert = {
        "InfluxDBData": "InfluxDB_2024.xlsx",
        "SimcardData": "Simcard_2024.xlsx"
    }

    influx_csv = None
    simcard_csv = None

    for label, filename in files_to_convert.items():
        if os.path.exists(filename):
            csv_path = convert_excel_to_csv(filename)
            if csv_path:
                print(f"Convert xlsx to csv ({label}) : {csv_path}")
                print_csv_header(csv_path)

                if label == "InfluxDBData":
                    count_boot_column(csv_path)
                    detect_time_gaps_and_insert_missing_rows(
                        csv_path,
                        threshold_minutes=6,
                        output_path="update.csv"
                    )
                    influx_csv = "update.csv"

                elif label == "SimcardData":
                    count_sno_column(csv_path)
                    simcard_csv = csv_path
        else:
            print(f"[!] File not found for {label}: {filename}")

    if influx_csv and simcard_csv:
        patch_missing_rows_with_simcard(influx_csv, simcard_csv)

    show_graph = input("Show graph Yes/No : ").strip().lower()
    if show_graph == "yes":
        print("[✓] Plotting update.csv graph...")
        plot_update_csv("update.csv")
    else:
        print("[i] Graph skipped.")


if __name__ == "__main__":
    main()
