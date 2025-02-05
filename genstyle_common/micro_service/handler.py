import os
import json
from typing import Type
from pydantic import BaseModel
import aio_pika
from pydantic import ValidationError
from ..schemas import ErrorResponse
import traceback
from ..exceptions import InnerException
class BaseHandler:
    """基础消息处理器，提供通用逻辑"""

    request_model: Type[BaseModel]
    response_model: Type[BaseModel]
    hanlder_name: str
    timeout: int = 5
    need_auth: bool = True
    method: str = "POST"
    
    def __init__(self, exchange: aio_pika.Exchange):
        self.exchange = exchange

    async def handle(self, request_data):
        pass

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
                    raise Exception(f"Request data validation failed: {body} Error: {e}")

                # 调用具体处理函数
                response = await self.handle(request_data)
            except InnerException as e:
                response = ErrorResponse(message=f"Service inner exception: {str(e)}")
            except Exception as e:
                response = ErrorResponse(message=f"Parse message error: {str(e)}\n\nBacktrace: {traceback.format_exc()}")

            # 如果有 reply_to 队列，发送响应
            if message.reply_to:
                try:
                    body = json.dumps(response.model_dump()).encode()
                except Exception as e:
                    body = json.dumps(ErrorResponse(message=f"Response data validation failed").model_dump()).encode()
                await self.exchange.publish(
                    aio_pika.Message(
                        body=body,
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to,
                )
