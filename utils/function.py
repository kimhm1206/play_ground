import psycopg2
import platform
from datetime import datetime,timedelta

# 운영체제 감지하여 호스트 분기
if platform.system() == 'Linux':
    DB_HOST = 'localhost'
else:
    DB_HOST = '43.201.35.182'

# PostgreSQL 접속 설정
DB_NAME = 'discord'
DB_PORT = 5432
DB_USER = 'hyunmoo'
DB_PASSWORD = 'khmkhw2580'

def now_kst():
    """KST(UTC+9) 기준 현재 시각"""
    return datetime.utcnow() + timedelta(hours=9)

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
def get_token():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT token
            FROM bot_token
            ORDER BY saved_at DESC
            LIMIT 1
        """)
        result = cursor.fetchone()

        if result:
            return result[0]  # 토큰 문자열
        else:
            print("⚠️ 저장된 봇 토큰이 없습니다.")
            return None

    except Exception as e:
        print("❌ 봇 토큰 조회 실패:", e)
        return None
    finally:
        conn.close()

def save_profile(
    user_id: int,
    favorite_games: str,
    referral: str,
    code: str,
    mbti: str | None = None,
    wanted_games: str | None = None,
    bio: str | None = None,
):
    """
    사용자 프로필 저장 또는 업데이트
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        mbti_value = (mbti or "").strip()
        favorite_games_value = (favorite_games or "").strip()
        wanted_games_value = (wanted_games or "").strip()
        referral_value = (referral or "").strip()
        bio_value = (bio or "").strip()
        code_value = (code or "미공개").strip()

        cursor.execute("""
            INSERT INTO user_profiles (user_id, mbti, favorite_games, wanted_games, referral, bio, code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET
                mbti = EXCLUDED.mbti,
                favorite_games = EXCLUDED.favorite_games,
                wanted_games = EXCLUDED.wanted_games,
                referral = EXCLUDED.referral,
                bio = EXCLUDED.bio,
                code = EXCLUDED.code;
        """, (
            user_id,
            mbti_value,
            favorite_games_value,
            wanted_games_value,
            referral_value,
            bio_value,
            code_value,
        ))

        cursor.execute("INSERT INTO voice_leaderboard (user_id) VALUES (%s) ON CONFLICT DO NOTHING;", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 프로필 저장 실패: {e}")
        return False
    finally:
        conn.close()

def get_profile(user_id: int):
    """
    특정 유저의 프로필 조회
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT mbti, favorite_games, wanted_games, referral, bio, code
            FROM user_profiles
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()

        if result:
            return {
                "mbti": result[0],
                "favorite_games": result[1],
                "wanted_games": result[2],
                "referral": result[3],
                "bio": result[4],
                "code": result[5]
            }
        return None
    except Exception as e:
        print(f"❌ 프로필 조회 실패: {e}")
        return None
    finally:
        conn.close()

def save_anonymous_log(user_id: int, nickname: str, message: str):
    """
    익명 로그 저장
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO anonymous_logs (time, user_id, nickname, text)
            VALUES (%s, %s, %s, %s)
        """, (timestamp, user_id, nickname, message))

        conn.commit()
    except Exception as e:
        print(f"❌ 익명 로그 저장 실패: {e}")
    finally:
        conn.close()

def delete_profile(user_id: int):
    """
    특정 유저 관련 DB 정보 전체 삭제
    - user_profiles
    - voice_leaderboard
    - casino_users
    - casino_loans
    - casino_transactions
    - loans_sign
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # ✅ 기존 프로필/레벨 기록 삭제
        cursor.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM voice_leaderboard WHERE user_id = %s", (user_id,))

        # ✅ 카지노 관련 모든 데이터 삭제
        cursor.execute("DELETE FROM casino_transactions WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM casino_loans WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM casino_users WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM loans_sign WHERE user_id = %s", (user_id,))

        conn.commit()
        print(f"✅ 유저 {user_id} 모든 DB 정보 삭제 완료")

    except Exception as e:
        print(f"❌ 프로필 삭제 실패: {e}")

    finally:
        conn.close()
        
def log_ticket(user_id: int, nickname: str, category: str, target: str, thread_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ticket_logs (user_id, nickname, category, target, thread_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, nickname, category, target, thread_id))
        conn.commit()
    except Exception as e:
        print(f"❌ 문의 로그 저장 실패: {e}")
    finally:
        conn.close()

def is_user_overdue(user_id: int) -> bool:
    """
    연체자인지 판별하는 함수 (더미)
    나중에 casino_loans 조회해서 실제 연체 여부 반환 예정
    지금은 항상 False
    """
    return False

def give_daily_money(user_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    now = now_kst()         # ✅ 현재 KST 시각
    today = now.date()      # ✅ 오늘 날짜 (KST)

    # ✅ 레벨 조회 (없으면 기본 1)
    cur.execute("""
        SELECT level 
        FROM voice_leaderboard 
        WHERE user_id=%s
    """, (user_id,))
    lvl_row = cur.fetchone()
    level = lvl_row[0] if lvl_row else 1

    # ✅ 레벨 5 미만이면 지급 불가
    if level < 5:
        cur.close()
        conn.close()
        return {
            "success": False,
            "message": (
                f"🚫 일당은 레벨 5 이상부터 받을 수 있어요!\n"
                f"현재 레벨: {level}\n\n"
                f"🎮 저희 PG에서는 **게임 이용 300시간** 달성 시 자동으로 레벨 5가 됩니다!"
            ),
            "amount": 0,
            "balance": None
        }

    # ✅ 유저 조회
    cur.execute("SELECT balance, last_donzoo_date FROM casino_users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    # 신규 유저면 2만 + 1만 지급
    if not row:
        cur.execute("""
            INSERT INTO casino_users (user_id, balance, last_donzoo_date)
            VALUES (%s, %s, %s)
        """, (user_id, 30000, today))

        cur.execute("""
            INSERT INTO casino_transactions (user_id, type, amount, description, created_at)
            VALUES (%s, 'DONZOO', %s, '신규 유저 첫 일당 지급', %s)
        """, (user_id, 30000, now))

        conn.commit()
        cur.close()
        conn.close()
        return {
            "success": True,
            "message": f"🎉 PG 카지노 첫 방문 환영!\n💸 일당 **20,000코인** + 첫 방문 **10,000코인** 지급 완료!",
            "amount": 30000,
            "balance": 30000
        }

    balance, last_donzoo_date = row

    # 오늘 이미 받았다면 실패
    if last_donzoo_date == today:
        cur.close()
        conn.close()
        return {
            "success": False,
            "message": "❌ 오늘은 이미 **일당**을 받았습니다. 내일 다시 시도하세요!",
            "amount": 0,
            "balance": balance
        }

    # 보유금 ≥ 20만이면 1만, 아니면 2만
    지급금 = 10000 if balance >= 1_000_000 else 20000

    cur.execute("""
        UPDATE casino_users
        SET balance = balance + %s,
            last_donzoo_date = %s
        WHERE user_id = %s
    """, (지급금, today, user_id))

    cur.execute("""
        INSERT INTO casino_transactions (user_id, type, amount, description, created_at)
        VALUES (%s, 'DONZOO', %s, '하루 일당 지급', %s)
    """, (user_id, 지급금, now))

    conn.commit()
    cur.close()
    conn.close()

    new_balance = balance + 지급금
    return {
        "success": True,
        "message": f"💸 오늘 일당 **{지급금:,}코인** 지급 완료!\n현재 보유금: **{new_balance:,}코인**",
        "amount": 지급금,
        "balance": new_balance
    }

    
def get_bank_info(user_id: int) -> dict:
    """
    유저 은행 정보 조회
    - balance는 casino_users에서
    - level은 voice_leaderboard에서
    - 대출 한도는 레벨 × 10,000 (코인금 기준)
    """
    conn = get_connection()
    cur = conn.cursor()

    # ✅ 잔액 조회 (casino_users)
    cur.execute("""
        SELECT balance 
        FROM casino_users 
        WHERE user_id=%s
    """, (user_id,))
    user_row = cur.fetchone()

    if not user_row:
        # 신규 유저 → 기본 balance=0 등록
        cur.execute("""
            INSERT INTO casino_users (user_id, balance) VALUES (%s, %s)
        """, (user_id, 0))
        conn.commit()
        balance = 0
    else:
        balance = user_row[0]

    # ✅ 레벨 조회 (voice_leaderboard)
    cur.execute("""
        SELECT level 
        FROM voice_leaderboard 
        WHERE user_id=%s
    """, (user_id,))
    lvl_row = cur.fetchone()
    level = lvl_row[0] if lvl_row else 1  # 없으면 기본 1레벨

    # ✅ 대출 내역 가져오기 (코인금과 상환금 모두)
    cur.execute("""
        SELECT loan_id, amount, remaining_amount, due_date, status 
        FROM casino_loans 
        WHERE user_id=%s AND status!='PAID'
        ORDER BY loan_date ASC
    """, (user_id,))
    loans = cur.fetchall()

    loan_list = []
    total_loan_principal = 0  # 코인금 합산
    overdue_flag = False

    for loan_id, amount, remain, due_date, status in loans:
        total_loan_principal += amount  # ✅ 한도 계산엔 코인금만
        if status in ("OVERDUE", "LONG_OVERDUE"):
            overdue_flag = True

        loan_list.append({
            "loan_id": loan_id,
            "amount": amount,                 # 코인금
            "remaining": remain,              # 이자 포함 상환금
            "due_date": due_date.strftime("%m월 %d일"),
            "status": status
        })

    conn.close()

    # ✅ 총 대출 한도 = 레벨 × 10,000 (코인금만 기준)
    loan_limit = level * 10000

    # ✅ 남은 대출 가능 금액 (코인금 기준)
    remaining_limit = max(0, loan_limit - total_loan_principal)

    return {
        "balance": balance,                 # 현재 잔액
        "level": level,                     # 레벨
        "loan_limit": loan_limit,           # 총 한도 (코인금)
        "total_loans": total_loan_principal,# 현재 사용 중 대출 코인금 합계
        "remaining_limit": remaining_limit, # 남은 대출 가능 금액
        "loans": loan_list,                 # 대출 상세 내역
        "overdue": overdue_flag             # 연체 여부
    }

def loan_money(user_id: int, amount: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    now = now_kst()
    
    # ✅ due_date = 오늘 +14일 + 1일 = 15일 후 자정까지
    today_date = now.date()
    due_date_date = today_date + timedelta(days=15)  # 14일 사용 + 하루 유예
    due_date = datetime.combine(due_date_date, datetime.min.time())  # KST 00:00

    # ✅ 레벨 조회 (대출 한도)
    cur.execute("SELECT level FROM voice_leaderboard WHERE user_id=%s", (user_id,))
    lvl_row = cur.fetchone()
    level = lvl_row[0] if lvl_row else 1
    loan_limit = level * 10000

    # ✅ 현재 사용 중 대출 합계 (코인금 기준)
    cur.execute("""
        SELECT COALESCE(SUM(amount),0) 
        FROM casino_loans 
        WHERE user_id=%s AND status!='PAID'
    """, (user_id,))
    used_loans = cur.fetchone()[0]

    # ✅ 현재 balance 조회
    cur.execute("SELECT balance FROM casino_users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO casino_users (user_id, balance)
            VALUES (%s, 0)
        """, (user_id,))
        balance_before = 0
    else:
        balance_before = row[0]

    # ✅ 한도 체크
    if used_loans + amount > loan_limit:
        conn.commit()
        conn.close()
        return {
            "success": False,
            "message": f"❌ 대출 불가! 한도 {loan_limit:,}코인 / 이미 {used_loans:,}코인 사용 중",
            "balance": balance_before
        }

    # ✅ 이자율 (현재 고정 10%)
    interest_rate = 0.10
    repay_amount = int(amount * (1 + interest_rate))

    # ✅ 신규 대출 등록 (due_date = 15일 후 00:00)
    cur.execute("""
        INSERT INTO casino_loans 
        (user_id, amount, interest_rate, total_repay_amount, remaining_amount, loan_date, due_date, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'NORMAL')
    """, (user_id, amount, interest_rate, repay_amount, repay_amount, now, due_date))

    # ✅ balance 증가
    cur.execute("""
        UPDATE casino_users SET balance = balance + %s WHERE user_id=%s
    """, (amount, user_id))

    # ✅ 거래 로그 기록
    cur.execute("""
        INSERT INTO casino_transactions (user_id, type, amount, description, created_at)
        VALUES (%s, 'LOAN', %s, %s, %s)
    """, (user_id, amount, f"대출 실행 (이자율 {int(interest_rate*100)}%)", now))

    # ✅ 최종 balance 조회
    cur.execute("SELECT balance FROM casino_users WHERE user_id=%s", (user_id,))
    new_balance_row = cur.fetchone()
    new_balance = new_balance_row[0] if new_balance_row else balance_before + amount

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": (
            f"💳 {amount:,}코인 대출 완료!\n"
            f"14일 내 상환 필요, 기한은 **{due_date.strftime('%m월 %d일 00시 00분')}** 까지입니다.\n"
            f"총 상환금은 **{repay_amount:,}코인** 입니다."
        ),
        "balance": new_balance
    }

def sign_loan_terms(user_id: int) -> None:
    """대출 설명서 동의 기록 저장"""
    conn = get_connection()
    cur = conn.cursor()

    now = now_kst()
    cur.execute("""
        INSERT INTO loans_sign (user_id, sign_date)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET sign_date = EXCLUDED.sign_date
    """, (user_id, now))

    conn.commit()
    conn.close()
    
def has_signed_loan_terms(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM loans_sign WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row)

def repay_loan(user_id: int, loan_id: int, repay_amount: int) -> dict:
    """
    특정 대출 상환 처리
    """
    conn = get_connection()
    cur = conn.cursor()

    # ✅ 유저 잔액 조회
    cur.execute("SELECT balance FROM casino_users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"success": False, "message": "❌ 유저 정보가 없습니다.", "balance": 0}
    balance = row[0]

    # ✅ 잔액 부족
    if repay_amount > balance:
        conn.close()
        return {"success": False, "message": "❌ 잔액이 부족합니다.", "balance": balance}

    # ✅ 대출 정보 조회
    cur.execute("""
        SELECT remaining_amount, status 
        FROM casino_loans 
        WHERE loan_id=%s AND user_id=%s
    """, (loan_id, user_id))
    loan_row = cur.fetchone()

    if not loan_row:
        conn.close()
        return {"success": False, "message": "❌ 해당 대출이 존재하지 않습니다.", "balance": balance}

    remaining_amount, status = loan_row

    # ✅ 상환 처리
    new_remaining = remaining_amount - repay_amount
    if new_remaining <= 0:
        # 완납
        cur.execute("""
            UPDATE casino_loans
            SET remaining_amount=0, status='PAID'
            WHERE loan_id=%s
        """, (loan_id,))
        repay_amount = remaining_amount  # 남은 금액만 차감
        msg_detail = "✅ **완납되었습니다!**"
    else:
        # 일부 상환
        cur.execute("""
            UPDATE casino_loans
            SET remaining_amount=%s
            WHERE loan_id=%s
        """, (new_remaining, loan_id))
        msg_detail = f"✅ 일부 상환되었습니다. 남은 상환금: {new_remaining:,}코인"

    # ✅ balance 차감
    cur.execute("""
        UPDATE casino_users SET balance = balance - %s WHERE user_id=%s
    """, (repay_amount, user_id))

    # ✅ 거래 로그 기록
    now = now_kst()
    cur.execute("""
        INSERT INTO casino_transactions (user_id, type, amount, description, created_at)
        VALUES (%s, 'REPAY', %s, %s, %s)
    """, (user_id, repay_amount, f"대출 상환 (loan_id={loan_id})", now))

    # ✅ 최종 잔액 조회
    cur.execute("SELECT balance FROM casino_users WHERE user_id=%s", (user_id,))
    new_balance = cur.fetchone()[0]

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"💸 {repay_amount:,}코인 상환 완료!\n{msg_detail}",
        "balance": new_balance
    }
    
def get_balance(user_id: int) -> int:
    """유저의 현재 보유금(balance) 조회"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM casino_users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    # 신규 유저 or 없으면 0 반환
    return row[0] if row else 0

def update_balance(user_id: int, change: int, description: str = "게임 베팅 결과"):
    """
    유저의 balance를 증감시키고, 거래 로그에 기록.
    change가 +면 증가 / -면 차감.
    """
    now = now_kst()
    conn = get_connection()
    cur = conn.cursor()

    # ✅ 유저 존재 여부 확인
    cur.execute("SELECT balance FROM casino_users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    current_balance = row[0]

    # ✅ balance 증감
    new_balance = current_balance + change
    if new_balance < 0:
        new_balance = 0  # 마이너스 방지 (코인하면 그대로 허용 가능)

    cur.execute("""
        UPDATE casino_users
        SET balance = %s
        WHERE user_id = %s
    """, (new_balance, user_id))

    # # ✅ 거래 로그 기록
    # cur.execute("""
    #     INSERT INTO casino_transactions (user_id, type, amount, description, created_at)
    #     VALUES (%s, 'GAME', %s, %s, %s)
    # """, (user_id, change, description, now))

    conn.commit()
    cur.close()
    conn.close()

    return new_balance  # 변경 후 최종 잔액 반환

def get_top_balances(limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, balance
        FROM casino_users
        ORDER BY balance DESC
        LIMIT %s
    """, (limit,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result  # [(user_id, balance), ...]

def is_crack_enabled(user_id: int) -> bool:
    conn = get_connection()  # 또는 다른 DB 커넥터
    cur = conn.cursor()
    cur.execute("SELECT value FROM crack_mode WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None and row[0] is True

def get_pg_point(user_id: int) -> int:
    """유저의 PG 포인트 조회"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT pg_point FROM casino_users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row else 0

# ✅ 유저 등록 여부 확인
def is_user_registered(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM casino_users WHERE user_id=%s", (user_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

# ✅ 유저 레벨 조회 (없으면 1로 처리)
def get_level(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT level FROM voice_leaderboard WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 1

# ✅ 송금자 → 수신자 오늘 보낸 금액 총합
def get_today_sent_to_user(sender_id: int, receiver_id: int, date) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(ABS(amount)), 0)
        FROM casino_transactions
        WHERE user_id=%s AND type='SENDER' AND description=%s AND DATE(created_at)=%s
    """, (sender_id, str(receiver_id), date))
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result

# ✅ 수신자 ← 송금자로부터 오늘 받은 금액 총합
def get_today_received_from_user(receiver_id: int, sender_id: int, date) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM casino_transactions
        WHERE user_id=%s AND type='RECEIVER' AND description=%s AND DATE(created_at)=%s
    """, (receiver_id, str(sender_id), date))
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result

# ✅ 트랜잭션 기록 삽입
def insert_transaction(user_id: int, tx_type: str, amount: int, description: str, created_at):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO casino_transactions (user_id, type, amount, description, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, tx_type, amount, description, created_at))
    conn.commit()
    cur.close()
    conn.close()


def get_openai_token() -> str:
    """DB에서 OpenAI Token 가져오기"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT value FROM tts_setting WHERE key='token'")
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row else None


def get_tts_type() -> str:
    """DB에서 현재 TTS 목소리 타입 가져오기"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT value FROM tts_setting WHERE key='type'")
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row else "alloy"   # 기본값 alloy


def edit_tts_type(new_type: str) -> None:
    """DB의 TTS 목소리 타입 변경"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tts_setting
        SET value=%s
        WHERE key='type'
    """, (new_type,))

    conn.commit()
    cur.close()
    conn.close()
