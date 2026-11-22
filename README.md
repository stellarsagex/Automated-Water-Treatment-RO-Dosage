# Automated RO Scaling Control & Chemical Dosing Digital Twin

A real-time process control prototype that links aqueous geochemical modeling (**PHREEQC**) with industrial telemetry (IIOT) (**MQTT** and **Node-RED**) to optimize sulfuric acid dosing on an 80% recovery Reverse Osmosis (RO) skid.

## Why Was This Built This
In industrial water reuse and Zero Liquid Discharge (ZLD) plants, RO membranes frequently fail from mineral scaling (primarily calcium carbonate and gypsum) when feedwater hardness fluctuates. Because operators rarely have real-time visibility into brine saturation inside the pressure vessels, most plants dose sulfuric acid at a fixed worst-case rate 24/7. That approach wastes chemicals, lowers permeate pH, and risks pipe corrosion.

I built this project to test a feedforward control loop that calculates the exact minimum acid dose needed for incoming water quality in real time.

## How It Works
The system runs as a closed telemetry loop across three layers:

1. **Simulated Field Sensors (Python):** Generates fluctuating industrial cooling tower blowdown data (Calcium, Alkalinity, and pH) for a 100 m³/hr RO feed stream.
2. **Geochemical Solver (`phreeqpython` + `pitzer.dat`):** Concentrates the feedwater 5x (80% recovery) using the Pitzer high-salinity activity model. It iteratively solves for the lowest $H_2SO_4$ dose required to keep reject brine **Calcite Saturation Index (SI) ≤ 0.25** while tracking **Gypsum SI** and applying a ±5 mg/L deadband to prevent pump chatter.
3. **SCADA HMI & Telemetry (MQTT + Node-RED):** Publishes JSON sensor and dosing setpoints over MQTT (`paho-mqtt`) to a live Node-RED operator dashboard displaying brine scaling risk, pump dosing trends, high-hardness alarms, and daily chemical cost savings against a static 260 mg/L dosing baseline.

## Tech Stack
* **Geochemical Modeling:** USGS PHREEQC (`pitzer.dat` - database for high salinity), `phreeqpython`
* **Backend & Control Logic:** Python 3.12
* **Industrial Messaging:** MQTT (`paho-mqtt`, Eclipse Mosquitto broker)
* **SCADA / HMI:** Node-RED (`@flowfuse/node-red-dashboard`)

## Project Structure
* `Phrqc1.pqi` – Standalone PHREEQC desktop validation model (feed characterization, 80% recovery concentration, and acid titration curve).
* `ro_scada_publisher.py` – Live Python feedforward controller, deadband filter, ROI calculator, and MQTT publisher.
* `node_red_flow.json` – Exported Node-RED SCADA dashboard configuration.

## Running It Locally
1. Install dependencies:
   ```bash
   pip install phreeqpython paho-mqtt
   ```
2. Start Node-RED (`node-red`), import `node_red_flow.json`, and click **Deploy**.
3. Run the Python controller:
   ```bash
   python ro_scada_publisher.py
   ```
4. Open `http://127.0.0` in your browser to view the live SCADA interface.

