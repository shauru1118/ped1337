import os
import sys
from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import telebot
from telebot import types
from loguru import logger
<<<<<<< HEAD
from stego.funcs import (
    generate_key,
    load_key,
    encrypt_data,
    decrypt_data,
    embed_lsb,
    extract_lsb,
    get_visualized_lsb_blocks,
=======
from stego import (
    StegoFacade,
    StegoError,
    CapacityExceededError,
    CorruptedBlockMapError,
    TransformationError,
    InvalidKeyError,
>>>>>>> 045529e (v0.2.0 done app; OOP code)
)
import config


<<<<<<< HEAD
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<level>{level}\t| {message}</level>",
)
logger.info("Start bot")

TOKEN = config.TELEGRAM_BOT_TOKEN
TEMP_DIR = Path(config.TEMP_DIR_PATH)
KEY_FILE = Path(config.KEY_FILE_PATH)
ADMIN_CHAT_ID = config.ADMIN_CHAT_ID

bot = telebot.TeleBot(TOKEN)
TEMP_DIR.mkdir(exist_ok=True)
if not os.path.exists(KEY_FILE):
    generate_key(KEY_FILE)
    logger.info(f"Generated new key: {KEY_FILE}")
key = load_key(KEY_FILE)
=======
class UserState(Enum):
    IDLE = auto()
    WAITING_MASK_IMAGE = auto()
    WAITING_MASK_TEXT = auto()
    WAITING_UNMASK_IMAGE = auto()
    WAITING_IMAGE_ACTION = auto()
>>>>>>> 045529e (v0.2.0 done app; OOP code)


@dataclass
class UserSession:
    state: UserState = UserState.IDLE
    cover_image_path: Optional[Path] = None
    pending_image_path: Optional[Path] = None


class UserSessionManager:
    """Manages conversational states and temporary image files per Telegram user."""

    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}

    def get_session(self, user_id: int) -> UserSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession()
        return self._sessions[user_id]

    def set_state(self, user_id: int, state: UserState) -> None:
        session = self.get_session(user_id)
        session.state = state

    def set_cover_image(self, user_id: int, image_path: Path) -> None:
        session = self.get_session(user_id)
        session.cover_image_path = image_path

    def set_pending_image(self, user_id: int, image_path: Path) -> None:
        session = self.get_session(user_id)
        session.pending_image_path = image_path

    def reset(self, user_id: int) -> Tuple[Optional[Path], Optional[Path]]:
        cover_path, pending_path = None, None
        if user_id in self._sessions:
            session = self._sessions[user_id]
            cover_path = session.cover_image_path
            pending_path = session.pending_image_path
            self._sessions[user_id] = UserSession()
        return cover_path, pending_path


<<<<<<< HEAD
@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\nЯ умею шифровать и расшифровывать данные в изображениях.\n\n"
        + "Для шифровки отправь мне фото с подписью текста.\nДля расшифровки отправь мне изображение файлом!",
    )


# ----------------- Обработка документов -----------------
@bot.message_handler(content_types=["document"])
def handle_document(message: telebot.types.Message):
    temp_file = None
    outimg_file = None
    try:
        bot.send_message(message.chat.id, "Принят файл")
        logger.info(
            f"@{message.from_user.username}: document '{message.document.file_name}'"
        )
=======
class StegoBotService:
    """Enterprise Telegram Bot Service with FSM dialog, Inline Keyboard smart photo flow, and action logging."""

    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.temp_dir = Path(config.TEMP_DIR_PATH or "./temp")
        self.key_file_path = str(Path(config.KEY_FILE_PATH or "./key.key"))
        self.admin_chat_id = config.ADMIN_CHAT_ID
