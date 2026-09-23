import os
import random
import asyncio
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_balances = {}
user_levels = {}
user_history = {}
daily_cooldown = {}

# 🔐 MẬT KHẨU BẢO MẬT CHO ADMIN (Sếp có thể thay đổi chuỗi mật khẩu này tùy ý)
ADMIN_SECRET_KEY = "admin123"

SYMBOLS = ["🍒", "🍋", "🔔", "💎", "7️⃣", "⭐"]
MULTIPLIERS = {
    "🍒": 2,
    "🍋": 4,
    "🔔": 8,
    "💎": 16,
    "7️⃣": 32,
    "⭐": 64,
}

# ==================== VIEW QUAY HŨ ====================
class SlotView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet_amount = 100

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Máy này người khác đang chơi! Hãy gõ `!quayhu` để mở máy riêng.", ephemeral=True)
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
            await interaction.response.send_message(f"❌ Không đủ xu! Số dư: **{balance:,} xu**.", ephemeral=True)
            return

        user_balances[user_id] -= self.bet_amount

        for child in self.children:
            child.disabled = True

        spin_embed = discord.Embed(
            title="🎰 ⚡ MÁY QUAY HŨ ĐANG QUAY... ⚡ 🎰",
            description=f"👑 Chủ nhân: **{interaction.user.name}** | 💰 Cược: **{self.bet_amount:,} xu**\n\n```text\n 🌀 ➔ [ 🔄 | 🔄 | 🔄 ] ➔ 🌀\n```",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=spin_embed, view=self)

        for _ in range(8):
            await asyncio.sleep(0.1)
            r1 = [random.choice(SYMBOLS) for _ in range(3)]
            anim_grid = f" 💫 {' | '.join(r1)} 💫 "
            spin_embed.description = f"👑 Chủ nhân: **{interaction.user.name}** | 💰 Cược: **{self.bet_amount:,} xu**\n\n```text\n{anim_grid}\n```"
            await interaction.message.edit(embed=spin_embed)

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

        res_color = 0xFFD700 if is_jackpot else (0x00FF00 if is_win else 0xFF3333)
        result_embed = discord.Embed(
            title="🎰 🌟 KẾT QUẢ QUAY HŨ 🌟 🎰",
            description=f"👑 Chủ nhân: **{interaction.user.name}** | 💰 Cược: **{self.bet_amount:,} xu**\n\n```text\n{board_str}\n```",
            color=res_color
        )

        if is_jackpot:
            symbol = middle_row[0]
            multiplier = MULTIPLIERS.get(symbol, 50)
            payout = self.bet_amount * multiplier * 5
            user_balances[user_id] += payout
            result_embed.add_field(name="🔥 👑 NỔ HŨ HOÀNG TRÁNG! 👑 🔥", value=f"Trúng 3 biểu tượng {symbol}! Nhận **+{payout:,} xu**!", inline=False)
        elif is_win:
            symbol = middle_row[1]
            multiplier = MULTIPLIERS.get(symbol, 2)
            payout = self.bet_amount * multiplier
            user_balances[user_id] += payout
            result_embed.add_field(name="✨ 💰 THẮNG LỚN! 💰 ✨", value=f"Khớp hàng {symbol}! Nhận **+{payout:,} xu**!", inline=False)
        else:
            payout = 0
            result_embed.add_field(name="💀 💸 MẤT TRẮNG! 💸", value="Tay trắng! Chúc sếp may mắn ván sau nhé!", inline=False)

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].insert(0, f"[Quay Hũ] Cược {self.bet_amount:,} xu ➔ Nhận {payout:,} xu")
        if len(user_history[user_id]) > 5:
            user_history[user_id].pop()

        footer_text = f"💳 Ví: {user_balances[user_id]:,} xu | 🎖️ Level {user_levels[user_id]['level']} (+15 EXP)"
        if level_up:
            footer_text += f" 🎉 LÊN LEVEL {user_levels[user_id]['level']}!"
        result_embed.set_footer(text=footer_text)

        for child in self.children:
            child.disabled = False
        await interaction.message.edit(embed=result_embed, view=self)


