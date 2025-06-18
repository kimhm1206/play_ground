import discord
from discord.ext import commands
import re
from utils.function import *

COLOR_EMOJI_MAP = {
    "WHITE": "⚪", "GRAY": "⬜", "BLACK": "⬛",
    "RED": "🔴", "PINK": "🌸",  "PINK2": "🩷","PINK3": "🎀",
    "ORANGE": "🟠", "BROWN": "🟤", "YELLOW": "🟡", "YELLOW2": "🌕",
    "GREEN": "🟢", "GREEN2": "🍀", "GREEN3": "🌱","SKY": "☁️",
    "BLUE": "🔵", "BLUE2": "💧", "BLUE3": "🧊", 
    "NAVY": "📘",
    "PURPLE": "🟣", "PURPLE2": "🔮", "PURPLE3": "💜"
}

WELCOME_CHANNEL_ID = 1384518277786505257
Profile_CHANNEL_ID = 1384447074241740871

NICKNAME_REGEX = re.compile(r'^[가-힣a-zA-Z0-9_@!#\.,]{2,15}$')

class ProfileView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="별명 변경", style=discord.ButtonStyle.primary, custom_id="profile_nick")
    async def change_nickname(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(NicknameModal())

    @discord.ui.button(label="닉네임 색 변경", style=discord.ButtonStyle.success, custom_id="profile_color")
    async def change_color(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild = interaction.guild

        # 모든 색상 역할을 mention 형식으로 표현
        mentions = []
        for role_name in COLOR_EMOJI_MAP:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                mentions.append(f"{role.mention}")
            else:
                mentions.append(f"`{role_name}` (❌ 역할 없음)")

        embed = discord.Embed(
            title="🎨 색상 선택 미리보기",
            description="\n".join(mentions),
            color=discord.Color.blurple()
        )

        view = ColorSelectionView(self.bot, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="프로필 설정", style=discord.ButtonStyle.secondary, custom_id="profile_setup")
    async def profile_setup(self, button: discord.ui.Button, interaction: discord.Interaction):
        user_nick = interaction.user.nick or interaction.user.name
        guild = interaction.guild
        user_id = interaction.user.id

        # 기존 프로필 불러오기
        from utils.function import get_profile
        existing_profile = get_profile(user_id)

        if existing_profile:
        # 기존 정보 있으면 중복 검사 생략, 기존 값 모달로 전달
            await interaction.response.send_modal(ProfileModal(user_nick, user_id, new=False, existing_data=existing_profile))
        else:
            # 중복 닉네임 검사 + 정규식 조건 포함
            for member in guild.members:
                other_nick = member.nick or member.name
                if (
                    member.id != user_id
                    and other_nick == user_nick
                    and NICKNAME_REGEX.fullmatch(other_nick)  # ✅ 유효 닉네임만 체크
                ):
                    embed = discord.Embed(
                        description="⚠️ 중복, 잘못된 닉네임 입니다.\n먼저 **별명 변경**을 해주세요!",
                        color=discord.Color.orange()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                    return

            # 신규 입력 모달 호출
            await interaction.response.send_modal(ProfileModal(user_nick, user_id, new=True))

        
async def send_profile_embed(bot):
    channel = bot.get_channel(Profile_CHANNEL_ID)
    if channel is None:
        print("❌ 프로필 채널을 찾을 수 없습니다.")
        return

    # 이전 메시지 삭제
    def is_bot_message(m):
        return m.author == bot.user

    deleted = await channel.purge(limit=100, check=is_bot_message)
    print(f"🧹 삭제된 메시지 수: {len(deleted)}")

    # Embed 구성
    embed = discord.Embed(
        title="🎯 프로필 설정 메뉴",
        description="프로필 설정 버튼을 클릭해 짧은 설문에 응답 해주세요. \n설정을 완료하지 않으면 활동 채널이 보이지 않습니다!",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="모든 설정은 언제든지 다시 변경할 수 있어요 ✨")

    # 버튼 포함 메시지 전송
    view = ProfileView(bot)
    await channel.send(embed=embed, view=view)
    
    
class NicknameModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📝 별명 변경하기")
        self.nickname = discord.ui.InputText(
            label="변경할 별명을 입력해주세요",
            placeholder="한글/영문/숫자 2자~15자 !@#_., 포함",
            required=True,
            max_length=15
        )
        
        self.add_item(self.nickname)

    async def callback(self, interaction: discord.Interaction):
        new_nick = self.nickname.value.strip()
        print(new_nick)
        # 1. 유효성 검사
        if not NICKNAME_REGEX.fullmatch(new_nick):
            await interaction.response.send_message(
                "❌ 별명은 2~15자의 한글/영문/숫자만 사용할 수 있어요!",
                ephemeral=True,delete_after=10
            )
            return

        # 2. 중복 검사 (서버 내 같은 닉네임 존재 여부)
        guild = interaction.guild
        for member in guild.members:
            if (member.nick or member.name).lower() == new_nick.lower():
                await interaction.response.send_message(
                    f"❌ `{new_nick}` 는 이미 사용 중인 별명이에요!",
                    ephemeral=True,delete_after=10
                )
                return

        # 3. 별명 변경
        try:
            await interaction.user.edit(nick=new_nick)
            await interaction.response.send_message(
                f"✅ 별명이 `{new_nick}`(으)로 변경되었어요!",
                ephemeral=True,delete_after=10
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ 관리자의 별명은 봇 권한이 부족해 별명을 변경할 수 없어요.", ephemeral=True,delete_after=10)
            

class ColorSelectionView(discord.ui.View):
    def __init__(self, bot: commands.Bot, member: discord.Member):
        super().__init__(timeout=60)
        self.bot = bot
        self.member = member
        self.selected_color = None

        # 드롭다운 추가
        self.add_item(ColorSelect(self))

    @discord.ui.button(label="✅ 완료", style=discord.ButtonStyle.primary,row=4)
    async def confirm_selection(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.selected_color:
            await interaction.response.send_message("❌ 먼저 색상을 선택해주세요!", ephemeral=True)
            return

        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.selected_color)
        if not role:
            await interaction.response.send_message("❌ 해당 역할을 찾을 수 없습니다.", ephemeral=True)
            return

        # 기존 색상 역할 제거
        color_roles = [r for r in guild.roles if r.name in COLOR_EMOJI_MAP]
        await self.member.remove_roles(*[r for r in self.member.roles if r in color_roles])
        await self.member.add_roles(role)

        embed = discord.Embed(
            description=f"{self.member.mention} 님의 색상이 **{self.selected_color}** 으로 변경되었습니다!",
            color=role.color
        )
        await interaction.response.edit_message(embed=embed, view=None, delete_after=3)
        
    @discord.ui.button(label="❌ 취소", style=discord.ButtonStyle.danger, row=4)
    async def cancel_selection(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            description="⛔ 색상 변경이 취소되었습니다.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None, delete_after=3)


class ColorSelect(discord.ui.Select):
    def __init__(self, parent_view: ColorSelectionView):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label=name, value=name, description=f"{name} 역할 선택")
            for name in COLOR_EMOJI_MAP.keys()
        ]
        super().__init__(placeholder="색상 역할을 선택해주세요", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_color = self.values[0]
        await interaction.response.defer()  # 별도 메시지 없이 응답 처리만


class ProfileModal(discord.ui.Modal):
    def __init__(self, nickname, id, new=True, existing_data=None):
        super().__init__(title=f"📝 {nickname} 프로필 설정")
        self.id = id
        self.nickname = nickname
        self.new = new
        self.mbti = discord.ui.InputText(
            label="MBTI (16종류, 영문 대문자 or 소문자)",
            placeholder="예: INFP 또는 infp, 미공개",
            required=True,
            max_length=4,
            value=existing_data['mbti'] if not new and existing_data else None
        )
        self.games = discord.ui.InputText(
            label="자주 하는 게임 (','로 구분, 최대 100자)",
            placeholder="예: 리그오브레전드, 오버워치",
            max_length=100,
            required=False,
            value=existing_data['favorite_games'] if not new and existing_data else None
        )
        self.wanted = discord.ui.InputText(
            label="하고 싶은 게임 (','로 구분, 최대 100자)",
            placeholder="예: 세븐데이즈투다이, 마인크래프트",
            max_length=100,
            required=False,
            value=existing_data['wanted_games'] if not new and existing_data else None
        )
        self.referral = discord.ui.InputText(
            label="가입 경로 (지인 소개 시 닉네임 포함)",
            placeholder="예: 디스보드, 친구추천(별명)",
            required=True,
            value=existing_data['referral'] if not new and existing_data else None
        )
        self.bio = discord.ui.InputText(
            label="간단 한줄 자기소개 (최대 100자)",
            placeholder="예: 다양한 게임을 좋아하는 사람입니다!",
            max_length=100,
            required=True,
            value=existing_data['bio'] if not new and existing_data else None
        )

        self.add_item(self.mbti)
        self.add_item(self.games)
        self.add_item(self.wanted)
        self.add_item(self.referral)
        self.add_item(self.bio)
        

    async def callback(self, interaction: discord.Interaction):
        mbti_value = self.mbti.value.strip()
        valid_mbti = {
            'intj','intp','entj','entp','infj','infp','enfj','enfp',
            'istj','isfj','estj','esfj','istp','isfp','estp','esfp', '미공개'
        }

        if mbti_value.lower() not in valid_mbti:
            await interaction.response.send_message(
                f"❌ `{mbti_value}` 는 올바른 MBTI 값이 아니에요!",
                ephemeral=True, delete_after=5
            )
            return

        # ✅ DB 저장
        if mbti_value and mbti_value.lower() != "미공개":
            mbti_value = mbti_value.upper()
        else:
            mbti_value = mbti_value or "미공개"
        save_profile(
            user_id=self.id,
            mbti=mbti_value,
            favorite_games=self.games.value.strip(),
            wanted_games=self.wanted.value.strip(),
            referral=self.referral.value.strip(),
            bio=self.bio.value.strip()
        )

        # 🎖️ 역할 부여 (ID: 1384442724580720680)
        role = interaction.guild.get_role(1384442724580720680)
        if role:
            await interaction.user.add_roles(role, reason="프로필 설정")

        await interaction.response.send_message(
            f"✅ `{self.nickname}` 님의 프로필이 성공적으로 설정되었습니다!",
            ephemeral=True, delete_after=10
            )
            
        if self.new == 1:
            channel = interaction.guild.get_channel(WELCOME_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🎉 새로운 멤버가 도착했어요!",
                    description=f"{interaction.user.mention} 님의 프로필입니다:",
                    color=discord.Color.green()
                )
                
                if mbti_value and mbti_value.lower() != "미공개":
                    mbti_display = mbti_value.upper()
                else:
                    mbti_display = mbti_value or "미공개"

                embed.add_field(name="MBTI", value=f"**{mbti_display}**", inline=True)
                embed.add_field(name="자주 하는 게임", value=f"**{self.games.value.strip() or '없음'}**", inline=False)
                embed.add_field(name="하고 싶은 게임", value=f"**{self.wanted.value.strip() or '없음'}**", inline=False)
                embed.add_field(name="가입 경로", value=f"**{self.referral.value.strip()}**", inline=False)
                embed.add_field(name="한줄 소개", value=f"``{self.bio.value.strip()}``", inline=False)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)

                await channel.send(content=f"🎊 새로운 맴버 **{interaction.user.mention}** 님이 들어오셨어요!", embed=embed)
        