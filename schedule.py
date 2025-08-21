import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from utils.function import get_connection, now_kst
import pytz

# ✅ 카지노 알림 채널 ID (전역)
CASINO_ALERT_CHANNEL_ID = 1398040397338509443

# ✅ APScheduler 스케줄러
scheduler = AsyncIOScheduler()


async def daily_loan_check(bot: discord.Client):
    now = now_kst()
    today = now.date()
    today_midnight = datetime.combine(today, datetime.min.time())
    tomorrow = today + timedelta(days=1)

    alert_channel = bot.get_channel(CASINO_ALERT_CHANNEL_ID)

    conn = get_connection()
    cur = conn.cursor()

    # ✅ 연체 임박자 (내일 기한)
    cur.execute("""
        SELECT DISTINCT user_id 
        FROM casino_loans
        WHERE status='NORMAL' AND due_date = %s
    """, (tomorrow,))
    almost_overdue_users = [row[0] for row in cur.fetchall()]

    # ✅ 연체 전환 (due_date < 오늘 자정)
    cur.execute("""
        SELECT loan_id, remaining_amount, user_id
        FROM casino_loans
        WHERE status='NORMAL' AND due_date <= %s
    """, (today_midnight,))
    overdue_list = cur.fetchall()

    newly_overdue_users = set()
    for loan_id, remaining_amount, user_id in overdue_list:
        new_remaining = int(remaining_amount * 1.1)
        cur.execute("""
            UPDATE casino_loans
            SET status='OVERDUE',
                remaining_amount=%s,
                overdue_date=%s
            WHERE loan_id=%s
        """, (new_remaining, today, loan_id))
        newly_overdue_users.add(user_id)

    # ✅ 장기 연체 전환 (7일 지난 OVERDUE → LONG_OVERDUE)
    cur.execute("""
        UPDATE casino_loans
        SET status='LONG_OVERDUE'
        WHERE status='OVERDUE'
        AND overdue_date < %s
    """, (today - timedelta(days=7),))

    conn.commit()

    # ✅ 1) 연체 임박자 알림
    for user_id in almost_overdue_users:
        await alert_channel.send(
            f"⏰ <@{user_id}>, 오늘 내로 상환하지 않으면 **연체**됩니다!"
        )

    # ✅ 2) 연체된 당일 알림
    for user_id in newly_overdue_users:
        await alert_channel.send(
            f"⚠️ <@{user_id}>, **연체되었습니다.**\n"
            f"7일 내로 상환하지 않으면 장기 연체자로 전환됩니다."
        )

    # ✅ 3) 장기 연체 하루 전 알림
    cur.execute("""
        SELECT DISTINCT user_id
        FROM casino_loans
        WHERE status='OVERDUE' AND overdue_date = %s
    """, (today - timedelta(days=7),))
    almost_long_overdue_users = [row[0] for row in cur.fetchall()]

    for user_id in almost_long_overdue_users:
        await alert_channel.send(
            f"🚨 <@{user_id}>, **오늘까지 갚지 않으면 장기 연체자로 전환됩니다!**\n"
            f"장기 연체가 되면 강제 상환이 시작됩니다."
        )

    # ✅ 4) 장기 연체자 강제 상환
    await force_repay_long_overdue(alert_channel, conn, cur, today)

    cur.close()
    conn.close()


async def force_repay_long_overdue(channel, conn, cur, today):
    """장기 연체자 강제 상환 처리"""
    # ✅ LONG_OVERDUE 유저 목록 조회
    cur.execute("""
        SELECT DISTINCT user_id 
        FROM casino_loans 
        WHERE status='LONG_OVERDUE'
    """)
    long_overdue_users = [row[0] for row in cur.fetchall()]

    for user_id in long_overdue_users:
        # ✅ 유저 잔액 / 오늘 일당 확인
        cur.execute("""
            SELECT balance, last_donzoo_date 
            FROM casino_users WHERE user_id=%s
        """, (user_id,))
        row = cur.fetchone()
        if not row:
            continue

        balance, last_donzoo_date = row
        if balance <= 0:
            continue  # 잔액 없으면 스킵

        # ✅ 오늘 일당 받았으면 10,000코인 남기고 몰수
        leave_amount = 10000 if last_donzoo_date == today else 0
        repay_amount = max(0, balance - leave_amount)

        if repay_amount <= 0:
            continue  # 남길 금액만 있고 상환할 게 없으면 패스

        # ✅ 유저 LONG_OVERDUE 대출 목록 (loan_date 오래된 순)
        cur.execute("""
            SELECT loan_id, remaining_amount 
            FROM casino_loans 
            WHERE user_id=%s AND status='LONG_OVERDUE'
            ORDER BY loan_date ASC
        """, (user_id,))
        loans = cur.fetchall()

        remain_repay = repay_amount
        total_forced_repay = 0

        for loan_id, remaining_amount in loans:
            if remain_repay <= 0:
                break

            if remain_repay >= remaining_amount:
                # 이 대출 완납 가능
                total_forced_repay += remaining_amount
                remain_repay -= remaining_amount
                cur.execute("""
                    UPDATE casino_loans
                    SET remaining_amount=0, status='PAID'
                    WHERE loan_id=%s
                """, (loan_id,))
            else:
                # 일부만 상환
                total_forced_repay += remain_repay
                new_remaining = remaining_amount - remain_repay
                remain_repay = 0
                cur.execute("""
                    UPDATE casino_loans
                    SET remaining_amount=%s
                    WHERE loan_id=%s
                """, (new_remaining, loan_id))

        # ✅ 실제 차감된 금액
        actual_repay = repay_amount - remain_repay

        # ✅ 최종 balance = leave_amount + 상환 못한 잔액
        final_balance = leave_amount + remain_repay
        cur.execute("""
            UPDATE casino_users SET balance=%s WHERE user_id=%s
        """, (final_balance, user_id))

        # ✅ 거래 로그 기록
        now = now_kst()
        cur.execute("""
            INSERT INTO casino_transactions (user_id, type, amount, description, created_at)
            VALUES (%s, 'FORCE_REPAY', %s, '장기 연체 강제 상환 처리', %s)
        """, (user_id, actual_repay, now))

        # ✅ 안내 메시지
        user_mention = f"<@{user_id}>"
        if last_donzoo_date == today:
            await channel.send(
                f"⚠️ {user_mention}, **장기 연체 상태**라 강제 상환 처리되었습니다.\n"
                f"오늘 일당은 이미 수령하셨으므로 최소 **10,000코인만 남기고 {actual_repay:,}코인 상환**되었습니다.\n"
                f"💬 남은 대출금을 확인해주세요."
            )
        else:
            await channel.send(
                f"⚠️ {user_mention}, **장기 연체 상태**라 강제 상환 처리되었습니다.\n"
                f"오늘 일당은 아직 수령 전이므로 **{actual_repay:,}코인 상환**되었으며,\n"
                f"💬 남은 금액은 오늘 일당 수령 후 이용해주세요.\n"
                f"💬 남은 대출금을 확인해주세요."
            )

    conn.commit()


def setup_scheduler(bot: discord.Client):
    """APScheduler 스케줄러 등록"""
    # ✅ 매일 00:01 실행
    seoul_tz = pytz.timezone("Asia/Seoul")
    scheduler.add_job(daily_loan_check, 'cron', hour=0, minute=1, args=[bot],timezone=seoul_tz)
    scheduler.start()
    print("✅ APScheduler 스케줄러 시작됨 (매일 00:01 자동 실행)")
