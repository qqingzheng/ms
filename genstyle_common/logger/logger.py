import os
import json
import aio_pika
from ..conn.rabbitmq import get_rabbitmq_connection

async def log(type, message, error_type="", error_file="", traceback=""):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        service_name = os.getenv("SERVICE_NAME", "unknown")
        if type == "error" or type == "critical":
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps({
                        "service": service_name,
                        "type": type,
                        "message": message,
                        "error_type": error_type,
                        "error_file": error_file,
                        "traceback": traceback
                    }).encode()
                ),
                routing_key="monitor_log"
            )
        elif type == "warning":
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps({
                        "service": service_name,
                        "type": type,
                        "message": message
                    }).encode()
                ),
                routing_key="monitor_log"
            )
        else:
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps({
                        "service": service_name,
                        "type": type,
                        "message": message
                    }).encode()
                ),
                routing_key="monitor_log"
            )
