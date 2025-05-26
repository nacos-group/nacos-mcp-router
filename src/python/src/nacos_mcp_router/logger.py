#-*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler


class NacosMcpRouteLogger:
    logger: logging.Logger | None = None
    @classmethod
    def setup_logger(cls):
        NacosMcpRouteLogger.logger = logging.getLogger("nacos_mcp_router")
        NacosMcpRouteLogger.logger.setLevel(logging.INFO)
        log_file = os.path.expanduser("~") + "/logs/nacos_mcp_router/router.log"
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        formatter = logging.Formatter(
            "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # 保留5个备份文件
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)  # 文件记录所有级别
        file_handler.setFormatter(formatter)

        NacosMcpRouteLogger.logger.addHandler(file_handler)
    @classmethod
    def get_logger(cls) -> logging.Logger:
        if NacosMcpRouteLogger.logger is None:
            NacosMcpRouteLogger.setup_logger()
        if NacosMcpRouteLogger.logger is None:
            return logging.getLogger("nacos_mcp_router")
        else:
            return NacosMcpRouteLogger.logger
