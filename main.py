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
user_history = {}  # Lưu lịch sử quay gần nhất của từng user

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
            await interaction.response.send_message("❌ Máy này của sếp khác! Hãy tự gõ `!quayhu` để mở máy riêng.", ephemeral=True)
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
        await interaction.response.send_message(f"🔥 Đã chơi tất tay: **{bal:,} xu**!", ephemeral=True)

    @discord.ui.button(label="🎰 QUAY NGAY!", style=discord.ButtonStyle.success, row=1)
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.user_id
        balance = user_balances.get(user_id, 1000)
        user_balances[user_id] = balance

        if balance < self.bet_amount:
            await interaction.response.send_message(f"❌ Không đủ tiền! Số dư: **{balance:,} xu**. Gõ `!diemdanh` lấy vốn.", ephemeral=True)
            return

        user_balances[user_id] -= self.bet_amount

        for child in self.children:
            child.disabled = True

        # Hiệu ứng guồng quay chuyển động mượt mà liên tục (Mô phỏng máy quay thật)
        spin_embed = discord.Embed(
            title="🎰 MÁY QUAY HŨ ĐANG GUỒNG QUAY... 🎰",
            description=f"Chủ nhân: **{interaction.user.name}** | Cược: **{self.bet_amount:,} xu**\n\n```text\n⏳ | ⏳ | ⏳\n🔄 | 🔄 | 🔄\n⏳ | ⏳ | ⏳\n```",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=spin_embed, view=self)

        # Chạy hiệu ứng trượt mượt mà 5 khung hình
        for _ in range(5):
            await asyncio.sleep(0.3)
            r1 = [random.choice(SYMBOLS) for _ in range(3)]
            r2 = [random.choice(SYMBOLS) for _ in range(3)]
            r3 = [random.choice(SYMBOLS) for _ in range(3)]
            anim_grid = f"{' | '.join(r1)}\n{' | '.join(r2)}\n{' | '.join(r3)}"
            spin_embed.description = f"Chủ nhân: **{interaction.user.name}** | Cược: **{self.bet_amount:,} xu**\n\n```text\n{anim_grid}\n```"
            await interaction.message.edit(embed=spin_embed)

        # Chốt kết quả cuối cùng
        grid = [[random.choice(SYMBOLS) for _ in range(3)] for _ in range(3)]
        board_str = "\n".join([" | ".join(row) for row in grid])
        middle_row = grid[1]
        is_jackpot = middle_row[0] == middle_row[1] == middle_row[2]
        is_win = (middle_row[0] == middle_row[1]) or (middle_row[1] == middle_row[2])

        # EXP & Level
        if user_id not in user_levels:
            user_levels[user_id] = {"exp": 0, "level": 1}
        user_levels[user_id]["exp"] += 15
        current_exp = user_levels[user_id]["exp"]
        current_level = user_levels[user_id]["level"]
        
        level_up = False
        if current_exp >= current_level * 100:
            user_levels[user_id]["level"] += 1
            level_up = True

        result_embed = discord.Embed(
            title="🎰 KẾT QUẢ QUAY HŨ 🎰",
            description=f"Chủ nhân: **{interaction.user.name}** | Cược: **{self.bet_amount:,} xu**\n\n```text\n{board_str}\n```",
            color=0xFFD700 if is_jackpot else (0x00FF00 if is_win else 0xFF0000)
        )

        result_text = ""
        if is_jackpot:
            symbol = middle_row[0]
            multiplier = MULTIPLIERS.get(symbol, 50)
            payout = self.bet_amount * multiplier * 5
            user_balances[user_id] += payout
            result_text = f"🔥 NỔ HŨ HOÀNG TRÁNG! Trúng 3 {symbol}! Nhận **+{payout:,} xu**!"
            result_embed.add_field(name="🎉 THẮNG CỰC LỚN!", value=result_text, inline=False)
        elif is_win:
            symbol = middle_row[1]
            multiplier = MULTIPLIERS.get(symbol, 2)
            payout = self.bet_amount * multiplier
            user_balances[user_id] += payout
            result_text = f"✨ THẮNG LỚN! Khớp hàng {symbol}! Nhận **+{payout:,} xu**!"
            result_embed.add_field(name="🎉 CHÚC MỪNG!", value=result_text, inline=False)
        else:
            payout = 0
            result_text = "💀 Mất trắng ván này! Chúc sếp phục thù ván sau."
            result_embed.add_field(name="💥 TRƯỢT RỒI", value=result_text, inline=False)

        # Lưu lịch sử quay gần nhất
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].insert(0, f"Cược {self.bet_amount:,} xu ➔ Nhận {payout:,} xu ({'Thắng' if payout > 0 else 'Thua'})")
        if len(user_history[user_id]) > 5:
            user_history[user_id].pop()

        footer_text = f"Số dư: {user_balances[user_id]:,} xu | Level {user_levels[user_id]['level']} (+15 EXP)"
        if level_up:
            footer_text += f" 🎉 LÊN LEVEL {user_levels[user_id]['level']}!"
        result_embed.set_footer(text=footer_text)

        for child in self.children:
            child.disabled = False
        await interaction.message.edit(embed=result_embed, view=self)

