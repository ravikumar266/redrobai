import logging
import asyncio
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel
from backend.config import settings

logger = logging.getLogger(__name__)

class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass

class QuotaExceededError(LLMProviderError):
    """Quota or rate limit exceeded error."""
    pass


class BaseLLMProvider:
    """
    Abstract Base Class for LLM Providers.
    """
    async def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Send a request to the LLM provider.
        """
        raise NotImplementedError("Providers must implement the generate method.")

    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], system_instruction: Optional[str] = None) -> BaseModel:
        """
        Send a request to the LLM provider demanding a structured JSON response matching a Pydantic model.
        """
        raise NotImplementedError("Providers must implement the generate_structured method.")


class GeminiProvider(BaseLLMProvider):
    """
    Provider implementation for Google Gemini.
    """
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized GeminiProvider using key prefix: {self.api_key[:5]}...")
            except Exception as e:
                logger.error(f"Failed to initialize google-generativeai client: {e}")
        else:
            logger.info("GeminiProvider initialized without API key.")

    async def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Call Gemini API with retry and specific key.
        """
        logger.debug(f"GeminiProvider calling generate with model {self.model_name}")
        if not self.api_key or not self.client:
            raise LLMProviderError("No API key configured or client not initialized for Gemini provider.")
        
        try:
            import google.generativeai as genai
            
            def _call():
                if system_instruction:
                    model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
                else:
                    model = self.client
                return model.generate_content(prompt)
                
            response = await asyncio.to_thread(_call)
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "429" in err_str or "rate limit" in err_str:
                raise QuotaExceededError(f"Gemini quota exceeded: {e}")
            raise LLMProviderError(f"Gemini generation failed: {e}")

    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], system_instruction: Optional[str] = None) -> BaseModel:
        """
        Call Gemini API and return validated Pydantic model.
        """
        logger.debug(f"GeminiProvider structured call with model {self.model_name}")
        if not self.api_key or not self.client:
            raise LLMProviderError("No API key configured or client not initialized for Gemini provider.")
            
        try:
            import google.generativeai as genai
            
            def _call():
                generation_config = {
                    "response_mime_type": "application/json",
                }
                if system_instruction:
                    model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
                else:
                    model = self.client
                
                # We inject the JSON schema into the prompt to bypass the SDK's bug with Pydantic default fields
                modified_prompt = f"{prompt}\n\nYou must return a valid JSON object that perfectly matches the following JSON Schema:\n{response_model.model_json_schema()}"
                return model.generate_content(modified_prompt, generation_config=generation_config)
                
            response = await asyncio.to_thread(_call)
            return response_model.model_validate_json(response.text)
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "429" in err_str or "rate limit" in err_str:
                raise QuotaExceededError(f"Gemini quota exceeded: {e}")
            raise LLMProviderError(f"Gemini structured generation failed: {e}")


