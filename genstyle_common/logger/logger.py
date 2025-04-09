import os
from ..conn.rabbitmq import get_rabbitmq_connection
from ..micro_service.inner_request import inner_request

async def log(
    type, message, error_type="", error_file="", traceback="", user_id=None, request_id=None, service_name=None
):
    print(f"正在记录日志，类型：{type}，消息：{message}，错误类型：{error_type}，错误文件：{error_file}，traceback：{traceback}，用户ID：{user_id}，请求ID：{request_id}，服务名称：{service_name}", flush=True)
    # connection = await get_rabbitmq_connection()
    # async with connection:
    #     channel = await connection.channel()
    #     if service_name is None:  # 如果service_name为None，则使用当前服务的名称。
    #         service_name = os.getenv("SERVICE_NAME", "unknown")
    #     if type == "error" or type == "critical":
    #         response = await inner_request("monitor", "log", {
    #             "service": service_name,
    #             "type": type,
    #             "message": message,
    #             "error_type": error_type,
    #             "error_file": error_file,
    #             "traceback": traceback,
    #             "user_id": user_id,
    #             "request_id": request_id,
    #         })
    #     elif type == "warning":
    #         response = await inner_request("monitor", "log", {
    #             "service": service_name,
    #             "type": type,
    #             "message": message,
    #             "user_id": user_id,
    #             "request_id": request_id,
    #         })
    #     else:
    #         response = await inner_request("monitor", "log", {
    #             "service": service_name,
    #             "type": type,
    #             "message": message,
    #         })