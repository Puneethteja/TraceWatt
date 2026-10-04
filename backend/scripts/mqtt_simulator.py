"""
backend/scripts/mqtt_simulator.py
==================================
MQTT Smart Meter Telemetry Publisher Simulator for TraceWatt.

Publishes 15-minute interval smart meter readings (Voltage, Current, Power kW,
Cumulative kWh, Meter Status, Comm Status) to an MQTT Broker under the standard
topic pattern: tracewatt/telemetry/{consumer_id}/reading

Usage:
    python backend/scripts/mqtt_simulator.py --broker test.mosquitto.org --num-meters 20 --interval-sec 1
"""

import argparse
import json
import random
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt


def generate_meter_reading(consumer_id: str, scenario: str = "normal") -> dict:
    """Generates a realistic smart meter reading for a given scenario."""
    now_iso = datetime.now(timezone.utc).isoformat()
    
    if scenario == "theft":
        # Simulates 75% drop in consumption with stable grid voltage
        voltage = round(random.uniform(225.0, 235.0), 1)
        kwh = round(random.uniform(0.02, 0.08), 3)
        power_kw = round((kwh * 4), 2)
        current = round((power_kw * 1000.0) / (voltage * 0.9), 2) if voltage > 0 else 0.0
        meter_status = "OK"
        comm_status = "OK"
    elif scenario == "malfunction":
        voltage = round(random.uniform(225.0, 235.0), 1)
        kwh = 0.0
        power_kw = 0.0
        current = 0.0
        meter_status = "SENSOR_ERROR"
        comm_status = "OK"
    elif scenario == "comm_fail":
        voltage = round(random.uniform(225.0, 235.0), 1)
        kwh = None
        power_kw = 0.0
        current = 0.0
        meter_status = "OK"
        comm_status = "FAILED"
    else:  # normal
        voltage = round(random.uniform(220.0, 240.0), 1)
        kwh = round(random.uniform(0.40, 1.80), 3)
        power_kw = round((kwh * 4), 2)
        current = round((power_kw * 1000.0) / (voltage * 0.9), 2) if voltage > 0 else 0.0
        meter_status = "OK"
        comm_status = "OK"

    return {
        "consumer_id": consumer_id,
        "ts": now_iso,
        "kwh": kwh,
        "voltage": voltage,
        "current": current,
        "power_kw": power_kw,
        "meter_status": meter_status,
        "comm_status": comm_status,
    }


def main():
    parser = argparse.ArgumentParser(description="TraceWatt MQTT Smart Meter Simulator")
    parser.add_argument("--broker", type=str, default="test.mosquitto.org", help="MQTT Broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT Broker port")
    parser.add_argument("--num-meters", type=int, default=10, help="Number of simulated smart meters")
    parser.add_argument("--interval-sec", type=float, default=2.0, help="Publish interval in seconds")
    parser.add_argument("--burst-count", type=int, default=50, help="Total message count before stopping (0 for infinite)")
    args = parser.parse_args()

    client_id = f"tracewatt_sim_{int(time.time())}"
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
    except AttributeError:
        client = mqtt.Client(client_id=client_id)

    print(f"Connecting to MQTT Broker {args.broker}:{args.port} ...")
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_start()
    time.sleep(1)

    meter_ids = [f"CONS_{i:04d}" for i in range(1, args.num_meters + 1)]
    # Designate some meters for scenarios
    theft_meter = meter_ids[0] if len(meter_ids) > 0 else None
    malfunc_meter = meter_ids[1] if len(meter_ids) > 1 else None
    comm_meter = meter_ids[2] if len(meter_ids) > 2 else None

    print(f"Streaming smart meter telemetry over MQTT to topic: tracewatt/telemetry/<consumer_id>/reading")
    print(f"Meters active: {len(meter_ids)} (Theft injected: {theft_meter}, Malfunction: {malfunc_meter}, Comm error: {comm_meter})")
    print("=" * 70)

    sent = 0
    try:
        while True:
            for cid in meter_ids:
                if cid == theft_meter:
                    scenario = "theft"
                elif cid == malfunc_meter:
                    scenario = "malfunction"
                elif cid == comm_meter:
                    scenario = "comm_fail"
                else:
                    scenario = "normal"

                payload = generate_meter_reading(cid, scenario)
                topic = f"tracewatt/telemetry/{cid}/reading"
                msg_json = json.dumps(payload)
                
                info = client.publish(topic, msg_json, qos=1)
                sent += 1
                print(f"[{sent:04d}] MQTT -> {topic} | kWh: {payload['kwh']} | V: {payload['voltage']}V | Status: {payload['meter_status']}")

                if args.burst_count and sent >= args.burst_count:
                    print("\nCompleted requested message burst count. Exiting.")
                    return

            time.sleep(args.interval_sec)

    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("MQTT Client disconnected.")


if __name__ == "__main__":
    main()
