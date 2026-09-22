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

SYMBOLS = ["🍒", "🍋", "🔔", "💎", "7️⃣", "⭐"]
MULTIPLIERS = {
    "🍒": 2,
    "🍋": 4,
    "🔔": 8,
    "💎": 16,
    "7️⃣": 32,
    "⭐": 64,
}

# Giao diện nút bấm chọn mức cược và quay hũ
class SlotView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet_amount = 100  # Mức cược mặc định

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Đây không phải máy quay của sếp! Hãy tự gõ `!quayhu` để mở máy riêng.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Cược 100", style=discord.ButtonStyle.secondary)
    async def bet_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bet_amount = 100
        await interaction.response.send_message(f"✅ Đã chọn mức cược: **100 xu**", ephemeral=True)

    @discord.ui.button(label="Cược 500", style=discord.ButtonStyle.secondary)
    async def bet_500(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bet_amount = 500
        await interaction.response.send_message(f"✅ Đã chọn mức cược: **500 xu**", ephemeral=True)

    @discord.ui.button(label="Cược 1000", style=discord.ButtonStyle.secondary)
    async def bet_1000(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bet_amount = 1000
        await interaction.response.send_message(f"✅ Đã chọn mức cược: **1,000 xu**", ephemeral=True)

    @discord.ui.button(label="🔥 ALL-IN (Tất tay)", style=discord.ButtonStyle.danger)
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
            await interaction.response.send_message(f"❌ Sếp không đủ tiền! Số dư: **{balance:,} xu**. Gõ `!diemdanh` lấy vốn nhé.", ephemeral=True)
            return

        # Trừ tiền cược
        user_balances[user_id] -= self.bet_amount

        # Khóa nút bấm trong lúc quay
        for child in self.children:
            child.disabled = True
        
        spin_embed = discord.Embed(
            title="🎰 MÁY QUAY HŨ ĐANG QUAY... 🎰",
            description=f"Chủ nhân: **{interaction.user.name}** | Cược: **{self.bet_amount:,} xu**\n\n```text\n🔄 | 🔄 | 🔄\n🔄 | 🔄 | 🔄\n🔄 | 🔄 | 🔄\n```",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=spin_embed, view=self)

        # Hiệu ứng guồng quay chạy lộn xộn trong 2 giây
        for _ in range(4):
            await asyncio.sleep(0.4)
            fake_grid = "\n".join([" | ".join([random.choice(SYMBOLS) for _ in range(3)]) for _ in range(3)])
            spin_embed.description = f"Chủ nhân: **{interaction.user.name}** | Cược: **{self.bet_amount:,} xu**\n\n```text\n{fake_grid}\n```"
            await interaction.message.edit(embed=spin_embed)

        # Chốt kết quả cuối cùng
        grid = []
        for _ in range(3):
            row = [random.choice(SYMBOLS) for _ in range(3)]
            grid.append(row)

        board_str = "\n".join([" | ".join(row) for row in grid])
        middle_row = grid[1]
        is_jackpot = middle_row[0] == middle_row[1] == middle_row[2]
        is_win = (middle_row[0] == middle_row[1]) or (middle_row[1] == middle_row[2])

        # EXP & Level
        if user_id not in user_levels:
            user_levels[user_id] = {"exp": 0, "level": 1}
        user_levels[user_id]["exp"] += 10
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

        if is_jackpot:
            symbol = middle_row[0]
            multiplier = MULTIPLIERS.get(symbol, 50)
            payout = self.bet_amount * multiplier * 5
            user_balances[user_id] += payout
            result_embed.add_field(name="🔥 NỔ HŨ HOÀNG TRÁNG! 🔥", value=f"Trúng 3 biểu tượng {symbol}! Chúc mừng sếp hốt trọn **+{payout:,} xu**!", inline=False)
        elif is_win:
            symbol = middle_row[1]
            multiplier = MULTIPLIERS.get(symbol, 2)
            payout = self.bet_amount * multiplier
            user_balances[user_id] += payout
            result_embed.add_field(name="✨ THẮNG LỚN! ✨", value=f"Khớp hàng {symbol}! Chúc mừng sếp nhận **+{payout:,} xu**!", inline=False)
        else:
            result_embed.add_field(name="💀 MẤT MÁT RỒI!", value="Tay trắng hoàn tay trắng! Chúc sếp phục thù ván sau.", inline=False)

        footer_text = f"Số dư: {user_balances[user_id]:,} xu | Level {user_levels[user_id]['level']} (+10 EXP)"
        if level_up:
            footer_text += f" 🎉 LÊN LEVEL {user_levels[user_id]['level']}!"
        result_embed.set_footer(text=footer_text)

        # Mở lại nút bấm để tiếp tục chơi ván mới
        for child in self.children:
            child.disabled = False
        await interaction.message.edit(embed=result_embed, view=self)

@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} đã sẵn sàng với hệ thống nút bấm tương tác!")
    await bot.change_presence(activity=discord.Game(name="!quayhu | !top | !diemdanh"))

@bot.command(name="diemdanh", help="Nhận vốn khởi nghiệp hàng ngày")
async def diemdanh(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000
        await ctx.send(f"🎉 Chào mừng **{ctx.author.name}**, sếp nhận ngay **1,000 xu** vốn khởi nghiệp!")
    else:
        user_balances[user_id] += 500
        await ctx.send(f"💰 Sếp đã điểm danh nhận thêm **500 xu**. Số dư ví: **{user_balances[user_id]:,} xu**.")

@bot.command(name="sodu", help="Kiểm tra tài khoản xu và cấp độ")
async def sodu(ctx):
    user_id = ctx.author.id
    balance = user_balances.get(user_id, 0)
    user_data = user_levels.get(user_id, {"exp": 0, "level": 1})
    await ctx.send(f"💳 Sếp **{ctx.author.name}** | Số dư: **{balance:,} xu** | Cấp độ: **Level {user_data['level']}** (EXP: {user_data['exp']})")

@bot.command(name="top", help="Xem bảng xếp hạng đại gia")
async def top(ctx):
    if not user_balances:
        await ctx.send("📊 Bảng xếp hạng đang trống!")
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

@bot.command(name="quayhu", help="Mở bảng điều khiển máy quay hũ tương tác")
async def quayhu(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000

    view = SlotView(user_id)
    embed = discord.Embed(
        title="🎰 MÁY QUAY HŨ TƯƠNG TẠC 🎰",
        description=f"Chủ nhân: **{ctx.author.name}**\n\nHãy chọn mức cược ở các nút bên dưới rồi bấm **QUAY NGAY!**",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Hệ thống máy xèng sẵn sàng hoạt động!")
    await ctx.send(embed=embed, view=view)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Lỗi: Không tìm thấy biến môi trường DISCORD_TOKEN trên Railway!")
