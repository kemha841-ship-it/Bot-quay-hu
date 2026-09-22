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
            await interaction.response.send_message(f"❌ Không đủ xu! Số dư: **{balance:,} xu**. Dùng lệnh `/nhanxu` để lấy vốn.", ephemeral=True)
            return

        user_balances[user_id] -= self.bet_amount

        for child in self.children:
            child.disabled = True

        # Hiệu ứng màu cam lửa rực rỡ khi máy bắt đầu guồng quay
        spin_embed = discord.Embed(
            title="🎰 ⚡ MÁY QUAY HŨ ĐANG QUAY SIÊU MƯỢT... ⚡ 🎰",
            description=f"👑 Chủ nhân: **{interaction.user.name}** | 💰 Cược: **{self.bet_amount:,} xu**\n\n```text\n 🌀 ➔ [ 🔄 | 🔄 | 🔄 ] ➔ 🌀\n ⚡ ➔ [ ✨ | ✨ | ✨ ] ➔ ⚡\n 🌀 ➔ [ 🔄 | 🔄 | 🔄 ] ➔ 🌀\n```",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=spin_embed, view=self)

        # Tăng tốc độ khung hình và số vòng quay để máy chạy mượt, sống động hơn hẳn
        for _ in range(10):
            await asyncio.sleep(0.12)
            r1 = [random.choice(SYMBOLS) for _ in range(3)]
            r2 = [random.choice(SYMBOLS) for _ in range(3)]
            r3 = [random.choice(SYMBOLS) for _ in range(3)]
            anim_grid = f" 💫 {' | '.join(r1)} 💫 \n 🔥 {' | '.join(r2)} 🔥 \n 💫 {' | '.join(r3)} 💫 "
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
    try:
        synced = await bot.tree.sync()
        print(f"Đã đồng bộ thành công {len(synced)} lệnh gạch chéo (Slash Commands) gồm cả Admin Pro.")
    except Exception as e:
        print(f"Lỗi đồng bộ lệnh: {e}")
    print(f"Bot Quay Hũ Pro mượt mà đã sẵn sàng!")
    await bot.change_presence(activity=discord.Game(name="/nhanxu | !quayhu | /napxu"))

# ==================== CÁC LỆNH GẠCH CHÉO (USER) ====================
@bot.tree.command(name="nhanxu", description="Nhận vốn khởi nghiệp hoặc điểm danh nhận xu hằng ngày!")
async def nhanxu(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000
        await interaction.response.send_message(f"🎉 Chào sếp **{interaction.user.name}**, nhận ngay **1,000 xu** vốn khởi nghiệp thành công!", ephemeral=False)
    else:
        user_balances[user_id] += 500
        await interaction.response.send_message(f"💰 Điểm danh thành công! Nhận thêm **500 xu**. Số dư ví: **{user_balances[user_id]:,} xu**.", ephemeral=False)

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

# ==================== BỘ LỆNH ADMIN PRO (GẠCH CHÉO /ADMIN) ====================
@bot.tree.command(name="napxu", description="[Admin Pro] Nạp tiền trực tiếp vào tài khoản thành viên")
@discord.app_commands.checks.has_permissions(administrator=True)
async def napxu(interaction: discord.Interaction, member: discord.Member, amount: int):
    user_id = member.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount
    await interaction.response.send_message(f"💳 [Admin Pro] Nạp thành công **{amount:,} xu** vào tài khoản của **{member.name}**. Số dư mới: **{user_balances[user_id]:,} xu**.")

@bot.tree.command(name="congxu", description="[Admin Pro] Thưởng xu sự kiện cho thành viên")
@discord.app_commands.checks.has_permissions(administrator=True)
async def congxu(interaction: discord.Interaction, member: discord.Member, amount: int):
    user_id = member.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount
    await interaction.response.send_message(f"🛠️ [Admin Pro] Đã thưởng **{amount:,} xu** cho **{member.name}**. Số dư mới: **{user_balances[user_id]:,} xu**.")

@bot.tree.command(name="truxu", description="[Admin Pro] Thu hồi / trừ xu của thành viên")
@discord.app_commands.checks.has_permissions(administrator=True)
async def truxu(interaction: discord.Interaction, member: discord.Member, amount: int):
    user_id = member.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] = max(0, user_balances[user_id] - amount)
    await interaction.response.send_message(f"🛠️ [Admin Pro] Đã thu hồi **{amount:,} xu** của **{member.name}**. Số dư còn lại: **{user_balances[user_id]:,} xu**.")

@bot.tree.command(name="setxu", description="[Admin Pro] Cố định chính xác số dư xu của thành viên")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setxu(interaction: discord.Interaction, member: discord.Member, amount: int):
    user_id = member.id
    user_balances[user_id] = max(0, amount)
    await interaction.response.send_message(f"🛠️ [Admin Pro] Đã set số dư của **{member.name}** thành chính xác **{user_balances[user_id]:,} xu**.")

# Xử lý lỗi thiếu quyền Admin cho lệnh gạch chéo
@napxu.error
@congxu.error
@truxu.error
@setxu.error
async def admin_slash_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        if interaction.response.is_done():
            await interaction.followup.send("❌ Sếp không có quyền Admin Pro để sử dụng lệnh này!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Sếp không có quyền Admin Pro để sử dụng lệnh này!", ephemeral=True)
    else:
        if interaction.response.is_done():
            await interaction.followup.send("⚠️ Lệnh không hợp lệ hoặc thiếu thông tin!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Lệnh không hợp lệ hoặc thiếu thông tin!", ephemeral=True)

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
