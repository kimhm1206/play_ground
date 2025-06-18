# leaderboard.py
import discord
from discord.ext import commands
from utils.function import get_connection
from discord.ui import View, Button
from discord import Interaction

DAILY_LIMIT = 360
LEVEL_UNIT = 30
top10_cache: list[dict] = []  # {"user_id": int, "level": int, "total": int}


def get_exp_percentage(level: int, total_minutes: int) -> int:
    required = level * LEVEL_UNIT
    percent = int((total_minutes / required) * 100) if required > 0 else 0
    return min(percent, 100)


async def cache_leaderboard_top10():
    global top10_cache
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, level, total_minutes
        FROM voice_leaderboard
        ORDER BY level DESC, total_minutes DESC
        LIMIT 10
    """)
    top10_cache = [
        {"user_id": row[0], "level": row[1], "total": row[2]}
        for row in cur.fetchall()
    ]
    conn.close()


async def send_leaderboard_embed(bot: commands.Bot):
    global top10_cache

    channel = bot.get_channel(1384893153273970760)
    if channel is None:
        print("❌ 리더보드 채널을 찾을 수 없습니다.")
        return

    # ✅ 기존 봇 메시지 모두 삭제
    deleted = 0
    async for msg in channel.history(limit=100):
        if msg.author == bot.user:
            try:
                await msg.delete()
                deleted += 1
            except:
                pass
    print(f"🧹 삭제된 메시지 수: {deleted}")

    # ✅ Embed 생성
    embed = discord.Embed(
        title="🎖️ 음성 리더보드 – 상위 10명",
        description="※ 레벨 및 다음 레벨까지 경험치 진행률 기준입니다\n※ 하루 최대 360분까지만 누적됩니다",
        color=discord.Color.gold()
    )

    medal_emojis = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(top10_cache, start=1):
        member = channel.guild.get_member(user["user_id"])
        name = member.display_name if member else f"Unknown({user['user_id']})"
        level = user["level"]
        total = user["total"]
        percent = int((total / (level * LEVEL_UNIT)) * 100) if level > 0 else 0

        title = f"{medal_emojis[i-1]} {name}" if i <= 3 else f"{i}위: {name}"
        embed.add_field(
            name=title,
            value=f"레벨 {level} ({percent}%)",
            inline=False
        )

    # ✅ 새 메시지 전송 및 핀 고정
    msg = await channel.send(embed=embed,view=LeaderboardView(bot))


async def check_leaderboard_update(user_id: int, level: int, total: int, bot: commands.Bot):
    global top10_cache

    all_users = top10_cache + [{"user_id": user_id, "level": level, "total": total}]
    # 중복 제거 (동일 user_id 마지막 항목만 유지)
    unique_users = {u["user_id"]: u for u in all_users}.values()
    sorted_all = sorted(unique_users, key=lambda x: (-x["level"], -x["total"]))
    new_top10 = sorted_all[:10]

    if top10_cache != new_top10:
        top10_cache = new_top10
        await send_leaderboard_embed(bot)


class LeaderboardView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎖️ 순위 확인", style=discord.ButtonStyle.primary)
    async def check_rank(self, button: Button, interaction: Interaction):
        user_id = interaction.user.id

        # DB에서 전체 순위 계산
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, level, total_minutes
            FROM voice_leaderboard
            ORDER BY level DESC, total_minutes DESC
        """)
        all_users = cur.fetchall()
        conn.close()

        rank = None
        for i, row in enumerate(all_users, start=1):
            if row[0] == user_id:
                level, total = row[1], row[2]
                percent = int((total / (level * LEVEL_UNIT)) * 100) if level > 0 else 0
                rank = i
                break

        if rank:
            await interaction.response.send_message(
                f"🎖️ 당신의 순위는 **{rank}위**입니다!\n"
                f"📊 레벨 **{level}**, 경험치 **{percent}%** 진행 중이에요!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "🔍 아직 순위에 등록되지 않았어요.\n(음성 채널에서 활동 기록이 필요합니다!)",
                ephemeral=True
            )