import asyncio
import os, json
from .handler import BaseHandler
from ..conn.rabbitmq import get_rabbitmq_connection
from ..logger.logger import log
import aio_pika
async def register_service(handlers: list[BaseHandler]):
    """注册服务"""
    print("服务注册中", flush=True)
    # 连接到 RabbitMQ
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        exchange = channel.default_exchange
        
        # 注册handler
        handler_instances = []
        for handler in handlers:
            handler_instance = handler(exchange)
            
            # 向api-gateway注册
            queue_name = f"api_gate_way_registry"
            queue = await channel.declare_queue(queue_name)
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps({
                        "service": os.getenv('SERVICE_NAME'),
                        "handler": handler.hanlder_name
                    }).encode()
                ),
                routing_key=queue_name
            )
            
            queue = await channel.declare_queue(f"{os.getenv('SERVICE_NAME')}_{handler.hanlder_name}")
            # 注册消费者
            await queue.consume(
                handler_instance.process_message
            )
            handler_instances.append(handler_instance)
            print(f"服务已注册： {os.getenv('SERVICE_NAME')}/{handler.hanlder_name}", flush=True)
        await log(type="info", message=f"服务注册完成")
        try:
            await asyncio.Future()  # 持续运行
        finally:
            await connection.close()