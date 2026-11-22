import time
import json
import math
import paho.mqtt.client as mqtt
from phreeqpython import PhreeqPython

# 1. Initialize PHREEQC
pp = PhreeqPython(database='pitzer.dat')

# 2. MQTT Setup
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "saksham/waterplant/ro1/telemetry"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)

# 3. Plant Economic & Hydraulic Constants
PLANT_FLOW_M3_HR = 100.0          # 100 m3/hr (2,400 m3/day) industrial RO feed
ACID_COST_USD_PER_KG = 0.35       # Bulk 98% Sulfuric Acid cost ($/kg)
STATIC_BASELINE_MGL = 260.0       # Conventional fixed worst-case dosing (mg/L)
DEADBAND_MGL = 5.0                # PLC deadband to protect dosing pump diaphragm

last_sent_dose = 160.0

def calculate_dosing(ca_mgL, alk_mgL, feed_pH, target_si=0.25):
    for dose_step in range(0, 500, 10):
        acid_mmol = dose_step / 100.0
        feed = pp.add_solution({
            'temp': 25.0, 'pH': feed_pH, 'units': 'mg/L',
            'Ca': ca_mgL, 'Mg': 95.0, 'Na': '650 charge', 'K': 35.0,
            'Alkalinity': f'{alk_mgL} as CaCO3', 'S(6)': '780 as SO4', 'Cl': 920.0
        })
        if acid_mmol > 0:
            feed.add('H2SO4', acid_mmol, 'mmol')
        feed.remove('H2O', 0.80 * 55.51, 'mol')
        
        calcite_si = round(feed.si('Calcite'), 3)
        gypsum_si = round(feed.si('Gypsum'), 3)
        brine_pH = round(feed.pH, 2)
        feed.forget()
        
        if calcite_si <= target_si:
            return round(acid_mmol * 98.08, 1), brine_pH, calcite_si, gypsum_si
    return 490.0, 5.0, 0.0, 0.5

step = 0
print("Streaming Live Process & Financial ROI Telemetry...")
try:
    while True:
        # Simulate diurnal industrial feedwater fluctuations
        ca_live = round(280.0 + 70.0 * math.sin(step * 0.4), 1)
        alk_live = round(320.0 + 60.0 * math.sin(step * 0.4), 1)
        feed_pH_live = round(7.8 + 0.2 * math.sin(step * 0.3), 2)
        
        # Calculate optimal dose
        raw_acid_mgL, brine_pH, calcite_si, gypsum_si = calculate_dosing(ca_live, alk_live, feed_pH_live)
        
        # Apply PLC Deadband Filter
        if abs(raw_acid_mgL - last_sent_dose) >= DEADBAND_MGL:
            active_dose_mgL = raw_acid_mgL
            last_sent_dose = raw_acid_mgL
        else:
            active_dose_mgL = last_sent_dose

        # Financial ROI Calculations (mg/L == g/m3)
        daily_flow_m3 = PLANT_FLOW_M3_HR * 24.0
        static_kg_day = (STATIC_BASELINE_MGL * daily_flow_m3) / 1000.0
        smart_kg_day = (active_dose_mgL * daily_flow_m3) / 1000.0
        
        daily_savings_usd = round(max(0.0, (static_kg_day - smart_kg_day) * ACID_COST_USD_PER_KG), 2)
        annual_savings_usd = round(daily_savings_usd * 365.0, 0)
        
        alarm = "HIGH_HARDNESS_BOOST" if ca_live > 320.0 else "NORMAL"
        
        payload = {
            "feed_Ca_mgL": ca_live,
            "acid_pump_setpoint_mgL": active_dose_mgL,
            "brine_Calcite_SI": calcite_si,
            "daily_savings_usd": daily_savings_usd,
            "annual_savings_usd": annual_savings_usd,
            "system_status": alarm
        }
        
        client.publish(TOPIC, json.dumps(payload))
        print(f"[Step {step}] Dose: {active_dose_mgL} mg/L | Saving: ${daily_savings_usd}/day (${annual_savings_usd}/yr)")
        
        step += 1
        time.sleep(3)

except KeyboardInterrupt:
    client.disconnect()
