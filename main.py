from keep_alive import keep_alive
keep_alive()

import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)

# ----- Konfigurasi Bot -----
TOKEN = "7237229468:AAH0QEea9LQkP5XTLNimnI6cPE1AhWrxBmQ"  # Ganti dengan token Bot Telegram kamu.
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwNXyltn57HV601RA18pLFIfJKuXIIMPHysecc8J4xSvnb7JlASLrvhAmP5F6MrjhJm/exec"  # Ganti dengan URL Web App GAS kamu.

# ----- Status Percakapan (Flow baru) -----
(
    MINTA_EMAIL,
    MINTA_BRIEF,
    PILIH_URGENSI,
    PILIH_REQUEST_TYPE,
    PILIH_CONTENT,  # Hanya muncul jika request type ≠ Business Intelligence
    MINTA_MO_NUMBERS,  # Hanya muncul jika content type adalah ADV/CPD atau Specific MO
    MINTA_TGL_MULAI,
    MINTA_TGL_SELESAI,
    MINTA_BRAND,
    MINTA_AGENCY,
    MINTA_ATTACHMENTS,
    MINTA_CC_EMAIL,  # New state: meminta ccEmail
    PILIH_LEGAL_CHECK,
    KONFIRMASI) = range(14)

# ----- Setup Logging -----
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Handler Percakapan -----


def mulai(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Halo! Selamat datang di BD Request Bot lewat Telegram!\n\nSilakan masukkan email kamu:"
    )
    return MINTA_EMAIL


def minta_email(update: Update, context: CallbackContext) -> int:
    context.user_data['requesterEmail'] = update.message.text.strip()
    update.message.reply_text("Kamu mau minta tolong apa? (Brief)")
    return MINTA_BRIEF


