
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

TOKEN = "8866684441:AAFrzPZztyUjkgby3FeFySFWnZJauSHEbY0"
ADMIN_ID = 5653088167
db = Database()

# --- ADMIN STATES ---
class AdminState(StatesGroup):
    waiting_for_welcome_text = State()
    waiting_for_welcome_photo = State()
    waiting_for_button_text = State()

class PaymentState(StatesGroup):
    entering_donation_amount = State()

# --- HELPER FUNCTIONS ---
def get_main_kb():
    kb = InlineKeyboardBuilder()
    # Row 1: Web App Injection
    kb.row(types.InlineKeyboardButton(text="🔍 حقن وتلغيم تطبيق", web_app=types.WebAppInfo(url=db.config['webapp_url'])))
    # Row 2: Invites & Account
    kb.row(
        types.InlineKeyboardButton(text="🎁 دعوة صديق", callback_data="invite"),
        types.InlineKeyboardButton(text="👤 حسابي", callback_data="my_acc")
    )
    # Row 3: VIP & Donate
    kb.row(
        types.InlineKeyboardButton(text="💎 VIP", callback_data="vip_menu"),
        types.InlineKeyboardButton(text="⭐️ تبرع بالنجوم", callback_data="donate_menu")
    )
    # Row 4: Extra Tools
    kb.row(types.InlineKeyboardButton(text="🆔 ابحث بدون يوزر", callback_data="extra_search"))
    # Row 5: Security
    kb.row(types.InlineKeyboardButton(text="❌ منع رقمي", callback_data="block_num"))
    return kb.as_markup()

