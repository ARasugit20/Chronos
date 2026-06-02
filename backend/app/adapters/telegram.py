import httpx
import structlog

from app.config import get_settings
from app.models.event import Event
from app.models.recommendation import Recommendation
from app.models.signal import Signal

logger = structlog.get_logger(__name__)


class TelegramAdapter:
    """If TELEGRAM_BOT_TOKEN is empty string, all sends go to structlog instead."""

    def format_recommendation(self, rec: Recommendation, signal: Signal, event: Event) -> str:
        return (
            f"Recommendation {rec.id}\n"
            f"Ticker: {signal.ticker}\n"
            f"Action: {rec.action}\n"
            f"Amount USD: {rec.amount_usd}\n"
            f"Probability: {signal.probability_calibrated:.2f}\n"
            f"Expires: {rec.expires_at.isoformat()}\n"
            f"Reason: {rec.reason}\n"
            f"Event: {event.title}\n"
            f"Model: {signal.model_version}\n"
            f"{rec.disclaimer}"
        )

    async def send(self, message: str) -> bool:
        settings = get_settings()
        if not settings.telegram_bot_token:
            logger.info("telegram.disabled", message=message)
            return True
        try:
            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json={"chat_id": settings.telegram_chat_id, "text": message},
                )
            return response.status_code == 200
        except Exception as exc:  # noqa: BLE001
            logger.warning("telegram.send_failed", error=str(exc))
            return False
