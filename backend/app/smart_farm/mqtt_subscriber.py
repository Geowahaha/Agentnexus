import asyncio
import json
import logging
from typing import Any

from app.core.config import settings
from app.core.database import async_session_maker
from app.repositories.smart_farm_repository import SmartFarmRepository
from app.services.smart_farm_service import SmartFarmService

logger = logging.getLogger(__name__)

_subscriber_task: asyncio.Task | None = None


async def _handle_message(topic: str, payload: dict[str, Any]) -> None:
    async with async_session_maker() as session:
        service = SmartFarmService(SmartFarmRepository(session))
        try:
            await service.ingest_mqtt_payload(topic, payload)
        except Exception as exc:
            logger.warning("MQTT ingest failed topic=%s: %s", topic, exc)


async def _mqtt_loop() -> None:
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning("paho-mqtt not installed — MQTT ingest disabled")
        return

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()

    def on_connect(client, _userdata, _flags, rc):
        if rc != 0:
            logger.error("MQTT connect failed rc=%s", rc)
            return
        client.subscribe(settings.smart_farm_mqtt_topic_wildcard)
        logger.info("MQTT subscribed to %s", settings.smart_farm_mqtt_topic_wildcard)

    def on_message(_client, _userdata, msg):
        try:
            raw = msg.payload.decode("utf-8")
            payload = json.loads(raw) if raw.strip().startswith(("{", "[")) else {"value": raw}
            if isinstance(payload, list):
                payload = {"readings": payload}
            loop.call_soon_threadsafe(queue.put_nowait, (msg.topic, payload))
        except Exception as exc:
            logger.warning("MQTT message parse error: %s", exc)

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        client_id=settings.smart_farm_mqtt_client_id,
        protocol=mqtt.MQTTv311,
    )
    if settings.smart_farm_mqtt_username:
        client.username_pw_set(settings.smart_farm_mqtt_username, settings.smart_farm_mqtt_password or "")
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(settings.smart_farm_mqtt_host, settings.smart_farm_mqtt_port, keepalive=60)
            client.loop_start()
            while True:
                topic, payload = await queue.get()
                await _handle_message(topic, payload)
        except asyncio.CancelledError:
            client.loop_stop()
            client.disconnect()
            raise
        except Exception as exc:
            logger.warning("MQTT loop error, retrying in 5s: %s", exc)
            await asyncio.sleep(5)


async def _auto_export_loop() -> None:
    while True:
        try:
            await asyncio.sleep(settings.smart_farm_auto_export_interval_seconds)
            async with async_session_maker() as session:
                service = SmartFarmService(SmartFarmRepository(session))
                count = await service.run_auto_exports()
                if count:
                    logger.info("Smart farm auto-export: %s dataset(s)", count)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Smart farm auto-export error: %s", exc)

async def _irrigation_check_loop() -> None:
    """Auto background check every 10 min for rain -> stop irrigation via Bridge + push notification."""
    while True:
        try:
            await asyncio.sleep(600)  # 10 minutes
            async with async_session_maker() as session:
                service = SmartFarmService(SmartFarmRepository(session))
                # For farms with irrigation enabled + weather_alerts
                # Fetch weather per farm location, if should_stop_irrigation, 
                # dispatch bridge 'control_irrigation' action='stop' if device paired,
                # and send push via edge_notify or notification service.
                # Placeholder: log + example (integrate with your Eve device via Bridge tool)
                logger.info("Auto irrigation check (10min): would fetch weather, check rain, stop Eve via Bridge if needed, push notification to user.")
                # To send real push: use edge_notify_service or notification hub
                # Example:
                # if should_stop:
                #     await dispatch... 'control_irrigation'
                #     # publish to user via existing notify service
                #     from app.services.edge_notify_service import publish_notification
                #     await publish_notification(user_id, {"type": "irrigation_stop", "reason": "rain"})
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Irrigation check error: %s", exc)


async def start_smart_farm_background_tasks() -> list[asyncio.Task]:
    global _subscriber_task
    tasks: list[asyncio.Task] = []
    if settings.smart_farm_mqtt_enabled:
        tasks.append(asyncio.create_task(_mqtt_loop(), name="smart-farm-mqtt"))
    if settings.smart_farm_auto_export_enabled:
        tasks.append(asyncio.create_task(_auto_export_loop(), name="smart-farm-auto-export"))
    tasks.append(asyncio.create_task(_irrigation_check_loop(), name="smart-farm-irrigation-check"))
    _subscriber_task = tasks[0] if tasks else None
    return tasks


async def stop_smart_farm_background_tasks(tasks: list[asyncio.Task]) -> None:
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)