import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import urllib.parse
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(
    page_title="딴딴영어 에빙하우스 회화 튜터",
    page_icon="🗣️",
    layout="wide"
)

DATA_FILE = "ebbinghaus_progress.json"

def render_tts_button(text_to_speak, label="🔊 발음 듣기"):
    safe_text = json.dumps(text_to_speak)
    btn_id = abs(hash(text_to_speak + str(label))) & 0xffffffff
    html_code = f"""
    <div style="margin: 2px 0;">
        <button onclick="speakText_{btn_id}()" style="
            background-color: #2e7d32;
            color: white;
            border: none;
            padding: 6px 14px;
            text-align: center;
            font-size: 13px;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {label}
        </button>
    </div>
    <script>
    function speakText_{btn_id}() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance({safe_text});
            msg.lang = 'en-US';
            msg.rate = 0.85;
            window.speechSynthesis.speak(msg);
        }}
    }}
    </script>
    """
    components.html(html_code, height=42)

def get_content_link(pattern):
    query = f"딴딴영어 {pattern}"
    encoded = urllib.parse.quote(query)
    return f"https://www.google.com/search?q={encoded}"


# 딴딴 패턴영어 30가지 원어민 필수 패턴 DB (소스 기반)
PATTERN_DB = [
    {
        "id": "P001",
        "pattern": "Do you want me to~?",
        "meaning": "내가 ~해줄까?",
        "examples": {
            "stage1": {"q": "내가 커피 만들어 줄까?", "target": "Do you want me to make coffee?"},
            "stage2": {"q": "내가 너 대신 그건 처리해 줄까?", "target": "Do you want me to handle that for you?"},
            "stage3": {"q": "[상황] 무거운 짐을 들고 있는 사람에게 도움을 제안할 때", "target": "Do you want me to help you with that?"},
            "stage4": {"q": "[롤플레잉] A: 'I'm so tired.' / B: '내가 집까지 바래다줄까?'", "target": "Do you want me to drive you home?"}
        }
    },
    {
        "id": "P002",
        "pattern": "Do you happen to~?",
        "meaning": "혹시 ~하세요? / 혹시 ~있나요?",
        "examples": {
            "stage1": {"q": "혹시 저분 아세요?", "target": "Do you happen to know her?"},
            "stage2": {"q": "혹시 펜 하나 가지고 계신가요?", "target": "Do you happen to have a pen?"},
            "stage3": {"q": "[상황] 길 가다 충전기가 필요해 상인에게 물어볼 때", "target": "Do you happen to have a charger?"},
            "stage4": {"q": "[롤플레잉] A: 'I'm lost.' / B: '혹시 근처 마트 위치 아세요?'", "target": "Do you happen to know where the market is?"}
        }
    },
    {
        "id": "P003",
        "pattern": "Have you ever~?",
        "meaning": "~해본 적 있어?",
        "examples": {
            "stage1": {"q": "파리에 가본 적 있어?", "target": "Have you ever been to Paris?"},
            "stage2": {"q": "그 사람 직접 만나본 적 있어?", "target": "Have you ever met him in person?"},
            "stage3": {"q": "[상황] 친구에게 굵은 눈물을 흘려본 적 있는지 물어볼 때", "target": "Have you ever cried like that?"},
            "stage4": {"q": "[롤플레잉] A: 'I love spicy food.' / B: '불닭볶음면 먹어본 적 있어?'", "target": "Have you ever tried fire noodles?"}
        }
    },
    {
        "id": "P004",
        "pattern": "It's worth~",
        "meaning": "~할 만해 / ~할 가치가 있어",
        "examples": {
            "stage1": {"q": "이 영화 볼 만해.", "target": "It's worth watching this movie."},
            "stage2": {"q": "줄 서서 기다릴 만해.", "target": "It's worth the wait."},
            "stage3": {"q": "[상황] 비용이 들더라도 시도해볼 가치가 있다고 추천할 때", "target": "It's worth a try."},
            "stage4": {"q": "[롤플레잉] A: 'Is it expensive?' / B: '응, 하지만 돈 들일 만해.'", "target": "Yes, but it's worth the money."}
        }
    },
    {
        "id": "P005",
        "pattern": "Why don't you~?",
        "meaning": "~하는 게 어때?",
        "examples": {
            "stage1": {"q": "잠깐 쉬는 게 어때?", "target": "Why don't you take a break?"},
            "stage2": {"q": "한번 해보는 게 어때?", "target": "Why don't you give it a try?"},
            "stage3": {"q": "[상황] 피곤해 보이는 동료에게 앉으라고 권할 때", "target": "Why don't you sit down?"},
            "stage4": {"q": "[롤플레잉] A: 'I'm stuck.' / B: '그 사람에게 도움을 요청해보는 건 어때?'", "target": "Why don't you ask him for help?"}
        }
    },
    {
        "id": "P006",
        "pattern": "You've got to~",
        "meaning": "너 꼭 ~해야 해 (강한 권유/조언)",
        "examples": {
            "stage1": {"q": "너 조심해야 해!", "target": "You've got to be careful!"},
            "stage2": {"q": "너 꼭 나를 믿어야 해.", "target": "You've got to trust me."},
            "stage3": {"q": "[상황] 추운 날씨에 나가는 친구에게 옷차림 조언을 할 때", "target": "You've got to dress warm."},
            "stage4": {"q": "[롤플레잉] A: 'I'm walking home alone at midnight.' / B: '너 진짜 조심해야 해!'", "target": "You've got to be careful!"}
        }
    },
    {
        "id": "P007",
        "pattern": "I'm heading to~",
        "meaning": "~로 가는 중이야",
        "examples": {
            "stage1": {"q": "나 집에 가는 중이야.", "target": "I'm heading home."},
            "stage2": {"q": "나 회사로 출근하는 중이야.", "target": "I'm heading to work."},
            "stage3": {"q": "[상황] 친구가 전화로 어디 가냐고 물어볼 때 (시내 가는 중)", "target": "I'm heading downtown."},
            "stage4": {"q": "[롤플레잉] A: 'Where are you now?' / B: '나 지금 공항 가는 중이야.'", "target": "I'm heading to the airport."}
        }
    },
    {
        "id": "P008",
        "pattern": "How come~?",
        "meaning": "왜 ~한 거야? (이유 추궁)",
        "examples": {
            "stage1": {"q": "왜 늦었어?", "target": "How come you're late?"},
            "stage2": {"q": "왜 나한테 말 안 했어?", "target": "How come you didn't tell me?"},
            "stage3": {"q": "[상황] 약속 시각에 전화도 안 한 친구에게 물을 때", "target": "How come you didn't call me?"},
            "stage4": {"q": "[롤플레잉] A: 'I quit my job.' / B: '왜 갑자기 그만둔 거야?'", "target": "How come you quit all of a sudden?"}
        }
    },
    {
        "id": "P009",
        "pattern": "Don't tell me~",
        "meaning": "설마 ~인 건 아니겠지?",
        "examples": {
            "stage1": {"q": "설마 잊어버린 건 아니겠지?", "target": "Don't tell me you forgot."},
            "stage2": {"q": "설마 그거 잃어버린 건 아니지?", "target": "Don't tell me you lost it."},
            "stage3": {"q": "[상황] 우산을 집에 두고 온 친구에게 황당해하며 할 때", "target": "Don't tell me you left it at home."},
            "stage4": {"q": "[롤플레잉] A: 'Oops...' / B: '설마 또 실수한 건 아니겠지?'", "target": "Don't tell me you made a mistake again."}
        }
    },
    {
        "id": "P010",
        "pattern": "I'm not in the mood to~",
        "meaning": "~할 기분이 아니야",
        "examples": {
            "stage1": {"q": "나 지금 일할 기분이 아니야.", "target": "I'm not in the mood to work."},
            "stage2": {"q": "나 지금 얘기할 기분이 아니야.", "target": "I'm not in the mood to talk."},
            "stage3": {"q": "[상황] 주말에 나가자는 친구의 제안을 거절할 때", "target": "I'm not in the mood to go out."},
            "stage4": {"q": "[롤플레잉] A: 'Let's party!' / B: '미안, 나 오늘 놀 기분이 아니야.'", "target": "Sorry, I'm not in the mood to party today."}
        }
    },
    {
        "id": "P011",
        "pattern": "It's no use~",
        "meaning": "~해도 소용없어",
        "examples": {
            "stage1": {"q": "울어도 소용없어.", "target": "It's no use crying."},
            "stage2": {"q": "소리쳐도 소용없어.", "target": "It's no use shouting."},
            "stage3": {"q": "[상황] 이미 지나간 일에 불평하는 사람에게 조언할 때", "target": "It's no use complaining."},
            "stage4": {"q": "[롤플레잉] A: 'Should I call him again?' / B: '설득하려고 해봐야 소용없어.'", "target": "It's no use trying to persuade him."}
        }
    },
    {
        "id": "P012",
        "pattern": "It's up to you",
        "meaning": "네가 결정해 / 너한테 달렸어",
        "examples": {
            "stage1": {"q": "네가 결정해, 난 상관없어.", "target": "It's up to you, I really don't mind."},
            "stage2": {"q": "네가 결정해, 어느 쪽이든 괜찮아.", "target": "It's up to you, I don't mind either way."},
            "stage3": {"q": "[상황] 옳다고 생각하는 대로 결정하라고 격려할 때", "target": "It's up to you, do what feels right."},
            "stage4": {"q": "[롤플레잉] A: 'Where should we eat?' / B: '네가 골라, 난 다 좋아.'", "target": "It's up to you, I'm good with anything."}
        }
    },
    {
        "id": "P013",
        "pattern": "I have no choice but to~",
        "meaning": "~할 수밖에 없어",
        "examples": {
            "stage1": {"q": "기다릴 수밖에 없어.", "target": "I have no choice but to wait."},
            "stage2": {"q": "취소할 수밖에 없어.", "target": "I have no choice but to cancel."},
            "stage3": {"q": "[상황] 막차를 놓쳐 걸어갈 수밖에 없을 때", "target": "I have no choice but to walk."},
            "stage4": {"q": "[롤플레잉] A: 'The event was postponed.' / B: '일정을 변경할 수밖에 없겠네.'", "target": "We have no choice but to reschedule."}
        }
    },
    {
        "id": "P014",
        "pattern": "It's about time~",
        "meaning": "~할 때도 됐잖아",
        "examples": {
            "stage1": {"q": "너 이제 자러 갈 시간이야.", "target": "It's about time you went to bed."},
            "stage2": {"q": "너 이제 철들 때도 됐잖아.", "target": "It's about time you grew up."},
            "stage3": {"q": "[상황] 나이가 찼는데 결혼할 생각이 없는 친구에게 말할 때", "target": "It's about time you got married."},
            "stage4": {"q": "[롤플레잉] A: 'I'm still considering it.' / B: '이제 결정을 내릴 때도 됐어.'", "target": "It's about time you made a decision."}
        }
    },
    {
        "id": "P015",
        "pattern": "What happens if~",
        "meaning": "~하면 어떻게 돼?",
        "examples": {
            "stage1": {"q": "이거 클릭하면 어떻게 돼?", "target": "What happens if I click this?"},
            "stage2": {"q": "내일 비 오면 어떻게 돼?", "target": "What happens if it rains tomorrow?"},
            "stage3": {"q": "[상황] 모임에 내가 안 갈 경우 일어날 일을 물어볼 때", "target": "What happens if I don't go?"},
            "stage4": {"q": "[롤플레잉] A: 'Don't press that button.' / B: '누르면 무슨 일이 나는데?'", "target": "What happens if I press it?"}
        }
    },
    {
        "id": "P016",
        "pattern": "There goes my~",
        "meaning": "내 ~가 날아갔네 / 망했네",
        "examples": {
            "stage1": {"q": "내 다이어트 망했네.", "target": "There goes my diet."},
            "stage2": {"q": "내 돈 날아갔네.", "target": "There goes my money."},
            "stage3": {"q": "[상황] 주말에 비가 와서 여행 기회를 날렸을 때", "target": "There goes our chance."},
            "stage4": {"q": "[롤플레잉] A: 'Look at this delicious cake!' / B: '아, 내 다이어트도 끝이구나!'", "target": "There goes my diet!"}
        }
    },
    {
        "id": "P017",
        "pattern": "All I'm saying is~",
        "meaning": "내 말은 ~라는 거야 (취지 설명)",
        "examples": {
            "stage1": {"q": "내 말은 내가 널 믿는다는 거야.", "target": "All I'm saying is I trust you."},
            "stage2": {"q": "내 말은 내가 못 간다는 거야.", "target": "All I'm saying is I can't go."},
            "stage3": {"q": "[상황] 너무 비싸서 구매를 주저하는 이유를 덧붙일 때", "target": "All I'm saying is it's too expensive."},
            "stage4": {"q": "[롤플레잉] A: 'Are you mad at me?' / B: '아니, 조심하자는 뜻이야.'", "target": "All I'm saying is we should be careful."}
        }
    },
    {
        "id": "P018",
        "pattern": "You don't have to~",
        "meaning": "~하지 않아도 돼",
        "examples": {
            "stage1": {"q": "미안해하지 않아도 돼.", "target": "You don't have to say sorry."},
            "stage2": {"q": "완벽하지 않아도 돼.", "target": "You don't have to be perfect."},
            "stage3": {"q": "[상황] 남은 음식을 억지로 다 먹으려는 친구에게 할 때", "target": "You don't have to finish it."},
            "stage4": {"q": "[롤플레잉] A: 'I'll change my clothes.' / B: '그렇게 차려입지 않아도 돼.'", "target": "You don't need to dress up."}
        }
    },
    {
        "id": "P019",
        "pattern": "Give it to me straight",
        "meaning": "솔직하게 말해 줘",
        "examples": {
            "stage1": {"q": "솔직히 말해 줘, 이거 마음에 들어?", "target": "Give it to me straight. Do you like it?"},
            "stage2": {"q": "솔직히 말해 줘, 그렇게 별로야?", "target": "Give it to me straight. Is it that bad?"},
            "stage3": {"q": "[상황] 본인이 잘못했는지 솔직한 피드백을 구할 때", "target": "Give it to me straight. Am I wrong?"},
            "stage4": {"q": "[롤플레잉] A: 'Well...' / B: '빙빙 돌리지 말고 솔직히 말해 줘.'", "target": "Don't beat around the bush. Give it to me straight."}
        }
    },
    {
        "id": "P020",
        "pattern": "When you are done~",
        "meaning": "~하고 나면 / ~ 다 하고 나서",
        "examples": {
            "stage1": {"q": "책 다 읽고 나면 불 좀 꺼줘.", "target": "When you are done reading, turn off the light."},
            "stage2": {"q": "밥 다 먹고 나면 테이블 닦아줘.", "target": "When you are done eating, wipe the table."},
            "stage3": {"q": "[상황] 울고 있는 아이를 달랠 때", "target": "When you are done crying, everything will be okay."},
            "stage4": {"q": "[롤플레잉] A: 'I'm using the bathroom.' / B: '다 쓰면 알려줘.'", "target": "When you are done, let me know."}
        }
    },
    {
        "id": "P021",
        "pattern": "I didn't realize~",
        "meaning": "~인 줄 몰랐어",
        "examples": {
            "stage1": {"q": "이게 공짜인 줄 몰랐어.", "target": "I didn't realize this was free."},
            "stage2": {"q": "시간이 이렇게 늦은 줄 몰랐어.", "target": "I didn't realize it was so late."},
            "stage3": {"q": "[상황] 밖에 비가 내리고 있는 것을 나중에 알았을 때", "target": "I didn't realize it was raining."},
            "stage4": {"q": "[롤플레잉] A: 'You're step on my foot!' / B: '아 미안해, 몰랐어!'", "target": "Oh sorry, I didn't realize that!"}
        }
    },
    {
        "id": "P022",
        "pattern": "There used to be~",
        "meaning": "예전에 ~가 있었어",
        "examples": {
            "stage1": {"q": "여기에 예전에 카페가 있었어.", "target": "There used to be a cafe here."},
            "stage2": {"q": "여기에 예전에 마트가 있었어.", "target": "There used to be a mart here."},
            "stage3": {"q": "[상황] 옛 동네를 지나며 빵집 위치를 기억할 때", "target": "There used to be a bakery nearby."},
            "stage4": {"q": "[롤플레잉] A: 'Where is the park?' / B: '예전에 여기에 공원이 있었는데 변했어.'", "target": "There used to be a park here."}
        }
    },
    {
        "id": "P023",
        "pattern": "What matters most is~",
        "meaning": "가장 중요한 것은 ~이야",
        "examples": {
            "stage1": {"q": "가장 중요한 것은 너의 마음가짐이야.", "target": "What matters most is your mindset."},
            "stage2": {"q": "가장 중요한 것은 정직함이야.", "target": "What matters most is honesty."},
            "stage3": {"q": "[상황] 여행 준비 시 안전의 중요성을 언급할 때", "target": "What matters most is safety."},
            "stage4": {"q": "[롤플레잉] A: 'Did we win?' / B: '결과보다 최선을 다한 게 중요해.'", "target": "What matters most is that you tried."}
        }
    },
    {
        "id": "P024",
        "pattern": "I can't bring myself to~",
        "meaning": "차마 ~를 못하겠어",
        "examples": {
            "stage1": {"q": "차마 발걸음이 떨어지지 않네.", "target": "I can't bring myself to leave."},
            "stage2": {"q": "차마 눈 뜨고 못 보겠어.", "target": "I can't bring myself to watch this."},
            "stage3": {"q": "[상황] 상처를 줄까 봐 차마 거절의 말을 못 할 때", "target": "I can't bring myself to say it."},
            "stage4": {"q": "[롤플레잉] A: 'Did you tell him?' / B: '아니, 차마 진실을 말 못 했어.'", "target": "I can't bring myself to tell him the truth."}
        }
    },
    {
        "id": "P025",
        "pattern": "There's no harm in~",
        "meaning": "~해서 나쁠 건 없잖아",
        "examples": {
            "stage1": {"q": "물어본다고 나쁠 건 없잖아.", "target": "There's no harm in asking."},
            "stage2": {"q": "시도해 봐서 나쁠 건 없지.", "target": "There's no harm in trying."},
            "stage3": {"q": "[상황] 돌다리도 두들겨 건너듯 조심성을 강조할 때", "target": "There's no harm in being careful."},
            "stage4": {"q": "[롤플레잉] A: 'Should I double check?' / B: '확인해서 나쁠 건 없지.'", "target": "There's no harm in checking."}
        }
    },
    {
        "id": "P026",
        "pattern": "I see your point, but~",
        "meaning": "무슨 말인지 알겠는데, ~",
        "examples": {
            "stage1": {"q": "무슨 말인지 알겠는데 나는 동의하지 않아.", "target": "I see your point, but I disagree."},
            "stage2": {"q": "무슨 말인지 알겠는데 그건 너무 위험해.", "target": "I see your point, but it's too risky."},
            "stage3": {"q": "[상황] 상대 의견은 이해하지만 현실적 어려움을 토로할 때", "target": "I see your point, but it's not that easy."},
            "stage4": {"q": "[롤플레잉] A: 'We should buy it now.' / B: '취지는 알겠는데 예산이 부족해.'", "target": "I see your point, but we don't have enough budget."}
        }
    },
    {
        "id": "P027",
        "pattern": "That's what friends are for",
        "meaning": "친구 좋다는 게 그런 거지",
        "examples": {
            "stage1": {"q": "고마워! - 친구 좋다는 게 그런 거지.", "target": "Thank you! - That's what friends are for."},
            "stage2": {"q": "가족 좋다는 게 그런 거지.", "target": "That's what family is for."},
            "stage3": {"q": "[상황] 힘들 때 도와준 친구에게 고마움을 표할 때의 답장", "target": "That's what friends are for!"},
            "stage4": {"q": "[롤플레잉] A: 'Thanks for helping me move!' / B: '에이, 친구끼리 당연한 거지!'", "target": "No problem! That's what friends are for."}
        }
    },
    {
        "id": "P028",
        "pattern": "At the end of the day~",
        "meaning": "결국 ~이 가장 중요해 (최종 결론)",
        "examples": {
            "stage1": {"q": "결국 가족이 가장 중요해.", "target": "At the end of the day, family comes first."},
            "stage2": {"q": "결국 건강이 가장 중요해.", "target": "At the end of the day, health is the most important."},
            "stage3": {"q": "[상황] 여러 복잡한 문제를 뒤로하고 완벽한 사람은 없음을 상기할 때", "target": "At the end of the day, nobody is perfect."},
            "stage4": {"q": "[롤플레잉] A: 'We had a lot of arguments.' / B: '결국 우린 여전히 친구잖아.'", "target": "At the end of the day, we are still friends."}
        }
    },
    {
        "id": "P029",
        "pattern": "As soon as~",
        "meaning": "~하자마자",
        "examples": {
            "stage1": {"q": "퇴근하자마자 전화할게.", "target": "I'll call you as soon as I get off work."},
            "stage2": {"q": "나는 눕자마자 잠들었어.", "target": "I fell asleep as soon as I lay down."},
            "stage3": {"q": "[상황] 아침 습관으로 눈뜨자마자 커피를 마신다고 할 때", "target": "I drink coffee as soon as I wake up."},
            "stage4": {"q": "[롤플레잉] A: 'When will you arrive?' / B: '도착하자마자 알려줄게.'", "target": "I'll let you know as soon as I arrive."}
        }
    },
    {
        "id": "P030",
        "pattern": "Speaking of~",
        "meaning": "~얘기가 나와서 말인데",
        "examples": {
            "stage1": {"q": "생일 얘기가 나와서 말인데, 너 생일 언제야?", "target": "Speaking of birthdays, when is yours?"},
            "stage2": {"q": "음식 얘기가 나와서 말인데, 나 배고파지고 있어.", "target": "Speaking of food, I'm getting hungry."},
            "stage3": {"q": "[상황] 대화 중 파티 주제가 나왔을 때 참석자를 물어볼 때", "target": "Speaking of the party, who is coming?"},
            "stage4": {"q": "[롤플레잉] A: 'I visited New York last year.' / B: '뉴욕 얘기 나와서 말인데 거기 날씨 어땠어?'", "target": "Speaking of New York, how was the weather?"}
        }
    }
]

