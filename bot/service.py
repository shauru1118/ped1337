import os
import sys
import struct
from pathlib import Path
from typing import List, Optional, Tuple

import telebot
from telebot import types
from loguru import logger

from app import config
from bot.sessions import UserSession, UserSessionManager, UserState
from stego import (
    StegoFacade,
    StegoError,
    CapacityExceededError,
    CorruptedBlockMapError,
    TransformationError,
    InvalidKeyError,
)
from stego.utils.file_parser import extract_text_from_file, FileParserError


class StegoBotService:
    """Enterprise Telegram Bot Service with FSM dialog, Inline Keyboard smart photo flow, and action logging."""

    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        if not self.token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set or is invalid "
                "(use a real bot token, not 'false')."
            )

        self.temp_dir = Path(config.TEMP_DIR_PATH)
        self.key_file_path = str(config.KEY_FILE_PATH)
        self.admin_chat_id = config.ADMIN_CHAT_ID

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.facade = StegoFacade()
        self.key = self.facade.key_manager.load_or_create(self.key_file_path)
        self.session_manager = UserSessionManager()

        self._configure_logging()
        self.bot = telebot.TeleBot(self.token)
        self._bind_event_handlers()

    def _configure_logging(self) -> None:
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
            colorize=True,
            format="<level>{level}\t| {message}</level>",
        )
        logger.info("Initializing StegoBotService FSM & Action Logger...")

    def log_user(self, user: telebot.types.User, action_description: str) -> None:
        username = f"@{user.username}" if user.username else "NoUsername"
        logger.info(f"User {username} (ID: {user.id}) | {action_description}")

    def log_success(self, user: telebot.types.User, action_description: str) -> None:
        username = f"@{user.username}" if user.username else "NoUsername"
        logger.success(f"User {username} (ID: {user.id}) | {action_description}")

    def log_warning(self, user: telebot.types.User, action_description: str) -> None:
        username = f"@{user.username}" if user.username else "NoUsername"
        logger.warning(f"User {username} (ID: {user.id}) | {action_description}")

    def log_error(self, user: telebot.types.User, action_description: str) -> None:
        username = f"@{user.username}" if user.username else "NoUsername"
        logger.error(f"User {username} (ID: {user.id}) | {action_description}")

    def _save_file(self, content: bytes, filename: str) -> Path:
        target = self.temp_dir / filename
        with open(target, "wb") as f:
            f.write(content)
        return target

    @staticmethod
    def _cleanup_file(path: Optional[Path]) -> None:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def _cleanup_session_files(
        self, cover_path: Optional[Path], pending_path: Optional[Path], payload_path: Optional[Path] = None
    ) -> None:
        self._cleanup_file(cover_path)
        self._cleanup_file(pending_path)
        self._cleanup_file(payload_path)

    @staticmethod
    def _is_image_file(filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]

    def _bind_event_handlers(self) -> None:
        @self.bot.message_handler(commands=["start", "help"])
        def on_start_or_help(message: telebot.types.Message):
            self.handle_start_or_help(message)

        @self.bot.message_handler(commands=["cancel"])
        def on_cancel(message: telebot.types.Message):
            self.handle_cancel(message)

        @self.bot.message_handler(commands=["mask", "embed"])
        def on_mask_command(message: telebot.types.Message):
            self.handle_mask_command(message)

        @self.bot.message_handler(commands=["unmask", "extract"])
        def on_unmask_command(message: telebot.types.Message):
            self.handle_unmask_command(message)

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("choice_") or call.data.startswith("filechoice_")
        )
        def on_choice_callback(call: telebot.types.CallbackQuery):
            self.handle_choice_callback(call)

        @self.bot.message_handler(content_types=["document", "photo"])
        def on_media(message: telebot.types.Message):
            self.handle_media_message(message)

        @self.bot.message_handler(content_types=["text"])
        def on_text(message: telebot.types.Message):
            self.handle_text_message(message)

    def handle_start_or_help(self, message: telebot.types.Message) -> None:
        user = message.from_user
        self.log_user(user, "invoked /start or /help")
        c_path, p_path, pay_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path, pay_path)

        text = (
            f"👋 Привет, {user.first_name}!\n"
            "Я бот для безопасного шифрования и скрытия текста или файлов в изображениях.\n\n"
            "📌 **Доступные способы работы:**\n"
            "• Просто **отправьте фото или файл картинки**, и я спрошу, что с ней сделать.\n"
            "• Просто **отправьте любой документ** (txt, pdf, docx или другой файл), чтобы спрятать его в картинку.\n"
            "• /mask (или /embed) — пошагово замаскировать зашифрованный текст в картинку.\n"
            "• /unmask (или /extract) — извлечь и расшифровать скрытый текст или файл из картинки.\n"
            "• /cancel — отменить текущую операцию.\n\n"
            "Отправьте картинку/документ или выберите команду для начала!"
        )
        self.bot.send_message(message.chat.id, text, parse_mode="Markdown")

    def handle_cancel(self, message: telebot.types.Message) -> None:
        user = message.from_user
        self.log_user(user, "invoked /cancel command")
        c_path, p_path, pay_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path, pay_path)

        self.bot.send_message(
            message.chat.id,
            "🛑 Операция отменена. Состояние сброшено.\n"
            "Вы можете отправить фото, документ или использовать /mask или /unmask.",
            parse_mode="Markdown",
        )

    def handle_mask_command(self, message: telebot.types.Message) -> None:
        user = message.from_user
        self.log_user(user, "invoked /mask command")
        c_path, p_path, pay_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path, pay_path)

        self.session_manager.set_state(user.id, UserState.WAITING_MASK_IMAGE)
        self.bot.send_message(
            message.chat.id,
            "🖼️ **Шаг 1 из 2 (Маскировка)**\n\n"
            "Отправьте изображение (фотографией или файлом), которое будет использоваться как обложка.\n"
            "*(Отправьте /cancel для отмены)*",
            parse_mode="Markdown",
        )

    def handle_unmask_command(self, message: telebot.types.Message) -> None:
        user = message.from_user
        self.log_user(user, "invoked /unmask command")
        c_path, p_path, pay_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path, pay_path)

        self.session_manager.set_state(user.id, UserState.WAITING_UNMASK_IMAGE)
        self.bot.send_message(
            message.chat.id,
            "🔍 **Демаскировка**\n\n"
            "Отправьте зашифрованное стего-изображение (в формате PNG файлом или фото), из которого нужно извлечь скрытый текст или файл.\n"
            "*(Отправьте /cancel для отмены)*",
            parse_mode="Markdown",
        )

    def handle_media_message(self, message: telebot.types.Message) -> None:
        user = message.from_user
        user_id = user.id
        session = self.session_manager.get_session(user_id)

        # Check if incoming document is actually an image file
        is_incoming_image = False
        if message.photo:
            is_incoming_image = True
        elif message.document and self._is_image_file(message.document.file_name):
            is_incoming_image = True

        if session.state == UserState.WAITING_MASK_IMAGE:
            if not is_incoming_image:
                self.bot.send_message(message.chat.id, "⚠️ Пожалуйста, отправьте изображение (фото или PNG/JPG файл) в качестве обложки.")
                return
            self.log_user(user, "uploaded cover image for /mask step 1")
            self._process_mask_image_step(message, user_id)

        elif session.state == UserState.WAITING_MASK_IMAGE_FOR_FILE:
            if not is_incoming_image:
                self.bot.send_message(message.chat.id, "⚠️ Пожалуйста, отправьте изображение (фото или PNG/JPG файл) в качестве обложки.")
                return
            self.log_user(user, "uploaded cover image for file masking")
            self._process_mask_image_for_file_step(message, user_id)

        elif session.state == UserState.WAITING_UNMASK_IMAGE:
            if not is_incoming_image:
                self.bot.send_message(message.chat.id, "⚠️ Пожалуйста, отправьте зашифрованную стего-картинку.")
                return
            self.log_user(user, "uploaded stego image for /unmask")
            self._process_unmask_image_step(message, user_id, is_pending=False)

        elif session.state == UserState.WAITING_MASK_TEXT:
            self.log_warning(user, "sent image when text input was expected")
            self.bot.send_message(
                message.chat.id,
                "⚠️ Сейчас ожидается **текстовое сообщение** для зашифровки.\n"
                "Пожалуйста, введите текст сообщением или отправьте /cancel для сброса.",
                parse_mode="Markdown",
            )

        elif session.state == UserState.WAITING_IMAGE_ACTION:
            self.bot.send_message(message.chat.id, "⚠️ Пожалуйста, сделайте выбор в меню выше или отправьте /cancel.")

        elif session.state == UserState.WAITING_FILE_ACTION:
            self.bot.send_message(message.chat.id, "⚠️ Пожалуйста, сделайте выбор в меню выше или отправьте /cancel.")

        else:
            # Smart Media Routing based on format
            if is_incoming_image:
                self.log_user(
                    user,
                    "uploaded image directly without prior command. Presenting Inline Choice...",
                )
                try:
                    temp_path = self._download_media_to_path(message, f"pending_{user_id}")
                    self.session_manager.set_pending_image(user_id, temp_path)
                    self.session_manager.set_state(user_id, UserState.WAITING_IMAGE_ACTION)

                    markup = types.InlineKeyboardMarkup(row_width=1)
                    b_mask_into = types.InlineKeyboardButton(
                        "🔒 Спрятать текст В эту картинку", callback_data="choice_mask_into"
                    )
                    b_mask_self = types.InlineKeyboardButton(
                        "📦 Спрятать ЭТУ картинку (как файл)", callback_data="choice_mask_self"
                    )
                    b_unmask = types.InlineKeyboardButton(
                        "🔓 Демаскировать (извлечь данные)", callback_data="choice_unmask"
                    )
                    b_cancel = types.InlineKeyboardButton(
                        "❌ Отмена", callback_data="choice_cancel"
                    )
                    markup.add(b_mask_into, b_mask_self, b_unmask, b_cancel)

                    self.bot.send_message(
                        message.chat.id,
                        "🖼️ **Изображение получено!**\nЧто вы хотите с ним сделать?",
                        reply_markup=markup,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    self.log_error(user, f"Error saving pending image: {e}")
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Не удалось загрузить изображение. Попробуйте еще раз.",
                    )
            else:
                # Document payload flow
                doc_name = message.document.file_name
                self.log_user(user, f"uploaded document '{doc_name}' directly. Prompting mode choice...")
                try:
                    temp_path = self._download_media_to_path(message, f"pending_doc_{user_id}")
                    self.session_manager.set_pending_payload(user_id, temp_path, None)
                    self.session_manager.set_state(user_id, UserState.WAITING_FILE_ACTION)

                    suffix = Path(doc_name).suffix.lower()
                    markup = types.InlineKeyboardMarkup(row_width=1)

                    if suffix in [".txt", ".pdf", ".docx"]:
                        # Text parsing is supported
                        b_text = types.InlineKeyboardButton("📝 Считать текст и спрятать", callback_data="filechoice_text")
                        b_bin = types.InlineKeyboardButton("📦 Спрятать файл целиком как бинарник", callback_data="filechoice_binary")
                        b_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data="filechoice_cancel")
                        markup.add(b_text, b_bin, b_cancel)
                    else:
                        # Only binary embedding is supported
                        b_bin = types.InlineKeyboardButton("📦 Спрятать файл целиком как бинарник", callback_data="filechoice_binary")
                        b_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data="filechoice_cancel")
                        markup.add(b_bin, b_cancel)

                    self.bot.send_message(
                        message.chat.id,
                        f"📄 **Файл '{doc_name}' получен!**\nВыберите режим маскировки для этого файла:",
                        reply_markup=markup,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    self.log_error(user, f"Error saving pending document payload: {e}")
                    self.bot.send_message(message.chat.id, "❌ Не удалось загрузить файл. Попробуйте еще раз.")

    def handle_choice_callback(self, call: telebot.types.CallbackQuery) -> None:
        user = call.from_user
        user_id = user.id
        session = self.session_manager.get_session(user_id)
        action = call.data

        self.log_user(user, f"clicked inline button: {action}")
        self.bot.answer_callback_query(call.id)

        # Image smart flow callbacks
        if action.startswith("choice_"):
            if (
                session.state != UserState.WAITING_IMAGE_ACTION
                or not session.pending_image_path
            ):
                self.bot.send_message(
                    call.message.chat.id,
                    "⚠️ Время ожидания ответа истекло. Пожалуйста, отправьте фото снова.",
                )
                c_path, p_path, pay_path = self.session_manager.reset(user_id)
                self._cleanup_session_files(c_path, p_path, pay_path)
                return

            if action == "choice_mask_into":
                pending_path = session.pending_image_path
                self.session_manager.set_cover_image(user_id, pending_path)
                self.session_manager.set_pending_image(user_id, None)
                self.session_manager.set_state(user_id, UserState.WAITING_MASK_TEXT)

                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="✅ **Изображение выбрано как обложка!**\n\n"
                    "📝 **Теперь отправьте текстовым сообщением** данные, которые вы хотите зашифровать и спрятать в этой картинке.\n"
                    "*(Повторная отправка картинки НЕ требуется)*",
                    parse_mode="Markdown",
                )
                self.log_user(user, "transitioned from pending image to WAITING_MASK_TEXT (mask into)")

            elif action == "choice_mask_self":
                pending_path = session.pending_image_path
                self.session_manager.set_pending_payload(user_id, pending_path, "binary")
                self.session_manager.set_pending_image(user_id, None)
                self.session_manager.set_state(user_id, UserState.WAITING_MASK_IMAGE_FOR_FILE)

                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📦 **Картинка будет замаскирована как скрываемый файл!**\n\n"
                    "🖼️ Теперь отправьте **картинку-обложку** (другое фото или файл), в которую мы спрячем текущее изображение.",
                    parse_mode="Markdown",
                )
                self.log_user(user, "selected self-masking mode for pending image")

            elif action == "choice_unmask":
                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="⏳ **Извлечение и расшифровка данных из картинки...**",
                    parse_mode="Markdown",
                )
                self._process_unmask_image_step(call.message, user_id, is_pending=True)

            elif action == "choice_cancel":
                c_path, p_path, pay_path = self.session_manager.reset(user_id)
                self._cleanup_session_files(c_path, p_path, pay_path)
                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="🛑 Операция отменена. Файл удален.",
                )
                self.log_user(user, "canceled pending image choice")

        # Document payload callbacks
        elif action.startswith("filechoice_"):
            if (
                session.state != UserState.WAITING_FILE_ACTION
                or not session.pending_payload_path
            ):
                self.bot.send_message(
                    call.message.chat.id,
                    "⚠️ Время ожидания ответа истекло. Пожалуйста, отправьте файл снова.",
                )
                c_path, p_path, pay_path = self.session_manager.reset(user_id)
                self._cleanup_session_files(c_path, p_path, pay_path)
                return

            if action == "filechoice_text":
                self.session_manager.set_pending_payload(user_id, session.pending_payload_path, "text")
                self.session_manager.set_state(user_id, UserState.WAITING_MASK_IMAGE_FOR_FILE)
                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📝 **Выбран режим извлечения текста.**\n\n"
                    "🖼️ Теперь отправьте **картинку-обложку** (фотографией или файлом), в которую мы спрячем этот текст.",
                    parse_mode="Markdown",
                )
                self.log_user(user, "selected text extraction mode for pending document")

            elif action == "filechoice_binary":
                self.session_manager.set_pending_payload(user_id, session.pending_payload_path, "binary")
                self.session_manager.set_state(user_id, UserState.WAITING_MASK_IMAGE_FOR_FILE)
                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📦 **Выбран режим маскировки файла целиком.**\n\n"
                    "🖼️ Теперь отправьте **картинку-обложку** (фотографией или файлом), в которую мы спрячем этот файл.",
                    parse_mode="Markdown",
                )
                self.log_user(user, "selected binary file masking mode for pending document")

            elif action == "filechoice_cancel":
                c_path, p_path, pay_path = self.session_manager.reset(user_id)
                self._cleanup_session_files(c_path, p_path, pay_path)
                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="🛑 Операция отменена. Временный файл удален.",
                )
                self.log_user(user, "canceled pending document choice")

    def _download_media_to_path(
        self, message: telebot.types.Message, filename_prefix: str
    ) -> Path:
        if message.document:
            file_info = self.bot.get_file(message.document.file_id)
            filename = f"{filename_prefix}_{message.document.file_name}"
        else:
            file_info = self.bot.get_file(message.photo[-1].file_id)
            filename = f"{filename_prefix}_cover.jpg"

        data = self.bot.download_file(file_info.file_path)
        return self._save_file(data, filename)

    def _process_mask_image_step(
        self, message: telebot.types.Message, user_id: int
    ) -> None:
        user = message.from_user
        try:
            temp_path = self._download_media_to_path(message, f"user_{user_id}")
            self.session_manager.set_cover_image(user_id, temp_path)
            self.session_manager.set_state(user_id, UserState.WAITING_MASK_TEXT)

            self.bot.send_message(
                message.chat.id,
                "✅ Изображение принято!\n\n"
                "📝 **Шаг 2 из 2 (Маскировка)**\n"
                "Теперь отправьте текстовым сообщением данные, которые нужно зашифровать и спрятать в этой картинке.\n"
                "*(Отправьте /cancel для отмены)*",
                parse_mode="Markdown",
            )
            self.log_user(
                user, f"cover image saved to {temp_path}. Waiting for secret text..."
            )
        except Exception as e:
            self.log_error(user, f"Error saving mask cover image: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Не удалось загрузить изображение. Попробуйте отправить другое фото или файл.",
            )

    def _process_mask_image_for_file_step(
        self, message: telebot.types.Message, user_id: int
    ) -> None:
        user = message.from_user
        session = self.session_manager.get_session(user_id)
        payload_path = session.pending_payload_path
        mode = session.pending_payload_mode

        if not payload_path or not os.path.exists(payload_path):
            self.bot.send_message(message.chat.id, "⚠️ Ошибка: исходный файл не найден. Начните заново с отправки файла.")
            c_path, p_path, pay_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path, pay_path)
            return

        cover_path = None
        out_stego_path = self.temp_dir / f"stego_out_{user_id}.png"
        visual_overlays: List[str] = []

        try:
            cover_path = self._download_media_to_path(message, f"cover_{user_id}")
            self.bot.send_message(message.chat.id, "⏳ Выполняется обработка, шифрование и маскировка...")

            # Build envelope data
            if mode == "text":
                text = extract_text_from_file(payload_path)
                envelope_bytes = self.facade.create_text_envelope(text)
            else:
                # Mode is "binary"
                filename = payload_path.name.replace(f"pending_doc_{user_id}_", "", 1)
                with open(payload_path, "rb") as f:
                    file_content = f.read()
                envelope_bytes = self.facade.create_file_envelope(filename, file_content)

            self.facade.embed_encrypted(
                str(cover_path),
                str(out_stego_path),
                envelope_bytes,
                self.key,
            )

            # Send stego image
            if os.path.exists(out_stego_path):
                with open(out_stego_path, "rb") as f:
                    self.bot.send_document(
                        message.chat.id,
                        f,
                        caption="✅ **Маскировка файла завершена!**\n"
                        "Сохраните этот файл PNG без сжатия для последующей демаскировки через /unmask.",
                        parse_mode="Markdown",
                    )

            # Generate and send visualization maps
            self.bot.send_message(message.chat.id, "📊 Генерация карт визуализации LSB...")
            visual_overlays = list(self.facade.generate_visualization(str(out_stego_path)))

            for overlay_path in visual_overlays:
                if overlay_path and os.path.exists(overlay_path):
                    with open(overlay_path, "rb") as f:
                        self.bot.send_document(message.chat.id, f)

            self.log_success(user, f"Successfully masked payload file into {out_stego_path}")

        except FileParserError as e:
            self.log_warning(user, f"FileParserError: {e}")
            self.bot.send_message(message.chat.id, f"❌ **Ошибка чтения файла:**\n{e}")
        except CapacityExceededError as e:
            self.log_warning(user, f"CapacityExceededError: payload fits only {round(e.required_ratio * 100, 1)}%")
            self.bot.send_message(
                message.chat.id,
                f"⚠️ **Ошибка емкости изображения**\n\n"
                f"Ваш файл слишком велик для данного изображения! Вмещается лишь **{round(e.required_ratio * 100, 1)}%**.\n\n"
                "💡 **Рекомендация:** Отправьте картинку большего разрешения или сожмите файл в zip-архив.",
                parse_mode="Markdown",
            )
        except Exception as e:
            self.send_friendly_error(message.chat.id, e, user)
        finally:
            c_path, p_path, pay_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path, pay_path)
            self._cleanup_file(cover_path)
            self._cleanup_file(out_stego_path)
            for overlay in visual_overlays:
                self._cleanup_file(Path(overlay))

    def _process_unmask_image_step(
        self, message: telebot.types.Message, user_id: int, is_pending: bool = False
    ) -> None:
        user = message.from_user if message.from_user else None
        session = self.session_manager.get_session(user_id)
        temp_stego_file = None
        extracted_file_to_clean = None

        try:
            if is_pending and session.pending_image_path:
                temp_stego_file = session.pending_image_path
            else:
                self.bot.send_message(
                    message.chat.id, "⏳ Извлечение и расшифровка данных..."
                )
                temp_stego_file = self._download_media_to_path(
                    message, f"unmask_{user_id}"
                )

            self.log_user(
                user or message.chat, f"Extracting payload from {temp_stego_file}..."
            )
            decrypted_bytes = self.facade.extract_decrypted(
                str(temp_stego_file), self.key
            )

            # Parse envelope
            env_type, payload = self.facade.parse_envelope(decrypted_bytes)

            if env_type == "file":
                filename = payload["filename"]
                content = payload["content"]
                extracted_file_to_clean = self.temp_dir / f"extracted_{user_id}_{filename}"
                with open(extracted_file_to_clean, "wb") as f:
                    f.write(content)

                with open(extracted_file_to_clean, "rb") as f:
                    self.bot.send_document(
                        message.chat.id,
                        f,
                        caption=f"🎉 **Файл успешно извлечен!**\nИмя файла: `{filename}`",
                        parse_mode="Markdown"
                    )
                self.log_success(user or message.chat, f"successfully extracted payload file '{filename}'")

            else:
                # Text or legacy text mode
                text = payload["text"]
                # If text length is large, send as text file instead of telegram message limit
                if len(text) > 3500:
                    extracted_file_to_clean = self.temp_dir / f"extracted_text_{user_id}.txt"
                    with open(extracted_file_to_clean, "w", encoding="utf-8") as f:
                        f.write(text)
                    with open(extracted_file_to_clean, "rb") as f:
                        self.bot.send_document(
                            message.chat.id,
                            f,
                            caption="🎉 **Скрытый текст успешно извлечен (в виде файла из-за размера)!**",
                            parse_mode="Markdown"
                        )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        f"🎉 **Скрытый текст успешно извлечен!**\n\n```\n{text}\n```",
                        parse_mode="Markdown",
                    )
                self.log_success(
                    user or message.chat,
                    f"successfully unmasked text payload ({len(decrypted_bytes)} bytes)",
                )

        except CorruptedBlockMapError:
            self.log_warning(
                user or message.chat,
                "unmask failed: CorruptedBlockMapError (magic bytes not found)",
            )
            self.bot.send_message(
                message.chat.id,
                "❌ **Данные не найдены**\n"
                "В этом изображении отсутствует зашифрованный контейнер LSB или файл был поврежден при пересылке.\n"
                "*(Примечание: для сохранения метаданных отправляйте стего-картинки ФАЙЛОМ без сжатия Telegram)*",
                parse_mode="Markdown",
            )
        except (TransformationError, InvalidKeyError) as e:
            self.log_warning(user or message.chat, f"unmask failed decryption: {e}")
            self.bot.send_message(
                message.chat.id,
                "🔐 **Ошибка расшифровки**\n"
                "Не удалось расшифровать данные. Возможно, изображение или ключ были изменены.",
                parse_mode="Markdown",
            )
        except Exception as e:
            self.send_friendly_error(message.chat.id, e, user)
        finally:
            c_path, p_path, pay_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path, pay_path)
            self._cleanup_file(temp_stego_file)
            self._cleanup_file(extracted_file_to_clean)

    def handle_text_message(self, message: telebot.types.Message) -> None:
        user = message.from_user
        user_id = user.id
        session = self.session_manager.get_session(user_id)

        if session.state == UserState.WAITING_MASK_TEXT:
            self.log_user(user, f"submitted secret text ({len(message.text)} chars)")
            self._process_mask_text_step(message, user_id, session)

        elif session.state == UserState.WAITING_MASK_IMAGE:
            self.log_warning(user, "sent text when image was expected for /mask step 1")
            self.bot.send_message(
                message.chat.id,
                "🖼️ Сейчас ожидается **изображение** (Шаг 1 из 2).\n"
                "Пожалуйста, отправьте фото/файл картинки или /cancel для отмены.",
                parse_mode="Markdown",
            )

        elif session.state == UserState.WAITING_MASK_IMAGE_FOR_FILE:
            self.log_warning(user, "sent text when cover image was expected for file masking")
            self.bot.send_message(
                message.chat.id,
                "🖼️ Сейчас ожидается **картинка-обложка**.\n"
                "Пожалуйста, отправьте фото или файл картинки или /cancel для отмены.",
                parse_mode="Markdown",
            )

        elif session.state == UserState.WAITING_UNMASK_IMAGE:
            self.log_warning(
                user, "sent text when stego image was expected for /unmask"
            )
            self.bot.send_message(
                message.chat.id,
                "🔍 Сейчас ожидается **стего-изображение** для извлечения.\n"
                "Пожалуйста, отправьте файл или фото картинки или /cancel для отмены.",
                parse_mode="Markdown",
            )

        elif session.state == UserState.WAITING_IMAGE_ACTION:
            self.bot.send_message(message.chat.id, "⚠️ Пожалуйста, сделайте выбор в меню выше или отправьте /cancel.")

        elif session.state == UserState.WAITING_FILE_ACTION:
            self.bot.send_message(message.chat.id, "⚠️ Пожалуйста, сделайте выбор в меню выше или отправьте /cancel.")

        else:
            self.log_user(user, "sent text in IDLE state without command")
            self.bot.send_message(
                message.chat.id,
                "💡 Чтобы начать работу:\n"
                "• Просто **отправьте фото или файл картинки**, и я спрошу, что с ней сделать.\n"
                "• Просто **отправьте файл документа** (txt, docx, pdf и др.), чтобы спрятать его в картинку.\n"
                "• Или введите команду /mask для маскировки / /unmask для извлечения.",
                parse_mode="Markdown",
            )

    def _process_mask_text_step(
        self, message: telebot.types.Message, user_id: int, session: UserSession
    ) -> None:
        user = message.from_user
        cover_path = session.cover_image_path
        if not cover_path or not os.path.exists(cover_path):
            self.log_error(user, "cover image path not found during mask text step")
            self.bot.send_message(
                message.chat.id,
                "⚠️ Ошибка: исходное изображение не найдено. Начните заново с команды /mask.",
                parse_mode="Markdown",
            )
            c_path, p_path, pay_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path, pay_path)
            return

        text_to_hide = message.text
        out_stego_path = self.temp_dir / f"stego_out_{user_id}.png"
        visual_overlays: List[str] = []

        try:
            self.bot.send_message(
                message.chat.id,
                "⏳ Идет сжатие, шифрование (Кузнечик) и маскировка...",
            )

            # Wrap in text envelope
            envelope_bytes = self.facade.create_text_envelope(text_to_hide)

            self.facade.embed_encrypted(
                str(cover_path),
                str(out_stego_path),
                envelope_bytes,
                self.key,
            )

            # Send main stego container PNG first
            if os.path.exists(out_stego_path):
                with open(out_stego_path, "rb") as f:
                    self.bot.send_document(
                        message.chat.id,
                        f,
                        caption="✅ **Маскировка завершена!**\n"
                        "Сохраните этот файл PNG без сжатия для последующей демаскировки через /unmask.",
                        parse_mode="Markdown",
                    )

            # Generate and send visualization overlays
            self.bot.send_message(
                message.chat.id, "📊 Генерация карт визуализации LSB..."
            )
            visual_overlays = list(
                self.facade.generate_visualization(str(out_stego_path))
            )

            for overlay_path in visual_overlays:
                if overlay_path and os.path.exists(overlay_path):
                    with open(overlay_path, "rb") as f:
                        self.bot.send_document(message.chat.id, f)

            self.log_success(
                user,
                f"successfully masked secret text ({len(text_to_hide)} chars) into {out_stego_path}",
            )

        except CapacityExceededError as e:
            self.log_warning(
                user,
                f"CapacityExceededError: payload fits only {round(e.required_ratio * 100, 1)}%",
            )
            self.bot.send_message(
                message.chat.id,
                f"⚠️ **Ошибка емкости изображения**\n\n"
                f"Ваш текст слишком длинный для данного изображения! Удалось вместить лишь **{round(e.required_ratio * 100, 1)}%**.\n\n"
                "💡 **Рекомендация:** Отправьте картинку большего разрешения/с более сложной текстурой или сократите текст.",
                parse_mode="Markdown",
            )
        except Exception as e:
            self.send_friendly_error(message.chat.id, e, user)
        finally:
            c_path, p_path, pay_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path, pay_path)
            self._cleanup_file(out_stego_path)
            for overlay in visual_overlays:
                self._cleanup_file(Path(overlay))

    def send_friendly_error(
        self,
        chat_id: int,
        error: Exception,
        user: Optional[telebot.types.User] = None,
    ) -> None:
        self.log_error(user or chat_id, f"Unhandled Bot Error: {error}")
        error_msg = (
            f"🛑 **Произошла ошибка при обработке:**\n"
            f"`{error.__class__.__name__}: {error}`\n\n"
            "Состояние сброшено. Попробуйте снова вызвать /mask или /unmask."
        )
        self.bot.send_message(chat_id, error_msg, parse_mode="Markdown")
        if self.admin_chat_id:
            report = f"==== BOT ERROR ====\nChat ID: {chat_id}\nException: {error.__class__.__name__}: {error}"
            try:
                self.bot.send_message(self.admin_chat_id, report)
            except Exception:
                pass

    def run(self) -> None:
        logger.info("Starting Telegram Bot FSM Polling with Action Logging...")
        self.bot.infinity_polling()


def main():
    service = StegoBotService()
    service.run()


if __name__ == "__main__":
    main()