>>>>>>> 045529e (v0.2.0 done app; OOP code)

        self.temp_dir.mkdir(exist_ok=True)
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
        self, cover_path: Optional[Path], pending_path: Optional[Path]
    ) -> None:
        self._cleanup_file(cover_path)
        self._cleanup_file(pending_path)

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
            func=lambda call: call.data.startswith("choice_")
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
        c_path, p_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path)

        text = (
            f"👋 Привет, {user.first_name}!\n"
            "Я бот для безопасного шифрования и скрытия текста в изображениях.\n\n"
            "📌 **Доступные способы работы:**\n"
            "• Просто **отправьте фото или файл картинки**, и я спрошу, что с ней сделать.\n"
            "• /mask (или /embed) — пошагово замаскировать зашифрованный текст в картинку.\n"
            "• /unmask (или /extract) — извлечь и расшифровать скрытый текст из картинки.\n"
            "• /cancel — отменить текущую операцию.\n\n"
            "Отправьте картинку или выберите команду для начала!"
        )
        self.bot.send_message(message.chat.id, text, parse_mode="Markdown")

    def handle_cancel(self, message: telebot.types.Message) -> None:
        user = message.from_user
        self.log_user(user, "invoked /cancel command")
        c_path, p_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path)

        self.bot.send_message(
            message.chat.id,
            "🛑 Операция отменена. Состояние сброшено.\n"
            "Вы можете отправить фото или использовать /mask или /unmask.",
            parse_mode="Markdown",
        )

    def handle_mask_command(self, message: telebot.types.Message) -> None:
        user = message.from_user
        self.log_user(user, "invoked /mask command")
        c_path, p_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path)

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
        c_path, p_path = self.session_manager.reset(user.id)
        self._cleanup_session_files(c_path, p_path)

        self.session_manager.set_state(user.id, UserState.WAITING_UNMASK_IMAGE)
        self.bot.send_message(
            message.chat.id,
            "🔍 **Демаскировка**\n\n"
            "Отправьте зашифрованное стего-изображение (в формате PNG файлом или фото), из которого нужно извлечь скрытый текст.\n"
            "*(Отправьте /cancel для отмены)*",
            parse_mode="Markdown",
        )

    def handle_media_message(self, message: telebot.types.Message) -> None:
        user = message.from_user
        user_id = user.id
        session = self.session_manager.get_session(user_id)

        if session.state == UserState.WAITING_MASK_IMAGE:
            self.log_user(user, "uploaded cover image for /mask step 1")
            self._process_mask_image_step(message, user_id)

        elif session.state == UserState.WAITING_UNMASK_IMAGE:
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

<<<<<<< HEAD
            outimg_file = TEMP_DIR / (message.document.file_name + "_OUT.png")
            err, p = embed_lsb(
                str(temp_file),
                str(outimg_file),
                encrypt_data(message.caption.encode(), key),
            )
            if err:
                bot.send_message(
                    message.chat.id,
                    f"Сообщение слишком длинное!\nПолучилось вместить лишь {round(p * 100)}% текста.",
                )
                logger.error(f"Embed error: {round(p * 100)}%")
            else:
                images = get_visualized_lsb_blocks(str(outimg_file))
                for img in images:
                    bot.send_document(message.chat.id, open(img, "rb"))
                bot.send_document(message.chat.id, open(outimg_file, "rb"))
                logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровываю данные...")
            logger.info("Decrypting in progress...")
            extracted = extract_lsb(str(temp_file))
            decrypted_text = decrypt_data(extracted, key).decode()
            bot.send_message(message.chat.id, decrypted_text)
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка!")
        error_message_str = f"==== REPORT ====\n\n@{message.from_user.username}\n'{message.text if message.text else ''}'\n\n---- Error ----\n{e.__class__.__name__}: {e.args}"
        bot.send_message(ADMIN_CHAT_ID, error_message_str)
        logger.error(error_message_str)
    finally:
        if temp_file:
            remove_file(temp_file)
        if outimg_file:
            remove_file(outimg_file)
        for img in images:
            if not img:
                continue
            if os.path.exists(img):
                remove_file(img)
=======
        else:
            # Smart Photo Flow: Direct image upload without prior command
            self.log_user(
                user,
                "uploaded image directly without prior command. Presenting Inline Choice...",
            )
            try:
                temp_path = self._download_media_to_path(message, f"pending_{user_id}")
                self.session_manager.set_pending_image(user_id, temp_path)
                self.session_manager.set_state(user_id, UserState.WAITING_IMAGE_ACTION)
>>>>>>> 045529e (v0.2.0 done app; OOP code)

                markup = types.InlineKeyboardMarkup(row_width=1)
                b_mask = types.InlineKeyboardButton(
                    "🔒 Замаскировать (спрятать текст)", callback_data="choice_mask"
                )
                b_unmask = types.InlineKeyboardButton(
                    "🔓 Демаскировать (извлечь текст)", callback_data="choice_unmask"
                )
                b_cancel = types.InlineKeyboardButton(
                    "❌ Отмена", callback_data="choice_cancel"
                )
                markup.add(b_mask, b_unmask, b_cancel)

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

    def handle_choice_callback(self, call: telebot.types.CallbackQuery) -> None:
        user = call.from_user
        user_id = user.id
        session = self.session_manager.get_session(user_id)
        action = call.data

        self.log_user(user, f"clicked inline button: {action}")
        self.bot.answer_callback_query(call.id)

