import warnings
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings("ignore")

import builtins
import logging
import multiprocessing

import coloredlogs
import fontLoader
import traceback
import os
import json
import requests

from bottle import Bottle, request, response

# from fastapi import FastAPI, Query, Request, Response
# from uvicorn import Config, Server
from cachetools import LRUCache, TTLCache
import asyncio
import ssl

import utils
from dirmonitor import dirmonitor
import config

logger = logging.getLogger(f'{"main"}:{"loger"}')
# app = FastAPI()
app = Bottle()


def custom_print(*args, **kwargs):
    logger.info("".join([str(x) for x in args]))


def init_logger():
    LOGGER_NAMES = (
        "uvicorn",
        "uvicorn.access",
    )
    for logger_name in LOGGER_NAMES:
        logging_logger = logging.getLogger(logger_name)
        fmt = f"🌏 %(asctime)s.%(msecs)03d .%(levelname)s \t%(message)s"  # 📨
        coloredlogs.install(
            level=logging.DEBUG,
            logger=logging_logger,
            milliseconds=True,
            datefmt="%X",
            fmt=fmt,
        )


# @app.post("/process_bytes")
# async def process_bytes(request: Request):
#     """传入字幕字节"""
#     print(request.headers)
#     subtitleBytes = await request.body()
#     try:
#         sub_HNmae = utils.bytes_to_hashName(subtitleBytes)
#         srt, bytes = utils.process(pool, sub_HNmae, subtitleBytes, externalFonts, fontPathMap, subCache, fontCache)
#         return Response(
#             content=bytes, headers={"Srt2Ass": str(srt), "fontinass-exception": "None"}
#         )
#     except Exception as e:
#         logger.error(f"处理出错，返回原始内容 : \n{traceback.format_exc()}")
#         return Response(
#             content=subtitleBytes,
#             headers={"Srt2Ass": str(False), "fontinass-exception": str(e)},
#         )


# @app.get("/process_url")
# async def process_url(ass_url: str = Query(None)):
#     """传入字幕url"""
#     print("loading " + ass_url)
#     try:
#         subtitleBytes = requests.get(ass_url).content
#         sub_HNmae = utils.bytes_to_hashName(subtitleBytes)
#         srt, bytes = utils.process(pool, sub_HNmae, subtitleBytes, externalFonts, fontPathMap, subCache, fontCache)
#         return Response(
#             content=bytes, headers={"Srt2Ass": str(srt), "fontinass-exception": "None"}
#         )
#     except Exception as e:
#         logger.error(f"处理出错，返回原始内容 : \n{traceback.format_exc()}")
#         return Response(
#             content=subtitleBytes,
#             headers={"Srt2Ass": str(False), "fontinass-exception": str(e)},
#         )


@app.route("/<path:path>", method="GET")
def catch_all(path):
    try:
        host = os.environ.get("EMBY_SERVER_URL") or EMBY_SERVER_URL
        url = f"{request.path}?{request.query_string}" if request.query_string else request.path
        embyRequestUrl = host + url
        logger.info(f"字幕URL: {embyRequestUrl}")
        # print({key: value for key, value in request.headers.items()})
        serverResponse = requests.get(url=embyRequestUrl)
    except Exception as e:
        info = f"fontinass获取原始字幕出错:{str(e)}"
        logger.error(info)
        return info
    try:
        subtitleBytes = serverResponse.content
        logger.info(f"原始大小: {len(subtitleBytes) / (1024 * 1024):.2f}MB")
        sub_HNmae = utils.bytes_to_hashName(subtitleBytes)
        srt, bytes = utils.process(pool, thread_pool, sub_HNmae, subtitleBytes, config.externalFonts, fontPathMap, subCache, fontCache)
        logger.info(f"处理后大小: {len(bytes) / (1024 * 1024):.2f}MB")
        if srt:
            if "user-agent" in request.headers and "infuse" in request.headers["user-agent"].lower():
                raise ValueError("infuse客户端，无法使用SRT转ASS功能，返回原始字幕")

        response.content_type = "application/octet-stream"
        # response.set_header("Content-Disposition", 'attachment; filename="data.bin"')
        return bytes
    except Exception as e:
        logger.error(f"处理出错，返回原始内容 : \n{traceback.format_exc()}")
        response.content_type = "application/octet-stream"
        return serverResponse.content


# @app.get("/{path:path}")
# async def proxy_pass(request: Request, response: Response):
#     try:
#         host = os.environ.get("EMBY_SERVER_URL") or EMBY_SERVER_URL
#         url = (
#             f"{request.url.path}?{request.url.query}"
#             if request.url.query
#             else request.url.path
#         )
#         embyRequestUrl = host + url
#         logger.info(f"字幕URL: {embyRequestUrl}")
#         serverResponse = requests.get(url=embyRequestUrl, headers=request.headers)
#         copyHeaders = {key: str(value) for key, value in response.headers.items()}
#     except Exception as e:
#         info = f"fontinass获取原始字幕出错:{str(e)}"
#         logger.error(info)
#         return info
#     try:
#         subtitleBytes = serverResponse.content
#         logger.info(f"原始大小: {len(subtitleBytes) / (1024 * 1024):.2f}MB")
#         sub_HNmae = utils.bytes_to_hashName(subtitleBytes)
#         srt, bytes = utils.process(pool, sub_HNmae, subtitleBytes, externalFonts, fontPathMap, subCache, fontCache)
#         logger.info(f"处理后大小: {len(bytes) / (1024 * 1024):.2f}MB")
#         copyHeaders["Content-Length"] = str(len(bytes))
#         if srt:
#             if (
#                 "user-agent" in request.headers
#                 and "infuse" in request.headers["user-agent"].lower()
#             ):
#                 raise ValueError("infuse客户端，无法使用SRT转ASS功能，返回原始字幕")
#         return Response(content=bytes)
#     except Exception as e:
#         logger.error(f"处理出错，返回原始内容 : \n{traceback.format_exc()}")
#         return Response(content=serverResponse.content)


