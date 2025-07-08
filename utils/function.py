import psycopg2
import platform
from datetime import datetime

# 운영체제 감지하여 호스트 분기
if platform.system() == 'Linux':
    DB_HOST = 'localhost'
else:
    DB_HOST = '3.39.78.125'

# PostgreSQL 접속 설정
DB_NAME = 'discord'
DB_PORT = 5432
DB_USER = 'hyunmoo'
DB_PASSWORD = 'khmkhw2580'

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


def save_profile(user_id: int, mbti: str, favorite_games: str, wanted_games: str, referral: str, bio: str, code: str):
    """
    사용자 프로필 저장 또는 업데이트
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

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
        """, (user_id, mbti.strip(), favorite_games.strip(), wanted_games.strip(), referral.strip(), bio.strip(),code.strip()))
        
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
            SELECT mbti, favorite_games, wanted_games, referral, bio
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
    특정 유저 프로필 삭제
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM voice_leaderboard WHERE user_id = %s;", (user_id,))
        conn.commit()
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
