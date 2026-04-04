import asyncio
import pydantic.v1 # Fixes Python 3.13 deadlock via langchain_core
import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()

from trading_agent import TradingAgent
from risk_manager import RiskManager
from error_cache import error_cache

async def test_prompt_engineering():
    print("==================================")
    print(" DEBATE ENGINE: PROMPT TEST       ")
    print("==================================")
    
    test_market = {
        "id": "KX-TIKTOK-2026",
        "question": "Will TikTok be abruptly banned in the US by Dec 31, 2026?",
        "mid_price": 0.35
    }
    
    class MockKalshi:
        async def place_order(self, *args, **kwargs):
            return {"status": "simulated", "mock": True}
            
    risk_manager = RiskManager()
    agent = TradingAgent(kalshi_client=MockKalshi(), risk_manager=risk_manager)
    
    state = {
        "market_id": test_market["id"],
        "market_question": test_market["question"],
        "market_mid_price": test_market["mid_price"],
        "context": ["Congress passes resolution, stalls in Senate.", "ByteDance refuses divestiture."],
        "bull_arg": "", "bear_arg": "", "forecast_arg": "", "risk_arg": "",
        "llm_prob": 0.0, "edge": 0.0, "decision": "", "trade_amount": 0.0, "trade_result": {}
    }
    
    print("\n[+] Testing Debate Engine Personas in Parallel... (Waiting for LLM generation)")
    
    final_state = await agent.multi_agent_debate_node(state)
    
    print("\n--- SYNTHESIZED OUTPUTS ---")
    print(f"[BULL]: {final_state.get('bull_arg', 'MISSING')[:200]}...")
    print(f"[BEAR]: {final_state.get('bear_arg', 'MISSING')[:200]}...")
    
    print(f"\n[LEAD ANALYST SYNTHESIS]: {final_state.get('llm_prob')} (Type: {type(final_state.get('llm_prob'))})")
    
    print("\nPROMPT ENGINEERING TEST COMPLETE.")

if __name__ == "__main__":
    asyncio.run(test_prompt_engineering())