# def getServer(port,serverLoop):
#     serverConfig = Config(
#         app=app,
#         # host="::",
#         host="0.0.0.0",
#         port=port,
#         log_level="info",
#         loop=serverLoop,
#         ws_max_size=1024 * 1024 * 1024 * 1024,
#     )
# return Server(serverConfig)

if __name__ == "__main__":
    # 进程池最大数量
    cpu_count = int(os.cpu_count())
    POOL_CPU_MAX = int(os.environ.get("POOL_CPU_MAX", default=cpu_count))
    if POOL_CPU_MAX >= cpu_count or POOL_CPU_MAX <= 0:
        POOL_CPU_MAX = cpu_count
    # 根据CPU逻辑处理器数创建进程池
    pool = multiprocessing.Pool(POOL_CPU_MAX)
    # 创建线程池
    thread_pool = ThreadPoolExecutor(max_workers= POOL_CPU_MAX * 2)

    fmt = f"🤖 %(asctime)s.%(msecs)03d .%(levelname)s \t%(message)s"
    coloredlogs.install(level=logging.DEBUG, logger=logger, milliseconds=True, datefmt="%X", fmt=fmt)
    original_print = builtins.print
    builtins.print = custom_print
    # 手动修改此处，或者使用环境变量
    EMBY_SERVER_URL = "尚未EMBY_SERVER_URL环境变量"
    fontDirList = [config.DEFAULT_FONT_PATH]
    if not os.path.exists(config.LOCAL_FONT_MAP_PATH):
        with open(config.LOCAL_FONT_MAP_PATH, "w", encoding="UTF-8") as f:
            json.dump({}, f)
    os.makedirs(config.DEFAULT_FONT_PATH, exist_ok=True)
    # externalFonts = utils.updateLocal(fontDirList)
    # with open(config.LOCAL_FONT_MAP_PATH, "r", encoding="UTF-8") as f:
    #     localFonts = utils.updateFontMap(fontDirList, json.load(f))
    #
    # with open(config.LOCAL_FONT_MAP_PATH, "w", encoding="UTF-8") as f:
    #     json.dump(localFonts, f, indent=4, ensure_ascii=True)

    config.externalFonts = utils.updateLocal(fontDirList)
    with open(config.FONT_MAP_PATH, "r", encoding="UTF-8") as f:
        fontPathMap = fontLoader.makeFontMap(json.load(f))

    if os.environ.get("FONT_DIRS"):
        for dirPath in os.environ.get("FONT_DIRS").split(";"):
            if dirPath.strip() != "" and os.path.exists(dirPath):
                fontDirList.append(dirPath.strip())
    logger.info("本地字体文件夹:" + ",".join(fontDirList))

    # 字幕文件缓存的过期时间，分钟为单位，默认60分钟，字幕文件占用很小。
    SUB_TTL = int(os.environ.get("SUB_TTL", default=60 * 60))
    # if SUB_TTL < 0:
    #     SUB_TTL = 60 * 60
    # 字体文件缓存的过期时间，分钟为单位，默认30分钟
    FONT_TTL = int(os.environ.get("FONT_TTL", default=30 * 60))
    # if FONT_TTL < 0:
    #     FONT_TTL = 30 * 60

    # 最大50条目
    SUB_CACHE_SIZE = int(os.environ.get("SUB_CACHE_SIZE", default=50))
    subCache = TTLCache(maxsize=SUB_CACHE_SIZE, ttl=SUB_TTL) if SUB_TTL > 0 else LRUCache(maxsize=SUB_CACHE_SIZE)  # 过期时间小于等于0 则永不过期

    # 最大30条目
    FONT_CACHE_SIZE = int(os.environ.get("FONT_CACHE_SIZE", default=30))
    fontCache = TTLCache(maxsize=FONT_CACHE_SIZE, ttl=FONT_TTL) if FONT_TTL > 0 else LRUCache(maxsize=FONT_CACHE_SIZE)  # 过期时间小于等于0 则永不过期

    serverLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(serverLoop)
    ssl._create_default_https_context = ssl._create_unverified_context

    # 创建fonts字体文件夹监视实体
    event_handler = dirmonitor(fontDirList)
    event_handler.start()
    # 启动web服务
    # serverInstance = getServer(8011,serverLoop)
    # 初始化日记
    init_logger()
    # serverLoop.run_until_complete(serverInstance.serve())
    app.run(host="0.0.0.0", port=8011)

    # 关闭和清理资源
    event_handler.stop()  # 停止文件监视器
    event_handler.join()  # 等待文件监视退出

    pool.close()  # 关闭进程池
    pool.join()  # 等待所有进程完成

    thread_pool.shutdown()  # 关闭线程池

    config.loop.stop()  # 停止事件循环
    config.loop.close()  # 清理资源