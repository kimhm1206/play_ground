import discord
from discord.ext import commands
from discord import Activity, ActivityType
from profile_setting import send_profile_embed
from slash_command import register_slash_commands
from utils.function import get_token

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
    
    await bot.sync_commands()
    
    await send_profile_embed(bot)
    await bot.change_presence(activity=Activity(
        type=ActivityType.playing,  # 또는 watching, listening 등
        name="📝 PLAY GROUND 전용 Moly 입니다!"))
    
register_slash_commands(bot)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    TARGET_MESSAGE_ID = 1384421415503269898
    TARGET_EMOJI = "✅"  # :white_check_mark:
    TARGET_ROLE_ID = 1384442724580720680

    if payload.message_id != TARGET_MESSAGE_ID:
        return

    if str(payload.emoji) != TARGET_EMOJI:
        return

    # 봇이 누른 리액션은 무시
    if payload.user_id == bot.user.id:
        return

    # 필요한 정보 불러오기
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    if member is None:
        return  # 멤버 정보 없을 경우 종료

    # ✅ 프로필 확인
    from utils.function import get_profile
    profile = get_profile(member.id)

    if profile is None:
        # 프로필이 없으면 아무 것도 하지 않음
        return

    # ✅ 역할 부여
    role = guild.get_role(TARGET_ROLE_ID)
    if role is not None and role not in member.roles:
        try:
            await member.add_roles(role, reason="✅ 체크로 인한 자동 역할 부여")
        except discord.Forbidden:
            print(f"❌ 권한 부족으로 역할 부여 실패: {member}")
        except Exception as e:
            print(f"❌ 역할 부여 중 오류 발생: {e}")


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

# 봇 토큰 입력
bot.run(get_token())

