import discord
from discord.ext import commands
from discord import Activity, ActivityType
from profile_setting import send_profile_embed
from slash_command import register_slash_commands
from ticket import send_ticket_message
from utils.function import get_token
from voice_tracker import VoiceTracker
from leaderboard import send_leaderboard_embed, cache_leaderboard_top10
from voice_room import VoiceRoomCog


intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = False  # 이건 필요 없음, just info
intents.members = True
bot = commands.Bot(intents=intents)

Profile_CHANNEL_ID = 1384447074241740871  # 대상 채널 ID

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.add_cog(VoiceRoomCog(bot))
    bot.add_cog(VoiceTracker(bot))
    # bot.add_cog(VoiceRoomCog(bot))
    
    await bot.sync_commands()
    await cache_leaderboard_top10()
    await send_leaderboard_embed(bot)
    await send_profile_embed(bot)
    await send_ticket_message(bot)
    await bot.change_presence(activity=Activity(
        type=ActivityType.playing,  # 또는 watching, listening 등
        name="📝 놀이터 전용 Moly bot"))
    


@bot.event
async def on_member_remove(member: discord.Member):

    # 1. 로그 채널 가져오기
    channel = bot.get_channel(1384416986926288909)
    if channel:
        await channel.send(f"📤 **{member.name}** 님이 서버에서 탈퇴했습니다.")

    # 2. DB에서 프로필 삭제
    try:
        from utils.function import delete_profile  # 삭제 함수는 아래 참고
        delete_profile(member.id)
    except Exception as e:
        print(f"❌ 프로필 삭제 실패: {e}")
        
        
        
register_slash_commands(bot)

bot.run(get_token())

