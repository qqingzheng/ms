import os
import json
from typing import Type
from pydantic import BaseModel
import aio_pika
from pydantic import ValidationError
from ..schemas import ErrorResponse


class BaseHandler:
    """基础消息处理器，提供通用逻辑"""
    request_model: Type[BaseModel]
    response_model: Type[BaseModel]
    hanlder_name: str
    
    def __init__(self, exchange: aio_pika.Exchange):
        self.exchange = exchange

    async def process_message(
        self,
        message: aio_pika.IncomingMessage,
    ):
        """处理消息的通用逻辑"""
        async with message.process():
            try:
                # 解析消息体
                body = json.loads(message.body.decode())
                # 校验 request_data
                try:
                    request_data = self.request_model(**body)
                except ValidationError as e:
                    response = ErrorResponse(
                        message=f"Request data validation failed: {e}"
                    )
                    return response

                # 调用具体处理函数
                response = await self.__call__(request_data)
            except Exception as e:
                response = ErrorResponse(message=f"{str(e)}")

            # 如果有 reply_to 队列，发送响应
            if message.reply_to:
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(response.model_dump()).encode(),
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to,
                )

