import os
import random
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_balances = {}
user_levels = {}
user_history = {}

SYMBOLS = ["🍒", "🍋", "🔔", "💎", "7️⃣", "⭐"]
MULTIPLIERS = {
    "🍒": 2,
    "🍋": 4,
    "🔔": 8,
    "💎": 16,
    "7️⃣": 32,
    "⭐": 64,
}

class SlotView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet_amount = 100

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Máy này của người khác! Hãy gõ `!quayhu` để mở máy của sếp.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Cược 100", style=discord.ButtonStyle.secondary)
    async def bet_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bet_amount = 100
        await interaction.response.send_message("✅ Đã chọn mức cược: **100 xu**", ephemeral=True)

    @discord.ui.button(label="Cược 500", style=discord.ButtonStyle.secondary)
    async def bet_500(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bet_amount = 500
        await interaction.response.send_message("✅ Đã chọn mức cược: **500 xu**", ephemeral=True)

    @discord.ui.button(label="Cược 1000", style=discord.ButtonStyle.secondary)
    async def bet_1000(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bet_amount = 1000
        await interaction.response.send_message("✅ Đã chọn mức cược: **1,000 xu**", ephemeral=True)

    @discord.ui.button(label="🔥 ALL-IN", style=discord.ButtonStyle.danger)
    async def bet_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = user_balances.get(self.user_id, 1000)
        self.bet_amount = bal
        await interaction.response.send_message(f"🔥 Cược tất tay: **{bal:,} xu**!", ephemeral=True)

    @discord.ui.button(label="🎰 QUAY NGAY!", style=discord.ButtonStyle.success, row=1)
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.user_id
        balance = user_balances.get(user_id, 1000)
        user_balances[user_id] = balance

        if balance < self.bet_amount:
            await interaction.response.send_message(f"❌ Không đủ xu! Số dư: **{balance:,} xu**. Gõ `!diemdanh` lấy vốn.", ephemeral=True)
            return

        user_balances[user_id] -= self.bet_amount

        for child in self.children:
            child.disabled = True

        # Hiệu ứng màu cam lửa rực rỡ khi máy đang chạy
        spin_embed = discord.Embed(
            title="🎰 ⚡ MÁY QUAY HŨ ĐANG QUAY MƯỢT MÀ... ⚡ 🎰",
            description=f"👑 Chủ nhân: **{interaction.user.name}** | 💰 Cược: **{self.bet_amount:,} xu**\n\n```text\n ⏳ ➔ [ 🔄 | 🔄 | 🔄 ] ➔ ⏳\n 🚀 ➔ [ ✨ | ✨ | ✨ ] ➔ 🚀\n ⏳ ➔ [ 🔄 | 🔄 | 🔄 ] ➔ ⏳\n```",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=spin_embed, view=self)

        # Hiệu ứng guồng quay chuyển động trượt nhiều tầng siêu mượt
        for _ in range(7):
            await asyncio.sleep(0.2)
            r1 = [random.choice(SYMBOLS) for _ in range(3)]
            r2 = [random.choice(SYMBOLS) for _ in range(3)]
            r3 = [random.choice(SYMBOLS) for _ in range(3)]
            anim_grid = f" 🌀 {' | '.join(r1)} 🌀 \n ⚡ {' | '.join(r2)} ⚡ \n 🌀 {' | '.join(r3)} 🌀 "
            spin_embed.description = f"👑 Chủ nhân: **{interaction.user.name}** | 💰 Cược: **{self.bet_amount:,} xu**\n\n```text\n{anim_grid}\n```"
            await interaction.message.edit(embed=spin_embed)

        # Kết quả chính thức
        grid = [[random.choice(SYMBOLS) for _ in range(3)] for _ in range(3)]
        board_str = "\n".join([f" ✨ {' | '.join(row)} ✨ " for row in grid])
        middle_row = grid[1]
        is_jackpot = middle_row[0] == middle_row[1] == middle_row[2]
        is_win = (middle_row[0] == middle_row[1]) or (middle_row[1] == middle_row[2])

        if user_id not in user_levels:
            user_levels[user_id] = {"exp": 0, "level": 1}
        user_levels[user_id]["exp"] += 15
        current_exp = user_levels[user_id]["exp"]
        current_level = user_levels[user_id]["level"]
        
        level_up = False
        if current_exp >= current_level * 100:
            user_levels[user_id]["level"] += 1
            level_up = True

        # Màu sắc kết quả: Vàng rực cho Jackpot, Xanh lá cho Thắng, Đỏ cho Thua
        res_color = 0xFFD700 if is_jackpot else (0x00FF00 if is_win else 0xFF3333)
        result_embed = discord.Embed(
            title="🎰 🌟 KẾT QUẢ QUAY HŨ ĐỈNH CAO 🌟 🎰",
            description=f"👑 Chủ nhân: **{interaction.user.name}** | 💰 Cược: **{self.bet_amount:,} xu**\n\n```text\n{board_str}\n```",
            color=res_color
        )

        if is_jackpot:
            symbol = middle_row[0]
            multiplier = MULTIPLIERS.get(symbol, 50)
            payout = self.bet_amount * multiplier * 5
            user_balances[user_id] += payout
            result_embed.add_field(name="🔥 👑 NỔ HŨ HOÀNG TRÁNG! 👑 🔥", value=f"Trúng 3 biểu tượng {symbol}! Đại gia hốt trọn **+{payout:,} xu**!", inline=False)
        elif is_win:
            symbol = middle_row[1]
            multiplier = MULTIPLIERS.get(symbol, 2)
            payout = self.bet_amount * multiplier
            user_balances[user_id] += payout
            result_embed.add_field(name="✨ 💰 THẮNG LỚN CỰC ĐÃ! 💰 ✨", value=f"Khớp hàng {symbol}! Nhận ngay **+{payout:,} xu**!", inline=False)
        else:
            payout = 0
            result_embed.add_field(name="💀 💸 MẤT TRẮNG RỒI! 💸", value="Tay trắng hoàn tay trắng! Nạp năng lượng phục thù ván sau nhé sếp!", inline=False)

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].insert(0, f"Cược {self.bet_amount:,} xu ➔ Nhận {payout:,} xu ({'Thắng' if payout > 0 else 'Thua'})")
        if len(user_history[user_id]) > 5:
            user_history[user_id].pop()

        footer_text = f"💳 Số dư ví: {user_balances[user_id]:,} xu | 🎖️ Level {user_levels[user_id]['level']} (+15 EXP)"
        if level_up:
            footer_text += f" 🎉 CHÚC MỪNG LÊN LEVEL {user_levels[user_id]['level']}!"
        result_embed.set_footer(text=footer_text)

        for child in self.children:
            child.disabled = False
        await interaction.message.edit(embed=result_embed, view=self)

@bot.event
async def on_ready():
    print(f"Bot Quay Hũ Pro màu mè sống động đã sẵn sàng!")
    await bot.change_presence(activity=discord.Game(name="!quayhu | !lichsu | !top"))

@bot.command(name="diemdanh")
async def diemdanh(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000
        await ctx.send(f"🎉 Chào sếp **{ctx.author.name}**, nhận ngay **1,000 xu** vốn khởi nghiệp!")
    else:
        user_balances[user_id] += 500
        await ctx.send(f"💰 Điểm danh thành công! Nhận thêm **500 xu**. Số dư: **{user_balances[user_id]:,} xu**.")

@bot.command(name="sodu")
async def sodu(ctx):
    user_id = ctx.author.id
    balance = user_balances.get(user_id, 0)
    user_data = user_levels.get(user_id, {"exp": 0, "level": 1})
    await ctx.send(f"💳 Sếp **{ctx.author.name}** | Số dư: **{balance:,} xu** | Level: **{user_data['level']}**")

@bot.command(name="lichsu")
async def lichsu(ctx):
    user_id = ctx.author.id
    history = user_history.get(user_id, [])
    if not history:
        await ctx.send("📜 Sếp chưa chơi ván nào cả!")
        return
    desc = "\n".join([f"• {h}" for h in history])
    embed = discord.Embed(title=f"📜 LỊCH SỬ QUAY CỦA {ctx.author.name.upper()}", description=desc, color=0x00FFFF)
    await ctx.send(embed=embed)

@bot.command(name="top")
async def top(ctx):
    if not user_balances:
        await ctx.send("📊 Bảng xếp hạng trống!")
        return
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="🏆 🌟 BẢNG XẾP HẠNG ĐẠI GIA QUAY HŨ 🌟 🏆", color=0xFFD700)
    desc = ""
    for idx, (uid, bal) in enumerate(sorted_users[:10], 1):
        user = bot.get_user(uid)
        name = user.name if user else f"User ID: {uid}"
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        desc += f"{medal} **{name}** — 💰 **{bal:,} xu**\n"
    embed.description = desc
    await ctx.send(embed=embed)

# ==================== BỘ LỆNH ADMIN PRO ====================
@bot.command(name="congxu")
@commands.has_permissions(administrator=True)
async def congxu(ctx, member: discord.Member, amount: int):
    user_id = member.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount
    await ctx.send(f"🛠️ [Admin Pro] Đã bơm thành công **{amount:,} xu** cho **{member.name}**. Số dư mới: **{user_balances[user_id]:,} xu**.")

@bot.command(name="truxu")
@commands.has_permissions(administrator=True)
async def truxu(ctx, member: discord.Member, amount: int):
    user_id = member.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] = max(0, user_balances[user_id] - amount)
    await ctx.send(f"🛠️ [Admin Pro] Đã thu hồi **{amount:,} xu** của **{member.name}**. Số dư còn lại: **{user_balances[user_id]:,} xu**.")

