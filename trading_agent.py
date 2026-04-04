import asyncio
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from data_scraper import DataScraper
from sentiment_analyzer import SentimentAnalyzer
from risk_manager import RiskManager
from kalshi_client_wrapper import KalshiClientWrapper
from settings import settings
from src.agents.debate_engine import DebateEngine

class AgentState(TypedDict):
    market_id: str
    market_question: str
    market_mid_price: float
    context: List[str]
    bull_arg: str
    bear_arg: str
    forecast_arg: str
    risk_arg: str
    llm_prob: float
    edge: float
    decision: str  # "TRADE", "SKIP", "PAPER_TRADE", "RISK_FAILED"
    trade_amount: float
    trade_result: Dict[str, Any]

class TradingAgent:
    """
    LangGraph orchestration compiling logic from monitor_markets -> multi_agent_debate -> risk_check -> execute_trade
    """
    def __init__(self, kalshi_client, risk_manager):
        self.scraper = DataScraper()
        self.analyzer = SentimentAnalyzer()
        self.risk_manager = risk_manager
        self.kalshi = kalshi_client
        self.debate = DebateEngine()
        
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # Define Nodes
        workflow.add_node("monitor_markets", self.monitor_markets_node)
        workflow.add_node("multi_agent_debate", self.multi_agent_debate_node)
        workflow.add_node("risk_check", self.risk_check_node)
        workflow.add_node("execute_kalshi_trade", self.execute_trade_node)
        workflow.add_node("paper_execution", self.paper_execution_node)
        workflow.add_node("record_skip", self.record_skip_node)

        # Define Edges
        workflow.set_entry_point("monitor_markets")
        workflow.add_edge("monitor_markets", "multi_agent_debate")
        workflow.add_edge("multi_agent_debate", "risk_check")
        
        # Conditional branching after risk_check
        workflow.add_conditional_edges(
            "risk_check",
            lambda state: state["decision"],
            {
                "TRADE": "execute_kalshi_trade",
                "PAPER_TRADE": "paper_execution",
                "RISK_FAILED": "record_skip",
                "SKIP": "record_skip"
            }
        )
        
        workflow.add_edge("execute_kalshi_trade", END)
        workflow.add_edge("paper_execution", END)
        workflow.add_edge("record_skip", END)

        return workflow.compile()

    async def monitor_markets_node(self, state: AgentState) -> AgentState:
        print(f"[NODE] monitor_markets for: {state.get('market_id')}")
        context = await self.scraper.fetch_headlines(state["market_question"])
        state["context"] = context
        return state

    async def multi_agent_debate_node(self, state: AgentState) -> AgentState:
        print("[NODE] multi_agent_debate (Parallel)")
        
        market_question = state["market_question"]
        context_str = "\n".join(state["context"])
        user_prompt = f"Event: {market_question}\nContext: {context_str}"
        
        # Execute 4 personas in parallel
        bull_task = self.analyzer.evaluate_persona(self.debate.get_bull_prompt(), user_prompt)
        bear_task = self.analyzer.evaluate_persona(self.debate.get_bear_prompt(), user_prompt)
        forecast_task = self.analyzer.evaluate_persona(self.debate.get_forecaster_prompt(), user_prompt)
        risk_task = self.analyzer.evaluate_persona(self.debate.get_risk_manager_prompt(), user_prompt)
        
        bull_arg, bear_arg, forecast_arg, risk_arg = await asyncio.gather(
            bull_task, bear_task, forecast_task, risk_task
        )
        
        state["bull_arg"] = bull_arg
        state["bear_arg"] = bear_arg
        state["forecast_arg"] = forecast_arg
        state["risk_arg"] = risk_arg
        
        print("       --> Sub-personas completed debate computation")
        
        # Lead Analyst synthesis
        lead_prompt = self.debate.get_lead_analyst_prompt(bull_arg, bear_arg, forecast_arg, risk_arg)
        lead_response = await self.analyzer.evaluate_persona(
            lead_prompt, 
            "Please formulate your final prediction float.", 
            expects_json=True,
            engine="cloud_gemini"
        )
        
        prob = await self.analyzer.extract_probability(lead_response)
        state["llm_prob"] = prob
        
        # Calculate Edge
        mid_price = state.get("market_mid_price", 0.5)
        edge = abs(prob - mid_price)
        state["edge"] = round(edge, 4)
        
        print(f"       Lead Analyst Prob: {prob:.2f} | Mid Price: {mid_price:.2f} | Edge: {edge:.4f}")
        
        if edge > 0.005:
            state["decision"] = "EVALUATE_RISK"
        else:
            state["decision"] = "SKIP"
            state["trade_result"] = {"status": "skipped", "reason": "Edge < 0.5%"}
            
        return state

    async def risk_check_node(self, state: AgentState) -> AgentState:
        print("[NODE] risk_check")
        if state["decision"] == "SKIP":
            return state
            
        amount_to_trade = min(2.0, settings.MAX_TRADE_SIZE)
        state["trade_amount"] = amount_to_trade
        
        if self.risk_manager.validate_trade(amount_to_trade):
            if settings.PAPER_MODE:
                state["decision"] = "PAPER_TRADE"
            else:
                state["decision"] = "TRADE"
        else:
            state["decision"] = "RISK_FAILED"
            state["trade_result"] = {"status": "skipped", "reason": "Failed risk checks."}
            
        return state

    async def execute_trade_node(self, state: AgentState) -> AgentState:
        print(f"[NODE] execute_kalshi_trade (LIVE) - Amount: {state['trade_amount']}")
        mid_cents = int(state.get("market_mid_price", 0.5) * 100)
        amount_cents = int(state["trade_amount"] * 100)
        
        res = await self.kalshi.place_order(state["market_id"], "buy", amount_cents, mid_cents)
        
        if res.get("status") == 200:
            self.risk_manager.record_trade(state["trade_amount"])
        state["trade_result"] = {"status": "live_executed", "api_response": res}
        return state

    async def paper_execution_node(self, state: AgentState) -> AgentState:
        print(f"[NODE] paper_execution (SIMULATED) - Amount: {state['trade_amount']}")
        mid_cents = int(state.get("market_mid_price", 0.5) * 100)
        amount_cents = int(state["trade_amount"] * 100)
        
        res = await self.kalshi.place_order(state["market_id"], "buy", amount_cents, mid_cents)
        
        if res.get("status") == "simulated":
            self.risk_manager.record_trade(state["trade_amount"])
        state["trade_result"] = {"status": "paper_executed", "api_response": res, "edge": state["edge"]}
        return state

    async def record_skip_node(self, state: AgentState) -> AgentState:
        print(f"[NODE] record_skip - Reason: {state.get('decision')}")
        return state

    async def run_market_cycle(self, market_data: dict) -> dict:
        initial_state: AgentState = {
            "market_id": market_data["id"],
            "market_question": market_data["question"],
            "market_mid_price": market_data["mid_price"],
            "context": [],
            "bull_arg": "",
            "bear_arg": "",
            "forecast_arg": "",
            "risk_arg": "",
            "llm_prob": 0.0,
            "edge": 0.0,
            "decision": "",
            "trade_amount": 0.0,
            "trade_result": {}
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state
