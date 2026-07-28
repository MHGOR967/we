
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LabeledPrice, PreCheckoutQuery
from database import Database

TOKEN = "8866684441:AAFrzPZztyUjkgby3FeFySFWnZJauSHEbY0"
ADMIN_ID = 5653088167
db = Database()

# --- MR ROBOT IMAGE URL ---
MR_ROBOT_IMG = "https://i.ibb.co/L5Z5Z5Z/mr-robot.jpg" # صورة تعبيرية تشبه التي في الصورة

class AdminState(StatesGroup):
    waiting_for_welcome = State()

class DonationState(StatesGroup):
    entering_amount = State()

def get_main_kb():
    kb = InlineKeyboardBuilder()
    # Row 1
    kb.row(types.InlineKeyboardButton(text="🔍 حقن وتلغيم تطبيق", web_app=types.WebAppInfo(url=db.config['webapp_url'])))
    # Row 2
    kb.row(
        types.InlineKeyboardButton(text="🎁 دعوة صديق", callback_data="invite_friends"),
        types.InlineKeyboardButton(text="👤 حسابي", callback_data="my_account")
    )
    # Row 3
    kb.row(
        types.InlineKeyboardButton(text="💎 VIP", callback_data="vip_section"),
        types.InlineKeyboardButton(text="🤖 أضف بوتك", callback_data="add_bot")
    )
    # Row 4
    kb.row(types.InlineKeyboardButton(text="🆔 ابحث بدون يوزر", callback_data="search_no_user"))
    # Row 5
    kb.row(types.InlineKeyboardButton(text="❌ منع رقمي", callback_data="block_my_num"))
    return kb.as_markup()

def get_star_kb():
    kb = InlineKeyboardBuilder()
    for i in range(1, 10): kb.button(text=str(i), callback_data=f"star_{i}")
    kb.button(text="0", callback_data="star_0")
    kb.button(text="❌ حذف", callback_data="star_del")
    kb.button(text="✅ تأكيد", callback_data="star_ok")
    kb.adjust(3)
    return kb.as_markup()

async def run_bot():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: types.Message):
        uid = str(message.from_user.id)
        udata = db.get_user(uid)
        
        welcome_text = (
            f"😈 <b>أهلاً ИЛЛЮЗИЯ!</b>\n"
            f"--------------------------------------\n"
            f"🔍 <b>بوت حقن وتلغيم التطبيقات</b>\n"
            f"<b>عبر نظام g5wbot المتطور</b> 🔥\n"
            f"--------------------------------------\n"
            f"⌛ <b>محاولاتك اليوم:</b> {udata['attempts'] if not udata['is_vip'] else '∞'}\n"
            f"⚫ تتجدد كل 24 ساعة تلقائياً\n"
            f"--------------------------------------"
        )
        
        # في حال لم تتوفر الصورة، نرسل نص فقط، لكن سنحاول إرسال صورة الهكر
        try:
            await message.answer_photo(
                photo="https://upload.wikimedia.org/wikipedia/en/d/d0/Mr._Robot_Season_1.jpg", # رابط بديل لصورة إليوت
                caption=welcome_text,
                reply_markup=get_main_kb()
            )
        except:
            await message.answer(welcome_text, reply_markup=get_main_kb())

    # --- CALLBACKS ---
    @dp.callback_query(F.data == "vip_section")
    async def vip(callback: types.CallbackQuery):
        await callback.message.answer("💎 <b>قسم VIP</b>\nاشترك الآن للحصول على ميزات لا محدودة!\nالسعر: 99 نجمة", reply_markup=InlineKeyboardBuilder().button(text="شراء بالنجوم ⭐️", callback_data="buy_vip").as_markup())
        await callback.answer()

    @dp.callback_query(F.data == "invite_friends")
    async def invite(callback: types.CallbackQuery):
        link = f"https://t.me/g5wbot?start=ref_{callback.from_user.id}"
        await callback.message.answer(f"🎁 <b>نظام الدعوات</b>\n\nشارك رابطك واحصل على نقاط:\n<code>{link}</code>")
        await callback.answer()

    @dp.callback_query(F.data == "my_account")
    async def account(callback: types.CallbackQuery):
        udata = db.get_user(callback.from_user.id)
        await callback.message.answer(f"👤 <b>معلومات حسابك</b>\n🆔 ID: <code>{callback.from_user.id}</code>\n💎 VIP: {'نعم' if udata['is_vip'] else 'لا'}\n⭐ النقاط: {udata['points']}")
        await callback.answer()

    # --- STAR PAYMENT (INLINE) ---
    @dp.callback_query(F.data == "buy_vip")
    async def buy_vip_start(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(amt="")
        await callback.message.answer("⭐️ <b>تبرع بالنجوم</b>\nادخل عدد النجوم:", reply_markup=get_star_kb())
        await callback.answer()

    @dp.callback_query(F.data.startswith("star_"))
    async def star_proc(callback: types.CallbackQuery, state: FSMContext):
        action = callback.data.split("_")[1]
        data = await state.get_data()
        amt = data.get('amt', "")
        
        if action.isdigit(): amt += action
        elif action == "del": amt = amt[:-1]
        elif action == "ok":
            if amt:
                await callback.bot.send_invoice(callback.from_user.id, "دعم", "تبرع", f"pay_{amt}", "", "XTR", [LabeledPrice(label="Stars", amount=int(amt))])
                await state.clear(); return
        
        await state.update_data(amt=amt)
        await callback.message.edit_text(f"⭐️ المبلغ المختار: <b>{amt or '0'}</b> نجمة", reply_markup=get_star_kb())
        await callback.answer()

    @dp.pre_checkout_query()
    async def pre(q: PreCheckoutQuery): await q.answer(ok=True)

    @dp.message(F.successful_payment)
    async def success(m: types.Message):
        await m.answer("✅ تم استلام النجوم بنجاح! شكراً لك.")

    # --- ADMIN ---
    @dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
    async def admin(m: types.Message):
        await m.answer("🛠 <b>لوحة التحكم</b>\nاستخدم الأوامر لتعديل البوت.")

    print("🤖 WAHM MR.ROBOT BOT IS RUNNING...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run_bot())