# ==================== VIEW TÀI XỈU (TX) ====================
class TaiXiuView(discord.ui.View):
    def __init__(self, user_id, bet_amount):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.bet_amount = bet_amount

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Bàn Tài Xỉu này không phải của sếp!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🟢 CHỌN TÀI (11-17)", style=discord.ButtonStyle.success)
    async def chon_tai(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_taixiu(interaction, "TÀI")

    @discord.ui.button(label="🔴 CHỌN XỈU (3-10)", style=discord.ButtonStyle.danger)
    async def chon_xiu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_taixiu(interaction, "XỈU")

    async def process_taixiu(self, interaction: discord.Interaction, choice: str):
        user_id = self.user_id
        balance = user_balances.get(user_id, 1000)

        if balance < self.bet_amount:
            await interaction.response.send_message(f"❌ Không đủ xu để cược **{self.bet_amount:,} xu**!", ephemeral=True)
            return

        user_balances[user_id] -= self.bet_amount

        for child in self.children:
            child.disabled = True

        loading_embed = discord.Embed(
            title="🎲 ⚡ LẮC XÚ XẮC TÀI XỈU... ⚡ 🎲",
            description=f"👑 Chủ nhân: **{interaction.user.name}** | Cược: **{self.bet_amount:,} xu** vào cửa **{choice}**\n\n```text\n 🎲 [ 🎲 | 🎲 | 🎲 ] 🎲 \n```",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=loading_embed, view=self)
        await asyncio.sleep(2)

        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        d3 = random.randint(1, 6)
        total = d1 + d2 + d3
        result_side = "TÀI" if total >= 11 else "XỈU"
        is_win = (choice == result_side)

        dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        board_str = f"{dice_faces[d1]} {dice_faces[d2]} {dice_faces[d3]}"

        result_embed = discord.Embed(
            title="🎲 🌟 KẾT QUẢ TÀI XỈU 🌟 🎲",
            description=f"👑 Chủ nhân: **{interaction.user.name}**\n\n```text\n Xúc xắc: {board_str} (Tổng: {d1} + {d2} + {d3} = **{total} - {result_side}**)\n```",
            color=0x00FF00 if is_win else 0xFF3333
        )

        if is_win:
            payout = self.bet_amount * 2
            user_balances[user_id] += payout
            result_embed.add_field(name="🎉 THẮNG CỰC ĐÃ!", value=f"Sếp đã đoán chuẩn **{choice}** và hốt về **+{payout:,} xu**!", inline=False)
        else:
            payout = 0
            result_embed.add_field(name="😢 THUA MẤT RỒI!", value=f"Ra **{result_side}**, tiếc quá sếp ơi!", inline=False)

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].insert(0, f"[Tài Xỉu] Cược {self.bet_amount:,} vào {choice} (Ra {total}) ➔ Nhận {payout:,} xu")
        if len(user_history[user_id]) > 5:
            user_history[user_id].pop()

        result_embed.set_footer(text=f"💳 Số dư ví: {user_balances[user_id]:,} xu")
        await interaction.message.edit(embed=result_embed, view=None)


# ==================== BOT EVENTS & LỆNH CHUNG ====================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Đã đồng bộ {len(synced)} lệnh slash.")
    except Exception as e:
        print(f"Lỗi: {e}")
    print(f"Bot Casino Pro đã sẵn sàng!")
    await bot.change_presence(activity=discord.Game(name="/nhanxu | /taixiu | !quayhu"))

