import discord
from utils.function import give_daily_money,get_top_balances
from bank import open_bank_menu
class CasinoLobbyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💸 일당", style=discord.ButtonStyle.success)
    async def donzoo_button(self, button, interaction):
        user_id = interaction.user.id
        result = give_daily_money(user_id)

        # ✅ 임베드 생성
        embed = discord.Embed(
            title="💸 플그 카지노 일당 지급",
            description=result["message"],
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"잔액 : {result['balance']:,}원")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏦 은행", style=discord.ButtonStyle.primary)
    async def bank_button(self, button, interaction):
        await open_bank_menu(interaction)  # ✅ 은행 메뉴 호출

    @discord.ui.button(label="🛒 상점", style=discord.ButtonStyle.secondary)
    async def shop_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("🛒 **상점 메뉴**는 준비 중입니다!", ephemeral=True)

    @discord.ui.button(label="🎮 게임설명", style=discord.ButtonStyle.secondary)
    async def game_info_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 플그 카지노 게임 가이드",
            description="플그 카지노에서 즐길 수 있는 게임 목록과 설명입니다!\n**게임은 아래 카지노 채널에서 이용해주세요!**",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🎲 홀짝주사위",
            value="주사위 2개 합의 홀/짝을 맞추면 승리!\n`/홀짝주사위 [금액]`\n**배당 2배 (순이익+1배)**",
            inline=False
        )
        embed.add_field(
            name="🎲 주사위 합 맞추기",
            value="주사위 2개 합이 특정 숫자가 될지 맞추는 게임!\n`/주사위 [금액]`\n**배당: 합 확률에 따라 5배~30배!**",
            inline=False
        )
        embed.add_field(
            name="🎰 슬롯머신",
            value="2개 이상 심볼이 맞으면 당첨!\n`/슬롯 [금액]`\n2개=2배, 3개=20배, 잭팟👑=50배!",
            inline=False
        )
        embed.add_field(
            name="🃏 블랙잭 라이트",
            value="21에 가까운 숫자로 딜러보다 높으면 승리!\n`/블랙잭 [금액]`\n일반 승리 2배, 블랙잭(21) 3배!",
            inline=False
        )
        embed.add_field(
            name="🎯 업다운",
            value="1~50 숫자를 5번 안에 맞추면 3배!\n`/업다운 [금액]`",
            inline=False
        )
        embed.add_field(
            name="🏇 미니 경마",
            value="3마리 말 중 1등 할 말을 선택!\n`/경마 [금액]`\n승리 시 **3배 (순이익+2배)**",
            inline=False
        )
        embed.add_field(
            name="🪙 동전던지기",
            value="앞면/뒷면을 맞추는 심플 게임!\n`/동전던지기 [금액]`\n**승리 시 배당 2배 (순이익+1배)**",
            inline=False
        )
        embed.add_field(
            name="✅ 지갑 확인",
            value="본인 지갑의 잔액을 확인 합니다.\n`/지갑` , `/잔액`",
            inline=False
        )

        embed.set_footer(text="베팅은 최소 500원부터 가능합니다!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📊 랭킹", style=discord.ButtonStyle.secondary)
    async def ranking_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # ✅ TOP5 조회
        top_users = get_top_balances(limit=5)  # DB에서 [(user_id, balance), ...]

        if not top_users:
            await interaction.response.send_message("📊 랭킹 데이터가 없습니다!", ephemeral=True)
            return

        embed = discord.Embed(
            title="📊 플그 카지노 랭킹 TOP 5",
            description="현재 **잔액 기준** 상위 5명입니다!",
            color=discord.Color.gold()
        )

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        for idx, (uid, bal) in enumerate(top_users):
            member = interaction.guild.get_member(uid)
            name = member.nick or member.display_name if member else f"Unknown({uid})"
            embed.add_field(
                name=f"{medals[idx]} {name}",
                value=f"💰 {bal:,}원",
                inline=False
            )

        embed.set_footer(text="당신도 상위 랭커에 도전해보세요!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def send_casino_lobby(bot: discord.Client):
    channel = bot.get_channel(1396954107381551178)
    if not channel:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    # 기존 메시지 정리 (필요하면)
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            await msg.delete()

    embed = discord.Embed(
    title="🎰 **플그 카지노 로비**",
    description=(
        "💎 **어서오세요! 플그 카지노입니다.**\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💸 **일당** → 하루 일당 받기\n"
        "🏦 **은행** → 대출 / 상환 관리\n"
        "🛒 **상점** → (준비중)\n"
        "🎮 **게임설명** → 게임 목록 & 배당 안내\n"
        "📊 **랭킹** → 상위 랭커 확인\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🪙 오늘도 **행운**이 함께하길 바랍니다!\n"
        "🎯 **상점, 게임, 송금 기능은 계속 업데이트 예정!**"
    ),
    color=discord.Color.gold()
    )
    embed.set_footer(text="✨ Developed by 배액호오")
    view = CasinoLobbyView()
    await channel.send(embed=embed, view=view)
    print("✅ 플그 카지노 로비 생성 완료!")
