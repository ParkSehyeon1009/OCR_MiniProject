# =============================================================================
# 이 파일의 책임: client_protocol.py의 AIClientProtocol을 실제 OpenAI API 호출로
#   구현하는 자리. 지금은 껍데기만 두고, 실제 연동 로직은 이후에 채운다.
# 다른 파일과의 관계: core/config.py의 settings.API_KEY를 사용하게 될 것이고,
#   서비스 레이어는 이 클래스를 직접 참조하지 않고 client_protocol.AIClientProtocol
#   타입으로만 의존한다 (DI를 통해 FakeAIClient <-> OpenAIClient를 교체 가능하게 하기 위함).
# Spring 비교: interface AIClient의 실제 프로덕션 구현체(@Component/@Service)에 해당.
#   application.yml의 api-key 값을 생성자 주입받는 것과 동일하게, 여기서는
#   Settings(=config.py)를 생성자 인자로 받는 형태를 고려할 수 있습니다.
# =============================================================================

from app.ai.client_protocol import AIClientProtocol, AIResult
from app.core.config import Settings


class OpenAIClient(AIClientProtocol):
    #TODO: 여기서 openai SDK 클라이언트 인스턴스를 만들어 self._client에 보관
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.API_KEY
        self._client = None

    # TODO: AIClientProtocol을 만족하도록 generate 메서드를 구현하세요.
    #   지금은 실제 API 호출 로직을 채우지 말고 자리만 남겨둡니다.
    #   나중에 채울 위치:
    #   async def generate(self, prompt: str) -> str:
    #       result = await self.generate_with_meta(prompt)
    #       return result.text
    async def generate(self, prompt: str) -> str:
        pass

    # TODO: AIClientProtocol을 만족하도록 generate_with_meta 메서드를 구현하세요.
    #   나중에 채울 위치:
    #   async def generate_with_meta(self, prompt: str) -> AIResult:
    #       # TODO: self._client를 사용해 실제 OpenAI API(chat completion 등) 호출
    #       # TODO: response.usage.prompt_tokens / completion_tokens 에서 토큰 수 추출
    #       # TODO: 호출 전후 시각을 측정해 latency_ms 계산
    #       # TODO: 예외 발생 시 BusinessError(ErrorCode.AI_PROVIDER_ERROR 등)로 감싸서 던질지 결정
    #       pass
    async def generate_with_meta(self, prompt: str) -> AIResult:
        pass