def minta_brief(update: Update, context: CallbackContext) -> int:
    context.user_data['brief'] = update.message.text.strip()
    # Pilihan Priority
    keyboard = [[
        InlineKeyboardButton("Urgent", callback_data="urgensi_Urgent"),
        InlineKeyboardButton("Regular", callback_data="urgensi_Regular")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Pilih tingkat Urgensi:",
                              reply_markup=reply_markup)
    return PILIH_URGENSI


def tombol_urgensi(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    _, urgency = query.data.split("_", 1)
    context.user_data['urgency'] = urgency
    query.edit_message_text(text=f"Priority diset ke {urgency}.")
    # Pilihan Request Type
    keyboard = [
        [
            InlineKeyboardButton("Update Data",
                                 callback_data="reqtype_Update Data")
        ],
        [
            InlineKeyboardButton("Campaign Analysis",
                                 callback_data="reqtype_Campaign Analysis")
        ],
        [
            InlineKeyboardButton("Business Intelligence",
                                 callback_data="reqtype_Business Intelligence")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("Pilih Request Type:", reply_markup=reply_markup)
    return PILIH_REQUEST_TYPE


def tombol_request_type(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    _, reqtype = query.data.split("_", 1)
    context.user_data['requestType'] = reqtype
    query.edit_message_text(text=f"Request Type diset ke {reqtype}.")
    # Jika request type Business Intelligence, langsung lanjut ke tanggal
    if reqtype == "Business Intelligence":
        query.message.reply_text(
            "Masukkan tanggal mulai (format: YYYY-MM-DD):")
        return MINTA_TGL_MULAI
    else:
        # Jika Update Data atau Campaign Analysis, tampilkan pilihan Content Type
        keyboard = [
            [InlineKeyboardButton("Article", callback_data="content_Article")],
            [InlineKeyboardButton("Video", callback_data="content_Video")],
            [InlineKeyboardButton("ADV/CPD", callback_data="content_ADV/CPD")],
            [
                InlineKeyboardButton("Microsite",
                                     callback_data="content_Microsite")
            ],
            [
                InlineKeyboardButton("Specific MO",
                                     callback_data="content_Specific MO")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("Pilih Content Type:",
                                 reply_markup=reply_markup)
        return PILIH_CONTENT


def tombol_content(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    _, content = query.data.split("_", 1)
    context.user_data['content'] = content
    query.edit_message_text(text=f"Content Type diset ke {content}.")
    # Jika content type adalah ADV/CPD atau Specific MO, minta input MO Numbers
    if content in ["ADV/CPD", "Specific MO"]:
        query.message.reply_text("Masukkan MO Numbers:")
        return MINTA_MO_NUMBERS
    else:
        query.message.reply_text(
            "Masukkan tanggal mulai (format: YYYY-MM-DD):")
        return MINTA_TGL_MULAI


def minta_mo_numbers(update: Update, context: CallbackContext) -> int:
    context.user_data['moNumbers'] = update.message.text.strip()
    update.message.reply_text(
        "MO Numbers tercatat.\n\nMasukkan tanggal mulai (format: YYYY-MM-DD):")
    return MINTA_TGL_MULAI


def minta_tgl_mulai(update: Update, context: CallbackContext) -> int:
    context.user_data['startDate'] = update.message.text.strip()
    update.message.reply_text("Masukkan tanggal selesai (format: YYYY-MM-DD):")
    return MINTA_TGL_SELESAI


def minta_tgl_selesai(update: Update, context: CallbackContext) -> int:
    context.user_data['endDate'] = update.message.text.strip()
    update.message.reply_text("Masukkan nama Brand:")
    return MINTA_BRAND


def minta_brand(update: Update, context: CallbackContext) -> int:
    context.user_data['brand'] = update.message.text.strip()
    update.message.reply_text("Masukkan nama Agency (boleh dikosongkan):")
    return MINTA_AGENCY


def minta_agency(update: Update, context: CallbackContext) -> int:
    context.user_data['agency'] = update.message.text.strip()
    update.message.reply_text(
        "Masukkan link Attachment (pisahkan dengan koma jika lebih dari satu, atau kosongkan):"
    )
    return MINTA_ATTACHMENTS


def minta_attachments(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    attachments = [att.strip() for att in text.split(",")] if text else []
    context.user_data['attachments'] = attachments
    update.message.reply_text(
        "Attachment tercatat.\n\nMasukkan CC Email (pisahkan dengan koma jika lebih dari satu, atau kosongkan):"
    )
    return MINTA_CC_EMAIL


def minta_cc_email(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    ccEmails = [email.strip() for email in text.split(",")] if text else []
    context.user_data['ccEmail'] = ccEmails
    # Setelah cc email, lanjut ke Legal Check
    keyboard = [[
        InlineKeyboardButton("Iya, setuju", callback_data="legal_setuju"),
        InlineKeyboardButton("Enggak, tidak setuju",
                             callback_data="legal_tidak")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Apakah kamu bersedia bertanggung jawab untuk penggunaan data ini dengan benar?",
        reply_markup=reply_markup)
    return PILIH_LEGAL_CHECK


def tombol_legal_check(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    if query.data == "legal_setuju":
        context.user_data['legalCheck'] = True
    else:
        context.user_data['legalCheck'] = False
    query.edit_message_text(text="Legal Check tercatat.")
    # Tampilkan rekap data untuk konfirmasi
    data = context.user_data
    summary = (
        f"Berikut data yang kamu masukkan:\n"
        f"Email: {data.get('requesterEmail')}\n"
        f"Brief: {data.get('brief')}\n"
        f"Priority: {data.get('urgency')}\n"
        f"Request Type: {data.get('requestType')}\n"
        f"Content Type: {data.get('content', 'N/A')}\n"
        f"MO Numbers: {data.get('moNumbers', 'N/A')}\n"
        f"Tanggal: {data.get('startDate')} s/d {data.get('endDate')}\n"
        f"Brand: {data.get('brand')}\n"
        f"Agency: {data.get('agency')}\n"
        f"Attachments: {', '.join(data.get('attachments', []))}\n"
        f"CC Email: {', '.join(data.get('ccEmail', []))}\n"
        f"Legal Check: {'Ya' if data.get('legalCheck') else 'Tidak'}\n\n"
        "Konfirmasi data kamu:")
    keyboard = [[
        InlineKeyboardButton("Ya, bener", callback_data="konfirm_yes"),
        InlineKeyboardButton("Enggak, salah", callback_data="konfirm_no")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(summary, reply_markup=reply_markup)
    return KONFIRMASI


def tombol_konfirmasi(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    if query.data == "konfirm_yes":
        # Join ccEmail list into a string if it exists
        cc_email_list = context.user_data.get('ccEmail', [])
        cc_email_str = ", ".join(cc_email_list) if isinstance(
            cc_email_list, list) else cc_email_list

        formData = {
            "requesterEmail": context.user_data.get('requesterEmail'),
            "brief": context.user_data.get('brief'),
            "priority": context.user_data.get('urgency'),
            "requestType": context.user_data.get('requestType'),
            "content": context.user_data.get('content', ''),
            "moNumbers": context.user_data.get('moNumbers', ''),
            "startDate": context.user_data.get('startDate'),
            "endDate": context.user_data.get('endDate'),
            "brand": context.user_data.get('brand'),
            "agency": context.user_data.get('agency'),
            "attachments": context.user_data.get('attachments'),
            "ccEmail": cc_email_str,
            "legalCheck": context.user_data.get('legalCheck'),
        }
        try:
            response = requests.post(GAS_WEBAPP_URL, json=formData)
            result = response.json()
            if result.get("success"):
                query.edit_message_text(text=(
                    "Sip, request kamu berhasil dikirim!\n\n"
                    "Pantau status request melalui "
                    "<a href=\"https://docs.google.com/spreadsheets/d/1sQM7X6XSzr7k1-RFk2atK2yGA1YzR4NOuH9IqO61ylE/edit?gid=0\">link ini</a>.\n\n"
                    "Jika ingin request lagi, ketik /start"),
                                        parse_mode="HTML")
            else:
                query.edit_message_text(
                    text="Error saat ngirim request: " +
                    result.get("message", "Error nggak diketahui"))
        except Exception as e:
            query.edit_message_text(text="Error saat ngirim request: " +
                                    str(e))
    else:
        query.edit_message_text(
            text="Request dibatalkan. Jika mau ulang, ketik /start.")

    context.user_data.clear()
    return ConversationHandler.END


def batal(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Oke, percakapan udah dibatalkan.")
    context.user_data.clear()
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", mulai)],
        states={
            MINTA_EMAIL:
            [MessageHandler(Filters.text & ~Filters.command, minta_email)],
            MINTA_BRIEF:
            [MessageHandler(Filters.text & ~Filters.command, minta_brief)],
            PILIH_URGENSI:
            [CallbackQueryHandler(tombol_urgensi, pattern="^urgensi_")],
            PILIH_REQUEST_TYPE:
            [CallbackQueryHandler(tombol_request_type, pattern="^reqtype_")],
            PILIH_CONTENT:
            [CallbackQueryHandler(tombol_content, pattern="^content_")],
            MINTA_MO_NUMBERS: [
                MessageHandler(Filters.text & ~Filters.command,
                               minta_mo_numbers)
            ],
            MINTA_TGL_MULAI:
            [MessageHandler(Filters.text & ~Filters.command, minta_tgl_mulai)],
            MINTA_TGL_SELESAI: [
                MessageHandler(Filters.text & ~Filters.command,
                               minta_tgl_selesai)
            ],
            MINTA_BRAND:
            [MessageHandler(Filters.text & ~Filters.command, minta_brand)],
            MINTA_AGENCY:
            [MessageHandler(Filters.text & ~Filters.command, minta_agency)],
            MINTA_ATTACHMENTS: [
                MessageHandler(Filters.text & ~Filters.command,
                               minta_attachments)
            ],
            MINTA_CC_EMAIL:
            [MessageHandler(Filters.text & ~Filters.command, minta_cc_email)],
            PILIH_LEGAL_CHECK:
            [CallbackQueryHandler(tombol_legal_check, pattern="^legal_")],
            KONFIRMASI:
            [CallbackQueryHandler(tombol_konfirmasi, pattern="^konfirm_")],
        },
        fallbacks=[CommandHandler("cancel", batal)],
    )
    dp.add_handler(conv_handler)

    updater.start_polling()
    logger.info("Bot udah jalan. Tekan Ctrl+C buat berhenti.")
    updater.idle()


if __name__ == '__main__':
    main()
