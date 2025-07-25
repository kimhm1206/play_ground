import discord
from discord.ext import commands
from utils.function import get_balance, update_balance
from gametools import *

def register_game_commands(bot: commands.Bot):

    @bot.slash_command(
        name="홀짝주사위",
        description="주사위를 굴려 홀짝 맞추기 게임을 합니다!"
    )
    async def 홀짝주사위(
        ctx: discord.ApplicationContext,
        배팅금:discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)") # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)
        amount = 배팅금
        # ✅ 베팅 가능 여부 체크
        if amount < 500:
            await ctx.respond("❌ 베팅 금액은 500코인 이상이어야 합니다!", ephemeral=True)
            return

        if balance < amount:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}코인", ephemeral=True)
            return

        # ✅ 첫 번째 주사위 굴림
        first_roll = random.randint(1, 6)
        first_emoji = DICE_EMOJIS[first_roll]

        # ✅ 첫 번째 메시지 (홀/짝 버튼 표시)
        embed = discord.Embed(
            title="🎲 홀짝 주사위 게임",
            description=f"첫 번째 주사위: **{first_emoji}**\n\n홀짝을 선택하세요!",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {amount:,}코인")

        view = HolJjakButtonView(
            user_id=user_id,
            first_roll=first_roll,
            bet_amount=amount,
            balance=balance
        )
        await ctx.respond(embed=embed, view=view)
        
    @bot.slash_command(
        name="주사위",
        description="주사위 두 개의 합을 맞추는 게임!"
    )
    async def 주사위(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)") # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        # ✅ 베팅 가능 여부 체크
        if 배팅금 <= 500:
            await ctx.respond("❌ 베팅 금액은 500코인 이상이어야 합니다!", ephemeral=True)
            return

        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}코인", ephemeral=True)
            return

        # ✅ 배당 안내 자동 생성
        payout_lines = []
        for total in range(2, 13):
            house = get_payout_multiplier(total)
            payout_lines.append(
                f"{total:>2} → **x{house:.1f}**"
            )
        payout_text = "\n".join(payout_lines)

        embed = discord.Embed(
            title="🎲 주사위 합 맞추기 게임",
            description=(
                "두 개의 주사위를 굴린 합을 예상하세요!\n\n"
                f"💰 **배당률**\n"
                f"{payout_text}"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {배팅금:,}코인")

        # ✅ 버튼 뷰 생성
        view = DiceSumView(user_id, 배팅금, balance)
        await ctx.respond(embed=embed, view=view)
        
    @bot.slash_command(
    name="슬롯",
    description="슬롯머신을 돌립니다!"
)
    async def 슬롯(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)")  # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        # ✅ 베팅 가능 여부 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 베팅 금액은 최소 500코인 이상이어야 합니다!", ephemeral=True)
            return

        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}코인", ephemeral=True)
            return

        # ✅ 1~1000 난수 생성
        roll = random.randint(1, 1000)
        pattern = None
        payout_multiplier = 0
        result_text = ""
        reels = []

        # ✅ 패턴 결정
        if roll == 1:
            pattern = "잭팟"
        elif roll <= 3:
            pattern = "다이아"
        elif roll <= 6:
            pattern = "황금"
        elif roll <= 10:
            pattern = "과일3"
        elif roll <= 40:
            pattern = "과일모둠"
        elif roll == 41:
            pattern = "폭탄"
        elif roll <= 410:
            pattern = "두개매치"
        else:
            pattern = "꽝"

        # ✅ 패턴별 그림 + 배당 설정
        if pattern == "잭팟":
            reels = ["👑", "👑", "👑"]
            payout_multiplier = 50
            result_text = "🎉 **JACKPOT!** 👑👑👑 50배 당첨!"

        elif pattern == "다이아":
            reels = ["💎", "💎", "💎"]
            payout_multiplier = 30
            result_text = "💎 **보석 매치!** 다이아 3개 30배 당첨!"

        elif pattern == "황금":
            reels = ["🪙", "🪙", "🪙"]
            payout_multiplier = 20
            result_text = "🪙 **황금 매치!** 돈주머니 3개 20배 당첨!"

        elif pattern == "과일3":
            fruit = random.choice(["🍒", "🍋", "🍇"])
            reels = [fruit, fruit, fruit]
            payout_multiplier = 10
            result_text = f"{fruit} **과일 매치! 3개 10배!**"

        elif pattern == "과일모둠":
            reels = ["🍒", "🍋", "🍇"]
            random.shuffle(reels)
            payout_multiplier = 6
            result_text = "🍒🍋🍇 **과일 모둠 매치! 6배 당첨!**"

        elif pattern == "폭탄":
            reels = ["💣", "💣", "💣"]
            payout_multiplier = None  # 특수 처리
            result_text = "💥 **폭탄 등장! 보유 잔액 80% 차감!**"

        elif pattern == "두개매치":
            # 2개만 일치하는 랜덤 (전체 심볼 포함)
            base = random.choice(ALL_SYMBOLS)
            other = random.choice([s for s in ALL_SYMBOLS if s != base])
            reels = [base, base, other]
            random.shuffle(reels)
            payout_multiplier = 2
            result_text = "✅ **2개 일치! 2배!**"

        else:  # 기본 꽝
            # 전부 다 다른 심볼 (전체 심볼 포함)
            reels = random.sample(ALL_SYMBOLS, 3)
            payout_multiplier = 0
            result_text = "❌ **꽝... 다음 기회에!**"

        # ✅ 손익 계산
        if pattern == "폭탄":
            # 폭탄은 보유잔액 80% 차감
            loss = int(balance * 0.8)
            final_balance = balance - loss
            update_balance(user_id, -loss, "슬롯 폭탄 패널티")
            result_line = f"-{loss:,}코인 (잔액 80% 차감)"
            color = discord.Color.dark_red()

        elif payout_multiplier > 0:
            net_result = 배팅금 * (payout_multiplier - 1)
            final_balance = balance + net_result
            update_balance(user_id, net_result, f"슬롯 {pattern} 당첨")

            # 배당 표시 (2배 초과만)
            if payout_multiplier > 2:
                result_line = f"+{net_result:,}코인 (배당:{payout_multiplier})"
            else:
                result_line = f"+{net_result:,}코인"
            color = discord.Color.green()

        elif payout_multiplier == 0:  # 꽝
            net_result = -배팅금
            final_balance = balance - 배팅금
            update_balance(user_id, net_result, "슬롯 꽝")
            result_line = f"-{배팅금:,}코인"
            color = discord.Color.red()

        # ✅ 결과 Embed
        embed = discord.Embed(
            title="🎰 슬롯머신 결과",
            description=(
                f"{' | '.join(reels)}\n\n"
                f"{result_text}\n{result_line}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}코인")

        await ctx.respond(embed=embed)

    @bot.slash_command(
        name="블랙잭",
        description="블랙잭 라이트 버전 게임!"
    )
    async def 블랙잭(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅할 금액 (예: 5000)") # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        # ✅ 최소 베팅 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 최소 베팅 금액은 500코인입니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}코인", ephemeral=True)
            return

        # ✅ 초기 카드 배분
        player_cards = [draw_card(), draw_card()]
        dealer_cards = [draw_card(), draw_card()]

        player_score = calculate_score(player_cards)
        dealer_score = calculate_score(dealer_cards)

        # ✅ 즉시 블랙잭 (초기 21)
        if player_score == 21:
            # 블랙잭 → 2.5배
            payout = int(배팅금 * 2.7)
            update_balance(user_id, payout, "블랙잭 즉시 승리")
            embed = discord.Embed(
                title="🃏 블랙잭 결과",
                description=(
                    f"당신: {' '.join(player_cards)} (21)\n"
                    f"딜러: {' '.join(dealer_cards)} ({dealer_score})\n\n"
                    f"🎉 **BLACKJACK! 즉시 승리!**\n"
                    f"+{payout:,}코인 (배당 x2.7)"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"잔액: {balance + payout:,}코인")
            await ctx.respond(embed=embed)
            return

        # ✅ 기본 게임 시작 (히트/스탠드 선택)
        view = BlackjackView(user_id, 배팅금, balance, player_cards, dealer_cards)
        await ctx.respond(embed=view.build_embed(hide_dealer=True), view=view)

    @bot.slash_command(
    name="업다운",
    description="1~50 숫자를 맞추는 업다운 게임!"
)
    async def 업다운(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)")  # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        # ✅ 베팅 가능 여부 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 베팅 금액은 최소 500코인 이상이어야 합니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}코인", ephemeral=True)
            return

        # ✅ 정답 숫자 생성
        secret_number = random.randint(1, 50)
        attempts = 5

        # ✅ 초기 embed
        embed = discord.Embed(
            title="🎯 업다운 게임 시작!",
            description=(
                "1~50 중 하나의 숫자를 맞춰보세요!\n"
                f"총 **{attempts}번의 기회**가 있습니다.\n\n"
                "아래 버튼을 눌러 정답을 입력하세요."
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {배팅금:,}코인")

        # ✅ View 생성 (게임 상태 저장)
        view = UpDownView(
            user_id=user_id,
            secret=secret_number,
            attempts_left=attempts,
            bet_amount=배팅금,
            balance=balance
        )
        await ctx.respond(embed=embed, view=view)

    @bot.slash_command(
    name="경마",
    description="3마리 말 중 한 마리를 선택해 베팅하세요!"
)
    async def 경마(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)")  # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        # ✅ 베팅 가능 여부 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 베팅 금액은 최소 500코인 이상이어야 합니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}코인", ephemeral=True)
            return

        # ✅ 초기 안내 embed
        embed = discord.Embed(
            title="🏇 미니 경마 게임!",
            description=(
                "1번말, 2번말, 3번말 중 **한 마리**를 선택하세요!\n"
                "승리 시 **배당 3배 (순이익 +2배)**\n\n"
                "어떤 말이 1등으로 들어올까요? 🐎"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {배팅금:,}코인")

        # ✅ View 생성 (게임 상태 저장)
        view = HorseRaceView(
            user_id=user_id,
            bet_amount=배팅금,
            balance=balance
        )
        await ctx.respond(embed=embed, view=view)

    @bot.slash_command(
    name="동전던지기",
    description="앞면/뒷면을 맞추는 심플 게임!"
)
    async def 동전던지기(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)")  # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        # ✅ 베팅 가능 여부 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 베팅 금액은 최소 500코인 이상이어야 합니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}코인", ephemeral=True)
            return

        # ✅ 초기 안내 embed
        embed = discord.Embed(
            title="🪙 동전던지기",
            description=(
                "앞면과 뒷면 중 하나를 선택하세요!\n"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {배팅금:,}코인")

        # ✅ View 생성
        view = CoinFlipView(
            user_id=user_id,
            bet_amount=배팅금,
            balance=balance
        )
        await ctx.respond(embed=embed, view=view)

class DiceSumView(discord.ui.View):
    def __init__(self, user_id: int, bet_amount: int, balance: int):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.balance = balance

        # ✅ 2~12까지 버튼 생성
        for total in range(2, 13):
            self.add_item(DiceButton(total))

        # ✅ 마지막 row에 취소 버튼 추가
        self.add_item(CancelButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 이 게임은 당신의 것이 아닙니다!", ephemeral=True)
            return False
        return True

class DiceButton(discord.ui.Button):
    def __init__(self, total: int):
        # 버튼 row 자동 배치 (3개씩)
        super().__init__(label=str(total), style=discord.ButtonStyle.blurple, row=(total - 2) // 3)
        self.total = total

    async def callback(self, interaction: discord.Interaction):
        view: DiceSumView = self.view

        # ✅ 주사위 2개 굴림
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
        result_sum = roll1 + roll2

        # ✅ 배당률 (하우스 마진 적용)
        multiplier = get_payout_multiplier(self.total)

        # ✅ 승패 판정 → 순손익(net_result) 계산
        if result_sum == self.total:
            # 승리 → 순손익 = 베팅금 * (배당 - 1)
            net_result = int(view.bet_amount * (multiplier - 1))
            color = discord.Color.green()

            # 배당 표시 (2배 초과일 때만)
            if multiplier > 2:
                result_text = f"✅ 승리! +{net_result:,}코인 (배당:{multiplier:.1f})"
            else:
                result_text = f"✅ 승리! +{net_result:,}코인"

        else:
            # 패배 → 순손익 = -베팅금
            net_result = -view.bet_amount
            color = discord.Color.red()
            result_text = f"❌ 패배... -{view.bet_amount:,}코인 (결과: {result_sum})"

        # ✅ 최종 잔액 계산 & DB 1회 업데이트
        final_balance = view.balance + net_result
        update_balance(view.user_id, net_result, f"주사위 합 {self.total} 결과")

        # ✅ 결과 embed
        embed = discord.Embed(
            title="🎲 주사위 결과",
            description=(
                f"{DICE_EMOJIS[roll1]} + {DICE_EMOJIS[roll2]} = **{result_sum}**\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}코인")

        # ✅ 버튼 비활성화 후 결과 표시
        view.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=None)

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="취소", style=discord.ButtonStyle.red, row=4)

    async def callback(self, interaction: discord.Interaction):
        view: DiceSumView = self.view
        view.disable_all_items()

        embed = discord.Embed(
            title="❌ 베팅 취소됨",
            description="베팅이 취소되었습니다.",
            color=discord.Color.greyple()
        )
        embed.set_footer(text=f"잔액: {view.balance:,}코인")

        await interaction.response.edit_message(embed=embed, view=None)

class HolJjakButtonView(discord.ui.View):
    def __init__(self, user_id: int, first_roll: int, bet_amount: int, balance: int):
        super().__init__(timeout=20)
        self.user_id = user_id
        self.first_roll = first_roll
        self.bet_amount = bet_amount
        self.balance = balance

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # ✅ 본인만 클릭 가능
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 이 게임은 당신의 것이 아닙니다!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="홀", style=discord.ButtonStyle.green)
    async def 홀(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.resolve_game(interaction, choice="홀")

    @discord.ui.button(label="짝", style=discord.ButtonStyle.blurple)
    async def 짝(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.resolve_game(interaction, choice="짝")

    async def resolve_game(self, interaction: discord.Interaction, choice: str):
        # ✅ 두 번째 주사위 굴림
        second_roll = random.randint(1, 6)
        total = self.first_roll + second_roll
        second_emoji = DICE_EMOJIS[second_roll]

        # ✅ 홀짝 판정
        is_even = (total % 2 == 0)
        result_holjj = "짝" if is_even else "홀"

        # ✅ 승패 여부
        win = (result_holjj == choice)

        # ✅ 잔액 업데이트
        if win:
            update_balance(self.user_id, self.bet_amount)
            color = discord.Color.green()
            result_text = f"✅ 승리! +{self.bet_amount:,}코인"
            final_balance = self.balance + self.bet_amount
        else:
            update_balance(self.user_id, -self.bet_amount)
            color = discord.Color.red()
            result_text = f"❌ 패배... -{self.bet_amount:,}코인"
            final_balance = self.balance - self.bet_amount

        # ✅ 최종 결과 embed
        embed = discord.Embed(
            title="🎲 주사위 결과",
            description=(
                f"{DICE_EMOJIS[self.first_roll]} + {second_emoji} = **{total} ({result_holjj})**\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}코인")

        await interaction.response.edit_message(embed=embed, view=None)

class BlackjackView(discord.ui.View):
    def __init__(self, user_id, bet_amount, balance, player_cards, dealer_cards):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.balance = balance
        self.player_cards = player_cards
        self.dealer_cards = dealer_cards

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 이 게임은 당신의 것이 아닙니다!", ephemeral=True)
            return False
        return True

    def build_embed(self, hide_dealer=False):
        """현재 상태 Embed"""
        player_score = calculate_score(self.player_cards)
        dealer_score = calculate_score(self.dealer_cards)

        if hide_dealer:
            dealer_display = f"{self.dealer_cards[0]} [?]"
        else:
            dealer_display = f"{' '.join(self.dealer_cards)} (합계 {dealer_score})"

        embed = discord.Embed(
            title="🃏 블랙잭",
            description=(
                f"**당신:** {' '.join(self.player_cards)} (합계 {player_score})\n"
                f"**딜러:** {dealer_display}"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {self.bet_amount:,}코인")
        return embed

    @discord.ui.button(label="히트", style=discord.ButtonStyle.green)
    async def hit_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.player_cards.append(draw_card())
        score = calculate_score(self.player_cards)

        # ✅ 버스트 체크
        if score > 21:
            # 패배 → 순손실 -bet_amount
            net_result = -self.bet_amount
            final_balance = self.balance + net_result
            update_balance(self.user_id, net_result, "블랙잭 버스트 패배")

            embed = discord.Embed(
                title="🃏 블랙잭 결과",
                description=(
                    f"**당신:** {' '.join(self.player_cards)} (합계 {score})\n\n"
                    f"❌ **버스트! 21 초과로 패배...**\n"
                    f"-{self.bet_amount:,}코인"
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text=f"잔액: {final_balance:,}코인")
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            # 아직 진행 가능 → 다시 히트/스탠드 선택
            await interaction.response.edit_message(embed=self.build_embed(hide_dealer=True), view=self)

    @discord.ui.button(label="스탠드", style=discord.ButtonStyle.blurple)
    async def stand_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # ✅ 딜러 AI → 17 이상 될 때까지 히트
        while calculate_score(self.dealer_cards) < 17:
            self.dealer_cards.append(draw_card())

        player_score = calculate_score(self.player_cards)
        dealer_score = calculate_score(self.dealer_cards)

        # 기본 배당(2배)
        multiplier = 2.0

        # ✅ 승패 판정 → 순손익 계산
        if dealer_score > 21 or player_score > dealer_score:
            # 승리 → 순이익 +bet_amount
            net_result = self.bet_amount
            color = discord.Color.green()

            # 배당 표시 (기본 2배면 표시 안 함)
            if multiplier > 2:
                result_line = f"+{net_result:,}코인 (배당:{multiplier:.1f})"
            else:
                result_line = f"+{net_result:,}코인"

            result_text = f"✅ 승리! {result_line}"

        elif dealer_score == player_score:
            # 무승부 → 변화 없음
            net_result = 0
            color = discord.Color.greyple()
            result_text = f"🤝 무승부! 베팅금 환불"

        else:
            # 패배 → 순손실 -bet_amount
            net_result = -self.bet_amount
            color = discord.Color.red()
            result_text = f"❌ 패배... -{self.bet_amount:,}코인"

        # ✅ DB 1회 업데이트
        final_balance = self.balance + net_result
        update_balance(self.user_id, net_result, "블랙잭 결과")

        embed = discord.Embed(
            title="🃏 블랙잭 결과",
            description=(
                f"**당신:** {' '.join(self.player_cards)} (합계 {player_score})\n"
                f"**딜러:** {' '.join(self.dealer_cards)} (합계 {dealer_score})\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}코인")

        await interaction.response.edit_message(embed=embed, view=None)

class UpDownView(discord.ui.View):
    def __init__(self, user_id: int, secret: int, attempts_left: int, bet_amount: int, balance: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.secret = secret
        self.attempts_left = attempts_left
        self.bet_amount = bet_amount
        self.balance = balance

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 이 게임은 당신의 것이 아닙니다!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🎯 정답입력", style=discord.ButtonStyle.green)
    async def guess_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = UpDownGuessModal(
            secret=self.secret,
            view=self  # modal에서 다시 View 상태 업데이트
        )
        await interaction.response.send_modal(modal)

class UpDownGuessModal(discord.ui.Modal):
    def __init__(self, secret: int, view: UpDownView):
        super().__init__(title="🎯 업다운 정답 입력")
        self.secret = secret
        self.view = view

        self.answer_input = discord.ui.InputText(
            label="1~50 사이의 숫자를 입력하세요",
            placeholder="예: 27",
            required=True
        )
        self.add_item(self.answer_input)

    async def callback(self, interaction: discord.Interaction):
        guess_str = self.answer_input.value.strip()
        # ✅ 숫자 유효성 체크
        if not guess_str.isdigit():
            await interaction.response.send_message("❌ 숫자만 입력해주세요!", ephemeral=True)
            return

        guess = int(guess_str)
        if guess < 1 or guess > 50:
            await interaction.response.send_message("❌ 1~50 범위 내 숫자만 입력 가능합니다!", ephemeral=True)
            return

        # ✅ 정답 비교
        self.view.attempts_left -= 1  # 기회 차감

        if guess == self.secret:
            # ✅ 승리 → 순이익 +2배 (총 3배 반환)
            net_result = self.view.bet_amount * 2
            final_balance = self.view.balance + net_result
            update_balance(self.view.user_id, net_result, "업다운 승리")

            embed = discord.Embed(
                title="🎯 업다운 결과",
                description=(
                    f"정답: **{self.secret}**\n\n"
                    f"✅ 정답입니다! +{net_result:,}코인 (배당:3.0)"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"잔액: {final_balance:,}코인")

            # 버튼 비활성화
            self.view.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # ✅ 틀림 → 힌트 & 남은 기회 확인
        if guess < self.secret:
            hint = "정답은 더 **높습니다** ⬆️"
        else:
            hint = "정답은 더 **낮습니다** ⬇️"

        if self.view.attempts_left <= 0:
            # ✅ 기회 소진 → 패배
            net_result = -self.view.bet_amount
            final_balance = self.view.balance + net_result
            update_balance(self.view.user_id, net_result, "업다운 패배")

            embed = discord.Embed(
                title="🎯 업다운 결과",
                description=(
                    f"정답은 **{self.secret}** 이었습니다!\n\n"
                    f"❌ 패배... -{self.view.bet_amount:,}코인"
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text=f"잔액: {final_balance:,}코인")

            self.view.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=None)

        else:
            # ✅ 아직 기회 남음 → 힌트 주고 다시 버튼 유지
            embed = discord.Embed(
                title="🎯 업다운 게임",
                description=(
                    f"❌ **{guess}** 는 정답이 아닙니다!\n"
                    f"{hint}\n\n"
                    f"남은 기회: **{self.view.attempts_left}**회\n"
                    "정답 입력 버튼을 다시 눌러주세요."
                ),
                color=discord.Color.orange()
            )
            await interaction.response.edit_message(embed=embed, view=self.view)

class HorseRaceView(discord.ui.View):
    def __init__(self, user_id: int, bet_amount: int, balance: int):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.balance = balance

        # ✅ 버튼 3개 생성
        self.add_item(HorseButton("1번말🐎", 1))
        self.add_item(HorseButton("2번말🐎", 2))
        self.add_item(HorseButton("3번말🐎", 3))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 이 게임은 당신의 것이 아닙니다!", ephemeral=True)
            return False
        return True
    
class HorseButton(discord.ui.Button):
    def __init__(self, label: str, horse_number: int):
        super().__init__(label=label, style=discord.ButtonStyle.green)
        self.horse_number = horse_number

    async def callback(self, interaction: discord.Interaction):
        view: HorseRaceView = self.view

        # ✅ 랜덤 승마 결정
        winning_horse = random.choice([1, 2, 3])

        # ✅ 승패 판정
        if self.horse_number == winning_horse:
            # 승리 → 순이익 +2배
            net_result = view.bet_amount * 2
            color = discord.Color.green()
            result_text = f"✅ {winning_horse}번말이 1등으로 들어왔습니다!\n+{net_result:,}코인 (배당:3.0)"
        else:
            # 패배 → 순손실 -1배
            net_result = -view.bet_amount
            color = discord.Color.red()
            result_text = f"❌ 아쉽습니다! {winning_horse}번말이 승리했습니다.\n-{view.bet_amount:,}코인"

        # ✅ 최종 잔액 계산 & DB 1회 업데이트
        final_balance = view.balance + net_result
        update_balance(view.user_id, net_result, "미니 경마 결과")

        # ✅ 결과 embed
        embed = discord.Embed(
            title="🏇 미니 경마 결과",
            description=(
                f"**승리 말:** {winning_horse}번🐎\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}코인")

        # ✅ 버튼 비활성화 후 결과 표시
        view.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=None)

class CoinFlipView(discord.ui.View):
    def __init__(self, user_id: int, bet_amount: int, balance: int):
        super().__init__(timeout=20)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.balance = balance

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 이 게임은 당신의 것이 아닙니다!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="앞면 🪙", style=discord.ButtonStyle.green)
    async def heads_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.resolve_game(interaction, "앞면")

    @discord.ui.button(label="뒷면 🪙", style=discord.ButtonStyle.blurple)
    async def tails_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.resolve_game(interaction, "뒷면")

    async def resolve_game(self, interaction: discord.Interaction, choice: str):
        # ✅ 조작된 결과 (40%만 승리)
        coin_result = rigged_coin_result(choice)

        if choice == coin_result:
            # 승리 → 순이익 +bet_amount
            net_result = self.bet_amount
            final_balance = self.balance + net_result
            update_balance(self.user_id, net_result, "동전던지기 승리")
            color = discord.Color.green()
            result_text = f"✅ 맞췄습니다! +{net_result:,}코인"
        else:
            # 패배 → 순손실 -bet_amount
            net_result = -self.bet_amount
            final_balance = self.balance + net_result
            update_balance(self.user_id, net_result, "동전던지기 패배")
            color = discord.Color.red()
            result_text = f"❌ 틀렸습니다! -{self.bet_amount:,}코인"

        embed = discord.Embed(
            title="🪙 동전던지기 결과",
            description=(
                f"**결과:** {coin_result}\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}코인")

        self.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=None)