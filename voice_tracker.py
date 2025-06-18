import discord
from discord.ext import commands
from datetime import datetime, date
from utils.function import get_connection
from leaderboard import check_leaderboard_update

DAILY_LIMIT = 360
LEVEL_UNIT = 30

class VoiceTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_joins: dict[int, datetime] = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = member.id
        if before.channel is None and after.channel is not None:
            self.voice_joins[user_id] = datetime.utcnow()
        elif before.channel is not None and after.channel is None:
            joined_at = self.voice_joins.pop(user_id, None)
            if joined_at:
                minutes = int((datetime.utcnow() - joined_at).total_seconds() // 60)
                if minutes >= 1:
                    result = await update_user_leaderboard(user_id, minutes, self.bot)
                    print(f"[레벨 시스템] {member.display_name} → {result['message']}")


async def update_user_leaderboard(user_id, minutes_to_add, bot: commands.Bot):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT level, total_minutes, last_update_date, daily_minutes
        FROM voice_leaderboard WHERE user_id = %s
    """, (user_id,))
    row = cur.fetchone()

    if row:
        level, total_minutes, last_date, daily_minutes = row
        if last_date != today:
            daily_minutes = 0
    else:
        cur.execute("""
            INSERT INTO voice_leaderboard (user_id, level, total_minutes, last_update_date, daily_minutes)
            VALUES (%s, 1, 0, %s, 0)
        """, (user_id, today))
        conn.commit()
        level, total_minutes, daily_minutes = 1, 0, 0

    remaining = DAILY_LIMIT - daily_minutes
    actual_gain = min(minutes_to_add, remaining)
    if actual_gain <= 0:
        conn.close()
        return {
            "gained": 0,
            "level": level,
            "total": total_minutes,
            "message": "🛑 오늘은 더 이상 경험치를 얻을 수 없습니다."
        }

    total_minutes += actual_gain
    daily_minutes += actual_gain

    current_level = level
    while total_minutes >= current_level * LEVEL_UNIT:
        total_minutes -= current_level * LEVEL_UNIT
        current_level += 1

    cur.execute("""
        UPDATE voice_leaderboard
        SET level = %s,
            total_minutes = %s,
            last_update_date = %s,
            daily_minutes = %s
        WHERE user_id = %s
    """, (current_level, total_minutes, today, daily_minutes, user_id))
    conn.commit()
    conn.close()

    # ✅ await 붙여야 함
    await check_leaderboard_update(user_id, current_level, total_minutes, bot)

    return {
        "gained": actual_gain,
        "level": current_level,
        "total": total_minutes,
        "message": f"✅ {actual_gain}분 누적됨 / 현재 {current_level}레벨, {total_minutes}분"
    }
