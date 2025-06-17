import pandas as pd
import matplotlib.pyplot as plt

def plot_sensor_data(csv_path):
    try:
        # Read and parse the CSV
        df = pd.read_csv(csv_path, parse_dates=['time'])

        # Ensure the required columns exist
        required_cols = ['time', 'p', 'rh', 'temp', 'temp_soil']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")

        # Plotting
        plt.figure(figsize=(14, 7))
        plt.plot(df['time'], df['p'], label='p (Pressure)', color='blue', linewidth=1)
        plt.plot(df['time'], df['rh'], label='rh (Humidity)', color='green', linewidth=1)
        plt.plot(df['time'], df['temp'], label='temp (Air Temp)', color='red', linewidth=1)
        plt.plot(df['time'], df['temp_soil'], label='temp_soil (Soil Temp)', color='brown', linewidth=1)

        # Formatting
        plt.title("Sensor Data from update.csv")
        plt.xlabel("Time")
        plt.ylabel("Sensor Readings")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(rotation=45)

        # Show plot
        plt.show()

    except Exception as e:
        print(f"[ERROR] Failed to plot graph: {e}")

if __name__ == "__main__":
    plot_sensor_data("update.csv")
