import os
import json
import asyncio
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
            print("正在尝试获取通道", flush=True)
            channel = message.channel
            print("通道获取成功", flush=True)
        except Exception as e:
            print(f"Channel access error: {e}", flush=True)
            await log("error", f"无法访问消息通道，消息将被丢弃: {str(e)}")
            return ErrorResponse(message="Channel closed")

        try:
            print("正在处理消息", flush=True)
            try:
                # 解析消息体
                print("正在解析消息体", flush=True)
                body = json.loads(message.body.decode())
                print("消息体解析成功", flush=True)
                
                if self.only_inner_request:
                    if "inner_request" not in body or body["inner_request"] != True:
                        # 拒绝不符合内部请求要求的消息，不重新入队
                        # await message.reject(requeue=False)
                        raise InnerException("Only inner request is allowed")

                # 校验 request_data
                try:
                    print("正在校验请求数据", flush=True)
                    request_data = self.request_model(**body)
                    print("请求数据校验成功", flush=True)
                except ValidationError as e:
                    await log("info", f"请求数据验证失败: {body} 错误信息: {e}")
                    raise InnerException(f"Request data validation failed: {body} Error: {e}")

                # 调用具体处理函数
                print(f"正在调用具体处理函数。\n内容：{request_data.model_dump()}\n超时：{self.timeout}", flush=True)
                try:
                    response = await asyncio.wait_for(self.handle(request_data), timeout=self.timeout)
                except asyncio.TimeoutError:
                    raise InnerException(message=f"Request timeout")
                except Exception as e:
                    await log("error", f"{self.hanlder_name} 处理函数调用失败: {str(e)}", traceback=traceback.format_exc())
                    raise InnerException(message=f"Failed to call function: {str(e)}")
                print("具体处理函数调用成功", flush=True)
                
                # 处理成功
                success = True
            except InnerException as e:
                success = False
                await log("error", f"服务出错: {str(e)}")
                response =  ErrorResponse(message=f"Service inner exception: {str(e)}")
            except Exception as e:
                success = False
                await log("info", f"解析消息时发生异常: {str(e)}\n\nBacktrace: {traceback.format_exc()}")
                response =  ErrorResponse(message=f"Parse message error: {str(e)}\n\nBacktrace: {traceback.format_exc()}")

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

            # 根据处理结果确认或拒绝消息
            if success:
                # 处理成功，确认消息
                await message.ack()
            else:
                # 处理失败，拒绝消息但不重新入队
                # 如果需要重试，可以设置 requeue=True
                await message.reject(requeue=False)
                # await message.ack()

            print(f"消息处理结束：\n是否成功：{success}\n返回信息：{response.model_dump()}", flush=True)
        except Exception as e:
            print(f"Message processing error: {e}", flush=True)
            await log("error", f"消息处理失败: {str(e)}")
            try:
                # 尝试拒绝消息
                await message.reject(requeue=False)
                # await message.ack()
            except Exception as reject_error:
                print(f"Failed to reject message: {reject_error}", flush=True)
                await log("error", f"消息拒绝失败: {str(e)}")
            return ErrorResponse(message=f"Message processing failed: {str(e)}")