@bot.tree.command(name="nhanxu", description="Nhận vốn khởi nghiệp hoặc điểm danh nhận xu hằng ngày (1 lần/ngày)")
async def nhanxu(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = datetime.now(timezone(timedelta(hours=7)))
    today_str = now.strftime("%Y-%m-%d")

    if user_id in daily_cooldown and daily_cooldown[user_id] == today_str:
        await interaction.response.send_message("⏳ Sếp đã điểm danh nhận xu hôm nay rồi! Quay lại vào ngày mai nhé.", ephemeral=True)
        return

    daily_cooldown[user_id] = today_str

    if user_id not in user_balances:
        user_balances[user_id] = 1000
        await interaction.response.send_message(f"🎉 Chào sếp **{interaction.user.name}**, nhận ngay **1,000 xu** vốn khởi nghiệp!", ephemeral=False)
    else:
        user_balances[user_id] += 500
        await interaction.response.send_message(f"💰 Điểm danh thành công! Nhận thêm **500 xu**. Số dư: **{user_balances[user_id]:,} xu**.", ephemeral=False)

@bot.tree.command(name="taixiu", description="Chơi Tài Xỉu trực tiếp bằng xu")
async def taixiu(interaction: discord.Interaction, sotien: int):
    user_id = interaction.user.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000

    if sotien <= 0:
        await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
        return

    balance = user_balances.get(user_id, 1000)
    if balance < sotien:
        await interaction.response.send_message(f"❌ Không đủ xu! Số dư hiện tại: **{balance:,} xu**.", ephemeral=True)
        return

    view = TaiXiuView(user_id, sotien)
    embed = discord.Embed(
        title="🎲 ⚡ BÀN CƯỢC TÀI XỈU ⚡ 🎲",
        description=f"👑 Chủ nhân: **{interaction.user.name}**\n💰 Tiền cược: **{sotien:,} xu**\n\n👇 Bấm nút chọn cửa bên dưới để lắc xúc xắc:",
        color=0x9900FF
    )
    await interaction.response.send_message(embed=embed, view=view)

@bot.command(name="quayhu")
async def quayhu(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000

    view = SlotView(user_id)
    embed = discord.Embed(
        title="🎰 💎 MÁY QUAY HŨ ĐỈNH CAO 💎 🎰",
        description=f"👑 Chủ nhân: **{ctx.author.name}**\n\nChọn mức cược rồi bấm **QUAY NGAY!**",
        color=0x9900FF
    )
    await ctx.send(embed=embed, view=view)

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
    embed = discord.Embed(title=f"📜 LỊCH SỬ CỦA {ctx.author.name.upper()}", description=desc, color=0x00FFFF)
    await ctx.send(embed=embed)

@bot.command(name="top")
async def top(ctx):
    if not user_balances:
        await ctx.send("📊 Bảng xếp hạng trống!")
        return
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="🏆 🌟 BẢNG XẾP HẠNG ĐẠI GIA 🌟 🏆", color=0xFFD700)
    desc = ""
    for idx, (uid, bal) in enumerate(sorted_users[:10], 1):
        user = bot.get_user(uid)
        name = user.name if user else f"User ID: {uid}"
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        desc += f"{medal} **{name}** — 💰 **{bal:,} xu**\n"
    embed.description = desc
    await ctx.send(embed=embed)

# ==================== BỘ LỆNH ADMIN PRO (BẢO MẬT BẰNG MẬT KHẨU) ====================
@bot.tree.command(name="setxu", description="[Admin Pro] Set chính xác số dư xu (Yêu cầu mật khẩu)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setxu(interaction: discord.Interaction, password: str, member: discord.Member, amount: int):
    if password != ADMIN_SECRET_KEY:
        await interaction.response.send_message("❌ Mật khẩu Admin Pro không chính xác!", ephemeral=True)
        return
    
    user_id = member.id
    user_balances[user_id] = max(0, amount)
    await interaction.response.send_message(f"🛠️ [Admin Pro] Đã set số dư của **{member.name}** thành chính xác **{user_balances[user_id]:,} xu**.")

@bot.tree.command(name="resetxu", description="[Admin Pro] Reset toàn bộ ví tiền của toàn server về 0 (Yêu cầu mật khẩu)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def resetxu(interaction: discord.Interaction, password: str):
    if password != ADMIN_SECRET_KEY:
        await interaction.response.send_message("❌ Mật khẩu Admin Pro không chính xác!", ephemeral=True)
        return
    
    user_balances.clear()
    await interaction.response.send_message("🚨 [Admin Pro] Đã dọn sạch và reset toàn bộ ví xu của toàn bộ server về 0 để chống lạm phát!")

@setxu.error
@resetxu.error
async def admin_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Sếp không có quyền Admin trong server này!", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Lệnh không hợp lệ hoặc thiếu thông tin!", ephemeral=True)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Lỗi: Không tìm thấy DISCORD_TOKEN trên Railway!")