async def run_bot():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # --- START COMMAND ---
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        uid = str(message.from_user.id)
        udata = db.get_user(uid)
        
        # Handle Referral
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            ref_id = args[1].replace("ref_", "")
            if uid not in db.users and ref_id in db.users and ref_id != uid:
                db.users[ref_id]['points'] += db.config.get('invite_reward_points', 5)
                db.users[ref_id]['invites'] += 1
                db.users[ref_id].setdefault('invited_users', []).append(uid)
                db.save_users()
                try: await bot.send_message(int(ref_id), "🎉 انضم شخص جديد عبر رابطك! حصلت على نقاط مكافأة.")
                except: pass

        welcome_text = db.config.get('welcome_message', "أهلاً بك في بوت وَهْم")
        # Replace placeholders
        welcome_text = welcome_text.replace("#name", message.from_user.first_name)
        welcome_text = welcome_text.replace("#id", str(message.from_user.id))
        welcome_text = welcome_text.replace("#attempts", str(udata['attempts'] if not udata['is_vip'] else '∞'))
        
        photo_url = db.config.get('welcome_photo', "https://upload.wikimedia.org/wikipedia/en/d/d0/Mr._Robot_Season_1.jpg")
        
        try:
            await message.answer_photo(photo=photo_url, caption=welcome_text, reply_markup=get_main_kb())
        except:
            await message.answer(welcome_text, reply_markup=get_main_kb())

    # --- REAL TELEGRAM STARS PAYMENT ---
    @dp.callback_query(F.data == "vip_menu")
    async def vip_menu(callback: types.CallbackQuery):
        udata = db.get_user(callback.from_user.id)
        status = "✅ VIP" if udata['is_vip'] else "❌ عادي"
        price = db.config.get('vip_price', 99)
        text = f"👑 <b>قسم العضوية المميزة (VIP)</b>\n━━━━━━━━━━━━━━\nحالتك الحالية: {status}\nسعر التفعيل: {price} نجمة\n\n<b>الميزات:</b>\n- حقن وتلغيم لا محدود\n- أولوية في المعالجة\n- دعم فني خاص"
        
        kb = InlineKeyboardBuilder()
        kb.button(text=f"💳 شراء الآن ({price} ⭐️)", callback_data="buy_vip_real")
        kb.button(text="📞 المطور", url=f"https://t.me/{db.config.get('dev_user', 'hackwahm')}")
        kb.adjust(1)
        await callback.message.edit_caption(caption=text, reply_markup=kb.as_markup())

    @dp.callback_query(F.data == "buy_vip_real")
    async def buy_vip_real(callback: types.CallbackQuery):
        price = db.config.get('vip_price', 99)
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title="تفعيل عضوية VIP",
            description="تفعيل ميزات الحقن والتلغيم اللامحدودة مدى الحياة",
            payload="vip_upgrade",
            provider_token="", # Empty for Telegram Stars
            currency="XTR",
            prices=[LabeledPrice(label="VIP Membership", amount=price)]
        )
        await callback.answer()

    @dp.callback_query(F.data == "donate_menu")
    async def donate_menu(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(amt="")
        kb = InlineKeyboardBuilder()
        for i in range(1, 10): kb.button(text=str(i), callback_data=f"dnum_{i}")
        kb.button(text="0", callback_data="dnum_0")
        kb.button(text="❌ حذف", callback_data="dnum_del")
        kb.button(text="✅ تأكيد", callback_data="dnum_ok")
        kb.adjust(3)
        await callback.message.answer("⭐️ <b>تبرع لدعم المشروع</b>\nادخل عدد النجوم:", reply_markup=kb.as_markup())
        await callback.answer()

    @dp.callback_query(F.data.startswith("dnum_"))
    async def dnum_proc(callback: types.CallbackQuery, state: FSMContext):
        action = callback.data.split("_")[1]
        data = await state.get_data()
        amt = data.get('amt', "")
        
        if action.isdigit(): amt += action
        elif action == "del": amt = amt[:-1]
        elif action == "ok":
            if amt and int(amt) > 0:
                await callback.bot.send_invoice(
                    callback.from_user.id, "تبرع لدعم البوت", "شكراً لك على دعمك المستمر!",
                    f"donate_{amt}", "", "XTR", [LabeledPrice(label="Stars", amount=int(amt))]
                )
                await state.clear(); return
            else:
                await callback.answer("❌ ادخل مبلغ صحيح", show_alert=True); return
        
        await state.update_data(amt=amt)
        await callback.message.edit_text(f"⭐️ المبلغ المختار: <b>{amt or '0'}</b> نجمة", reply_markup=callback.message.reply_markup)
        await callback.answer()

    # --- PAYMENT HANDLING ---
    @dp.pre_checkout_query()
    async def pre_checkout(query: PreCheckoutQuery):
        await query.answer(ok=True)

    @dp.message(F.successful_payment)
    async def on_success_payment(message: types.Message):
        payload = message.successful_payment.invoice_payload
        uid = str(message.from_user.id)
        if payload == "vip_upgrade":
            db.users[uid]['is_vip'] = True
            db.save_users()
            await message.answer("👑 <b>مبروك!</b> تم تفعيل عضوية VIP بنجاح.")
        elif payload.startswith("donate_"):
            amt = payload.split("_")[1]
            await message.answer(f"🌟 <b>شكراً جزيلاً!</b> تم استلام تبرعك بـ {amt} نجمة بنجاح.")

    # --- ADVANCED ADMIN PANEL ---
    @dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
    async def admin_panel(message: types.Message):
        kb = InlineKeyboardBuilder()
        kb.button(text="📝 تعديل نص الترحيب", callback_data="adm_text")
        kb.button(text="🖼 تعديل صورة الترحيب", callback_data="adm_photo")
        kb.button(text="📊 إحصائيات النظام", callback_data="adm_stats")
        kb.adjust(1)
        await message.answer("🛠 <b>لوحة تحكم المدير المتقدمة</b>\nاختر الإجراء المطلوب:", reply_markup=kb.as_markup())

    @dp.callback_query(F.data == "adm_text", F.from_user.id == ADMIN_ID)
    async def adm_text_start(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer("ارسل نص الترحيب الجديد (HTML):\nالهاشتاقات المتاحة: #name, #id, #attempts")
        await state.set_state(AdminState.waiting_for_welcome_text)
        await callback.answer()

    @dp.message(AdminState.waiting_for_welcome_text, F.from_user.id == ADMIN_ID)
    async def adm_text_save(message: types.Message, state: FSMContext):
        db.config['welcome_message'] = message.html_text
        db.save_config()
        await message.answer("✅ تم تحديث النص بنجاح!")
        await state.clear()

    @dp.callback_query(F.data == "adm_photo", F.from_user.id == ADMIN_ID)
    async def adm_photo_start(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer("ارسل رابط الصورة الجديد (Direct Link):")
        await state.set_state(AdminState.waiting_for_welcome_photo)
        await callback.answer()

    @dp.message(AdminState.waiting_for_welcome_photo, F.from_user.id == ADMIN_ID)
    async def adm_photo_save(message: types.Message, state: FSMContext):
        db.config['welcome_photo'] = message.text
        db.save_config()
        await message.answer("✅ تم تحديث الصورة بنجاح!")
        await state.clear()

    # --- OTHER CALLBACKS ---
    @dp.callback_query(F.data == "my_acc")
    async def my_acc(callback: types.CallbackQuery):
        udata = db.get_user(callback.from_user.id)
        text = f"👤 <b>معلومات حسابك</b>\n🆔 ID: <code>{callback.from_user.id}</code>\n💎 الحالة: {'VIP' if udata['is_vip'] else 'عادي'}\n⭐ النقاط: {udata['points']}"
        await callback.message.answer(text)
        await callback.answer()

    @dp.callback_query(F.data == "invite")
    async def invite_link(callback: types.CallbackQuery):
        link = f"https://t.me/g5wbot?start=ref_{callback.from_user.id}"
        await callback.message.answer(f"🎁 <b>نظام الدعوات</b>\nانسخ رابطك وشاركه:\n<code>{link}</code>")
        await callback.answer()

    print("🤖 WAHM Pro Bot with REAL PAYMENTS is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run_bot())
