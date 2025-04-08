import os
import json
from typing import Type
from pydantic import BaseModel
import aio_pika
from pydantic import ValidationError
from ..schemas import ErrorResponse
import traceback
from ..exceptions import InnerException
from ..logger import log

class BaseHandler:
    """基础消息处理器，提供通用逻辑"""

    request_model: Type[BaseModel]
    response_model: Type[BaseModel]
    hanlder_name: str
    timeout: int = 5
    need_auth: bool = True
    only_inner_request: bool = False
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
        print("Processing message", flush=True)
        
        try:
            print("Trying to get channel", flush=True)
            message.channel
            print("Channel got", flush=True)
        except Exception as e:
            return ErrorResponse(message="Channel closed")
        
        try:
            print("Trying to process message", flush=True)
            async with message.process():
                try:
                    # 解析消息体
                    body = json.loads(message.body.decode())
                    if self.only_inner_request:
                        if "inner_request" not in body or body["inner_request"] != True:
                            return ErrorResponse(message="Only inner request is allowed")
                    # 校验 request_data
                    try:
                        request_data = self.request_model(**body)
                    except ValidationError as e:
                        await log("info", f"请求数据验证失败: {body} 错误信息: {e}")
                        return ErrorResponse(message=f"Request data validation failed: {body} Error: {e}")

                    # 调用具体处理函数
                    response = await self.handle(request_data)
                except InnerException as e:
                    response = ErrorResponse(message=f"Service inner exception: {str(e)}")
                except Exception as e:
                    await log("info", f"解析消息时发生异常: {str(e)}\n\nBacktrace: {traceback.format_exc()}")
                    response = ErrorResponse(message=f"Parse message error: {str(e)}\n\nBacktrace: {traceback.format_exc()}")

                # 如果有 reply_to 队列，发送响应
                if message.reply_to:
                    try:
                        body = json.dumps(response.model_dump()).encode()
                    except Exception as e:
                        await log("error", f"返回数据中存在不可序列化的数据: {str(e)}")
                        body = json.dumps(ErrorResponse(message=f"Response data validation failed").model_dump()).encode()
                    await self.exchange.publish(
                        aio_pika.Message(
                            body=body,
                            correlation_id=message.correlation_id,
                        ),
                        routing_key=message.reply_to,
                    )
        except Exception as e:
            return ErrorResponse(message="Channel closed")
