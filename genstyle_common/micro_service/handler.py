import os
import json
from typing import Type
from pydantic import BaseModel
import aio_pika
from pydantic import ValidationError
from ..schemas import ErrorResponse

class BaseHandler:
    """基础消息处理器，提供通用逻辑"""
    def __init__(self, exchange: aio_pika.Exchange):
        self.exchange = exchange

    async def process_message(self, message: aio_pika.IncomingMessage, request_model: Type[BaseModel], handler_func):
        """处理消息的通用逻辑"""
        async with message.process():
            try:
                # 解析消息体
                body = json.loads(message.body.decode())
                # 校验 request_data
                try:
                    request_data = request_model(**body)
                except ValidationError as e:
                    response = ErrorResponse(message=f"Request data validation failed: {e}")
                    return response
                
                # 调用具体处理函数
                response = await handler_func(request_data)
            except Exception as e:
                response = ErrorResponse(message=f"{str(e)}")

            # 如果有 reply_to 队列，发送响应
            if message.reply_to:
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(response.dict()).encode(),
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to,
                )

def handler(queue_name: str, request_model: Type[BaseModel]):
    """处理器装饰器，用于自动注册处理函数"""
    def decorator(func):
        func._queue_name = f"{os.getenv('SERVICE_NAME')}_{queue_name}"
        func._request_model = request_model
        return func
    return decorator
