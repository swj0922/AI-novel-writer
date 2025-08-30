# -*- coding: utf-8 -*-
"""
数据库配置和LLM调用记录表结构
"""
import os
import logging
import pymysql
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


class DatabaseConfig:
    """数据库配置类，负责MySQL数据库的连接配置和管理。"""
    # 初始化数据库连接参数（主机、端口、用户名、密码、数据库名、字符集）
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 3306,
                 user: str = "root",
                 password: str = "swjzlh2002",
                 database: str = "novel_generator",
                 charset: str = "utf8mb4"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
    
    def ensure_database_exists(self):
        """确保数据库存在，如果不存在则创建"""
        try:
            # 首先连接到MySQL服务器（不指定数据库）
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset=self.charset,
                autocommit=True
            )
            
            with connection.cursor() as cursor:
                # 创建数据库如果不存在
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                logging.info(f"数据库 '{self.database}' 已确保存在")
            
            connection.close()
            
        except Exception as e:
            logging.error(f"创建数据库失败: {e}")
            raise
        
    # @contextmanager 是一个装饰器，它可以将一个生成器函数转换为上下文管理器，使得该函数可以与 with 语句一起使用。
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        connection = None
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                autocommit=True
            )
            yield connection
        except Exception as e:
            logging.error(f"数据库连接失败: {e}")
            raise
        finally:
            if connection:
                connection.close()


class LLMCallLogger:
    """LLM调用记录器，用于记录和管理大语言模型调用的详细信息。"""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        # 确保数据库存在
        self.db_config.ensure_database_exists()
        self.init_table()
    
    def init_table(self):
        """初始化数据库表llm_call_logs"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS llm_call_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            call_id VARCHAR(100) UNIQUE NOT NULL COMMENT '调用ID',
            model_name VARCHAR(100) NOT NULL COMMENT '模型名称',
            call_purpose VARCHAR(200) NOT NULL COMMENT '调用目的',
            prompt_tokens INT NOT NULL DEFAULT 0 COMMENT '输入token数',
            completion_tokens INT NOT NULL DEFAULT 0 COMMENT '输出token数',
            total_tokens INT NOT NULL DEFAULT 0 COMMENT '总token数',
            cached_tokens INT DEFAULT 0 COMMENT '缓存token数',
            call_start_time DATETIME NOT NULL COMMENT '调用开始时间',
            call_end_time DATETIME COMMENT '调用结束时间',
            waiting_time_s INT DEFAULT 0 COMMENT '等待时间(秒)',
            success BOOLEAN DEFAULT TRUE COMMENT '是否成功',
            error_message TEXT COMMENT '错误信息',
            temperature FLOAT COMMENT '温度参数',
            INDEX idx_model_name (model_name),
            INDEX idx_call_purpose (call_purpose),
            INDEX idx_call_start_time (call_start_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='LLM调用记录表';
        """
        
        try:
            with self.db_config.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_table_sql)
                    logging.info("LLM调用记录表初始化成功")
        except Exception as e:
            logging.error(f"创建表失败: {e}")
            raise
    
    def log_call_start(self, call_id: str, model_name: str, call_purpose: str, 
                      temperature: float) -> None:
        """记录LLM调用开始前的信息"""
        insert_sql = """
        INSERT INTO llm_call_logs (
            call_id, model_name, call_purpose, call_start_time, temperature
        ) VALUES (%s, %s, %s, %s, %s)
        """
        
        try:
            with self.db_config.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(insert_sql, (
                        call_id, model_name, call_purpose, datetime.now(), temperature
                    ))
        except Exception as e:
            logging.error(f"记录调用开始失败: {e}")
    
    def log_call_end(self, call_id: str, prompt_tokens: int, completion_tokens: int, 
                    total_tokens: int, cached_tokens: int, success: bool, 
                    error_message: Optional[str] = None) -> None:
        """用于在LLM调用完成后更新数据库中的调用记录"""
        update_sql = """
        UPDATE llm_call_logs SET 
            call_end_time = %s,
            waiting_time_s = TIMESTAMPDIFF(SECOND, call_start_time, %s),
            prompt_tokens = %s,
            completion_tokens = %s,
            total_tokens = %s,
            cached_tokens = %s,
            success = %s,
            error_message = %s
        WHERE call_id = %s
        """
        
        try:
            end_time = datetime.now()
            with self.db_config.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(update_sql, (
                        end_time, end_time, prompt_tokens, completion_tokens, 
                        total_tokens, cached_tokens, success, error_message, call_id
                    ))
        except Exception as e:
            logging.error(f"记录调用结束失败: {e}")
    


# 默认数据库配置实例
default_db_config = DatabaseConfig()
default_llm_logger = LLMCallLogger(default_db_config)