STAGE_INTERVALS = {1: 1, 2: 3, 3: 7, 4: 30}

def load_progress():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    initial = {}
    now_str = datetime.now().strftime("%Y-%m-%d")
    for item in PATTERN_DB:
        initial[item["id"]] = {
            "stage": 1,
            "next_review": now_str,
            "review_count": 0,
            "last_result": None
        }
    return initial

def save_progress(progress):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def update_srs(progress, pid, rating):
    data = progress[pid]
    curr_stage = data["stage"]
    if rating == "Easy":
        new_stage = min(4, curr_stage + 2)
        days = STAGE_INTERVALS[new_stage] * 1.5
    elif rating == "Good":
        new_stage = min(4, curr_stage + 1)
        days = STAGE_INTERVALS[new_stage]
    elif rating == "Hard":
        new_stage = curr_stage
        days = 1
    else: # Again
        new_stage = 1
        days = 0
    
    next_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    data["stage"] = new_stage
    data["next_review"] = next_date
    data["review_count"] += 1
    data["last_result"] = rating
    save_progress(progress)
    return new_stage, next_date

# --- App UI Layout ---
st.title("🧠 딴딴 패턴영어 x 에빙하우스 자동화 튜터")
st.caption("🔊 원어민 TTS 영어 발음 지원 & 📺 딴딴영어 원본 콘텐츠 바로가기 연동 | 에빙하우스 스마트 튜터 v2")

