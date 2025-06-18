import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, InputText
from discord import VoiceChannel, CategoryChannel, PermissionOverwrite
import re
from collections import deque
from datetime import datetime, timedelta

# Constants
VOICE_ROOM_TRIGGER_CHANNEL_ID = 1384965457911480340
VOICE_ROOM_CATEGORY_ID = 1384416142172491898
ADMIN_ROLE_ID = 1384442724580720680

RENAME_LIMIT = 2
RENAME_WINDOW = timedelta(minutes=10)
channel_rename_logs = {}  # {channel_id: deque([datetime])}

# Utility function to sanitize Discord topic content
def sanitize_topic(text: str) -> str:
    text = re.sub(r"[@`<>]", "", text)
    return text.strip()

# View with buttons to interact with the voice room
class VoiceRoomControlView(View):
    def __init__(self, voice_channel: discord.VoiceChannel):
        super().__init__(timeout=None)
        self.voice_channel = voice_channel

    @discord.ui.button(label="방 제목 변경", style=discord.ButtonStyle.secondary, custom_id="rename")
    async def rename(self, button, interaction: discord.Interaction):
        await interaction.response.send_modal(ChannelSettingsModal(self.voice_channel))

from collections import deque
from datetime import datetime, timedelta

RENAME_LIMIT = 2
RENAME_WINDOW = timedelta(minutes=10)
channel_rename_logs = {}  # {channel_id: deque([datetime])}

class ChannelSettingsModal(Modal):
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(title="방 제목 변경")
        self.channel = channel
        self.add_item(InputText(label="방 제목", placeholder="공백이면 수다방N", required=False))

    async def callback(self, interaction: discord.Interaction):
        try:
            now = datetime.utcnow()
            cid = self.channel.id

            # ⏳ 변경 기록 확인 및 초기화
            log = channel_rename_logs.setdefault(cid, deque())
            # 오래된 기록 제거
            while log and now - log[0] > RENAME_WINDOW:
                log.popleft()

            # 💡 제한 초과 확인
            if len(log) >= RENAME_LIMIT:
                next_allowed_time = log[0] + RENAME_WINDOW
                remain = next_allowed_time - now
                minutes = remain.seconds // 60
                seconds = remain.seconds % 60
                await interaction.response.send_message(
                    f"❌ 최근 10분 내 2번 변경하셨습니다. {minutes}분 {seconds}초 후 다시 시도해주세요.",
                    ephemeral=True, delete_after=5
                )
                return

            # ✅ 변경 수행
            new_title_input = self.children[0].value.strip()
            guild = interaction.guild
            category = self.channel.category

            # 제목 자동 생성
            if not new_title_input:
                existing = [c.name for c in category.voice_channels if "수다방" in c.name]
                i = 1
                while f"수다방{i}" in existing:
                    i += 1
                new_title = f"수다방{i}"
            else:
                new_title = new_title_input

            # 채널명 변경
            await self.channel.edit(name=new_title)
            log.append(now)  # 변경 기록 추가

            # Embed 업데이트
            embed = discord.Embed(
                title=new_title,
                description=(
                    "```관전, 훈수, 난입 상태는\n채널상태에 적어주세요. \n디스코드API 정책에따라 10분에 2번만 \n제목변경이 가능합니다.```"
                ),
                color=discord.Color.blue()
            )
            view = VoiceRoomControlView(self.channel)
            await interaction.message.edit(embed=embed, view=view)

            await interaction.response.send_message("✅ 방 제목이 변경되었습니다!", ephemeral=True, delete_after=5)

        except Exception as e:
            print(f"[에러] Modal 처리 실패: {e}")


# Voice room creation logic
async def create_voice_room(guild: discord.Guild, member: discord.Member):
    category: CategoryChannel = guild.get_channel(VOICE_ROOM_CATEGORY_ID)
    existing = [c.name for c in category.voice_channels if c.name.startswith("수다방")]
    i = 1
    while f"수다방{i}" in existing:
        i += 1
    title = f"수다방{i}"

    overwrites = {
        guild.default_role: PermissionOverwrite(view_channel=False, connect=False),
        member: PermissionOverwrite(view_channel=True, connect=True),
        guild.get_role(ADMIN_ROLE_ID): PermissionOverwrite(view_channel=True, connect=True)
    }

    voice_channel = await guild.create_voice_channel(
        name=title,
        category=category,
        overwrites=overwrites
    )

    try:
        await member.move_to(voice_channel)
    except:
        pass

    embed = discord.Embed(
        title=f"{title}",
        description=(
            "```관전, 훈수, 난입 상태는\n채널상태에 적어주세요. \n디스코드API 정책에따라 10분에 2번만 \n제목변경이 가능합니다.```"
        ),
        color=discord.Color.blue()
    )
    view = VoiceRoomControlView(voice_channel)
    await voice_channel.send(embed=embed, view=view)

# Main Cog
class VoiceRoomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.id == VOICE_ROOM_TRIGGER_CHANNEL_ID:
            # ✅ 이미 방이 만들어졌는지 체크
            category = after.channel.guild.get_channel(VOICE_ROOM_CATEGORY_ID)
            if any(member in vc.members for vc in category.voice_channels if vc.id != VOICE_ROOM_TRIGGER_CHANNEL_ID):
                return  # 이미 방 들어감 → 방 생성 X

            await create_voice_room(member.guild, member)

# Setup for bot.load_extension
async def setup(bot):
    await bot.add_cog(VoiceRoomCog(bot))