<<<<<<< HEAD
            outimg_file = TEMP_DIR / f"{message.chat.id}_OUT.png"
            err, p = embed_lsb(
                str(temp_file),
                str(outimg_file),
                encrypt_data(message.caption.encode(), key),
            )
            if err:
                bot.send_message(
                    message.chat.id,
                    f"Сообщение слишком длинное!\nПолучилось вместить лишь {round(p * 100)}% текста.",
                )
                logger.error(f"Embed error: {round(p * 100)}%")
            else:
                images = get_visualized_lsb_blocks(str(outimg_file))
                for img in images:
                    bot.send_document(message.chat.id, open(img, "rb"))
                bot.send_document(message.chat.id, open(outimg_file, "rb"))
                logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровываю данные...")
            logger.info("Decrypting in progress...")
            extracted = extract_lsb(str(temp_file))
            decrypted_text = decrypt_data(extracted, key).decode()
            bot.send_message(message.chat.id, decrypted_text)
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка!")
        error_message_str = f"==== REPORT ====\n\n@{message.from_user.username}\n'{message.text if message.text else ''}'\n\n---- Error ----\n{e.__class__.__name__}: {e.args}"
        bot.send_message(ADMIN_CHAT_ID, error_message_str)
        logger.error(error_message_str)
    finally:
        if temp_file:
            remove_file(temp_file)
        if outimg_file:
            remove_file(outimg_file)
        for img in images:
            if not img:
                continue
            if os.path.exists(img):
                remove_file(img)


if __name__ == "__main__":
    logger.info("Bot polling...")
    bot.infinity_polling()
=======
        if (
            session.state != UserState.WAITING_IMAGE_ACTION
            or not session.pending_image_path
        ):
            self.bot.send_message(
                call.message.chat.id,
                "⚠️ Время ожидания ответа истекло. Пожалуйста, отправьте фото снова.",
            )
            c_path, p_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path)
            return

        if action == "choice_mask":
            # Move pending image to cover image
            pending_path = session.pending_image_path
            self.session_manager.set_cover_image(user_id, pending_path)
            self.session_manager.set_pending_image(user_id, None)
            self.session_manager.set_state(user_id, UserState.WAITING_MASK_TEXT)

            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="✅ **Изображение выбрано для маскировки!**\n\n"
                "📝 **Теперь отправьте текстовым сообщением** данные, которые вы хотите зашифровать и спрятать в этой картинке.\n"
                "*(Повторная отправка картинки НЕ требуется)*",
                parse_mode="Markdown",
            )
            self.log_user(user, "transitioned from pending image to WAITING_MASK_TEXT")

        elif action == "choice_unmask":
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="⏳ **Извлечение и расшифровка данных из картинки...**",
                parse_mode="Markdown",
            )
            self._process_unmask_image_step(call.message, user_id, is_pending=True)

        elif action == "choice_cancel":
            c_path, p_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path)
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🛑 Операция отменена. Файл удален.",
            )
            self.log_user(user, "canceled pending image choice")

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

    def _process_unmask_image_step(
        self, message: telebot.types.Message, user_id: int, is_pending: bool = False
    ) -> None:
        user = message.from_user if message.from_user else None
        session = self.session_manager.get_session(user_id)
        temp_stego_file = None

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
            decrypted_text = decrypted_bytes.decode("utf-8")

            self.bot.send_message(
                message.chat.id,
                f"🎉 **Скрытый текст успешно извлечен!**\n\n```\n{decrypted_text}\n```",
                parse_mode="Markdown",
            )
            self.log_success(
                user or message.chat,
                f"successfully unmasked payload ({len(decrypted_bytes)} bytes)",
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
            c_path, p_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path)
            self._cleanup_file(temp_stego_file)

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

        else:
            self.log_user(user, "sent text in IDLE state without command")
            self.bot.send_message(
                message.chat.id,
                "💡 Чтобы начать работу:\n"
                "• Просто **отправьте фото или файл картинки**, и я спрошу, что с ней сделать.\n"
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
            c_path, p_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path)
            return

        text_to_hide = message.text
        out_stego_path = self.temp_dir / f"stego_out_{user_id}.png"
        visual_overlays: List[str] = []

        try:
            self.bot.send_message(
                message.chat.id,
                "⏳ Идет сжатие, шифрование (AES-256-GCM) и маскировка...",
            )

            self.facade.embed_encrypted(
                str(cover_path),
                str(out_stego_path),
                text_to_hide.encode("utf-8"),
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
            c_path, p_path = self.session_manager.reset(user_id)
            self._cleanup_session_files(c_path, p_path)
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
>>>>>>> 045529e (v0.2.0 done app; OOP code)
