import asyncio
import json
import aio_pika
import time
from ..conn.rabbitmq import get_rabbitmq_connection
from ..logger.logger import log

async def inner_request(service_name: str, queue_name: str, request: dict):
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            connection = await get_rabbitmq_connection()
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
            if attempt < retry_attempts - 1:
                await log("error", f"内部接口访问错误，重试次数: {attempt + 1}，错误信息: {  str(e)}")
            else:
                raise Exception("Internal Server Error")