import asyncio
import os
from .handler import BaseHandler
from ..conn.rabbitmq import get_rabbitmq_connection
from ..logger.logger import log

async def register_service(handler: BaseHandler):
    """注册服务"""
    
    # 连接到 RabbitMQ
    print("连接到 RabbitMQ", flush=True)
    await log(type="info", message=f"服务注册中")
    connection = await get_rabbitmq_connection()
    print("连接到 RabbitMQ", flush=True)
    async with connection:
        print("获取通道", flush=True)
        channel = await connection.channel()
        print("获取默认交换机", flush=True)
        exchange = channel.default_exchange
        print("获取默认交换机", flush=True)
        # 初始化处理器
        print("初始化处理器", flush=True)
        handler_instance = handler(exchange)
        print("处理器初始化完成", flush=True)

        # 自动注册所有处理函数
        registered_methods = []
        for method_name in dir(handler_instance):
            print(f"方法名: {method_name}", flush=True)
            method = getattr(handler_instance, method_name)
            # 检查是否是处理器函数
            if hasattr(method, '_queue_name') and hasattr(method, '_request_model'):
                # 声明队列
                registered_methods.append(method)
                print(f"声明队列: {method._queue_name}", flush=True)
                queue = await channel.declare_queue(method._queue_name)
                # 注册消费者
                await queue.consume(
                    lambda message: handler_instance.process_message(
                        message,
                        request_model=method._request_model,
                        handler_func=method
                    )
                )
        await log(type="info", message=f"服务注册完成 {str(registered_methods)}")
        print(f"服务注册完成 {str(registered_methods)}", flush=True)
        try:
            await asyncio.Future()  # 持续运行
        finally:
            await connection.close()