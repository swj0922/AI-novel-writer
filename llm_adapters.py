# llm_adapters.py
# -*- coding: utf-8 -*-
import logging
import uuid
from typing import Optional
from openai import OpenAI
from database.llm_monitor import global_llm_monitor


class BaseLLMAdapter:
    """
    统一的 LLM 接口基类
    """
    def __init__(self):
        self.interface_format = "unknown"
        self.model_name = "unknown"
        self.base_url = ""
        self.temperature = 0.0
        self.max_tokens = 0
        
    def invoke(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement .invoke(prompt) method.")


class DoubaoAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        super().__init__()
        self.interface_format = "doubao"
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.model = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def invoke_with_monitoring(self, prompt: str, call_purpose: Optional[str] = None) -> str:
        """带监控的调用方法"""
        call_id = str(uuid.uuid4())
        
        try:
            # 记录调用开始
            if global_llm_monitor.enabled:
                final_call_purpose = call_purpose or "未指定"
                global_llm_monitor.logger.log_call_start(
                    call_id=call_id,
                    model_name=self.model_name,
                    call_purpose=final_call_purpose,
                    temperature=self.temperature
                )
            
            # 执行实际调用
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            # 记录调用结束
            if global_llm_monitor.enabled:
                usage_info = global_llm_monitor._parse_usage_from_response(completion)
                global_llm_monitor.logger.log_call_end(
                    call_id=call_id,
                    prompt_tokens=usage_info['prompt_tokens'],
                    completion_tokens=usage_info['completion_tokens'],
                    total_tokens=usage_info['total_tokens'],
                    cached_tokens=usage_info['cached_tokens'],
                    success=True
                )
            
            # 确保返回值不为None
            content = completion.choices[0].message.content
            return content if content is not None else ""
            
        except Exception as e:
            # 记录调用失败
            if global_llm_monitor.enabled:
                global_llm_monitor.logger.log_call_end(
                    call_id=call_id,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cached_tokens=0,
                    success=False,
                    error_message=str(e)
                )
            raise e
    
    def invoke(self, prompt: str, purpose: str = "未指定") -> str:
        """保持原有接口不变，默认启用监控"""
        return self.invoke_with_monitoring(prompt, call_purpose=purpose)


class GeminiAdapter(BaseLLMAdapter):
    """
    适配 Google Gemini (Google Generative AI) 接口
    """
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int = 65536, temperature: float = 0.7, timeout: Optional[int] = 600):
        super().__init__()
        self.interface_format = "gemini"
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url = base_url
        # gemini超时时间是毫秒
        self.timeout = (timeout * 1000) if timeout is not None else 600000

        self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    def invoke_with_monitoring(self, prompt: str, call_purpose: Optional[str] = None) -> str:
        """带监控的调用方法"""
        call_id = str(uuid.uuid4())
        
        try:
            # 记录调用开始
            if global_llm_monitor.enabled:
                final_call_purpose = call_purpose or "未指定"
                global_llm_monitor.logger.log_call_start(
                    call_id=call_id,
                    model_name=self.model_name,
                    call_purpose=final_call_purpose,
                    temperature=self.temperature
                )
            
            # 执行实际调用
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                reasoning_effort="high",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout if self.timeout is not None else 600000           
                )
            
            if response:
                print(f"response是：{response}")
                
                # 记录调用结束
                if global_llm_monitor.enabled:
                    usage_info = global_llm_monitor._parse_usage_from_response(response)
                    global_llm_monitor.logger.log_call_end(
                        call_id=call_id,
                        prompt_tokens=usage_info['prompt_tokens'],
                        completion_tokens=usage_info['completion_tokens'],
                        total_tokens=usage_info['total_tokens'],
                        cached_tokens=usage_info['cached_tokens'],
                        success=True
                    )
                
                # 确保返回值不为None
                content = response.choices[0].message.content
                return content if content is not None else ""
            else:
                logging.warning("No text response from Gemini API.")
                # 记录调用失败
                if global_llm_monitor.enabled:
                    global_llm_monitor.logger.log_call_end(
                        call_id=call_id,
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_tokens=0,
                        cached_tokens=0,
                        success=False,
                        error_message="No text response from Gemini API"
                    )
                return ""
        except Exception as e:
            logging.error(f"Gemini API 调用失败: {e}")
            # 记录调用失败
            if global_llm_monitor.enabled:
                global_llm_monitor.logger.log_call_end(
                    call_id=call_id,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cached_tokens=0,
                    success=False,
                    error_message=str(e)
                )
            return ""
    
    def invoke(self, prompt: str, purpose: str = "未指定") -> str:
        """保持原有接口不变，默认启用监控"""
        return self.invoke_with_monitoring(prompt, call_purpose=purpose)


class QwenAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        super().__init__()
        self.interface_format = "qwen"
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def invoke_with_monitoring(self, prompt: str, call_purpose: Optional[str] = None) -> str:
        """带监控的调用方法"""
        call_id = str(uuid.uuid4())
        
        try:
            # 检查 _client 是否已正确初始化
            if not hasattr(self, '_client') or self._client is None:
                raise ValueError("OpenAI client not initialized.")
            
            # 记录调用开始
            if global_llm_monitor.enabled:
                final_call_purpose = call_purpose or "未指定"
                global_llm_monitor.logger.log_call_start(
                    call_id=call_id,
                    model_name=self.model_name,
                    call_purpose=final_call_purpose,
                    temperature=self.temperature
                )

            # 执行实际调用
            completion = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                # enable_thinking 参数通常通过 extra_body 传递，具体取决于API版本和库支持
                # 如果直接支持 enable_thinking，则可以这样写：enable_thinking=True/False
                # 如果需要通过 extra_body 传递，则 extra_body 应该是一个字典
                extra_body={"enable_thinking": True}, # 假设通过 extra_body 传递
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout if self.timeout is not None else 600
            )
            
            # 记录调用结束
            if global_llm_monitor.enabled:
                usage_info = global_llm_monitor._parse_usage_from_response(completion)
                global_llm_monitor.logger.log_call_end(
                    call_id=call_id,
                    prompt_tokens=usage_info['prompt_tokens'],
                    completion_tokens=usage_info['completion_tokens'],
                    total_tokens=usage_info['total_tokens'],
                    cached_tokens=usage_info['cached_tokens'],
                    success=True
                )
            
            # 确保返回值不为None
            content = completion.choices[0].message.content
            return content if content is not None else ""
        except Exception as e:
            logging.error(f"Qwen API 调用失败: {e}")
            # 记录调用失败
            if global_llm_monitor.enabled:
                global_llm_monitor.logger.log_call_end(
                    call_id=call_id,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cached_tokens=0,
                    success=False,
                    error_message=str(e)
                )
            return ""
    
    def invoke(self, prompt: str, purpose: str = "未指定") -> str:
        """保持原有接口不变，默认启用监控"""
        return self.invoke_with_monitoring(prompt, call_purpose=purpose)


def create_llm_adapter(
    interface_format: str,  # 接口格式，如 "doubao","gemini"等
    base_url: str,  # 基础 URL
    model_name: str,  # 模型名称
    api_key: str,  # API 密钥
    max_tokens: int,  # 最大令牌数，限制生成文本的长度
    temperature: float = 0.6,  # 温度参数，控制生成文本的随机性
    timeout: int = 600  # 超时时间，单位秒
) -> BaseLLMAdapter:
    """
    工厂函数：根据 interface_format 返回不同的适配器实例。
    """
    fmt = interface_format.strip().lower()
    if fmt == "doubao":
        return DoubaoAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "gemini":
        return GeminiAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "qwen":
        return QwenAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    else:
        raise ValueError(f"Unknown interface_format: {interface_format}")


llm_gemini_flash = create_llm_adapter(interface_format="gemini",
                                      base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                                      model_name="gemini-2.5-flash",
                                      api_key="AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA",
                                      max_tokens=65536,
                                      )

llm_gemini_pro = create_llm_adapter(interface_format="gemini",
                                      base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                                      model_name="gemini-2.5-pro",
                                      api_key="AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA",
                                      max_tokens=65536,
                                      )

llm_qwen_plus = create_llm_adapter(interface_format="qwen",
                                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                                      model_name="qwen-plus",
                                      api_key="sk-1ef165b563f646a482c2a0b589fa9b09",
                                      max_tokens=32768
                                      )

llm_doubao = create_llm_adapter(interface_format="doubao",
                                      base_url="https://ark.cn-beijing.volces.com/api/v3",
                                      model_name="doubao-seed-1-6-250615",
                                      api_key="141c1a18-56d4-4799-a975-44585266f86c",
                                      max_tokens=32000
                                      )