progress = load_progress()

tab1, tab2, tab3, tab4 = st.tabs(["✍️ 1:1 대화형 퀴즈", "🎴 플래시카드", "📊 SRS 학습 대시보드", "📚 전체 패턴 라이브러리"])

# Tab 1: Interactive SRS Quiz
with tab1:
    st.subheader("에빙하우스 망각곡선 오늘의 맞춤 훈련")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Filter items due for review or overall active
    due_items = [item for item in PATTERN_DB if progress[item["id"]]["next_review"] <= today_str]
    if not due_items:
        due_items = PATTERN_DB # Fallback if all caught up
    
    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0
    
    idx = st.session_state.quiz_index % len(due_items)
    curr_item = due_items[idx]
    curr_prog = progress[curr_item["id"]]
    stage_num = curr_prog["stage"]
    stage_key = f"stage{stage_num}"
    ex_data = curr_item["examples"][stage_key]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📌 **현재 복습 패턴**: `{curr_item['pattern']}` ({curr_item['meaning']}) | **에빙하우스 {stage_num}단계**")
        audio_col, link_col = st.columns([2, 3])
        with audio_col:
            render_tts_button(curr_item['pattern'], label="🔊 패턴 발음 듣기")
        with link_col:
            v_url = get_content_link(curr_item['pattern'])
            st.markdown(f"[📺 원본 딴딴영어 패턴 콘텐츠 보기]({v_url})")

        st.markdown(f"### ❓ Q: {ex_data['q']}")
        
        user_ans = st.text_input("영어로 응답을 입력하세요 (또는 생각 후 정답 확인):", key=f"q_{idx}")
        
        if st.button("👁️ 정답 및 예시 확인", key=f"ans_btn_{idx}"):
            st.success(f"**정답**: `{ex_data['target']}`")
            render_tts_button(ex_data['target'], label="🔊 정답 문장 전체 발음 듣기")

            
        st.markdown("---")
        st.markdown("#### **회상 난이도 평가 (SRS 피드백)**")
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        
        with b_col1:
            if st.button("🟢 Easy (쉬움)", use_container_width=True):
                ns, nd = update_srs(progress, curr_item["id"], "Easy")
                st.toast(f"Easy! 단계 {ns}로 상승, 다음 복습: {nd}")
                st.session_state.quiz_index += 1
                st.rerun()
        with b_col2:
            if st.button("🔵 Good (적당함)", use_container_width=True):
                ns, nd = update_srs(progress, curr_item["id"], "Good")
                st.toast(f"Good! 단계 {ns}로 진행, 다음 복습: {nd}")
                st.session_state.quiz_index += 1
                st.rerun()
        with b_col3:
            if st.button("🟠 Hard (어려움)", use_container_width=True):
                ns, nd = update_srs(progress, curr_item["id"], "Hard")
                st.toast(f"Hard! 내일 다시 복습 예정: {nd}")
                st.session_state.quiz_index += 1
                st.rerun()
        with b_col4:
            if st.button("🔴 Again (재학습)", use_container_width=True):
                ns, nd = update_srs(progress, curr_item["id"], "Again")
                st.toast("Again! 1단계로 리셋되어 오늘 즉시 재복습합니다.")
                st.session_state.quiz_index += 1
                st.rerun()

    with col2:
        st.metric("오늘 복습 패턴 수", len(due_items))
        st.metric("현재 패턴 진행 Stage", f"Stage {stage_num} / 4")
        st.metric("총 누적 복습 횟수", f"{curr_prog['review_count']} 회")

