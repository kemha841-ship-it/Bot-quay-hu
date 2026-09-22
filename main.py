import os
import random
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Database giả lập trong bộ nhớ
# user_balances: {user_id: xu}
user_balances = {}
# user_levels: {user_id: {"exp": exp, "level": level}}
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

@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} đã sẵn sàng bùng nổ với hệ thống Level & Top!")
    await bot.change_presence(activity=discord.Game(name="!quayhu | !top | !diemdanh"))

@bot.command(name="diemdanh", help="Nhận vốn khởi nghiệp hàng ngày")
async def diemdanh(ctx):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000
        await ctx.send(f"🎉 Chào mừng **{ctx.author.name}**, sếp được tặng **1,000 xu** vốn khởi nghiệp!")
    else:
        user_balances[user_id] += 500
        await ctx.send(f"💰 Sếp đã điểm danh và nhận thêm **500 xu**. Số dư: **{user_balances[user_id]:,} xu**.")

@bot.command(name="sodu", help="Kiểm tra tài khoản xu và cấp độ")
async def sodu(ctx):
    user_id = ctx.author.id
    balance = user_balances.get(user_id, 0)
    user_data = user_levels.get(user_id, {"exp": 0, "level": 1})
    await ctx.send(f"💳 Sếp **{ctx.author.name}** | Số dư: **{balance:,} xu** | Cấp độ: **Level {user_data['level']}** (EXP: {user_data['exp']})")

@bot.command(name="top", help="Xem bảng xếp hạng đại gia quay hũ")
async def top(ctx):
    if not user_balances:
        await ctx.send("📊 Bảng xếp hạng hiện đang trống!")
        return
    
    # Sắp xếp người chơi theo số xu giảm dần
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    
    embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG ĐẠI GIA QUAY HŨ 🏆", color=0xFFD700)
    desc = ""
    for idx, (uid, bal) in enumerate(sorted_users[:10], 1):
        user = bot.get_user(uid)
        name = user.name if user else f"User ID: {uid}"
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        desc += f"{medal} **{name}** — 💰 **{bal:,} xu**\n"
    
    embed.description = desc
    embed.set_footer(text="Cố gắng quay hũ để giành ngôi vương nhé sếp!")
    await ctx.send(embed=embed)

@bot.command(name="congxu", help="[Admin] Bơm xu cho người chơi")
@commands.has_permissions(administrator=True)
async def congxu(ctx, member: discord.Member, amount: int):
    user_id = member.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount
    await ctx.send(f"🛠️ [Admin] Đã bơm thành công **{amount:,} xu** cho **{member.name}**. Số dư mới: **{user_balances[user_id]:,} xu**.")

@congxu.error
async def congxu_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Sếp không có quyền sử dụng lệnh đặc biệt này! Chỉ Admin mới được dùng.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Sai cú pháp! Dùng: `!congxu @tên_user [số_xu]`")

@bot.command(name="quayhu", help="Chơi quay hũ: !quayhu [số_xu_cược]")
async def quayhu(ctx, amount: int = None):
    user_id = ctx.author.id
    
    if user_id not in user_balances:
        user_balances[user_id] = 1000
        
    balance = user_balances[user_id]
    
    if amount is None or amount <= 0:
        await ctx.send("⚠️ Vui lòng nhập số xu cược hợp lệ! Ví dụ: `!quayhu 100`")
        return
        
    if balance < amount:
        await ctx.send(f"❌ Sếp không đủ tiền! Số dư hiện tại: **{balance:,} xu**. Gõ `!diemdanh` để nhận thêm vốn.")
        return

    # Trừ tiền cược
    user_balances[user_id] -= amount

    # Xử lý EXP và Level
    if user_id not in user_levels:
        user_levels[user_id] = {"exp": 0, "level": 1}
    
    user_levels[user_id]["exp"] += 10
    current_exp = user_levels[user_id]["exp"]
    current_level = user_levels[user_id]["level"]
    
    # Cứ mỗi 100 EXP lên 1 cấp
    level_up = False
    if current_exp >= current_level * 100:
        user_levels[user_id]["level"] += 1
        level_up = True

    # Quay hũ ngẫu nhiên 3x3
    grid = []
    for _ in range(3):
        row = [random.choice(SYMBOLS) for _ in range(3)]
        grid.append(row)

    board_str = "\n".join([" | ".join(row) for row in grid])

    middle_row = grid[1]
    is_jackpot = middle_row[0] == middle_row[1] == middle_row[2]
    is_win = (middle_row[0] == middle_row[1]) or (middle_row[1] == middle_row[2])

    embed = discord.Embed(
        title="🎰 MÁY QUAY HŨ ĐỈNH CAO 🎰",
        description=f"Chủ nhân: **{ctx.author.name}** | Cược: **{amount:,} xu**\n\n```text\n{board_str}\n```",
        color=0xFFD700 if is_jackpot else (0x00FF00 if is_win else 0xFF0000)
    )

    if is_jackpot:
        symbol = middle_row[0]
        multiplier = MULTIPLIERS.get(symbol, 50)
        payout = amount * multiplier * 5
        user_balances[user_id] += payout
        embed.add_field(name="🔥 NỔ HŨ HOÀNG TRÁNG! 🔥", value=f"Trúng 3 biểu tượng {symbol}! Nhận x{multiplier * 5}: **+{payout:,} xu**!", inline=False)
    elif is_win:
        symbol = middle_row[1]
        multiplier = MULTIPLIERS.get(symbol, 2)
        payout = amount * multiplier
        user_balances[user_id] += payout
        embed.add_field(name="✨ THẮNG LỚN! ✨", value=f"Khớp hàng {symbol}! Nhận x{multiplier}: **+{payout:,} xu**!", inline=False)
    else:
        embed.add_field(name="💀 MẤT MÁT RỒI!", value="Chúc sếp may mắn lần sau!", inline=False)

    footer_text = f"Số dư: {user_balances[user_id]:,} xu | Cấp độ: Level {user_levels[user_id]['level']} (+10 EXP)"
    if level_up:
        footer_text += f" 🎉 CHÚC MỪNG LÊN LEVEL {user_levels[user_id]['level']}!"
    
    embed.set_footer(text=footer_text)
    await ctx.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Lỗi: Không tìm thấy biến môi trường DISCORD_TOKEN trên Railway!")
