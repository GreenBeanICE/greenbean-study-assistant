from app.agents.classification_agent import RouterAgent
from app.prompts.chat_prompts import CHAT_SYSTEM_PROMPT, CHAT_USER_PROMPT_TPL
from app.providers.registry import ProviderRegistry
from app.schemas.chat_schema import ChatRequest, ChatResponse


class ChatAgent:
    def __init__(self) -> None:
        self.router = RouterAgent()

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        route_decision = await self.router.route_question(request.query)
        print(f"[CHAT AGENT] 识别到的意图 : {route_decision.route}")

        # TODO : 后续替换为真实的 RAG 检索
        mock_retrieved_context = (
            "Le polymorphisme est un concept fondamental en programmation "
            "orientée objet qui permet à des objets de classes différentes "
            "d'être traités comme des objets d'une classe commune."
        )

        provider = ProviderRegistry.get_active()
        response = await provider.chat_completion(
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                *[{"role": msg.role, "content": msg.content} for msg in request.history],
                {
                    "role": "user",
                    "content": CHAT_USER_PROMPT_TPL.substitute(
                        context=mock_retrieved_context,
                        question=request.query,
                    ),
                },
            ],
            temperature=0.3,
        )

        answer = response.content
        return ChatResponse(session_id=request.session_id, answer=answer)
