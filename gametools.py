import random
# ✅ 주사위 값 → 이모지 매핑
DICE_EMOJIS = {
    1: "🎲①",
    2: "🎲②",
    3: "🎲③",
    4: "🎲④",
    5: "🎲⑤",
    6: "🎲⑥",
}

# ✅ 하우스 마진 (0.1 = 10%)
HOUSE_EDGE = 0.15

# ✅ 2D6 실제 확률 (36가지 경우 중)
DICE_PROB = {
    2: 1/36,
    3: 2/36,
    4: 3/36,
    5: 4/36,
    6: 5/36,
    7: 6/36,
    8: 5/36,
    9: 4/36,
    10: 3/36,
    11: 2/36,
    12: 1/36,
}

FRUITS = ["🍒", "🍋", "🍇"]
NON_FRUITS = ["🪙", "💎", "👑", "💣"]
ALL_SYMBOLS = ["🍒","🍋","🍇","🪙","💎","👑","💣"]
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
JACKPOT_CHANNEL_ID = 1398040397338509443  # 잭팟 공지 채널 ID
# ✅ 정배 → 하우스 마진 적용된 배당 계산 함수
def get_payout_multiplier(total: int) -> float:
    prob = DICE_PROB[total]
    fair_odds = 1 / prob  # 정배
    house_odds = fair_odds * (1 - HOUSE_EDGE)  # 마진 적용
    return house_odds


def draw_card():
    """랜덤 카드 한 장 반환"""
    return f"{random.choice(RANKS)}{random.choice(SUITS)}"

def calculate_score(cards):
    """블랙잭 점수 계산 (A는 1 or 11 유리하게 계산)"""
    total = 0
    aces = 0
    for card in cards:
        rank = card[:-1]  # A, 2~10, J, Q, K
        if rank in ["J", "Q", "K"]:
            total += 10
        elif rank == "A":
            total += 11
            aces += 1
        else:
            total += int(rank)

    # A를 11 → 1로 변경해서 21 이하 유지
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total

def rigged_coin_result(user_choice: str) -> str:
    # ✅ 40% 확률로 유저 선택을 승리시킴
    if random.random() < 0.47:
        return user_choice
    else:
        # 반대 결과 리턴
        return "앞면" if user_choice == "뒷면" else "뒷면"