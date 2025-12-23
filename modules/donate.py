from pyrogram import filters
from pyrogram.types import LabeledPrice, PreCheckoutQuery, Message

from defs.glover import admin
from init import bot


@bot.on_message(filters.incoming & filters.command(["donate"]))
async def send_donate(_, message: Message):
    amount = 10
    try:
        amount = int(message.command[1])
    except Exception:
        pass
    if amount < 1 or amount > 1000:
        amount = 10
    await bot.send_invoice(
        message.chat.id,
        title="Donate",
        description="Support me",
        currency="XTR",
        prices=[LabeledPrice(label="Star", amount=amount)],
        payload="stars",
    )


@bot.on_message(
    filters.successful_payment,
)
async def successful_payment(_, message: Message):
    uuid = message.successful_payment.telegram_payment_charge_id
    await message.reply_text(
        f"Thank you for your donation! If you have any questions, please contact @omg_xtao . UUID: `{uuid}`"
    )


@bot.on_message(
    filters.incoming
    & filters.private
    & filters.user(admin)
    & filters.command(["donate_refund"])
)
async def refund_donate(_, message: Message):
    uid = message.command[1] if len(message.command) > 1 else None
    uuid = message.command[2] if len(message.command) > 2 else None
    if not (uuid and uid):
        return await message.reply_text("Please provide a UID and UUID")
    try:
        await bot.refund_star_payment(
            user_id=int(uid),
            telegram_payment_charge_id=uuid,
        )
        await message.reply_text("Refund successful")
    except Exception as e:
        await message.reply_text(f"Refund failed: {e}")


@bot.on_pre_checkout_query()
async def pre_checkout_query_handler(_, query: PreCheckoutQuery):
    await query.answer(ok=True)
