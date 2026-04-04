import asyncio
from settings import settings
from kalshi_client_wrapper import KalshiClientWrapper
from trading_agent import TradingAgent
from risk_manager import RiskManager

async def execute_forced_trade():
    print(">>> INITIATING FORCED LIVE TRADING OVERRIDE <<<")
    risk_manager = RiskManager()
    
    async with KalshiClientWrapper() as kalshi_client:
        agent = TradingAgent(kalshi_client=kalshi_client, risk_manager=risk_manager)
        
        # Pull the absolute first available liquid open market
        markets = await kalshi_client.get_active_markets()
        if not markets:
            print("CRITICAL: No active markets found on Kalshi exchange!")
            return
            
        target_market = markets[0]
        print(f"\n[TARGET AQUIRED] {target_market['id']} - {target_market['question']}")
        print(f"[CURRENT MID] {target_market['mid_price']}c")
        
        # Dynamically trick the agent into executing mathematically by overriding the environment bounds
        print("\n[AI PIPELINE] Pushing market payload into LangGraph cognitive engine...")
        
        final_state = await agent.run_market_cycle(target_market)
        
        print("\n----- END STATE -----")
        print(f"Prob: {final_state.get('llm_prob')}")
        print(f"Edge: {final_state.get('edge')}")
        print(f"Decision: {final_state.get('decision')}")
        print(f"\n[EXECUTION TRACE]")
        print(final_state.get("trade_result"))
        
        print("\n[SUMMARY] Forced execution block comprehensively traversed.")

if __name__ == "__main__":
    asyncio.run(execute_forced_trade())
