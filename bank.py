import discord
from utils.function import get_bank_info,loan_money,has_signed_loan_terms,sign_loan_terms,repay_loan # DB 조회 함수


class BankView(discord.ui.View):
    def __init__(self, user_id: int, remaining_limit: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.remaining_limit = remaining_limit

    @discord.ui.button(label="💳 대출하기", style=discord.ButtonStyle.success, row=1)
    async def loan_button(self, button, interaction):
        if not has_signed_loan_terms(self.user_id):
            await show_loan_terms(interaction, self.user_id)
            return

        await interaction.response.edit_message(
            content=f"💳 대출 메뉴\n남은 대출 가능 금액: {self.remaining_limit:,}머니\n얼마를 대출할까요?",
            view=LoanView(self.user_id, self.remaining_limit),
            embed=None
        )

    @discord.ui.button(label="💸 상환하기", style=discord.ButtonStyle.secondary, row=1)
    async def repay_button(self, button, interaction):
        # ✅ 유저 대출 목록 조회
        info = get_bank_info(self.user_id)
        if not info["loans"]:
            await interaction.response.edit_message(
                content="✅ 현재 상환할 대출이 없습니다.",
                view=None
            )
            return

        embed = discord.Embed(
            title="💸 상환할 대출 선택",
            description="상환할 대출을 선택해주세요.",
            color=discord.Color.blue()
        )
        view = RepaySelectView(self.user_id, info["loans"])
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📜 대출 설명서", style=discord.ButtonStyle.primary, row=2)
    async def terms_button(self, button, interaction):
        await show_loan_terms(interaction, self.user_id)

    @discord.ui.button(label="❌ 은행 종료", style=discord.ButtonStyle.danger, row=4)
    async def exit_button(self, button, interaction):
        await interaction.response.edit_message(
            content="✅ 은행 이용이 종료되었습니다. 이용해주셔서 감사합니다!",
            embed=None,
            view=None
        )
        await interaction.delete_original_response(delay=5)

async def open_bank_menu(interaction: discord.Interaction):
    """은행 메인 메뉴 열기"""
    user_id = interaction.user.id
    info = get_bank_info(user_id)

    # ✅ 메인 은행 Embed 생성
    embed = discord.Embed(
        title="🏦 PG 카지노 은행",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="💳 총 대출 한도",
        value=f"{info['loan_limit']:,}머니 (레벨 {info['level']})",
        inline=False
    )
    embed.add_field(
        name="💰 현재 사용",
        value=f"{info['total_loans']:,}머니",
        inline=False
    )

        # ✅ 대출 내역 표시
    if info["loans"]:
        desc = ""
        for loan in info["loans"]:
            status_emoji = "✅" if loan["status"] == "NORMAL" else "⚠️"
            desc += (
                f"[#{loan['loan_id']}] "
                f"대출금: {loan['amount']:,}머니 / 남은 상환금: {loan['remaining']:,}머니 "
                f"→ {loan['due_date']} {status_emoji}\n"
            )
        embed.add_field(name="📅 대출 내역", value=desc, inline=False)
    else:
        embed.add_field(name="📅 대출 내역", value="대출 내역이 없습니다.", inline=False)

    # ✅ 연체 상태 안내
    if info["overdue"]:
        embed.add_field(
            name="⚠️ 연체 안내",
            value="연체 상태입니다! 오늘 첫 카지노 이용 시 강제 상환됩니다.",
            inline=False
        )

    embed.set_footer(text=f"잔액 : {info['balance']:,}머니")

    view = BankView(user_id,info["remaining_limit"])
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class LoanAmountModal(discord.ui.Modal):
    def __init__(self, user_id: int, remaining_limit: int):
        super().__init__(title="💳 대출하기")
        self.user_id = user_id
        self.remaining_limit = remaining_limit

        self.amount_input = discord.ui.InputText(
            label=f"얼마를 대출할까요? (남은 한도: {remaining_limit:,}머니)",
            placeholder="예: 50000 (숫자만 입력)",
            required=True
        )
        self.add_item(self.amount_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            if amount <= 0:
                await interaction.response.edit_message(
                    content="❌ 0머니 이하 금액은 대출할 수 없습니다.",
                    view=None
                )
                return

            result = loan_money(self.user_id, amount)

            # ✅ 결과 Embed 생성
            embed = discord.Embed(
                title="💳 대출 결과",
                description=result["message"],
                color=discord.Color.gold() if result["success"] else discord.Color.red()
            )
            embed.set_footer(text=f"잔액 : {result['balance']:,}머니")

            # ✅ 기존 메시지 수정 (edit_message)
            await interaction.response.edit_message(embed=embed, view=None)

        except ValueError:
            await interaction.response.edit_message(
                content="❌ 올바른 숫자를 입력하세요!",
                view=None
            )

class LoanView(discord.ui.View):
    def __init__(self, user_id: int, remaining_limit: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.remaining_limit = remaining_limit

    @discord.ui.button(label="💳 대출 금액 입력", style=discord.ButtonStyle.success)
    async def enter_amount(self, button, interaction):
        await interaction.response.send_modal(LoanAmountModal(self.user_id, self.remaining_limit))

class LoanTermsView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="✅ 내용 확인 및 동의", style=discord.ButtonStyle.success)
    async def confirm_terms(self, button, interaction):
        sign_loan_terms(self.user_id)
        await interaction.response.edit_message(
            content="✅ 대출 설명서를 확인하고 동의하셨습니다.\n이제 대출 메뉴를 이용할 수 있습니다.",
            embed=None,
            view=None
        )
        
async def show_loan_terms(interaction: discord.Interaction, user_id: int):
    embed = discord.Embed(
        title="📜 PG 카지노 대출 설명서",
        description=(
            "1️⃣ 대출 한도는 **레벨 × 10,000머니**입니다.\n"
            "2️⃣ 대출 시 **이자율 10%**, 14일 내 상환 필요\n"
            "3️⃣ **대출 중 상점 이용 불가**\n"
            "4️⃣ **14일 초과 시 연체**, 추가 이자 +10% 부과\n"
            "5️⃣ 연체 기간이 **7일을 넘으면 장기 연체**로 전환됩니다.\n"
            "6️⃣ 장기 연체 상태에서는 매일 00시 강제 상환됩니다.\n"
            "7️⃣ 장기 연체 중에도 **게임/돈줘는 가능**합니다.\n\n"
            "✅ 위 내용을 이해하고 동의해야 대출이 가능합니다."
        ),
        color=discord.Color.orange()
    )
    view = LoanTermsView(user_id)
    await interaction.response.edit_message(embed=embed, view=view)
    
class RepaySelectView(discord.ui.View):
    def __init__(self, user_id: int, loans: list):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.loans = loans

        # ✅ 선택 메뉴 생성 (최대 25개 제한)
        options = []
        for loan in loans[:25]:
            label = f"#{loan['loan_id']} | {loan['amount']:,}머니 남은 금액:{loan['remaining']:,}머니"
            desc = f"{loan['due_date']} ({loan['status']})"
            options.append(discord.SelectOption(label=label, description=desc, value=str(loan['loan_id'])))

        self.add_item(RepaySelectMenu(user_id, options))
        
class RepaySelectMenu(discord.ui.Select):
    def __init__(self, user_id: int, options: list):
        super().__init__(placeholder="상환할 대출을 선택하세요", options=options)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        loan_id = int(self.values[0])
        await interaction.response.send_modal(RepayAmountModal(self.user_id, loan_id))
        
class RepayAmountModal(discord.ui.Modal):
    def __init__(self, user_id: int, loan_id: int):
        super().__init__(title="💸 상환 금액 입력")
        self.user_id = user_id
        self.loan_id = loan_id

        self.repay_input = discord.ui.InputText(
            label="얼마를 상환하시겠습니까?",
            placeholder="예: 50000 (숫자만 입력)",
            required=True
        )
        self.add_item(self.repay_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            repay_amount = int(self.repay_input.value)
            if repay_amount <= 0:
                await interaction.response.edit_message(
                    content="❌ 0머니 이하 금액은 상환할 수 없습니다.",
                    view=None
                )
                return

            result = repay_loan(self.user_id, self.loan_id, repay_amount)

            embed = discord.Embed(
                title="💸 상환 결과",
                description=result["message"],
                color=discord.Color.green() if result["success"] else discord.Color.red()
            )
            embed.set_footer(text=f"잔액 : {result['balance']:,}머니")
            await interaction.response.edit_message(embed=embed, view=None)

        except ValueError:
            await interaction.response.edit_message(
                content="❌ 올바른 숫자를 입력하세요!",
                view=None
            )
