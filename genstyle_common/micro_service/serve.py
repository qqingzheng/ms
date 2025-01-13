import asyncio
import os
from .handler import BaseHandler
from ..conn.rabbitmq import get_rabbitmq_connection
from ..logger.logger import log

async def register_service(handler: BaseHandler):
    """注册服务"""
    
    # 连接到 RabbitMQ
    log(type="info", message=f"服务注册中", service_name=os.getenv('SERVICE_NAME'))
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        exchange = channel.default_exchange

        # 初始化处理器
        handler_instance = handler(exchange)

        # 自动注册所有处理函数
        registered_methods = []
        for method_name in dir(handler_instance):
            method = getattr(handler_instance, method_name)
            # 检查是否是处理器函数
            if hasattr(method, '_queue_name') and hasattr(method, '_request_model'):
                # 声明队列
                registered_methods.append(method)
                # queue = await channel.declare_queue(method._queue_name)
                # # 注册消费者
                # await queue.consume(
                #     lambda message: handler_instance.process_message(
                #         message,
                #         request_model=method._request_model,
                #         handler_func=method
                #     )
                # )
        log(type="info", message=f"服务注册完成 {str(registered_methods)}")
        try:
            await asyncio.Future()  # 持续运行
        finally:
            await connection.close()