import discord
import asyncio
import os
from openai import OpenAI
from discord.ext import commands
from utils.function import get_profile , save_anonymous_log, get_connection,get_balance,get_pg_point
from utils.function import (
    now_kst, get_balance, get_level, is_user_registered,
    get_today_sent_to_user, get_today_received_from_user,
    update_balance, insert_transaction,edit_tts_type,get_tts_type,get_openai_token
)

tts_queue = asyncio.Queue()   # ✅ 메시지 큐
is_playing = False            # ✅ 현재 재생 상태
openai_token = get_openai_token()
DAILY_LIMIT = 360
LEVEL_UNIT = 30
WEBHOOK_URL = "https://discord.com/api/webhooks/1384529950782263408/2mIMMUVH790rezgL432Q4GWyssoL9WcBZxP9lrJNvtEfmRHrxoIPEYABnM_Gar-ljGg8"
TARGET_CHANNEL_ID = 1384527567280930859
CASINO_ALERT_CHANNEL_ID = 1398040397338509443
# 현재 봇 음성 연결 상태 저장
current_vc: discord.VoiceClient | None = None
tts_text_channel_id: int | None = None  # ✅ 읽을 텍스트 채널 ID 저장

# 메인 봇 객체가 있는 곳에서 불러올 예정이므로 Cog 사용 X
def register_slash_commands(bot: commands.Bot):

    async def send_avatar(
        ctx: discord.ApplicationContext,
        member: discord.Member,
        size: int = 1024,
    ) -> None:
        avatar_url = member.display_avatar.replace(size=size).url
        embed = discord.Embed(
            title=f"🖼️ {member.display_name} 님의 프로필 사진",
            description="이미지 크기는 옵션에서 조절할 수 있어요!",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="요청한 크기", value=f"{size}px", inline=True)
        embed.set_image(url=avatar_url)
        await ctx.respond(content=f"{member.mention} 님의 프로필 사진입니다.", embed=embed)

    @bot.slash_command(
        name="프로필사진",
        description="선택한 멤버의 프로필 사진을 크게 보여줍니다.",
    )
    async def show_avatar(
        ctx: discord.ApplicationContext,
        member: discord.Member,
        size: discord.Option(  # type: ignore
            int,
            "가져올 이미지 크기",
            choices=[
                discord.OptionChoice(name="256px", value=256),
                discord.OptionChoice(name="512px", value=512),
                discord.OptionChoice(name="1024px", value=1024),
            ],
            default=1024,
        ),
    ):
        await send_avatar(ctx, member, size)

    @bot.slash_command(
        name="프사",
        description="선택한 멤버의 프로필 사진을 크게 보여줍니다.",
    )
    async def show_avatar_shortcut(
        ctx: discord.ApplicationContext,
        member: discord.Member,
        size: discord.Option(  # type: ignore
            int,
            "가져올 이미지 크기",
            choices=[
                discord.OptionChoice(name="256px", value=256),
                discord.OptionChoice(name="512px", value=512),
                discord.OptionChoice(name="1024px", value=1024),
            ],
            default=1024,
        ),
    ):
        await send_avatar(ctx, member, size)

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

        embed.add_field(name="스팀 친구 코드", value=f"**{profile['code'] or '미공개'}**", inline=True)
        embed.add_field(
            name="자주 하는 게임 & 선호 장르",
            value=f"**{profile['favorite_games'] or '없음'}**",
            inline=False,
        )
        embed.add_field(
            name="가입 경로 & 목적",
            value=f"**{profile['referral'] or '없음'}**",
            inline=False,
        )

        await ctx.respond(content=f"🔍 {member.mention} 님의 프로필이에요.", embed=embed)
        
    
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
            
    @bot.slash_command(
        name="지갑",
        description="현재 보유 잔액을 확인합니다."
    )
    async def 지갑(ctx: discord.ApplicationContext):
        user_id = ctx.author.id
        balance = get_balance(user_id)
        point = get_pg_point(user_id)

        if balance is None:
            await ctx.respond(
                "❌ 아직 카지노에 등록되지 않았습니다!\n"
                "로비에서 **일당 버튼**을 클릭해 시작하세요!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{ctx.author.display_name} 님의 지갑 💼",
            description=(
                f"💰 PG 머니 : {balance:,}원\n"
                f"👛 PG 포인트 : {point:,}P"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Develop by 배액호오")


        await ctx.respond(embed=embed)
            
    @bot.slash_command(
        name="잔액",
        description="현재 보유 잔액을 확인합니다."
    )
    async def 잔액(ctx: discord.ApplicationContext):
        user_id = ctx.author.id
        balance = get_balance(user_id)
        point = get_pg_point(user_id)

        if balance is None:
            await ctx.respond(
                "❌ 아직 카지노에 등록되지 않았습니다!\n"
                "로비에서 **일당 버튼**을 클릭해 시작하세요!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{ctx.author.display_name} 님의 지갑 💼",
            description=(
                f"💰 PG 머니 : {balance:,}원\n"
                f"👛 PG 포인트 : {point:,}P"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Develop by 배액호오")

        await ctx.respond(embed=embed)
        
    @bot.slash_command(name="송금", description="다른 유저에게 머니를 송금합니다.")
    async def 송금(
        ctx: discord.ApplicationContext,
        대상: discord.Member,
        금액: discord.Option(int, "송금할 금액 (최소 500머니)")  # type: ignore
    ):
        sender_id = ctx.author.id
        receiver_id = 대상.id
        await ctx.defer()
        if sender_id == receiver_id:
            await ctx.respond("❌ 본인에게는 송금할 수 없습니다!", ephemeral=True)
            return

        if 금액 < 500:
            await ctx.respond("❌ 송금 금액은 최소 **500머니** 이상이어야 합니다!", ephemeral=True)
            return

        if not is_user_registered(sender_id):
            await ctx.respond("❌ 먼저 일당을 받아 PG 카지노에 가입해 주세요!", ephemeral=True)
            return

        sender_balance = get_balance(sender_id)
        if sender_balance < 금액:
            await ctx.respond(f"❌ 잔액이 부족합니다! 현재 잔액: **{sender_balance:,}머니**", ephemeral=True)
            return

        if not is_user_registered(receiver_id):
            await ctx.respond(
                "❌ 수신자가 아직 PG 카지노에 등록되지 않았습니다.\n"
                "📢 수신자에게 '일당' 버튼을 눌러 가입하도록 안내해주세요!",
                ephemeral=True
            )
            return

        now = now_kst()
        today = now.date()

        sender_level = get_level(sender_id)
        receiver_level = get_level(receiver_id)

        sender_limit = sender_level * 10_000
        receiver_limit = receiver_level * 10_000

        sent_today = get_today_sent_to_user(sender_id, receiver_id, today)
        if sent_today + 금액 > sender_limit:
            await ctx.respond(
                f"❌ 송금 한도 초과!\n"
                f"📤 당신의 레벨({sender_level}) 기준 1인당 하루 최대 **{sender_limit:,}머니** 송금 가능\n"
                f"현재 이 유저에게 보낸 금액: **{sent_today:,}머니**",
                ephemeral=True
            )
            return

        received_today = get_today_received_from_user(receiver_id, sender_id, today)
        if received_today + 금액 > receiver_limit:
            await ctx.respond(
                f"❌ 수신 한도 초과!\n"
                f"📥 수신자 레벨({receiver_level}) 기준 1인당 하루 최대 **{receiver_limit:,}머니** 수신 가능\n"
                f"오늘 당신으로부터 받은 금액: **{received_today:,}머니**",
                ephemeral=True
            )
            return

        update_balance(sender_id, -금액, f"→ {receiver_id}")
        update_balance(receiver_id, 금액, f"← {sender_id}")

        insert_transaction(sender_id, 'SENDER', -금액, str(receiver_id), now)
        insert_transaction(receiver_id, 'RECEIVER', 금액, str(sender_id), now)
        alert_channel = bot.get_channel(CASINO_ALERT_CHANNEL_ID)
        
        
        try:
            await alert_channel.send(f"✅ {ctx.author.display_name} 님이 → {대상.display_name} 님께 **{금액:,}머니**를 송금 했어요!")
            await 대상.send(f"📩 {ctx.author.display_name} 님이 당신에게 **{금액:,}머니**를 송금했습니다!")
        except discord.Forbidden:
            pass  # DM 차단한 경우 무시

        await ctx.followup.send(f"✅ {ctx.author.display_name} → {대상.display_name} 님께 **{금액:,}머니** 송금 완료!")
        
    # 🎙️ /들어와
    @bot.slash_command(name="들어와", description="몰리봇을 현재 음성 채널에 들어오게 합니다")
    async def join(ctx: discord.ApplicationContext):
        global current_vc, tts_text_channel_id

        if ctx.author.voice is None:
            await ctx.respond("❌ 먼저 음성 채널에 들어가주세요!", ephemeral=True)
            return

        channel = ctx.author.voice.channel

        # ✅ 플립플롭 (이미 사용 중이면 막기)
        if current_vc and current_vc.is_connected():
            if current_vc.channel.id == channel.id:
                await ctx.respond(f"⚠️ 이미 `{channel.name}` 에 접속 중입니다!")
            else:
                await ctx.respond("❌ 이미 다른 채널에서 사용 중입니다. 종료 후 다시 시도하세요.", ephemeral=True)
            return

        # 음성 채널 접속
        current_vc = await channel.connect()
        # ✅ 이 명령어를 입력한 텍스트 채널 저장
        tts_text_channel_id = ctx.channel.id

        await ctx.respond(f"✅ `나 왔다.")

    # 🎙️ /나가
    @bot.slash_command(name="나가", description="몰리봇을 음성 채널에서 내보냅니다")
    async def 나가(ctx: discord.ApplicationContext):
        global current_vc
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            current_vc = None
            await ctx.respond("👋 알았어.. 꺼질게..")
        else:
            await ctx.respond("❌ 현재 음성 채널에 없습니다")


    @bot.slash_command(name="tts설정", description="몰리봇 목소리 타입을 설정합니다")
    async def tts설정(
        ctx: discord.ApplicationContext,
        voice: discord.Option(  # type: ignore
            str,
            "사용할 목소리 타입을 선택하세요",
            choices=["alloy", "verse", "nova", "shimmer", "copper", "amber"]
        )
    ):
        edit_tts_type(voice)
        await ctx.respond(f"✅ TTS 목소리가 `{voice}` 로 설정되었습니다")
            
    async def play_tts_worker(vc: discord.VoiceClient):
        """큐에 쌓인 TTS를 순차적으로 재생하는 워커"""
        global is_playing

        if is_playing:  # 이미 워커 실행 중이면 중복 실행 방지
            return

        is_playing = True
        while not tts_queue.empty():
            text, voice_type, openai_token = await tts_queue.get()
            try:
                # ✅ OpenAI 클라이언트 초기화
                client = OpenAI(api_key=openai_token)

                # ✅ OpenAI TTS → 임시 파일 저장
                tmp_path = "tts_temp.wav"
                with client.audio.speech.with_streaming_response.create(
                    model="gpt-4o-mini-tts",
                    voice=voice_type,
                    input=text
                ) as response:
                    response.stream_to_file(tmp_path)

                # ✅ Discord 재생
                done = asyncio.Event()

                def after_play(err):
                    done.set()

                vc.play(discord.FFmpegPCMAudio(tmp_path), after=after_play)

                # 끝날 때까지 대기
                await done.wait()

                # ✅ 임시 파일 삭제
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            except Exception as e:
                print(f"TTS 변환 실패: {e}")

        is_playing = False


    @bot.event
    async def on_message(message: discord.Message):
        global current_vc, tts_text_channel_id

        if message.author.bot:
            return
        if current_vc is None:
            return
        if tts_text_channel_id is None or message.channel.id != tts_text_channel_id:
            return
        if not message.content or not message.content.strip():
            return

        # ✅ 텍스트 추출 (본문만)
        text = message.content.strip()
        voice_type = get_tts_type()

        # ✅ 큐에 추가
        await tts_queue.put((text, voice_type, openai_token))

        # ✅ 워커 실행
        await play_tts_worker(current_vc)

        # ✅ slash 명령어 처리 유지
        await bot.process_commands(message)