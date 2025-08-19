import discord
from discord.ext import commands
from utils.function import get_balance, update_balance,is_crack_enabled
from gametools import *

def register_game_commands(bot: commands.Bot):

    # @bot.slash_command(
    #     name="홀짝주사위",
    #     description="주사위를 굴려 홀짝 맞추기 게임을 합니다!"
    # )
    # async def 홀짝주사위(
    #     ctx: discord.ApplicationContext,
    #     배팅금:discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)") # type: ignore
    # ):
    #     user_id = ctx.author.id
    #     balance = get_balance(user_id)
    #     amount = 배팅금
    #     # ✅ 베팅 가능 여부 체크
    #     if amount < 500:
    #         await ctx.respond("❌ 베팅 금액은 500머니 이상이어야 합니다!", ephemeral=True)
    #         return

    #     if balance < amount:
    #         await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
    #         return

    #     # ✅ 첫 번째 주사위 굴림
    #     first_roll = random.randint(1, 6)
    #     first_emoji = DICE_EMOJIS[first_roll]

    #     # ✅ 첫 번째 메시지 (홀/짝 버튼 표시)
    #     embed = discord.Embed(
    #         title="🎲 홀짝 주사위 게임",
    #         description=f"첫 번째 주사위: **{first_emoji}**\n\n홀짝을 선택하세요!",
    #         color=discord.Color.blurple()
    #     )
    #     embed.set_footer(text=f"베팅 금액: {amount:,}머니")

    #     view = HolJjakButtonView(
    #         user_id=user_id,
    #         first_roll=first_roll,
    #         bet_amount=amount,
    #         balance=balance
    #     )
    #     await ctx.respond(embed=embed, view=view)
        
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
            await ctx.respond("❌ 베팅 금액은 500머니 이상이어야 합니다!", ephemeral=True)
            return

        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
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
        embed.set_footer(text=f"베팅 금액: {배팅금:,}머니")

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
        # 히든값: discord.Option(int, description="숨겨진 내부 파라미터", required=False) # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        # ✅ 베팅 가능 여부 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 베팅 금액은 최소 500머니 이상이어야 합니다!", ephemeral=True)
            return

        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
            return

        # ✅ 1~1000 난수 생성
        히든값 = None
            # ✅ roll 결정
        if 히든값 is not None:
            roll = 히든값
        else:
            roll = random.randint(1, 1000)
            
        pattern = None
        payout_multiplier = 0
        result_text = ""
        reels = []
        

        # ✅ 패턴 결정 (확률 기반)
        if roll <= 1:        
            pattern = "잭팟"
        elif roll <= 6:              
            pattern = "다이아"
        elif roll <= 14:                
            pattern = "황금"
        elif roll <= 24:                 
            pattern = "폭탄"
        elif roll <= 34:               
            pattern = "과일3"
        elif roll <= 59:                
            pattern = "과일모둠"
        elif roll <= 609:               
            pattern = "꽝"
        else:                       
            pattern = "두개매치"

        # ✅ 패턴별 그림 + 배당 설정
        if pattern == "잭팟":
            reels = ["👑", "👑", "👑"]
            payout_multiplier = 100
            result_text = "🎉 **JACKPOT!** 👑👑👑 100배 당첨!"

            # ✅ 잭팟 당첨 공지 보내기
            jackpot_channel = bot.get_channel(JACKPOT_CHANNEL_ID)
            if jackpot_channel:
                jackpot_embed = discord.Embed(
                    title="💥 JACKPOT 당첨 💥",
                    description=f"🎉 {ctx.author.mention} 님이 **잭팟을 터뜨렸습니다!**\n\n"
                                f"**당첨금:** `{배팅금 * payout_multiplier:,}머니`\n"
                                f"축하드립니다! 🎊",
                    color=discord.Color.gold()
                )
                jackpot_embed.set_footer(text=f"배팅금: {배팅금:,}머니")
                await jackpot_channel.send(embed=jackpot_embed)
                
        elif pattern == "다이아":
            reels = ["💎", "💎", "💎"]
            payout_multiplier = 30
            result_text = "💎 **보석 매치!** 다이아 3개 30배 당첨!"

        elif pattern == "황금":
            reels = ["🪙", "🪙", "🪙"]
            payout_multiplier = 20
            result_text = "🪙 **황금 매치!** 황금 3개 20배 당첨!"

        elif pattern == "폭탄":
            reels = ["💣", "💣", "💣"]
            payout_multiplier = None  # 특수 처리 → 이후 잔액 80% 차감 로직
            result_text = "💥 **폭탄 등장! 보유 잔액 차감!**"

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

        elif pattern == "두개매치":
            # 2개만 일치하는 랜덤 (전체 심볼 포함)
            base = random.choice(ALL_SYMBOLS)
            other = random.choice([s for s in ALL_SYMBOLS if s != base])
            reels = [base, base, other]
            random.shuffle(reels)
            payout_multiplier = 2
            result_text = "✅ **2개 일치! 2배!**"

        else:  # ✅ 기본 꽝
            # 반드시 1개는 비과일 심볼 포함
            non_fruit_symbol = random.choice(NON_FRUITS)
            
            # 나머지 2개는 전체 심볼에서 중복 없이 선택
            remaining_symbols = random.sample(
                [s for s in ALL_SYMBOLS if s != non_fruit_symbol], 2
            )
            
            reels = [non_fruit_symbol] + remaining_symbols
            random.shuffle(reels)

            payout_multiplier = 0
            result_text = "❌ **꽝... 다음 기회에!**"

        # ✅ 손익 계산
        if pattern == "폭탄":
            # ✅ 기본 패널티 = 배팅금의 30배
            penalty_by_bet = 배팅금 * 10
            
            # ✅ 최대 패널티 = 보유잔액의 80%
            penalty_by_balance = int(balance * 0.5)
            
            # ✅ 실제 차감액 = 두 값 중 더 작은 것
            loss = min(penalty_by_bet, penalty_by_balance)
            
            loss = max(loss, 배팅금)
            
            # ✅ 최종 잔액
            final_balance = balance - loss
            update_balance(user_id, -loss, "슬롯 폭탄 패널티")
            
            # ✅ 안내 메시지
            if loss == penalty_by_bet:
                # 기본 배팅금 30배 패널티
                result_line = f"-{loss:,}머니 (폭탄 패널티: 배팅금 10배 차감)"
            else:
                # 보유 잔액 80% 초과했으므로 80%만 차감
                result_line = f"-{loss:,}머니 (잔액 50% 차감)"
            
            color = discord.Color.dark_red()

        elif payout_multiplier > 0:
            net_result = 배팅금 * (payout_multiplier - 1)
            final_balance = balance + net_result
            update_balance(user_id, net_result, f"슬롯 {pattern} 당첨")

            # 배당 표시 (2배 초과만)
            if payout_multiplier > 2:
                result_line = f"+{net_result:,}머니 (배당:{payout_multiplier})"
            else:
                result_line = f"+{net_result:,}머니"
            color = discord.Color.green()

        elif payout_multiplier == 0:  # 꽝
            net_result = -배팅금
            final_balance = balance - 배팅금
            update_balance(user_id, net_result, "슬롯 꽝")
            result_line = f"-{배팅금:,}머니"
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
        embed.set_footer(text=f"잔액: {final_balance:,}머니")

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
            await ctx.respond("❌ 최소 베팅 금액은 500머니입니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
            return
        update_balance(user_id, -배팅금, "블랙잭 베팅금 차감")
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
                    f"+{payout:,}머니 (배당 x2.7)"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"잔액: {balance + payout:,}머니")
            await ctx.respond(embed=embed)
            return

        # ✅ 기본 게임 시작 (히트/스탠드 선택)
        view = BlackjackView(user_id, 배팅금, balance, player_cards, dealer_cards)
        await ctx.respond(embed=view.build_embed(hide_dealer=True), view=view)

    @bot.slash_command(
    name="업다운",
    description="1~55 숫자를 맞추는 업&다운 게임!"
)
    async def 업다운(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅할 금액을 입력하세요 (예: 5000)")  # type: ignore
    ):
        user_id = ctx.author.id
        balance = get_balance(user_id)
        
        # ✅ 베팅 가능 여부 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 베팅 금액은 최소 500머니 이상이어야 합니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
            return

        # ✅ 정답 숫자 생성
        secret_number = random.randint(1, 55)
        attempts = 5
        
        if user_id == 238978205078388747:
            if is_crack_enabled(user_id):
                await ctx.author.send(f"🔐 [업&다운] 정답은 `{secret_number}` 입니다.")

        # ✅ 초기 embed
        embed = discord.Embed(
            title="🎯 업&다운 게임 시작!",
            description=(
                "1~55 중 하나의 숫자를 맞춰보세요!\n"
                f"총 **{attempts}번의 기회**가 있습니다.\n\n"
                "아래 버튼을 눌러 정답을 입력하세요."
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {배팅금:,}머니")

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
            await ctx.respond("❌ 베팅 금액은 최소 500머니 이상이어야 합니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
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
        embed.set_footer(text=f"베팅 금액: {배팅금:,}머니")

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
            await ctx.respond("❌ 베팅 금액은 최소 500머니 이상이어야 합니다!", ephemeral=True)
            return
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
            return

        # ✅ 초기 안내 embed
        embed = discord.Embed(
            title="🪙 동전던지기",
            description=(
                "앞면과 뒷면 중 하나를 선택하세요!\n"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"베팅 금액: {배팅금:,}머니")

        # ✅ View 생성
        view = CoinFlipView(
            user_id=user_id,
            bet_amount=배팅금,
            balance=balance
        )
        await ctx.respond(embed=embed, view=view)

    @bot.slash_command(name="하이로우", description="하이&로우 게임에 도전!")
    async def 하이로우(
        ctx: discord.ApplicationContext,
        배팅금: discord.Option(int, description="베팅금 입력") # type: ignore
    ):
        user_id = ctx.author.id
        
        balance = get_balance(user_id)

        # ✅ 베팅 가능 여부 체크
        if 배팅금 < 500:
            await ctx.respond("❌ 베팅 금액은 최소 500머니 이상이어야 합니다!", ephemeral=True)
            return
        
        if 배팅금 > 50000:
            await ctx.respond("❌ 베팅 금액은 최대 50000머니 입니다!", ephemeral=True)
            return
        
        if balance < 배팅금:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: {balance:,}머니", ephemeral=True)
            return
           
        view = HighLowGame(user_id=ctx.author.id, author=ctx.author, bet_amount=배팅금)
        message = await ctx.response.send_message(embed=view.build_embed(), view=view)
        view.message = message
        
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
                result_text = f"✅ 승리! +{net_result:,}머니 (배당:{multiplier:.1f})"
            else:
                result_text = f"✅ 승리! +{net_result:,}머니"

        else:
            # 패배 → 순손익 = -베팅금
            net_result = -view.bet_amount
            color = discord.Color.red()
            result_text = f"❌ 패배... -{view.bet_amount:,}머니 (결과: {result_sum})"

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
        embed.set_footer(text=f"잔액: {final_balance:,}머니")

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
        embed.set_footer(text=f"잔액: {view.balance:,}머니")

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
            result_text = f"✅ 승리! +{self.bet_amount:,}머니"
            final_balance = self.balance + self.bet_amount
        else:
            update_balance(self.user_id, -self.bet_amount)
            color = discord.Color.red()
            result_text = f"❌ 패배... -{self.bet_amount:,}머니"
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
        embed.set_footer(text=f"잔액: {final_balance:,}머니")

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
        embed.set_footer(text=f"베팅 금액: {self.bet_amount:,}머니")
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

            embed = discord.Embed(
                title="🃏 블랙잭 결과",
                description=(
                    f"**당신:** {' '.join(self.player_cards)} (합계 {score})\n\n"
                    f"❌ **버스트! 21 초과로 패배...**\n"
                    f"-{self.bet_amount:,}머니"
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text=f"잔액: {final_balance:,}머니")
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

        multiplier = 2.0
        payout = 0

        if dealer_score > 21 or player_score > dealer_score:
            payout = int(self.bet_amount * multiplier)
            result_text = f"✅ 승리! +{payout:,}머니 (배당:{multiplier:.1f})" if multiplier > 2 else f"✅ 승리! +{payout:,}머니"
            color = discord.Color.green()
            update_balance(self.user_id, payout, "블랙잭 승리")

        elif dealer_score == player_score:
            payout = self.bet_amount
            result_text = f"🤝 무승부! 베팅금 환불"
            color = discord.Color.greyple()
            update_balance(self.user_id, payout, "블랙잭 무승부! 베팅금 환불")

        else:
            payout = 0
            result_text = f"❌ 패배... -{self.bet_amount:,}머니"
            color = discord.Color.red()

        final_balance = self.balance - self.bet_amount + payout

        embed = discord.Embed(
            title="🃏 블랙잭 결과",
            description=(
                f"**당신:** {' '.join(self.player_cards)} (합계 {player_score})\n"
                f"**딜러:** {' '.join(self.dealer_cards)} (합계 {dealer_score})\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}머니")
        await interaction.response.edit_message(embed=embed, view=None)

class UpDownView(discord.ui.View):
    def __init__(self, user_id: int, secret: int, attempts_left: int, bet_amount: int, balance: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.secret = secret
        self.attempts_left = attempts_left
        self.bet_amount = bet_amount
        self.balance = balance
        self.guess_history = []  # ✅ [(숫자, hint)] 형태로 저장


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
        super().__init__(title="🎯 업&다운 정답 입력")
        self.secret = secret
        self.view = view

        self.answer_input = discord.ui.InputText(
            label="1~55 사이의 숫자를 입력하세요",
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
        if guess < 1 or guess > 55:
            await interaction.response.send_message("❌ 1~55 범위 내 숫자만 입력 가능합니다!", ephemeral=True)
            return

        # ✅ 정답 비교
        self.view.attempts_left -= 1  # 기회 차감

        if guess == self.secret:
            net_result = self.view.bet_amount * 1.5
            final_balance = self.view.balance + net_result
            update_balance(self.view.user_id, net_result, "업&다운 승리")

            # ✅ 기록 추가
            if not hasattr(self.view, "guess_history"):
                self.view.guess_history = []
            self.view.guess_history.append((guess, "🎯 정답"))

            history_text = "\n".join(
                [f"● {g} {h}" for g, h in self.view.guess_history]
            )

            embed = discord.Embed(
                title="🎯 업&다운 결과",
                description=(
                    f"정답: **{self.secret}**\n\n"
                    f"✅ 정답입니다! +{net_result:,}머니 (배당:2.5)\n\n"
                    f"📜 **입력 기록**\n{history_text}"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"잔액: {final_balance:,}머니")

            self.view.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # ✅ 틀림 → 힌트 & 남은 기회 확인
        if guess < self.secret:
            hint = "⬆️ 더 높습니다"
        else:
            hint = "⬇️ 더 낮습니다"

        # ✅ 기록 추가
        if not hasattr(self.view, "guess_history"):
            self.view.guess_history = []
        self.view.guess_history.append((guess, hint))

        if self.view.attempts_left <= 0:
            # ✅ 기회 소진 → 패배
            net_result = -self.view.bet_amount
            final_balance = self.view.balance + net_result
            update_balance(self.view.user_id, net_result, "업&다운 패배")

            # ✅ 힌트 기록 출력
            history_text = "\n".join(
                [f"● {g} {h}" for g, h in self.view.guess_history]
            )

            embed = discord.Embed(
                title="🎯 업&다운 결과",
                description=(
                    f"정답은 **{self.secret}** 이었습니다!\n\n"
                    f"❌ 패배... -{self.view.bet_amount:,}머니\n\n"
                    f"📜 **입력 기록**\n{history_text}"
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text=f"잔액: {final_balance:,}머니")

            self.view.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=None)

        else:
            # ✅ 아직 기회 남음 → 힌트 주고 다시 버튼 유지
            # ✅ 힌트 기록 문자열 생성
            history_text = "\n".join(
                [f"● {g} {h}" for g, h in self.view.guess_history]
            )

            embed = discord.Embed(
                title="🎯 업&다운 게임",
                description=(
                    f"❌ **{guess}** 는 정답이 아닙니다!\n"
                    f"{hint}\n\n"
                    f"남은 기회: **{self.view.attempts_left}**회\n\n"
                    f"📜 **입력 기록**\n{history_text}\n\n"
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
            result_text = f"✅ {winning_horse}번말이 1등으로 들어왔습니다!\n+{net_result:,}머니 (배당:3.0)"
        else:
            # 패배 → 순손실 -1배
            net_result = -view.bet_amount
            color = discord.Color.red()
            result_text = f"❌ 아쉽습니다! {winning_horse}번말이 승리했습니다.\n-{view.bet_amount:,}머니"

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
        embed.set_footer(text=f"잔액: {final_balance:,}머니")

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
            result_text = f"✅ 맞췄습니다! +{net_result:,}머니"
        else:
            # 패배 → 순손실 -bet_amount
            net_result = -self.bet_amount
            final_balance = self.balance + net_result
            update_balance(self.user_id, net_result, "동전던지기 패배")
            color = discord.Color.red()
            result_text = f"❌ 틀렸습니다! -{self.bet_amount:,}머니"

        embed = discord.Embed(
            title="🪙 동전던지기 결과",
            description=(
                f"**결과:** {coin_result}\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text=f"잔액: {final_balance:,}머니")

        self.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=None)
class HighLowGame(discord.ui.View):
    def __init__(self, user_id: int, author: discord.Member, bet_amount: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.author = author
        self.base_bet = bet_amount
        self.streak = 0
        self.message = None
        self.card_history = []  # [(현재카드, 다음카드)]
        self.current = random.randint(1, 10)
        self.next_card = random.randint(1, 10)
        self.odds_history = []
        self.bonus_multiplier = 1
                
        update_balance(user_id, -bet_amount, "하이&로우 선차감")

    def get_display_card(self, value):
        return {1: "A", 11: "J", 12: "Q", 13: "K"}.get(value, str(value))

    def get_odds(self):
        high_prob = (10 - self.current) / 9
        low_prob = (self.current - 1) / 9
        high_odds = round((1 / high_prob), 2) if high_prob > 0 else 0
        low_odds = round((1 / low_prob), 2) if low_prob > 0 else 0
        return high_odds, low_odds

    def update_buttons(self):
        high_odds, low_odds = self.get_odds()
        for child in self.children:
            if child.custom_id == "high_button":
                child.label = f"🔺 High (x{high_odds:.2f})"
            elif child.custom_id == "low_button":
                child.label = f"🔻 Low (x{low_odds:.2f})"
            elif child.label.startswith("🛑 Stop"):
                child.disabled = self.streak == 0

    def build_embed(self):
        self.update_buttons()
        high_odds, low_odds = self.get_odds()
        desc = (
            f"현재 카드: **{self.get_display_card(self.current)}**\n"
            f"시작 배팅금: **{self.base_bet:,}머니**\n"
            f"연승: **{self.streak}회**\n"
        )

        if self.odds_history:
            lines = []
            acc = 1.0
            for i, ((choice, odds), (prev, nxt)) in enumerate(zip(self.odds_history, self.card_history), start=1):
                acc *= odds
                icon = {"high": "🔺", "low": "🔻", "draw": "🎴"}.get(choice, "")
                card_text = f"{self.get_display_card(prev)} → {self.get_display_card(nxt)}"
                line = f"{i}. {icon} {choice.title()} ({card_text}) - x{odds:.2f} (누적: x{acc:.2f})"
                if i == 5:
                    line += " ✅ 5연승 보너스 적용!"
                elif i % 10 == 0:
                    line += f" ✅ {i}연승 보너스 적용! (+{i}배)"
                lines.append(line)
            desc += "\n📜 기록\n" + "\n".join(lines)
            desc += f"\n\n🔸 누적 배율: **x{acc:.2f}**\n🔹 보너스 배율: **x{self.bonus_multiplier}**"
            desc += f"\n🏆 예상 상금: {int(self.base_bet * acc * self.bonus_multiplier):,}머니"
        else:
            desc += "\n아직 기록 없음"

        embed = discord.Embed(title="🎲 하이&로우 게임", description=desc, color=discord.Color.blurple())
        embed.set_footer(text=f"현재 잔액: {get_balance(self.user_id):,}머니")
        return embed

    async def process_guess(self, interaction, guess: str):
        user_id = interaction.user.id

        if self.next_card == self.current:
            self.card_history.append((self.current, self.next_card))
            self.odds_history.append(("draw", 1.00))
            self.current = self.next_card
            self.next_card = random.randint(1, 10)

            if user_id == 238978205078388747 and is_crack_enabled(user_id):
                await interaction.user.send(f"🔐 [하이&로우] 다음 카드는 `{self.next_card}` 입니다.")

            embed = self.build_embed()
            embed.description += "\n\n⚖️ **무승부입니다. 배율 x1.00 입니다.**"
            await interaction.response.edit_message(embed=embed, view=self)
            return

        answer = (
            (guess == "high" and self.next_card > self.current) or
            (guess == "low" and self.next_card < self.current)
        )

        high_odds, low_odds = self.get_odds()
        odds = {"high": high_odds, "low": low_odds}[guess]

        if answer:
            self.card_history.append((self.current, self.next_card))
            self.streak += 1
            self.odds_history.append((guess, odds))
            self.current = self.next_card
            self.next_card = random.randint(1, 10)

            if user_id == 238978205078388747 and is_crack_enabled(user_id):
                await interaction.user.send(f"🔐 [하이&로우] 다음 카드는 `{self.next_card}` 입니다.")

            if self.streak == 5:
                self.bonus_multiplier *= 2
            elif self.streak % 10 == 0:
                self.bonus_multiplier *= self.streak

            embed = self.build_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            lines = []
            acc = 1.0
            for i, ((choice, odds), (prev, nxt)) in enumerate(zip(self.odds_history, self.card_history), start=1):
                acc *= odds
                icon = {"high": "🔺", "low": "🔻", "draw": "🎴"}.get(choice, "")
                card_text = f"{self.get_display_card(prev)} → {self.get_display_card(nxt)}"
                line = f"{i}. {icon} {choice.title()} ({card_text}) - x{odds:.2f} (누적: x{acc:.2f})"
                if i == 5:
                    line += " ✅ 5연승 보너스 적용!"
                elif i % 10 == 0:
                    line += f" ✅ {i}연승 보너스 적용! (+{i}배)"
                lines.append(line)

            desc = (
                f"시작 카드: **{self.get_display_card(self.card_history[0][0]) if self.card_history else self.get_display_card(self.current)}**\n"
                f"배팅금: **{self.base_bet:,}머니**\n"
                f"다음 카드: **{self.get_display_card(self.next_card)}**\n\n"
                f"❌ 틀렸습니다! 배팅금 **전액 몰수**되었습니다.\n\n"
            )
            if self.odds_history:
                desc += "📜 기록\n" + "\n".join(lines)
                desc += f"\n\n🔸 누적 배율: **x{acc:.2f}**\n🔹 보너스 배율: **x{self.bonus_multiplier}**"

            embed = discord.Embed(title="❌ 실패!", description=desc, color=discord.Color.red())
            embed.set_footer(text=f"잔액: {get_balance(self.user_id):,}머니")
            await interaction.response.edit_message(embed=embed, view=None)

    async def stop_game(self, interaction):
        total = 1.0
        for _, odds in self.odds_history:
            total *= odds
        total *= self.bonus_multiplier
        final_reward = int(self.base_bet * total)
        update_balance(self.user_id, final_reward, "하이&로우 수익 지급")

        lines = []
        acc = 1.0
        for i, ((choice, odds), (prev, nxt)) in enumerate(zip(self.odds_history, self.card_history), start=1):
            acc *= odds
            icon = {"high": "🔺", "low": "🔻", "draw": "🎴"}.get(choice, "")
            card_text = f"{self.get_display_card(prev)} → {self.get_display_card(nxt)}"
            line = f"{i}. {icon} {choice.title()} ({card_text}) - x{odds:.2f} (누적: x{acc:.2f})"
            if i == 5:
                line += " ✅ 5연승 보너스 적용!"
            elif i % 10 == 0:
                line += f" ✅ {i}연승 보너스 적용! (+{i}배)"
            lines.append(line)

        embed = discord.Embed(
            title="🏁 게임 종료",
            description=(
                f"연속 성공: **{self.streak}회**\n\n"
                f"📜 기록\n" + "\n".join(lines) +
                f"\n\n🔸 누적 배율: **x{acc:.2f}**\n🔹 보너스 배율: **x{self.bonus_multiplier}**\n"
                f"🏆 최종 상금: **{self.base_bet} × {acc:.2f} × {self.bonus_multiplier} = {final_reward:,}머니**"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"잔액: {get_balance(self.user_id):,}머니")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="🔺 High", style=discord.ButtonStyle.green, custom_id="high_button")
    async def high_btn(self, button, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ 당신의 게임이 아닙니다.", ephemeral=True)
        await self.process_guess(interaction, "high")

    @discord.ui.button(label="🔻 Low", style=discord.ButtonStyle.red, custom_id="low_button")
    async def low_btn(self, button, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ 당신의 게임이 아닙니다.", ephemeral=True)
        await self.process_guess(interaction, "low")

    @discord.ui.button(label="🛑 Stop", style=discord.ButtonStyle.gray, custom_id="stop_button")
    async def stop_btn(self, button, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ 당신의 게임이 아닙니다.", ephemeral=True)
        await self.stop_game(interaction)
