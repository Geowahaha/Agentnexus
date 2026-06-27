"""Test MQTT TLS publish to production broker from dev machine."""
import json
import ssl
import sys
import time

import paho.mqtt.client as mqtt

host = sys.argv[1] if len(sys.argv) > 1 else "43.128.75.149"
port = 8883
username = "3915c8c5-f05f-478a-9f3a-4612ca259f76"
password = "sf_jGs4rKlKHDxZUjq4VFHLcAEOVEMirg-R1STakQ"
topic = "obolla/farm/b9bc802a-ab32-46cc-a479-f93c5e585964/telemetry"
payload = json.dumps(
    {
        "readings": [
            {"channel": "temp_day_c", "value": 28.4},
            {"channel": "humidity_pct", "value": 58},
        ],
        "growth_stage": "fruiting",
    }
)

rc_box: list[int] = []


def on_connect(_c, _u, _f, rc):
    rc_box.append(rc)
    print("connect rc", rc)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
    client_id="external-live-test",
    protocol=mqtt.MQTTv311,
)
client.username_pw_set(username, password)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.connect(host, port, 60)
client.loop_start()
time.sleep(2)
if rc_box and rc_box[0] == 0:
    client.publish(topic, payload)
    print("published ok")
else:
    print("connect failed", rc_box)
    sys.exit(1)
time.sleep(1)
client.loop_stop()
client.disconnect()