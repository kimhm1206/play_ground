import discord
from discord.ext import commands
from discord import Activity, ActivityType
from profile_setting import send_profile_embed
from slash_command import register_slash_commands
from minigame import register_game_commands
from ticket import send_ticket_message
from utils.function import get_token
from voice_tracker import VoiceTracker
from leaderboard import send_leaderboard_embed, cache_leaderboard_top10
from voice_room import VoiceRoomCog
from casino import send_casino_lobby
from schedule import setup_scheduler

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # 이건 필요 없음, just info
intents.members = True
bot = commands.Bot(intents=intents)

Profile_CHANNEL_ID = 1384447074241740871  # 대상 채널 ID

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.add_cog(VoiceRoomCog(bot))
    bot.add_cog(VoiceTracker(bot))
    
    await bot.sync_commands()
    await cache_leaderboard_top10()
    await send_leaderboard_embed(bot)
    await send_profile_embed(bot)
    await send_ticket_message(bot)
    await send_casino_lobby(bot)
    setup_scheduler(bot)
    await bot.change_presence(activity=Activity(
        type=ActivityType.playing,  # 또는 watching, listening 등
        name="📝 놀이터 전용 Moly bot"))
    


def get_display_name(member: discord.Member) -> str:
    """멤버의 표시 이름을 통일된 방식으로 가져오기"""
    return member.global_name or member.display_name or member.name


@bot.event
async def on_member_remove(member: discord.Member):
    channel = bot.get_channel(1384416986926288909)
    if channel:
        display_name = get_display_name(member)
        await channel.send(f"📤 **{display_name}** 님이 서버에서 탈퇴했습니다.")

    try:
        from utils.function import delete_profile
        delete_profile(member.id)
    except Exception as e:
        print(f"❌ 프로필 삭제 실패: {e}")


@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(1384416986926288909)
    if not channel:
        print("❌ 입장 로그 채널을 찾을 수 없습니다.")
        return

    display_name = get_display_name(member)
    await channel.send(f"📥 {member.mention}({display_name}) 님이 서버에 들어왔습니다.")

register_slash_commands(bot)
register_game_commands(bot)
bot.run(get_token())