# Tab 2: Flashcards
with tab2:
    st.subheader("🎴 딴딴영어 대표 패턴 플래시카드")
    fc_idx = st.slider("플래시카드 선택", 1, len(PATTERN_DB), 1) - 1
    fc_item = PATTERN_DB[fc_idx]
    
    col_fc1, col_fc2 = st.columns([3, 2])
    with col_fc1:
        st.markdown(f"### Card #{fc_idx+1}: **{fc_item['pattern']}**")
    with col_fc2:
        v_url = get_content_link(fc_item['pattern'])
        st.markdown(f"[📺 딴딴영어 원본 콘텐츠 보기]({v_url})")
    render_tts_button(fc_item['pattern'], label="🔊 대표 패턴 발음 듣기")

    
    show_back = st.toggle("카드 뒤집기 (답안 및 예문 보기)", value=False)
    
    if not show_back:
        st.markdown(f"""
        <div style="padding: 40px; border-radius: 15px; background-color: #f0f2f6; text-align: center; font-size: 28px; font-weight: bold; color: #1e1e1e;">
            {fc_item['pattern']}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding: 30px; border-radius: 15px; background-color: #e8f4f8; font-size: 20px; color: #0d47a1;">
            <h4>💡 뜻: {fc_item['meaning']}</h4>
            <hr>
            <p><b>Stage 1 예문:</b> {fc_item['examples']['stage1']['q']} ➔ <code>{fc_item['examples']['stage1']['target']}</code></p>
            <p><b>Stage 2 예문:</b> {fc_item['examples']['stage2']['q']} ➔ <code>{fc_item['examples']['stage2']['target']}</code></p>
            <p><b>Stage 3 예문:</b> {fc_item['examples']['stage3']['q']} ➔ <code>{fc_item['examples']['stage3']['target']}</code></p>
            <p><b>Stage 4 예문:</b> {fc_item['examples']['stage4']['q']} ➔ <code>{fc_item['examples']['stage4']['target']}</code></p>
        </div>
        st.markdown("#### 🔊 단계별 예문 발음 들어보기")
        s1, s2, s3, s4 = st.columns(4)
        with s1: render_tts_button(fc_item['examples']['stage1']['target'], label="🔊 Stage 1 발음")
        with s2: render_tts_button(fc_item['examples']['stage2']['target'], label="🔊 Stage 2 발음")
        with s3: render_tts_button(fc_item['examples']['stage3']['target'], label="🔊 Stage 3 발음")
        with s4: render_tts_button(fc_item['examples']['stage4']['target'], label="🔊 Stage 4 발음")

        """, unsafe_allow_html=True)

