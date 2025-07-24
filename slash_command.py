import discord
import requests
from discord.ext import commands
from utils.function import get_profile , save_anonymous_log, get_connection

DAILY_LIMIT = 360
LEVEL_UNIT = 30
WEBHOOK_URL = "https://discord.com/api/webhooks/1384529950782263408/2mIMMUVH790rezgL432Q4GWyssoL9WcBZxP9lrJNvtEfmRHrxoIPEYABnM_Gar-ljGg8"
TARGET_CHANNEL_ID = 1384527567280930859
# 메인 봇 객체가 있는 곳에서 불러올 예정이므로 Cog 사용 X
def register_slash_commands(bot: commands.Bot):
    @bot.slash_command(name="프로필", description="해당 유저의 프로필을 확인합니다.")
    async def show_profile(
        ctx: discord.ApplicationContext,
        member: discord.Member
    ):
        profile = get_profile(member.id)
        if not profile:
            await ctx.respond("❌ 해당 유저의 프로필이 등록되어 있지 않습니다!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📘 {member.display_name} 님의 프로필",
            color=discord.Color.blurple()
        )
        mbti_value = profile['mbti']
        if mbti_value and mbti_value.lower() != "미공개":
            mbti_display = mbti_value.upper()
        else:
            mbti_display = mbti_value or "미공개"

        embed.add_field(name="MBTI", value=f"**{mbti_display}**", inline=False)
        embed.add_field(name="스팀 친구 코드", value=f"**{profile['code'] or '미공개'}**", inline=True)
        embed.add_field(name="자주 하는 게임", value=f"**{profile['favorite_games'] or '없음'}**", inline=False)
        embed.add_field(name="하고 싶은 게임", value=f"**{profile['wanted_games'] or '없음'}**", inline=False)
        embed.add_field(name="가입 경로", value=f"**{profile['referral']}**", inline=False)
        embed.add_field(name="한줄 소개", value=f"``{profile['bio']}``", inline=False)
        

        # embed.set_footer(text="프로필은 언제든지 수정할 수 있어요 ✨")

        await ctx.respond(embed=embed)
        
    
    @bot.slash_command(
        name="익명대화",
        description="익명으로 익명대화방에 메시지를 보냅니다."
    )
    async def anonymous_message(
        ctx: discord.ApplicationContext,
        text: discord.Option(str, "전달할 메시지를 입력하세요")  # type: ignore
    ):
        # ✅ DB 저장
        nickname = ctx.user.nick or ctx.user.name
        user_id = ctx.user.id
        try:
            save_anonymous_log(user_id=user_id, nickname=nickname, message=text)
        except Exception as e:
            print("DB 저장 실패:", e)

        try:
            channel = ctx.guild.get_channel(1384527567280930859)
            if channel:
                await channel.send(f"\n{text}")
            else:
                await ctx.respond("❌ 채널을 찾을 수 없어요!", ephemeral=True, delete_after=3)
                return
        except Exception as e:
            await ctx.respond("❌ 익명 메시지 전송에 실패했어요!", ephemeral=True, delete_after=3)
            print("메시지 전송 오류:", e)
            return

        # ✅ 유저에게는 삭제되는 응답
        await ctx.respond("✅ 익명 메시지를 보냈습니다.", ephemeral=True, delete_after=1)

    @bot.slash_command(
            name="리더보드",
            description="해당 유저의 레벨과 전체 순위를 확인합니다.",
            default_member_permissions=discord.Permissions(administrator=True)
        )
    async def check_rank(
        ctx: discord.ApplicationContext,
        member: discord.Member
    ):
        user_id = member.id

        # DB에서 순위 정보 조회
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, level, total_minutes
            FROM voice_leaderboard
            ORDER BY level DESC, total_minutes DESC
        """)
        all_users = cur.fetchall()
        conn.close()

        # 순위 찾기
        rank = None
        for i, (uid, level, total) in enumerate(all_users, start=1):
            if uid == user_id:
                percent = int((total / (level * LEVEL_UNIT)) * 100) if level > 0 else 0
                rank = i
                break

        if rank:
            await ctx.respond(
                f"🎖️ {member.nick or member.name} 순위는 **{rank}위**입니다!\n"
                f"📊 레벨 **{level}**, 경험치 **{percent}%** 진행 중이에요!"
            ,ephemeral=True)
        else:
            await ctx.respond(
                "🔍 아직 순위에 등록되지 않았어요.\n(음성 채널에서 1분 이상 활동해야 등록됩니다!)"
            ,ephemeral=True)
            
            