class GroqProvider(BaseLLMProvider):
    """
    Provider implementation for Groq (Llama-3 model hosting).
    """
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("Initialized GroqProvider.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.info("GroqProvider initialized without API key.")

    async def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Call Groq API as a fallback.
        """
        logger.debug(f"GroqProvider calling generate with model {self.model_name}")
        if not self.api_key or not self.client:
            raise LLMProviderError("No API key configured or client not initialized for Groq provider.")
            
        try:
            def _call():
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                )
                return completion.choices[0].message.content
                
            return await asyncio.to_thread(_call)
        except Exception as e:
            raise LLMProviderError(f"Groq generation failed: {e}")

    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], system_instruction: Optional[str] = None) -> BaseModel:
        """
        Call Groq API and return validated Pydantic model.
        """
        logger.debug(f"GroqProvider structured call with model {self.model_name}")
        if not self.api_key or not self.client:
            raise LLMProviderError("No API key configured or client not initialized for Groq provider.")
            
        try:
            def _call():
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({
                    "role": "user", 
                    "content": f"{prompt}\n\nYou must return a JSON object that matches the following JSON Schema:\n{response_model.model_json_schema()}"
                })
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                return completion.choices[0].message.content
                
            res_text = await asyncio.to_thread(_call)
            return response_model.model_validate_json(res_text)
        except Exception as e:
            raise LLMProviderError(f"Groq structured generation failed: {e}")


class ProviderManager:
    """
    Manager responsible for rotating Gemini keys, executing retries with exponential backoff,
    and falling back to Groq if all Gemini keys fail.
    """
    def __init__(self):
        self.gemini_keys: List[str] = settings.gemini_keys
        self.current_key_index = 0
        self.groq_api_key = settings.GROQ_API_KEY
        
        # Instantiate provider structures
        self.providers: List[GeminiProvider] = [
            GeminiProvider(api_key=key, model_name=settings.GEMINI_MODEL_NAME)
            for key in self.gemini_keys
        ]
        self.fallback_provider = GroqProvider(api_key=self.groq_api_key, model_name=settings.GROQ_MODEL_NAME) if self.groq_api_key else None

    def rotate_key(self) -> None:
        """
        Rotate to the next Gemini key in the list.
        """
        if not self.providers:
            return
        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.providers)
        logger.warning(f"Rotating Gemini key from index {old_index} to {self.current_key_index}.")

    async def execute_with_fallback(self, call_type: str, *args, **kwargs) -> Any:
        """
        Executes an LLM call. Automatically handles:
        1. Key rotation on Gemini failures (such as quota exceeded).
        2. Exponential backoff and retry.
        3. Switching to Groq provider if all Gemini keys fail.
        """
        max_retries_per_key = 3
        backoff_factor = 2.0
        
        # 1. Try Gemini providers sequentially
        for provider_idx in range(len(self.providers)):
            current_provider = self.providers[self.current_key_index]
            for attempt in range(max_retries_per_key):
                try:
                    # Execute call dynamically (generate or generate_structured)
                    if call_type == "text":
                        return await current_provider.generate(*args, **kwargs)
                    elif call_type == "structured":
                        return await current_provider.generate_structured(*args, **kwargs)
                except QuotaExceededError as e:
                    logger.warning(f"Quota exceeded on Gemini key index {self.current_key_index}: {e}. Rotating key.")
                    self.rotate_key()
                    break  # Break inner loop to try next key immediately
                except Exception as e:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Error on Gemini key index {self.current_key_index} (Attempt {attempt+1}/{max_retries_per_key}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            
            # If we've exhausted retries on the current key and did not break due to quota, rotate for next provider iteration
            self.rotate_key()

        # 2. Fall back to Groq if all Gemini keys fail
        if self.fallback_provider:
            logger.error("All Gemini keys failed. Falling back to Groq Provider...")
            for attempt in range(max_retries_per_key):
                try:
                    if call_type == "text":
                        return await self.fallback_provider.generate(*args, **kwargs)
                    elif call_type == "structured":
                        return await self.fallback_provider.generate_structured(*args, **kwargs)
                except Exception as e:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Groq fallback attempt {attempt+1}/{max_retries_per_key} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        raise LLMProviderError("All LLM Providers (Gemini and Groq fallback) failed to generate response.")


class LLMService:
    """
    High-level LLM Service.
    This is the only class that graph nodes call directly to generate LLM responses.
    Hides all provider details, fallback, and rotation complexities.
    """
    _manager: ProviderManager = None

    @classmethod
    def get_manager(cls) -> ProviderManager:
        if cls._manager is None:
            cls._manager = ProviderManager()
        return cls._manager

    @classmethod
    def reset_manager(cls) -> None:
        """Reset manager instance (e.g. for testing/config changes)."""
        cls._manager = None

    @classmethod
    async def generate(cls, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Unified method to generate plain text using the LLM service.
        """
        manager = cls.get_manager()
        return await manager.execute_with_fallback("text", prompt=prompt, system_instruction=system_instruction)

    @classmethod
    async def generate_structured(
        cls, 
        prompt: str, 
        response_model: Type[BaseModel], 
        system_instruction: Optional[str] = None
    ) -> BaseModel:
        """
        Unified method to generate a Pydantic-validated structured object.
        """
        manager = cls.get_manager()
        return await manager.execute_with_fallback(
            "structured", 
            prompt=prompt, 
            response_model=response_model, 
            system_instruction=system_instruction
        )