# Tab 3: SRS Dashboard
with tab3:
    st.subheader("📊 에빙하우스 성취도 & 스케줄 대시보드")
    
    rows = []
    for item in PATTERN_DB:
        p_info = progress[item["id"]]
        rows.append({
            "ID": item["id"],
            "패턴": item["pattern"],
            "의미": item["meaning"],
            "현재 Stage": f"Stage {p_info['stage']}",
            "다음 복습일": p_info["next_review"],
            "복습 횟수": p_info["review_count"],
            "최근 평가": p_info["last_result"] or "미실행"
        })
    df = pd.DataFrame(rows)
    
    stage_counts = df["현재 Stage"].value_counts()
    
    mcol1, mcol2, mcol3 = st.columns(3)
    mcol1.metric("총 등록 패턴", f"{len(PATTERN_DB)} 개")
    mcol2.metric("Stage 4 (장기기억 정착)", f"{stage_counts.get('Stage 4', 0)} 개")
    mcol3.metric("Stage 1~3 (복습 진행 중)", f"{len(PATTERN_DB) - stage_counts.get('Stage 4', 0)} 개")
    
    st.markdown("### 📋 패턴별 상세 학습 이력")
    st.dataframe(df, use_container_width=True)

# Tab 4: Pattern Library
with tab4:
    st.subheader("📚 딴딴 패턴영어 전체 라이브러리")
    search_q = st.text_input("🔍 패턴 또는 의미 검색:", "")
    
    for item in PATTERN_DB:
        if search_q.lower() in item["pattern"].lower() or search_q in item["meaning"]:
            with st.expander(f"📌 {item['pattern']} - {item['meaning']}"):
                for stg, ex in item["examples"].items():
                    st.write(f"- **{stg.upper()}**: {ex['q']} ➔ `{ex['target']}`")
