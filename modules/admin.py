from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from modules.database import get_session
from modules.models import UserPreferences
from modules.constants import (
    ADMIN_ID,
    ADMIN_MENU,
    ADMIN_BROADCAST_SELECT_LANGUAGE,
    ADMIN_BROADCAST_MESSAGE,
    ADMIN_BROADCAST_CONFIRM,
    MAIN_MENU
)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return ADMIN_ID is not None and user_id == ADMIN_ID


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Display admin panel menu.
    Args:
        update (Update): The update object.
        context (ContextTypes.DEFAULT_TYPE): The context object.
    Returns:
        int: ADMIN_MENU state or ConversationHandler.END if not admin.
    """
    user_id = update.message.from_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
        return ConversationHandler.END

    keyboard = [
        ["📢 Рассылка сообщений"],
        ["❌ Закрыть админ-панель"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(
        "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    return ADMIN_MENU


async def admin_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle admin menu choice.
    Args:
        update (Update): The update object.
        context (ContextTypes.DEFAULT_TYPE): The context object.
    Returns:
        int: Next state based on choice.
    """
    user_id = update.message.from_user.id

    if not is_admin(user_id):
        return ConversationHandler.END

    choice = update.message.text

    if choice == "📢 Рассылка сообщений":
        return await select_broadcast_language(update, context)
    elif choice == "❌ Закрыть админ-панель":
        await update.message.reply_text(
            "✅ Админ-панель закрыта.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("❗ Неизвестная команда. Выберите из меню.")
        return ADMIN_MENU


async def select_broadcast_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ask admin to select target language for broadcast.
    Args:
        update (Update): The update object.
        context (ContextTypes.DEFAULT_TYPE): The context object.
    Returns:
        int: ADMIN_BROADCAST_SELECT_LANGUAGE state.
    """
    keyboard = [
        ["🇷🇺 Русский", "🇬🇧 English"],
        ["🇺🇦 Українська", "🇫🇮 Suomi"],
        ["🌐 Все языки"],
        ["⬅️ Назад в меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "📢 <b>Рассылка сообщений</b>\n\nВыберите целевую аудиторию:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    return ADMIN_BROADCAST_SELECT_LANGUAGE


async def save_broadcast_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save selected broadcast language and ask for message.
    Args:
        update (Update): The update object.
        context (ContextTypes.DEFAULT_TYPE): The context object.
    Returns:
        int: ADMIN_BROADCAST_MESSAGE state or ADMIN_MENU if back.
    """
    user_id = update.message.from_user.id

    if not is_admin(user_id):
        return ConversationHandler.END

    choice = update.message.text

    if choice == "⬅️ Назад в меню":
        return await admin_panel(update, context)

    # Map choice to language
    language_map = {
        "🇷🇺 Русский": "🇷🇺 Русский",
        "🇬🇧 English": "🇬🇧 English",
        "🇺🇦 Українська": "🇺🇦 Українська",
        "🇫🇮 Suomi": "🇫🇮 Suomi",
        "🌐 Все языки": "all"
    }

    if choice not in language_map:
        await update.message.reply_text("❗ Неверный выбор. Попробуйте снова.")
        return await select_broadcast_language(update, context)

    context.user_data['broadcast_language'] = language_map[choice]

    # Get count of target users
    session = get_session()
    if language_map[choice] == "all":
        user_count = session.query(UserPreferences).count()
    else:
        user_count = session.query(UserPreferences).filter_by(
            language=language_map[choice]
        ).count()
    session.close()

    keyboard = [["⬅️ Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"📝 <b>Введите сообщение для рассылки</b>\n\n"
        f"Целевая аудитория: <b>{choice}</b>\n"
        f"Количество пользователей: <b>{user_count}</b>\n\n"
        f"Вы можете использовать HTML-разметку.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    return ADMIN_BROADCAST_MESSAGE


async def save_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save broadcast message and ask for confirmation.
    Args:
        update (Update): The update object.
        context (ContextTypes.DEFAULT_TYPE): The context object.
    Returns:
        int: ADMIN_BROADCAST_CONFIRM state or previous state if back.
    """
    user_id = update.message.from_user.id

    if not is_admin(user_id):
        return ConversationHandler.END

    if update.message.text == "⬅️ Назад":
        return await select_broadcast_language(update, context)

    context.user_data['broadcast_message'] = update.message.text

    # Show preview
    keyboard = [
        ["✅ Отправить"],
        ["❌ Отменить"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "📋 <b>Предпросмотр сообщения:</b>\n\n"
        "─────────────────────",
        parse_mode='HTML'
    )

    await update.message.reply_text(
        update.message.text,
        parse_mode='HTML'
    )

    await update.message.reply_text(
        "─────────────────────\n\n"
        f"Язык: <b>{context.user_data['broadcast_language']}</b>\n\n"
        "Подтвердите отправку:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    return ADMIN_BROADCAST_CONFIRM


async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Confirm and send broadcast message.
    Args:
        update (Update): The update object.
        context (ContextTypes.DEFAULT_TYPE): The context object.
    Returns:
        int: ADMIN_MENU state.
    """
    user_id = update.message.from_user.id

    if not is_admin(user_id):
        return ConversationHandler.END

    choice = update.message.text

    if choice == "❌ Отменить":
        await update.message.reply_text("❌ Рассылка отменена.")
        return await admin_panel(update, context)

    if choice != "✅ Отправить":
        await update.message.reply_text("❗ Неверный выбор.")
        return ADMIN_BROADCAST_CONFIRM

    # Get message and language from context
    broadcast_message = context.user_data.get('broadcast_message')
    broadcast_language = context.user_data.get('broadcast_language')

    if not broadcast_message or not broadcast_language:
        await update.message.reply_text("❌ Ошибка: данные рассылки не найдены.")
        return await admin_panel(update, context)

    # Get target users
    session = get_session()
    if broadcast_language == "all":
        users = session.query(UserPreferences).all()
    else:
        users = session.query(UserPreferences).filter_by(language=broadcast_language).all()
    session.close()

    # Send broadcast
    await update.message.reply_text(
        f"📤 Начинаю рассылку...\nВсего пользователей: {len(users)}"
    )

    success_count = 0
    failed_count = 0

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=broadcast_message,
                parse_mode='HTML'
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to send to {user.telegram_id}: {e}")

    # Clean up context
    context.user_data.pop('broadcast_message', None)
    context.user_data.pop('broadcast_language', None)

    await update.message.reply_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {failed_count}",
        parse_mode='HTML'
    )

    return await admin_panel(update, context)


async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel admin panel."""
    await update.message.reply_text(
        "❌ Админ-панель закрыта.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
