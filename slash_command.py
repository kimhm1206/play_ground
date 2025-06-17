import discord
import requests
from discord.ext import commands
from utils.function import get_profile , save_anonymous_log


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
        embed.add_field(name="자주 하는 게임", value=f"**{profile['favorite_games'] or '없음'}**", inline=False)
        embed.add_field(name="하고 싶은 게임", value=f"**{profile['wanted_games'] or '없음'}**", inline=False)
        embed.add_field(name="가입 경로", value=f"**{profile['referral']}**", inline=False)
        embed.add_field(name="한줄 소개", value=f"```{profile['bio']}```", inline=False)

        # embed.set_footer(text="프로필은 언제든지 수정할 수 있어요 ✨")

        await ctx.respond(embed=embed)
        
    
    @bot.slash_command(
        name="익명대화",
        description="익명으로 뒤뜰에 메시지를 보냅니다."
    )
    async def anonymous_message(
        ctx: discord.ApplicationContext,
        text: discord.Option(str, "전달할 메시지를 입력하세요")  # type: ignore
    ):

        # ✅ DB 저장
        nickname = ctx.user.nick
        user_id = ctx.user.id
        try:
            save_anonymous_log(user_id=user_id, nickname=nickname, message=text)
        except Exception as e:
            print("DB 저장 실패:", e)

        # ✅ 익명 메시지 웹훅 전송
        try:
            requests.post(WEBHOOK_URL, json={"content": f"\n{text}"})
        except Exception as e:
            await ctx.respond("❌ 익명 메시지 전송에 실패했어요!", ephemeral=True, delete_after=3)
            print("웹훅 오류:", e)
            return

        # ✅ 유저에게는 삭제되는 응답
        await ctx.respond("✅ 익명 메시지를 보냈습니다.", ephemeral=True, delete_after=1)
