"""Telegram gateway with feature-flag-safe fallback behavior."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Awaitable, Callable

from pradysagican.config import load_config

logger = logging.getLogger(__name__)


class TelegramGateway:
    """Routes Telegram messages into PRADYSAGICAN handlers."""

    def __init__(self) -> None:
        self._cfg = load_config()
        self._enabled = self._cfg.upgrades.enable_telegram_gateway and not self._cfg.upgrades.kill_switch_new_paths
        self._token = os.getenv("PRADY_TELEGRAM_BOT_TOKEN", "")
        self._available = False
        self._app_builder = None
        if self._enabled:
            try:
                from telegram.ext import ApplicationBuilder  # type: ignore[import-not-found]
                self._app_builder = ApplicationBuilder
                self._available = True
            except Exception as exc:  # pragma: no cover
                logger.warning("Telegram SDK unavailable; gateway disabled: %s", exc)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._available and bool(self._token)

    async def start(self, handler: Callable[[str, str], Awaitable[str]]) -> bool:
        """Start polling bot; handler args are (user_id, message_text)."""
        if not self.enabled or self._app_builder is None:
            return False

        from telegram.ext import CommandHandler, MessageHandler, filters  # type: ignore[import-not-found]

        app = self._app_builder().token(self._token).build()

        async def _start_cmd(update, context):  # type: ignore[no-untyped-def]
            await update.message.reply_text("PRADYSAGICAN is online.")

        async def _on_message(update, context):  # type: ignore[no-untyped-def]
            text = update.message.text or ""
            user_id = str(update.effective_user.id) if update.effective_user else "unknown"
            reply = await handler(user_id, text)
            await update.message.reply_text(reply[:4000])

        app.add_handler(CommandHandler("start", _start_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))

        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        return True

    async def stop(self) -> None:
        await asyncio.sleep(0)

