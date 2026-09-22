import os
import random
import asyncio
import discord
from discord.ext import commands

# Cấu hình khởi tạo Bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Danh sách các biểu tượng để quay hũ
ICONS = ["🍒", "🍋", "🍊", "🔔", "💎", "7️⃣"]

# Hình ảnh minh họa khi quay hũ
SPINNING_IMAGE = "https://images.unsplash.com/photo-1596838132731-3301c3fd4317?w=600&auto=format&fit=crop&q=80"
JACKPOT_IMAGE = "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=600&auto=format&fit=crop&q=80"

@bot.event
async def on_ready():
    print(f'Bot Quay Hũ [{bot.user}] đã sẵn sàng quẩy cùng sếp!')
    await bot.change_presence(activity=discord.Game(name="!quayhu để nổ hũ!"))

@bot.command(name="quayhu", help="Lệnh quay hũ đổi đời có hình ảnh cực đẹp!")
async def quayhu(ctx):
    # 1. Tạo hiệu ứng đang quay (Spinning Embed)
    embed_spin = discord.Embed(
        title="🎰 QUAY HŨ ĐỔI ĐỜI 🎰",
        description="*Đang quay các ô số... Chúc sếp may mắn!* 🔄\n\n**[ 🔄 | 🔄 | 🔄 ]**",
        color=discord.Color.gold()
    )
    embed_spin.set_image(url=SPINNING_IMAGE)
    embed_spin.set_footer(text=f"Người quay: {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    
    msg = await ctx.send(embed=embed_spin)
    await asyncio.sleep(1.0)
    
    # 2. Random kết quả 3 ô
    slot1 = random.choice(ICONS)
    slot2 = random.choice(ICONS)
    slot3 = random.choice(ICONS)
    
    # 3. Kiểm tra kết quả thắng thua
    is_jackpot = (slot1 == slot2 == slot3)
    is_win = is_jackpot or (slot1 == slot2 or slot2 == slot3 or slot1 == slot3)
    
    if is_jackpot:
        color = discord.Color.brand_red()
        title = "🎉 NỔ HŨ JACKPOT CỰC LỚN! 🎉"
        desc = f"**[ {slot1} | {slot2} | {slot3} ]**\n\n🔥 **QUÁ ĐỈNH! Sếp đã trúng NỔ HŨ ĐẶC BIỆT! Ăn trọn vẹn giải thưởng lớn!** 🔥"
        image_url = JACKPOT_IMAGE
    elif is_win:
        color = discord.Color.green()
        title = "✨ CHÚC MỪNG SẾB ĐÃ THẮNG! ✨"
        desc = f"**[ {slot1} | {slot2} | {slot3} ]**\n\n🎯 Trúng 2 biểu tượng giống nhau! Húp trọn tiền thưởng nhỏ!"
        image_url = SPINNING_IMAGE
    else:
        color = discord.Color.dark_theme()
        title = "😢 CHÚC SẾB MAY MẮN LẦN SAU! 😢"
        desc = f"**[ {slot1} | {slot2} | {slot3} ]**\n\n❌ Lần này đen quá, làm lại ván nữa nào sếp ơi!"
        image_url = SPINNING_IMAGE

    embed_result = discord.Embed(
        title=title,
        description=desc,
        color=color
    )
    embed_result.set_image(url=image_url)
    embed_result.set_footer(text=f"Người quay: {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    
    await msg.edit(embed=embed_result)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Lỗi: Chưa thiết lập biến môi trường DISCORD_TOKEN!")