@bot.command(name="setxu")
@commands.has_permissions(administrator=True)
async def setxu(ctx, member: discord.Member, amount: int):
    user_id = member.id
    user_balances[user_id] = max(0, amount)
    await ctx.send(f"🛠️ [Admin Pro] Đã thiết lập số dư của **{member.name}** thành chính xác **{user_balances[user_id]:,} xu**.")

@congxu.error
@truxu.error
@setxu.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Sếp không có quyền Admin Pro để sử dụng lệnh này!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Sai cú pháp! Ví dụ: `!congxu @tên_user 5000` hoặc `!truxu @tên_user 1000`")

@bot.command(name="quayhu")
async def quayhu(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000

    view = SlotView(user_id)
    embed = discord.Embed(
        title="🎰 💎 MÁY QUAY HŨ ĐỈNH CAO 💎 🎰",
        description=f"👑 Chủ nhân: **{ctx.author.name}**\n\nHãy chọn mức cược ở các nút bên dưới rồi bấm **QUAY NGAY!** để săn hũ vàng!",
        color=0x9900FF
    )
    embed.set_footer(text="Hệ thống casino ảo sẵn sàng phục vụ sếp!")
    await ctx.send(embed=embed, view=view)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Lỗi: Không tìm thấy biến môi trường DISCORD_TOKEN trên Railway!")
