import discord

CHANNEL_ID = 1311793820857270292  # 카지노 로비 채널 ID

class CasinoLobbyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💸 돈줘", style=discord.ButtonStyle.success, custom_id="casino_money")
    async def money_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ {interaction.user.mention} 님에게 **1,000 코인**이 지급되었습니다! (테스트용)",
            ephemeral=True
        )

    @discord.ui.button(label="💳 대출", style=discord.ButtonStyle.primary, custom_id="casino_loan")
    async def loan_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"💳 {interaction.user.mention} 님, **대출 시스템**은 아직 준비 중입니다!",
            ephemeral=True
        )

    @discord.ui.button(label="🎮 게임 설명", style=discord.ButtonStyle.secondary, custom_id="casino_help")
    async def help_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎲 **카지노 게임 가이드**",
            description=(
                "🎯 **게임 목록**\n"
                "・홀짝 게임 → **50% 승률, 2배 배당**\n"
                "・주사위 합 맞추기 → **확률별 정배율**\n"
                "・슬롯머신 → **잭팟 가능!**\n\n"
                "💡 **명령어 예시:** `/casino_play`"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def send_casino_lobby(bot: discord.Client):
    """카지노 로비 고정 메시지를 보내는 함수"""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    # 기존 봇 메시지 삭제 (중복 방지)
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            await msg.delete()

    # ✨ 더 고급스러운 카지노 로비 Embed
    embed = discord.Embed(
        title="✨ **플그 카지노 로비** ✨",
        description=(
            "💎 **어서오세요!**\n"
            "행운과 스릴이 가득한 **럭셔리 카지노**에 오신 걸 환영합니다!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 **이용 방법**\n"
            "💸 **돈줘** → 기본 자금 받기\n"
            "💳 **대출** → 부족하면 빌리기\n"
            "📖 **게임 설명** → 규칙 확인하기\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🪙 **오늘도 행운이 함께하길!**"
        ),
        color=discord.Color.from_rgb(255, 215, 0)  # 금색 느낌
    )

    # 푸터 + 썸네일 추가 (카지노 느낌)
    embed.set_footer(text="🎰 카지노에서 행운을 시험해보세요!")
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1525/1525334.png")  # 슬롯머신 아이콘

    # 버튼 추가 (게임하기 제거됨)
    view = CasinoLobbyView()

    msg = await channel.send(embed=embed, view=view)
