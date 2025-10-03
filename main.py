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
    


def format_user(member: discord.Member, with_mention: bool = True) -> str:
    """유저를 @mention(친추ID) 또는 닉네임(친추ID) 형식으로 변환"""
    username = member.name  # 친추 가능한 아이디 (ex: xxmoly)
    nickname = member.display_name  # 현재 서버에서의 닉네임

    if with_mention:
        return f"{member.mention} ({username})"
    else:
        return f"{nickname} ({username})"


@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(1411965966233112647)
    if channel:
        await channel.send(f"📥 {format_user(member, with_mention=True)} 님 반가워요!👋 [프로필설정] 채널에 가셔서 별명 변경과 멤버 등록을 하시고 자유로운 활동을 시작해보세요🐹")

@bot.event
async def on_member_remove(member: discord.Member):
    channel = bot.get_channel(1384416986926288909)
    if channel:
        await channel.send(f"📤 {format_user(member, with_mention=False)} 님이 서버에서 탈퇴했습니다.")

    try:
        from utils.function import delete_profile
        delete_profile(member.id)
    except Exception as e:
        print(f"❌ 프로필 삭제 실패: {e}")

register_slash_commands(bot)
register_game_commands(bot)
bot.run(get_token())

