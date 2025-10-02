import discord
from discord.ext import commands
from discord.utils import get
from discord.ui import View, Button
from datetime import datetime
from utils.function import log_ticket  # DB 저장 함수 호출용

CATEGORY_ID = 1384419721532801034
CHANNEL_ID = 1384416861671653446
STAFF_ROLE_ID = 1384468243552534684
ADMIN_ROLE_ID = 1384411575158575206

class InquiryTypeView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def setup_ticket(self, interaction: discord.Interaction, inquiry_type: str):
        embed = discord.Embed(
            title=f"{inquiry_type} 문의 접수",
            description=(
                "이 문의를 누구에게 전달할까요?\n\n"
                "🔸 **전체 스탭**: 스탭과 관리자 모두에게 공유됩니다.\n"
                "🔹 **관리자만**: 관리자에게만 전달됩니다."
            ),
            color=discord.Color.blurple()
        )
        view = InquiryTargetView(self.bot, inquiry_type)
        if not interaction.response.is_done():
            await interaction.response.defer()  # 반응을 미리 잠금
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📢 사건 신고", style=discord.ButtonStyle.danger)
    async def report_button(self, button: Button, interaction: discord.Interaction):
        await self.setup_ticket(interaction, "사건 신고")

    @discord.ui.button(label="📘 문의&건의", style=discord.ButtonStyle.primary)
    async def rule_button(self, button: Button, interaction: discord.Interaction):
        await self.setup_ticket(interaction, "문의&건의")

    @discord.ui.button(label="💡 기능 문의", style=discord.ButtonStyle.success)
    async def feature_button(self, button: Button, interaction: discord.Interaction):
        # 기능 문의는 관리자에게만 전달되므로 바로 확인 단계로 이동
        if not interaction.response.is_done():
            await interaction.response.defer()  # 반응을 미리 잠금
        await interaction.followup.send(
            embed=discord.Embed(
                title="💡 기능 문의",
                description=(
                    "디스코드 기능 또는 봇 관련 문의를 시작할까요?\n"
                    "💬 아래 버튼을 눌러 진행해주세요."
                ),
                color=discord.Color.green()
            ),
            view=InquiryConfirmView(self.bot, "기능 문의", target="관리자만"),
            ephemeral=True
        )

class InquiryTargetView(View):
    def __init__(self, bot: commands.Bot, inquiry_type: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.inquiry_type = inquiry_type

    @discord.ui.button(label="전체 스탭", style=discord.ButtonStyle.secondary)
    async def staff_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{self.inquiry_type} 접수 준비 완료",
                description="🎫 문의를 시작하시려면 아래 확인 버튼을 눌러주세요!",
                color=discord.Color.blue()
            ),
            view=InquiryConfirmView(self.bot, self.inquiry_type, target="전체 스탭")
        )

    @discord.ui.button(label="관리자만", style=discord.ButtonStyle.primary)
    async def admin_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{self.inquiry_type} 접수 준비 완료",
                description="🎫 문의를 시작하시려면 아래 확인 버튼을 눌러주세요!",
                color=discord.Color.blurple()
            ),
            view=InquiryConfirmView(self.bot, self.inquiry_type, target="관리자만")
        )

    @discord.ui.button(label="❌ 취소", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(
                description="🚫 문의가 취소되었습니다.",
                color=discord.Color.red()
            ),
            view=None,delete_after=5
        )

