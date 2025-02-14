import asyncio
import os, json
from .handler import BaseHandler
from ..conn.rabbitmq import get_rabbitmq_connection
from ..logger.logger import log
import aio_pika
import time
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
                        "handler": handler.hanlder_name,
                        "timeout": handler.timeout,
                        "method": handler.method,
                        "need_auth": handler.need_auth
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
            
        try:
            await asyncio.Future()  # 持续运行
        finally:
            await connection.close()
            
async def inner_request(service_name: str, queue_name: str, request: dict):
    """内部请求处理 - 同步等待微服务返回"""
    connection = await get_rabbitmq_connection()
    try:
        async with connection:
            channel = await connection.channel()

            # 声明请求队列
            request_queue = f"{service_name}_{queue_name}"

            # 声明回调队列
            callback_queue = await channel.declare_queue(exclusive=True)

            # 存储correlation_id和结果的变量
            correlation_id = str(hash(f"{service_name}_{queue_name}_{time.time()}"))
            future = asyncio.Future()

            # 定义回调函数处理返回结果
            async def on_response(message: aio_pika.IncomingMessage):
                if message.correlation_id == correlation_id:
                    future.set_result(json.loads(message.body))

            # 监听回调队列
            await callback_queue.consume(on_response)

            # 发送消息到对应服务的队列
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(request).encode(),
                    correlation_id=correlation_id,
                    reply_to=callback_queue.name,
                ),
                routing_key=request_queue,
            )

            # 等待回复
            response = await future
            return response

    except Exception as e:
        raise Exception("Internal Server Error")