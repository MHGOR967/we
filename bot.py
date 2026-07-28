
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from database import Database

# ===== SETUP =====
TOKEN = "8866684441:AAFrzPZztyUjkgby3FeFySFWnZJauSHEbY0"
ADMIN_ID = 5653088167
db = Database()

class AdminState(StatesGroup):
    waiting_for_welcome = State()

class DonationState(StatesGroup):
    entering_amount = State()

# ===== KEYBOARDS =====
def get_main_kb(user, udata):
    kb = InlineKeyboardBuilder()
    for btn in db.config['buttons']:
        if btn['type'] == 'web_app':
            kb.row(types.InlineKeyboardButton(text=btn['text'], web_app=types.WebAppInfo(url=db.config['webapp_url'])))
        else:
            kb.row(types.InlineKeyboardButton(text=btn['text'], callback_data=btn['callback_data']))
    return kb.as_markup()

def get_star_keyboard(current_amount=""):
    kb = InlineKeyboardBuilder()
    for i in range(1, 10):
        kb.button(text=str(i), callback_data=f"star_num_{i}")
    kb.button(text="0", callback_data="star_num_0")
    kb.button(text="❌ حذف", callback_data="star_clear")
    kb.button(text="✅ تأكيد", callback_data="star_confirm")
    kb.adjust(3)
    return kb.as_markup()

# ===== HANDLERS =====
async def run_bot():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    def parse_text(template, user, udata):
        t = template
        t = t.replace("#name_user", f"<b>{user.first_name}</b>")
        t = t.replace("#id", f"<code>{user.id}</code>")
        t = t.replace("#points", str(udata['points']))
        t = t.replace("#invitelink", f"https://t.me/g5wbot?start=ref_{user.id}")
        return t

    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        uid = str(message.from_user.id)
        args = message.text.split()
        
        # Referral
        if len(args) > 1 and args[1].startswith("ref_"):
            ref_id = args[1].replace("ref_", "")
            if uid not in db.users and ref_id in db.users and ref_id != uid:
                db.users[ref_id]['points'] += db.config['invite_reward_points']
                db.users[ref_id]['invites'] += 1
                db.users[ref_id].setdefault('invited_users', []).append(uid)
                db.save_users()
                try: await bot.send_message(int(ref_id), "🎁 انضم شخص جديد عبر رابطك! حصلت على نقاط مكافأة.")
                except: pass

        udata = db.get_user(uid)
        text = parse_text(db.config['welcome_message'], message.from_user, udata)
        await message.answer(text, reply_markup=get_main_kb(message.from_user, udata))

    # --- DONATION SYSTEM (INLINE KEYBOARD) ---
    @dp.callback_query(F.data == "donate_stars")
    async def start_donation(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(amt="")
        await callback.message.edit_text("💰 <b>نظام التبرع بالنجوم</b>\n\nادخل عدد النجوم باستخدام الكيبورد أدناه:", reply_markup=get_star_keyboard())
        await callback.answer()

    @dp.callback_query(F.data.startswith("star_num_"))
    async def star_input(callback: types.CallbackQuery, state: FSMContext):
        num = callback.data.split("_")[-1]
        data = await state.get_data()
        amt = data.get('amt', "") + num
        await state.update_data(amt=amt)
        await callback.message.edit_text(f"💰 المبلغ المختار: <b>{amt}</b> نجمة\n\nاضغط تأكيد لتوليد الفاتورة:", reply_markup=get_star_keyboard(amt))
        await callback.answer()

    @dp.callback_query(F.data == "star_clear")
    async def star_clear(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(amt="")
        await callback.message.edit_text("💰 ادخل عدد النجوم:", reply_markup=get_star_keyboard())
        await callback.answer()

    @dp.callback_query(F.data == "star_confirm")
    async def star_confirm(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        amt = data.get('amt', "")
        if not amt or int(amt) <= 0:
            await callback.answer("❌ ادخل مبلغ صحيح!", show_alert=True)
            return
        
        prices = [LabeledPrice(label=f"تبرع {amt} نجمة", amount=int(amt))]
        await callback.bot.send_invoice(
            callback.from_user.id, "تبرع لدعم البوت", f"شكراً لدعمك بـ {amt} نجمة!",
            f"don_{amt}", "", "XTR", prices
        )
        await state.clear()
        await callback.answer()

    # --- VIP SYSTEM ---
    @dp.callback_query(F.data == "vip_section")
    async def vip_sec(callback: types.CallbackQuery):
        udata = db.get_user(callback.from_user.id)
        status = "✅ VIP" if udata['is_vip'] else "❌ عادي"
        text = f"👑 <b>قسم VIP</b>\n━━━━━━━━━━━━━━\nحالتك: {status}\nالسعر: {db.config['vip_price']} نجمة\n\n{db.config['vip_description']}"
        kb = InlineKeyboardBuilder()
        kb.button(text="💎 شراء الآن", callback_data="buy_vip_stars")
        kb.button(text="📞 المطور", url=f"https://t.me/{DEVELOPER_USERNAME}")
        kb.adjust(1)
        await callback.message.edit_text(text, reply_markup=kb.as_markup())

    @dp.callback_query(F.data == "buy_vip_stars")
    async def buy_vip(callback: types.CallbackQuery):
        prices = [LabeledPrice(label="عضوية VIP", amount=db.config['vip_price'])]
        await callback.bot.send_invoice(
            callback.from_user.id, "عضوية VIP", "تفعيل الميزات اللامحدودة",
            "vip_buy", "", "XTR", prices
        )
        await callback.answer()

    # --- PAYMENT HANDLING ---
    @dp.pre_checkout_query()
    async def checkout(query: PreCheckoutQuery):
        await query.answer(ok=True)

    @dp.message(F.successful_payment)
    async def payment_done(message: types.Message):
        payload = message.successful_payment.invoice_payload
        uid = str(message.from_user.id)
        if payload.startswith("don_"):
            amt = int(payload.split("_")[1])
            db.users[uid]['total_donations'] += amt
            db.save_users()
            await message.answer(f"🌟 شكراً جزيلاً! تم استلام {amt} نجمة بنجاح.")
        elif payload == "vip_buy":
            db.users[uid]['is_vip'] = True
            db.save_users()
            await message.answer("👑 تهانينا! أصبحت الآن عضواً VIP في نظام وَهْم.")

    # --- ADMIN PANEL ---
    @dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
    async def admin_panel(message: types.Message):
        kb = InlineKeyboardBuilder()
        kb.button(text="📝 تعديل الترحيب", callback_data="adm_welcome")
        kb.button(text="📊 الإحصائيات", callback_data="adm_stats")
        kb.adjust(1)
        await message.answer("🛠 <b>لوحة تحكم المدير</b>", reply_markup=kb.as_markup())

    @dp.callback_query(F.data == "adm_welcome")
    async def adm_w(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer("ارسل رسالة الترحيب الجديدة (يدعم HTML والإيموجي المميز):")
        await state.set_state(AdminState.waiting_for_welcome)
        await callback.answer()

    @dp.message(AdminState.waiting_for_welcome)
    async def set_welcome(message: types.Message, state: FSMContext):
        db.config['welcome_message'] = message.html_text
        db.save_config()
        await message.answer("✅ تم تحديث رسالة الترحيب بنجاح!")
        await state.clear()

    print("🤖 WAHM Bot is Running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run_bot())