class InquiryConfirmView(View):
    def __init__(self, bot: commands.Bot, inquiry_type: str, target: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.inquiry_type = inquiry_type
        self.target = target

    @discord.ui.button(label="✅ 확인", style=discord.ButtonStyle.success)
    async def confirm_button(self, button: Button, interaction: discord.Interaction):
        guild = interaction.guild
        category = get(guild.categories, id=CATEGORY_ID)
        member = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        # 역할 접근 권한 부여
        if self.target == "전체 스탭":
            overwrites[guild.get_role(STAFF_ROLE_ID)] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            overwrites[guild.get_role(ADMIN_ROLE_ID)] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        else:  # 관리자만
            overwrites[guild.get_role(ADMIN_ROLE_ID)] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # 스레드 채널 생성
        timestamp = datetime.now().strftime("%m%d%H%M%S")
        thread_name = f"{self.inquiry_type.replace(' ', '-')}-{member.name}-{timestamp}"
        thread = await guild.create_text_channel(name=thread_name, category=category, overwrites=overwrites)

        # 로그 저장
        log_ticket(
            user_id=member.id,
            nickname=member.display_name,
            category=self.inquiry_type,
            target=self.target,
            thread_id=thread.id
        )
        
        mention_roles = []
        if self.target == "전체 스탭":
            mention_roles = [guild.get_role(STAFF_ROLE_ID), guild.get_role(ADMIN_ROLE_ID)]
        elif self.target == "관리자만":
            mention_roles = [guild.get_role(ADMIN_ROLE_ID)]

        mention_str = ' '.join(role.mention for role in mention_roles if role)

        start_embed = discord.Embed(
            title=f"📨 {self.inquiry_type} 문의가 시작되었습니다",
            description="문의가 접수되었습니다.\n필요 시 아래 종료 버튼을 눌러주세요.",
            color=discord.Color.gold()
        )

        await thread.send(content=f"{mention_str} {member.mention}", embed=start_embed, view=CloseThreadView(thread, member))

        await interaction.response.edit_message(
            embed=discord.Embed(
                description=f"📂 `{thread.name}` 문의 스레드가 생성되었습니다!",
                color=discord.Color.green()
            ),
            view=None,delete_after=10
        )

    @discord.ui.button(label="❌ 취소", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(
                description="🚫 문의가 취소되었습니다.",
                color=discord.Color.red()
            ),
            view=None,delete_after=5
        )

async def send_ticket_message(bot: commands.Bot):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    async for msg in channel.history(limit=100):
        if msg.author == bot.user:
            await msg.delete()

    embed = discord.Embed(
        title="📩 문의 접수 센터",
        description=(
            "무엇을 도와드릴까요?\n"
            "아래에서 문의 유형을 선택해주세요!\n\n"
            "📢 **사건 신고**: 서버 내 문제 상황을 알려주세요.\n"
            "📘 **문의&건의**: 규칙 문의나 건의사항을 남겨주세요.\n"
            "💡 **기능 문의**: 디스코드 봇/기능 관련 문의를 남겨주세요."
        ),
        color=discord.Color.blue()
    )

    await channel.send(embed=embed, view=InquiryTypeView(bot))
    
    
# --- 1. ConfirmView: 종료 확인 단계 ---
class CloseConfirmView(View):
    def __init__(self, thread: discord.TextChannel, member: discord.Member):
        super().__init__(timeout=60)
        self.thread = thread
        self.member = member

    @discord.ui.button(label="✅ 확인", style=discord.ButtonStyle.success)
    async def confirm(self, button: Button, interaction: discord.Interaction):
        try:
            await self.thread.set_permissions(self.member, overwrite=None)  # 유저 내보내기
            await self.thread.edit(name=f"종료된-{self.thread.name}")
        except Exception as e:
            await interaction.response.send_message("❌ 유저 추방 또는 이름 변경 중 오류 발생", ephemeral=True)
            return

        # 관리자용 삭제 버튼 Embed 전송
        embed = discord.Embed(
            title="🗑️ 종료된 상담입니다.",
            description="삭제하시겠습니까?",
            color=discord.Color.red()
        )
        await self.thread.send(embed=embed, view=ThreadDeleteView())

        await interaction.response.edit_message(
            embed=discord.Embed(description="🔒 문의가 종료되었습니다.", color=discord.Color.green()),
            view=None
        )

    @discord.ui.button(label="❌ 취소", style=discord.ButtonStyle.danger)
    async def cancel(self, button: Button, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(description="종료 요청이 취소되었습니다.", color=discord.Color.greyple()),
            view=None
        )

# --- 2. DeleteView: 관리자용 삭제 버튼 ---
class ThreadDeleteView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🗑️ 삭제", style=discord.ButtonStyle.danger)
    async def delete_thread(self, button: Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.delete()

# --- 3. Close 버튼: 스레드 내 기본 메시지에 포함될 종료 버튼 ---
class CloseThreadView(View):
    def __init__(self, thread: discord.TextChannel, member: discord.Member):
        super().__init__(timeout=None)
        self.thread = thread
        self.member = member

    @discord.ui.button(label="🔚 문의 종료", style=discord.ButtonStyle.danger)
    async def close(self, button: Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="정말 문의를 종료하시겠습니까?",
            description="종료된 후에는 다시 열 수 없습니다.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=CloseConfirmView(self.thread, self.member), ephemeral=True)
