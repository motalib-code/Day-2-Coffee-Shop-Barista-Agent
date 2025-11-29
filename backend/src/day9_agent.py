import logging
from typing import Annotated, List, Dict, Any
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, deepgram, silero, murf

from day9_merchant import search_catalog, place_order, get_last_order_summary, add_to_cart, view_cart, checkout

logger = logging.getLogger("day9-ecommerce-agent")
logger.setLevel(logging.INFO)

class EcommerceAgent:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.agent = None

    async def start(self):
        # Initialize the agent
        self.agent = VoicePipelineAgent(
            vad=silero.VAD.load(),
            stt=deepgram.STT(model="nova-3"),
            llm=openai.LLM(), # Keeping OpenAI for reliability, though README says Ollama
            tts=murf.TTS(
                voice="en-IN-arjun", # Assuming this ID exists or falls back
                style="Conversation"
            ),
            chat_ctx=llm.ChatContext().append(
                role="system",
                text=(
                    "You are 'Natalie', a helpful and stylish E-commerce Shopping Assistant for 'TechStyle Store' - a developer merchandise shop. "
                    "Your goal is to help users browse products and place orders using the Agentic Commerce Protocol (Lite). "
                    "You have access to a product catalog, a shopping cart, and order management. "
                    "When a user asks to see products, use the 'search_products' tool. "
                    "Summarize the results concisely, mentioning price (in INR) and key attributes. "
                    "You can add items to the user's cart using 'add_to_cart'. "
                    "Users can view their cart with 'view_cart' and finalize the purchase with 'checkout'. "
                    "When checking out, ask for the user's name if not provided, and pass it to the 'checkout' tool. "
                    "If a user wants to buy something immediately without a cart, you can use 'place_order', also asking for their name. "
                    "Always be polite, professional, and confirm order details before placing them. "
                    "If the user asks about what they just bought, use the 'get_last_order' tool. "
                    "For 'add_to_cart' or 'place_order', you need the 'product_id'. "
                    "Quantity defaults to 1 if not specified. Options (like color/size) should be in an 'options' dictionary."
                ),
            ),
            fnc_ctx=self._create_fnc_ctx(),
        )

        # Start the agent
        await self.agent.start(self.ctx.room)
        await self.agent.say("Welcome to TechStyle Store! I'm Natalie. How can I help you shop for developer swag today?", allow_interruptions=True)

    def _create_fnc_ctx(self):
        fnc_ctx = llm.FunctionContext()

        @fnc_ctx.ai_callable(description="Search for products in the catalog")
        def search_products(
            query: Annotated[str, llm.TypeInfo(description="Search query (e.g., 'mug', 'hoodie')")] = None,
            category: Annotated[str, llm.TypeInfo(description="Filter by category (e.g., 'Mugs', 'T-Shirts', 'Hoodies')")] = None,
            max_price: Annotated[float, llm.TypeInfo(description="Filter by maximum price")] = None,
        ) -> str:
            return search_catalog(query, category, max_price)

        @fnc_ctx.ai_callable(description="Add an item to the shopping cart")
        def add_to_cart_tool(
            product_id: Annotated[str, llm.TypeInfo(description="ID of the product to add")],
            quantity: Annotated[int, llm.TypeInfo(description="Quantity to add")] = 1,
            options: Annotated[Dict[str, Any], llm.TypeInfo(description="Product options (color, size, etc.)")] = None,
        ) -> str:
            return add_to_cart(product_id, quantity, options)

        @fnc_ctx.ai_callable(description="View the current shopping cart")
        def view_cart_tool() -> str:
            return view_cart()

        @fnc_ctx.ai_callable(description="Checkout and place order for items in the cart")
        def checkout_tool(
            buyer_name: Annotated[str, llm.TypeInfo(description="Name of the buyer")] = "Guest"
        ) -> str:
            return checkout(buyer_name)

        @fnc_ctx.ai_callable(description="Place an immediate order for one or more products (bypassing cart)")
        def place_order_tool(
            items: Annotated[List[Dict[str, Any]], llm.TypeInfo(description="List of items to order. Each item must have 'product_id'. Optional: 'quantity' (int), 'options' (dict of color/size etc).")],
            buyer_name: Annotated[str, llm.TypeInfo(description="Name of the buyer")] = "Guest"
        ) -> str:
            return place_order(items, buyer_name)

        @fnc_ctx.ai_callable(description="Get a summary of the last placed order")
        def get_last_order() -> str:
            return get_last_order_summary()

        return fnc_ctx

def entrypoint(ctx: JobContext):
    agent = EcommerceAgent(ctx)
    ctx.loop.create_task(agent.start())

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
