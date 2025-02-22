import os
import json
import aio_pika
from ..conn.rabbitmq import get_rabbitmq_connection


async def log(
    type, message, error_type="", error_file="", traceback="", user_id=None, request_id=None, service_name=None
):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        if service_name is None:  # 如果service_name为None，则使用当前服务的名称。
            service_name = os.getenv("SERVICE_NAME", "unknown")
        if type == "error" or type == "critical":
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(
                        {
                            "service": service_name,
                            "type": type,
                            "message": message,
                            "error_type": error_type,
                            "error_file": error_file,
                            "traceback": traceback,
                            "user_id": user_id,
                            "request_id": request_id,
                        }
                    ).encode()
                ),
                routing_key="monitor_log",
            )
        elif type == "warning":
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(
                        {"service": service_name, "type": type, "message": message}
                    ).encode()
                ),
                routing_key="monitor_log",
            )
        else:
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(
                        {"service": service_name, "type": type, "message": message}
                    ).encode()
                ),
                routing_key="monitor_log",
            )
