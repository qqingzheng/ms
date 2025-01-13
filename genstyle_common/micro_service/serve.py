import asyncio
import os
from .handler import BaseHandler
from ..conn.rabbitmq import get_rabbitmq_connection
from ..logger.logger import log

async def register_service(handlers: list[BaseHandler]):
    """注册服务"""
    print("服务注册中", flush=True)
    # 连接到 RabbitMQ
    await log(type="info", message=f"服务注册中")
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        exchange = channel.default_exchange
        # 初始化处理器
        for handler in handlers:
            print(f"注册处理器: {handler}", flush=True)
            handler_instance = handler(exchange)
            queue = await channel.declare_queue(handler.hanlder_name)
            # 注册消费者
            await queue.consume(
                lambda message: handler_instance.process_message(
                    message
                )
            )
            print(f"服务注册完成 {handler}", flush=True)
        await log(type="info", message=f"服务注册完成 {str(handlers)}")
        try:
            await asyncio.Future()  # 持续运行
        finally:
            await connection.close()