@bot.event
async def on_ready():
    print(f"Bot Quay Hũ nâng cao đã sẵn sàng!")
    await bot.change_presence(activity=discord.Game(name="!quayhu | !lichsu | !top"))

@bot.command(name="diemdanh", help="Nhận vốn khởi nghiệp")
async def diemdanh(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000
        await ctx.send(f"🎉 Chào **{ctx.author.name}**, nhận ngay **1,000 xu** vốn khởi nghiệp!")
    else:
        user_balances[user_id] += 500
        await ctx.send(f"💰 Điểm danh thành công! Nhận thêm **500 xu**. Số dư: **{user_balances[user_id]:,} xu**.")

@bot.command(name="sodu", help="Xem số dư và cấp độ")
async def sodu(ctx):
    user_id = ctx.author.id
    balance = user_balances.get(user_id, 0)
    user_data = user_levels.get(user_id, {"exp": 0, "level": 1})
    await ctx.send(f"💳 **{ctx.author.name}** | Số dư: **{balance:,} xu** | Level: **{user_data['level']}** (EXP: {user_data['exp']})")

@bot.command(name="lichsu", help="Xem lịch sử 5 ván quay gần nhất")
async def lichsu(ctx):
    user_id = ctx.author.id
    history = user_history.get(user_id, [])
    if not history:
        await ctx.send("📜 Sếp chưa quay ván nào cả!")
        return
    desc = "\n".join([f"• {h}" for h in history])
    embed = discord.Embed(title=f"📜 LỊCH SỬ QUAY HŨ CỦA {ctx.author.name.upper()}", description=desc, color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command(name="top", help="Bảng xếp hạng đại gia")
async def top(ctx):
    if not user_balances:
        await ctx.send("📊 Bảng xếp hạng trống!")
        return
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG ĐẠI GIA QUAY HŨ 🏆", color=0xFFD700)
    desc = ""
    for idx, (uid, bal) in enumerate(sorted_users[:10], 1):
        user = bot.get_user(uid)
        name = user.name if user else f"User ID: {uid}"
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        desc += f"{medal} **{name}** — 💰 **{bal:,} xu**\n"
    embed.description = desc
    await ctx.send(embed=embed)

@bot.command(name="congxu", help="[Admin] Bơm xu")
@commands.has_permissions(administrator=True)
async def congxu(ctx, member: discord.Member, amount: int):
    user_id = member.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount
    await ctx.send(f"🛠️ [Admin] Đã bơm **{amount:,} xu** cho **{member.name}**. Số dư mới: **{user_balances[user_id]:,} xu**.")

@congxu.error
async def congxu_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Chỉ Admin mới dùng được lệnh này!")

@bot.command(name="quayhu", help="Mở máy quay hũ")
async def quayhu(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000

    view = SlotView(user_id)
    embed = discord.Embed(
        title="🎰 MÁY QUAY HŨ ĐỈNH CAO 🎰",
        description=f"Chủ nhân: **{ctx.author.name}**\n\nHãy chọn mức cược và bấm **QUAY NGAY!**",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Hệ thống máy xèng sẵn sàng!")
    await ctx.send(embed=embed, view=view)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Lỗi: Không tìm thấy biến môi trường DISCORD_TOKEN trên Railway!")
