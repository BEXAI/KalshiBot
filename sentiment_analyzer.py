import aiohttp
import json
import re
from typing import Dict, Any, Optional
from settings import settings

# Precompile optimization for hot loop execution
THINK_REGEX = re.compile(r'<think>.*?</think>', re.DOTALL)
SUMMARY_REGEX = re.compile(r'<summary>(.*?)</summary>', re.DOTALL)
PROB_REGEX_VERBOSE = re.compile(r'(?:probability(?: is)?|confidence|chance|prob).*?([0-1]?\.\d+|\d{1,3}%|\d{1,3})', re.IGNORECASE | re.DOTALL)
PROB_REGEX_STRICT = re.compile(r'\b(0\.\d+|1\.0)\b')

class SentimentAnalyzer:
    """
    Utilizes local Ollama for zero-latency, private evaluation.
    Supports injecting specific Personas for debate workflows.
    """
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_URL}/api/generate"
        self.local_model = settings.LLM_MODEL
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={settings.GEMINI_API_KEY}"
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def evaluate_persona(self, system_prompt: str, user_prompt: str, expects_json: bool = False, engine: str = "local_gemma") -> str:
        """
        Generic evaluation function for varied debate personas.
        Routes to 'local_gemma' via Ollama or 'cloud_gemini' via REST API.
        Includes parsing logic to remove Gemma 4 <think> streams.
        """
        
        # Enclose the prompt in data contracts per Gemma 4 best practice
        structured_user_prompt = f"<data>\n{user_prompt}\n</data>"
        
        if engine == "cloud_gemini":
            response = await self._evaluate_gemini(system_prompt, structured_user_prompt, expects_json)
        else:
            response = await self._evaluate_gemma(system_prompt, structured_user_prompt, expects_json)
            
        # Post-process Gemma output to strip internal monologues
        parsed_response = THINK_REGEX.sub('', response).strip()
        
        # Further refine to just the summary payload if it emitted <summary> tags
        summary_match = SUMMARY_REGEX.search(parsed_response)
        if summary_match:
            return summary_match.group(1).strip()
            
        return parsed_response

    async def _evaluate_gemini(self, system_prompt: str, user_prompt: str, expects_json: bool) -> str:
        """
        Hits the external Gemini 3.1 Pro API for maximum reasoning synthesis.
        """
        payload = {
            "contents": [{
                "parts": [{"text": f"System: {system_prompt}\nUser: {user_prompt}"}]
            }]
        }
        try:
            session = await self._get_session()
            async with session.post(self.gemini_url, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as response:
                if response.status == 200:
                    data = await response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                        return candidates[0]["content"]["parts"][0].get("text", "").strip()
                    else:
                        error_text = await response.text()
                        print(f"Gemini API Error {response.status}: {error_text}")
        except Exception as e:
            print(f"Error querying Gemini: {e}")
        return ""

    async def _evaluate_gemma(self, system_prompt: str, user_prompt: str, expects_json: bool) -> str:
        prompt_with_system = f"<system>\n{system_prompt}\n</system>\n\n<user>\n{user_prompt}\n</user>"
        
        payload = {
            "model": self.local_model,
            "prompt": prompt_with_system,
            "stream": False
        }
        if expects_json:
            payload["format"] = "json"

        try:
            session = await self._get_session()
            async with session.post(self.ollama_url, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "").strip()
                else:
                    print(f"Ollama API Error: {response.status}")
        except Exception as e:
            print(f"Error querying Ollama: {e}")
            
        return ""

    async def extract_probability(self, llm_response: str) -> float:
        """
        Helper to safely parse the probability float from the Lead Analyst's response.
        """
        try:
            prob = float(llm_response)
            return prob
        except ValueError:
            try:
                parsed = json.loads(llm_response)
                for val in parsed.values():
                    if isinstance(val, (int, float)):
                        return float(val)
            except json.JSONDecodeError:
                pass
                
            # Regex Fallback
            match = PROB_REGEX_VERBOSE.search(llm_response)
            if not match:
                match = PROB_REGEX_STRICT.search(llm_response)
                
            if match:
                val_str = match.group(1).replace('%', '')
                try:
                    parsed_val = float(val_str)
                    if parsed_val > 1.0:
                        parsed_val /= 100.0
                    if 0.0 <= parsed_val <= 1.0:
                        return parsed_val
                except ValueError:
                    pass
                    
            print(f"[WARN] Fallback: Parse failed. Returning 0.5. Response: {llm_response[:150]}")
            
        return 0.5 # Neutral fallback
