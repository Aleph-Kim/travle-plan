# 오사카 plan.json 원본. 일정을 고칠 때는 이 파일을 고친 뒤 python3 build.py 로 다시 만듦
import base64, json, os, struct

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan.json')


# 구글 지도 주소의 0x…:0x… 값을 장소 ID(ChIJ…)로 바꿈. 두 값을 protobuf fixed64 두 필드로 묶어 base64url 인코딩한 형태
def pid(a, b):
    raw = bytes([0x0a, 0x12, 0x09]) + struct.pack('<Q', int(a, 16)) + bytes([0x11]) + struct.pack('<Q', int(b, 16))
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


HOTEL = pid('0x6000ddf32703d843', '0x75e14710f76f4765')
HOTEL_Q = '2-chōme-3-2 Sannō, Nishinari Ward, Osaka'
HOTEL_NAME = '2-chōme-3-2 Sannō, Nishinari Ward, Osaka'
KIX = pid('0x6000b91323cdfaf7', '0xf171a79f8d908f88')
TSUTENKAKU = pid('0x6000e76077e042ff', '0xe5cbcf56def44557')
KIX_STA = 'ChIJ1wO5URO5AGARXZucj1YFJhI'
SHINIMAMIYA = 'ChIJ2X3WNmLnAGARXflVC-kjn-s'
DOBUTSUEN = 'ChIJTXqq84rdAGARRGeIee0S7yw'
NIPPONBASHI = 'ChIJa6lKL0DnAGARIymf-LMc-Pk'
MEET = 'ChIJnx1PWhXnAGAR3bDSVXbMW64'
SEVEN = 'ChIJc4Wu3_PdAGAR2bO64XmPwwY'
FAMIMA_KIX = 'ChIJhchzsm65AGAR_JBPtty2woY'

items = []


def add(it):
    items.append(it)
    return len(items) - 1


def move(name, time, note, cost, frm, fn, to, tn, mode):
    return add({'type': 'move', 'name': name, 'time': time, 'note': note, 'cost': cost,
                'route': {'label': None, 'fromName': fn, 'from': frm, 'toName': tn, 'to': to, 'mode': mode}})


SKIP = {'name': '생략'}

# 13일 (금) 도착
d13 = [
    add({'name': '간사이 국제공항 T2', 'pid': KIX, 'time': '16:00', 'g': [4.1, 24923],
         'note': '도착 (제주항공 7C1393). 입국 심사, 위탁 수하물(15kg) 찾기',
         'tip': 'T2는 저가항공 전용 터미널. 철도역은 T1 쪽 에어로플라자와 이어져 있어 무료 연결버스로 이동'}),
    move('무료 연결버스로 에어로플라자', '16:50', 'T2 버스 정류장에서 T1, 에어로플라자행 무료 연결버스. 약 7~9분', 0,
         KIX, 'Kansai International Airport', KIX_STA, 'Kansai Airport Station', 'transit'),
    move('난카이 공항급행으로 신이마미야', '17:10', '간사이공항역에서 난바행 공항급행을 타고 신이마미야에서 내림. 약 45분. 요금 970엔 (확인 필요)', 970,
         KIX_STA, 'Kansai Airport Station', SHINIMAMIYA, 'Shin-Imamiya Station', 'transit'),
    move('걸어서 숙소', '18:00', '약 800m, 짐을 끌고 평지로 약 12분', 0,
         SHINIMAMIYA, 'Shin-Imamiya Station', HOTEL, HOTEL_NAME, 'walking'),
    add({'name': '숙소 체크인', 'pid': HOTEL, 'q': HOTEL_Q, 'time': '18:15',
         'note': '체크인 15시부터, 체크아웃 11시. 짐 풀고 잠깐 쉬기'}),
    move('걸어서 신세카이', '18:50', '약 800m, 평지로 약 12분. 쓰텐카쿠 아래 먹자거리', 0,
         HOTEL, HOTEL_NAME, TSUTENKAKU, 'Tsutenkaku', 'walking'),
    add({'type': 'choice', 'title': '저녁 (신세카이)', 'time': '19:05', 'multi': False,
         'note': '웨이팅 후기가 있는 곳은 뺌. 숙소에서 걸어서 700~950m',
         'options': [
             {'name': '잇토쿠 총본점 (쿠시카츠)', 'pid': 'ChIJeb2_BWDnAGARy0zq5dYoSfE', 'rec': True, 'g': [4.5, 11007],
              'tip': '에비스히가시 3-5-15, 쓰텐카쿠 옆. 매일 11:00~24:00. QR 주문, 외국어 메뉴',
              'pro': ['튀김옷이 얇고 바삭하다는 후기가 많음', 'QR 주문과 번역 메뉴라 주문이 쉬움', '가게가 넓고 바 자리와 테이블이 모두 있음', '아이와 와도 쾌적했다는 후기', '밤늦게까지 영업'],
              'con': ['가격에 비해 양이 적다는 의견 (1인 1,500엔 이상)', '생맥주가 비싸다는 의견', '주문 후 나오는 속도가 느리다는 후기']},
             {'name': '야키니쿠 Ohno (야키니쿠)', 'pid': 'ChIJT_MD-j7nAGAR78LiWY1xDdI', 'g': [4.9, 4755],
              'tip': '에비스히가시 2-5-11 2층. 매일 11:30~23:00. QR 주문',
              'pro': ['우설이 특히 맛있다는 후기', '한국어로 설명해 주는 직원이 있음', '코스 구성이 푸짐하다는 평 (6,600엔 코스 등)', 'QR 주문이라 일본어를 몰라도 됨', '직원이 친절하다는 후기가 많음'],
              'con': ['2층이고 입구 계단이 좁음', '예약 시 1인 1음료 필수 정책에 대한 불만', '냉면은 별로라는 의견', '바쁠 때 음식이 늦을 수 있음']},
             {'name': '아파레 (쿠시카츠, 오코노미야키)', 'pid': 'ChIJneRaYwDnAGARIs6kqeqLq2w', 'g': [4.1, 991],
              'tip': '에비스히가시 2-5-1, 신세카이 먹자거리 입구. 월~목 11:00~23:00, 금 11:00~02:00, 토 10:00~02:00, 일 10:00~23:00. 앱 주문',
              'pro': ['자리가 넓어 바로 앉기 좋다는 후기', '음식이 빨리 나옴', '먹자거리 입구라 찾기 쉬움', '직원이 친절하다는 후기'],
              'con': ['자릿세 1인 330엔, 1인 1음료', '오코노미야키가 짜다는 의견', '무난하고 특별할 것 없다는 평']},
             {'name': "Johnny's (가라아게)", 'pid': 'ChIJ6eDmfN7nAGARKPeVtfx_4os', 'g': [4.9, 936],
              'tip': '에비스히가시 1-4-6, 덴노지 쪽. 화~토 17:00~23:00, 일 17:00~22:00, 월요일 휴무',
              'pro': ['닭이 부드럽고 튀김옷이 딱딱하지 않음', '한국어 메뉴판과 사진', '가격이 싼 편 (양념치킨 레귤러 690엔)', '사장이 친절하고 영어 가능', '밥을 추가해 식사 가능'],
              'con': ['작은 로컬 가게 분위기', '한국 치킨이 더 맛있다는 의견', '노래하는 손님이 있을 수 있음']},
             {'name': '소혼케 사라시나 (소바)', 'pid': 'ChIJlwBNfmDnAGARzvqWbXA2dt4', 'g': [4.4, 688],
              'tip': '에비스히가시 2-7-20 1층. 11:30~22:00, 수요일 휴무. 소바, 우동, 튀김, 덮밥',
              'pro': ['튀김과 소바를 함께 먹기 좋음', '조용하고 일본 정취가 있는 분위기', '사장과 직원이 친절', '우동, 오야코동, 다시마키 등 메뉴가 다양'],
              'con': ['일본어 위주 메뉴 (가게 앞 사진 메뉴판 참고)', '국물이 예전보다 짜졌다는 의견']},
             {'name': '편의점 (세븐일레븐 추천)', 'pid': SEVEN, 'g': [3.7, 68],
              'tip': '세븐일레븐 아사히마치 1-1-10, 숙소에서 약 450m. 24시간. 사서 숙소에서 먹기'},
             SKIP]}),
    add({'name': '쓰텐카쿠 전망대', 'pid': TSUTENKAKU, 'time': '20:15', 'cost': 1500, 'g': [4.1, 44236],
         'note': '신세카이 먹자거리 한가운데. 엘리베이터로 전망대까지',
         'tip': '09:00~21:45. 일반 전망대와 특별 옥외 전망대 세트 1,500엔 (2026년 4월 개정, 확인 필요)'}),
    add({'name': '숙소 가는 길 편의점에서 내일 아침거리', 'time': '21:00',
         'note': '14일은 07:15에 나가야 해서 아침은 미리 사 둠. 숙소까지 걸어서 약 15분'}),
    add({'type': 'sleep', 'name': '취침', 'time': '22:00'}),
]


def tour_morning(t_wake, guide, url):
    return [
        add({'name': '기상, 전날 사 둔 아침', 'time': t_wake}),
        move('걸어서 도부쓰엔마에역', '07:10', '약 300m, 4분', 0, HOTEL, HOTEL_NAME, DOBUTSUEN, 'Dobutsuen-mae Station', 'walking'),
        move('사카이스지선으로 닛폰바시', '07:15', '기타하마 방면, 2정거장 약 4분. 190엔 (확인 필요). 닛폰바시역은 개찰구와 지상 사이 엘리베이터 있음 (출구 번호 확인 필요). 역에서 집합 장소까지 약 300m', 190,
             DOBUTSUEN, 'Dobutsuen-mae Station', NIPPONBASHI, 'Nipponbashi Station', 'transit'),
        add({'name': '츠루동탄 소에몬초점 앞 집합', 'pid': MEET, 'time': '07:40', 'g': [4.0, 4947], 'note': guide, 'url': url}),
    ]


def tour_evening(t_end, dinner, sleep_t, buy):
    out = [
        add({'name': '투어 해산', 'pid': MEET, 'time': t_end, 'note': '해산 장소와 시각은 가정 (바우처 확인 필요). 출발지인 소에몬초 근처로 봄'}),
        dinner,
        move('사카이스지선으로 도부쓰엔마에', '19:45', '닛폰바시에서 덴가차야 방면, 2정거장 약 4분. 190엔 (확인 필요). 도부쓰엔마에역은 사카이스지선 홈에서 미도스지선 북개찰을 거쳐 5번 출구까지 단차 없음 (확인 필요). 숙소까지 약 300m', 190,
             NIPPONBASHI, 'Nipponbashi Station', DOBUTSUEN, 'Dobutsuen-mae Station', 'transit'),
    ]
    if buy:
        out.append(add({'name': '숙소 가는 길 편의점에서 내일 아침거리', 'time': '20:00', 'note': '내일도 07:15에 나감'}))
    out.append(add({'type': 'sleep', 'name': '취침', 'time': sleep_t}))
    return out


def dinner(time, options):
    return add({'type': 'choice', 'title': '저녁 (해산 장소 근처)', 'time': time, 'multi': False,
                'note': '해산 장소에서 걸어서 300m 안. 웨이팅 후기가 있는 곳은 뺌', 'options': options + [
                    {'name': '편의점 (세븐일레븐 추천)', 'pid': SEVEN, 'g': [3.7, 68],
                     'tip': '세븐일레븐 아사히마치 1-1-10, 숙소에서 약 450m. 24시간. 사서 숙소에서 먹기'}, SKIP]})


# 14일 (토) 나라, 고베 투어
d14 = tour_morning('06:45', '라쿠투어 나라, 고베 버스투어. 07:50 정시 출발, 늦으면 노쇼. 빨간 깃발 가이드에게 예약자 이름을 말하고 버스 배정', 'https://www.waug.com/ko/activities/129562') + [
    add({'name': '도다이지 대불전', 'pid': 'ChIJ05CPWJo5AWARJ31urWvbmR0', 'time': '09:30', 'g': [4.7, 3548],
         'note': '투어 장소의 순서와 시각은 가이드 안내를 따름', 'tip': '입장료 별도. 버스에서 내려 남대문까지 가깝고 평지'}),
    add({'name': '나라 공원 (사슴)', 'pid': 'ChIJYWCMvZY5AWARVnREV_OsbPk', 'time': '10:30', 'g': [4.6, 77930],
         'tip': '평지. 사슴 센베로 사슴에게 먹이 주기'}),
    add({'type': 'choice', 'title': '아리마 온천', 'time': '13:00', 'multi': False,
         'note': '입욕료 별도. 탕에 들어가기 힘들면 바로 앞 족탕으로',
         'options': [
             {'name': '금탕 (긴노유)', 'pid': 'ChIJb65UH0KKAGARz_AgIriHO4E', 'rec': True, 'g': [4.0, 4749],
              'tip': '금빛 온천수 외탕. 역에서 걸어서 약 5분으로 은탕(약 10분)보다 가까움. 요금은 확인 필요'},
             {'name': '태합의 족탕 (무료)', 'pid': 'ChIJq9VCH0KKAGAR10UO8_l2j4c', 'g': [4.1, 351],
              'tip': '금탕 바로 앞 무료 족탕. 08:00~22:00, 둘째와 넷째 화요일 휴무. 앉아서 쉬기 좋음'}]}),
    add({'type': 'choice', 'title': '기타노 이진칸', 'time': '15:00', 'multi': False,
         'note': '이진칸 거리는 가파른 언덕. 힘들면 언덕 중간 카페에서 쉬며 기다리기',
         'options': [
             {'name': '카자미도리노 야카타 (언덕 위)', 'pid': 'ChIJSYLOTd6OAGARXRwytsn7_HM', 'g': [4.1, 2103],
              'tip': '이진칸 거리 대표 건물. 언덕 끝 광장까지 올라가야 함'},
             {'name': '스타벅스 고베 기타노이진칸점에서 쉬기', 'pid': 'ChIJrVIbmeCOAGARQAS2XOtwiLs', 'rec': True, 'g': [4.4, 4248],
              'tip': '기타노자카 중간의 옛 서양식 주택을 쓴 매장. 언덕 위까지 오르지 않고 기다리기'}]}),
    add({'name': '메리켄 파크', 'pid': 'ChIJZVMziP-OAGAR11WzVqBbDIQ', 'time': '16:00', 'g': [4.3, 12307], 'tip': '바닷가 공원, 평지'}),
    add({'name': '하버랜드 모자이크', 'pid': 'ChIJf0p386qPAGARkwSdWbx_tS8', 'time': '16:30', 'g': [4.2, 6623], 'tip': '바닷가 쇼핑몰, 평지. 포트타워와 대관람차가 보임'}),
] + tour_evening('18:00', dinner('18:10', [
    {'name': '고베규 와노노미야 (철판구이)', 'pid': 'ChIJyW7UIRXnAGARnnWtyiPd6Io', 'rec': True, 'g': [4.8, 5178],
     'tip': '도톤보리 1-5-2. 매일 11:00~22:00. 셰프가 앞에서 구워 주는 바 자리 위주',
     'pro': ['고기가 부드럽다는 후기가 많음', '셰프가 친절하고 대화하며 구워 줌', '특별한 저녁으로 좋다는 평', '2~3명이 오기 좋은 바 자리'],
     'con': ['매우 비쌈 (고베규 300g에 5만 5천엔 후기)', '굽기를 요청과 다르게 했다는 후기', '바 자리 위주라 테이블은 적음']},
    {'name': '타츠노미야 (야키니쿠)', 'pid': 'ChIJvU1iiQ_nAGAR7THrKOi3LKw', 'g': [4.9, 5167],
     'tip': '소에몬초 1-14 1층, 해산 장소에서 약 60m. 매일 16:00~01:00. 무한리필 코스',
     'pro': ['무한리필인데 고기 질이 좋다는 후기가 많음', '한국어 메뉴판, 김치와 신라면도 있음', '고기 리필이 빠름', '직원이 친절', '해산 장소에서 가장 가까움'],
     'con': ['먹다 보면 느끼하다는 의견', '본점이 차면 다른 지점으로 안내함']},
    {'name': '자우오 (낚시 이자카야)', 'pid': 'ChIJoZwKdxrnAGARwVXWh7LlqBU', 'g': [4.3, 4021],
     'tip': '닛폰바시 1-1-13 호텔 소테츠 그랜드 프레사 지하 1층. 토 11:30~15:00, 16:00~23:00. 직접 낚은 생선을 요리해 줌',
     'pro': ['직접 낚시하는 특별한 경험', '간장조림이 맛있다는 후기', '직원 텐션이 높고 친절', '한국인 직원이 있음', '자리가 넉넉했다는 후기'],
     'con': ['물고기가 잘 안 잡힐 때가 있음', '회로 주문하면 일부만 준다는 의견', '1인 400엔 정도 자릿세', '수산시장 냄새가 남', '지하 1층 (엘리베이터는 확인 필요)']},
    {'name': '아케텐캇 (쿠시카츠)', 'pid': 'ChIJj3_Z2WvnAGARaIaY_8pMUFo', 'g': [4.8, 1808],
     'tip': '센니치마에 1-5-12. 매일 17:00~03:00. 2층에 금연석',
     'pro': ['튀김옷이 얇고 느끼하지 않다는 후기', '식지 않게 나눠서 내 줌', '사장과 직원이 매우 친절', '한국인 직원이 있음', '가성비가 좋다는 평'],
     'con': ['1층은 흡연 가능', '순서대로 내 줘서 늦게 나온다고 느낄 수 있음']},
    {'name': 'Toryumon (나베 이자카야)', 'pid': 'ChIJ3_sHxmvnAGARgoN-ilPsXNo', 'g': [4.9, 685],
     'tip': '소에몬초 2-30 1층. 화~일 18:00~03:00, 월요일 휴무. 치리토리 나베가 대표',
     'pro': ['나베가 푸짐하고 양념이 맛있음', '마지막에 리조또, 우동, 야키소바 중 골라 마무리', '직원과 사장이 매우 친절', '한국어 메뉴판', '맵기 조절 가능'],
     'con': ['간판이 잘 안 보여 지나치기 쉬움', '18시 개점']},
]), '22:00', True)

# 15일 (일) 교토 투어
d15 = tour_morning('06:45', '아이트립 교토 버스투어. 07:40~07:55 집합, 정각 출발. 아이트립 깃발 가이드 찾기. 미팅 장소와 시간은 바우처로 다시 확인', 'https://www.waug.com/ko/activities/148017') + [
    add({'type': 'choice', 'title': '후시미 이나리 신사', 'time': '09:00', 'multi': False,
         'note': '투어 장소의 순서와 시각은 가이드 안내를 따름. 본전까지는 평지, 센본도리이부터 오쿠샤 봉배소까지는 돌계단이 많음',
         'options': [
             {'name': '본전 참배와 센본도리이 입구까지', 'pid': 'ChIJIW0uPRUPAWAR6eI6dRzKGns', 'rec': True, 'g': [4.6, 93004],
              'tip': '계단을 오르지 않고 붉은 도리이 길 입구에서 사진 찍고 돌아오기'},
             {'name': '센본도리이 따라 오쿠샤 봉배소까지', 'pid': 'ChIJIW0uPRUPAWAR6eI6dRzKGns', 'g': [4.6, 93004],
              'tip': '돌계단이 이어짐. 힘든 사람은 본전 앞에서 기다리기'}]}),
    add({'name': '아라시야마 도게츠교', 'pid': 'ChIJd2mRAFMHAWARPSiWJOj4FOw', 'time': '10:30', 'g': [4.5, 5674], 'tip': '강을 건너는 다리. 강변은 평지'}),
    add({'name': '아라시야마 치쿠린 (대나무숲 길)', 'pid': 'ChIJrYtcv-urAWAR3XzWvXv8n_s', 'time': '11:00', 'g': [4.3, 26078], 'tip': '대나무숲 사이 산책길'}),
    add({'name': '금각사', 'pid': 'ChIJvUbrwCCoAWARX2QiHCsn5A4', 'time': '13:30', 'g': [4.6, 71409], 'tip': '입장료 별도'}),
    add({'name': '기요미즈데라', 'pid': 'ChIJB_vchdMIAWARujTEUIZlr2I', 'time': '15:30', 'g': [4.6, 73782],
         'tip': '입장료 별도. 경내에는 단차 없는 참배로가 있고, 건물 안팎과 오토와 폭포 주변 계단은 슬로프로 바뀌어 있음 (국토교통성 사례). 이 길로 돌기'}),
] + tour_evening('18:30', dinner('18:40', [
    {'name': 'Gyumon (규카츠, 와규 라멘)', 'pid': 'ChIJRSwwgmjnAGARl3C4V77_OVo', 'g': [4.9, 7096],
     'tip': '도톤보리 1-3-15 5층. 매일 12:00~23:00. 할랄 인증. 규카츠, 텐동, 매운 라멘',
     'pro': ['규카츠와 텐동이 맛있다는 후기', '라멘 국물이 진하고 한국인 입맛에 맞다는 평', '직원이 친절', '음식이 10~15분이면 나옴'],
     'con': ['가격이 매우 높은 편 (2명 약 12만원 후기)', '손님이 거의 외국인', '양이 적다는 의견', '5층 (엘리베이터는 확인 필요)']},
    {'name': '사콘 (야키니쿠)', 'pid': 'ChIJHzFKUADnAGARJT1R72JXmcE', 'g': [4.8, 4520],
     'tip': '도톤보리 1-4-22 2층. 매일 11:00~24:00. 무한리필, 셀프바',
     'pro': ['부모님과 왔는데 입맛에 맞아 만족했다는 후기', '고기 질이 좋고 양이 많음', '카레, 과일 등 사이드가 다양', '매장이 깨끗함', '직원이 친절'],
     'con': ['소고기는 전표를 들고 가서 주문하는 방식', '주류 무한리필은 직접 섞어야 함', '첫 고기가 늦게 나왔다는 후기', '2층']},
    {'name': '와규토부타 (샤브샤브, 스키야키)', 'pid': 'ChIJzfABJADnAGAR4MGxwHN7PpA', 'g': [4.8, 3152],
     'tip': '히가시신사이바시 2-5-8 2층. 매일 16:00~01:00. 무한리필 7,500엔 코스 등. 구글 예약 가능',
     'pro': ['A5 와규가 입에서 녹는다는 후기', '조용해서 가족끼리 오기 좋다는 평', '김치가 한국식', '주류 무한리필 선택 가능', '구글로 쉽게 예약'],
     'con': ['코스 가격이 높은 편', '2층']},
    {'name': 'Riverside Grill Wonder (강변 술집)', 'pid': 'ChIJOekXXtLnAGARFGJDmqRmmtU', 'g': [4.8, 1762],
     'tip': '도톤보리 1-1-6 지하 1층, 강가. 일~목 17:00~24:00, 금, 토 17:00~02:00. 타코 등 간단한 안주',
     'pro': ['도톤보리 강 바로 옆이라 분위기가 좋음', '난로가 있어 따뜻함', '직원이 친절하고 유쾌', '가격이 적당'],
     'con': ['술집이라 식사 메뉴는 간단함', '흥겨운 분위기라 시끄러울 수 있음', '좁은 길 옆, 강가로 내려가야 함']},
    {'name': '쇼쿠도엔 (야키니쿠, 스키야키)', 'pid': 'ChIJTfxr_hTnAGARJ2MrUG8rx18', 'g': [4.4, 1000],
     'tip': '소에몬초 5-13. 매일 11:30~23:00. 한국 출신 사장. 스키야키 정식 3,500엔 후기',
     'pro': ['어머니와 왔는데 넓고 깔끔했다는 후기', '조용하고 고급스러운 분위기', '음식이 빨리 나옴', '와규와 꼬리곰탕 호평', '돌솥비빔밥, 김밥 등 한식도 있음'],
     'con': ['가격이 있는 편', '김치와 냉면은 한국 맛과 다르다는 의견']},
]), '22:30', False)

# 16일 (월) 출국
d16 = [
    add({'name': '체크아웃', 'pid': HOTEL, 'q': HOTEL_Q, 'time': '11:00', 'note': '아침 일정 없음. 11시까지 체크아웃'}),
    move('걸어서 신이마미야역', '11:05', '약 800m, 짐을 끌고 평지로 약 12분', 0,
         HOTEL, HOTEL_NAME, SHINIMAMIYA, 'Shin-Imamiya Station', 'walking'),
    move('난카이 공항급행으로 간사이공항', '11:25', '신이마미야에서 간사이공항행 공항급행. 약 45분. 요금 970엔 (확인 필요)', 970,
         SHINIMAMIYA, 'Shin-Imamiya Station', KIX_STA, 'Kansai Airport Station', 'transit'),
    add({'type': 'choice', 'title': '점심 (간사이공항 T1, 에어로플라자)', 'time': '12:20', 'multi': False,
         'note': 'T2 출국장에는 식당이 거의 없어 T1 쪽에서 먹고 이동. 웨이팅 후기가 없는 곳이 4곳뿐이라 4곳만',
         'options': [
             {'name': '키네야 무기마루 (우동)', 'pid': 'ChIJJQ143GO5AGARqAlAZwkQYq4', 'rec': True, 'g': [4.2, 264],
              'tip': 'T1 2층 푸드코트. 매일 07:00~22:00. 우동을 고르고 튀김을 골라 계산하는 셀프 방식',
              'pro': ['공항치고 가격이 싸다는 평', '면이 쫄깃하다는 후기', '유부우동 국물이 맛있다는 후기', '빨리 먹을 수 있음'],
              'con': ['튀김이 식어 있다는 후기', '튀김을 많이 고르면 비싸짐', '세트 계산이 이상했다는 후기']},
             {'name': 'LE PAN 고베 기타노 (베이커리 카페)', 'pid': 'ChIJtYO5ZB65AGARKmioiWTTZXo', 'g': [3.9, 782],
              'tip': 'T1 2층. 매일 06:30~22:00. 빵, 케이크, 커피, 식사 메뉴',
              'pro': ['앉아서 쉬며 비행기 기다리기 좋음', '케이크가 부드럽다는 후기', '직원이 친절', '식사와 디저트를 함께 먹을 수 있음'],
              'con': ['가격이 비싸다는 의견', '소금빵은 실망스러웠다는 후기', '세트 주스 맛이 이상하다는 후기']},
             {'name': 'The Brasserie (호텔 닛코 뷔페)', 'pid': 'ChIJZea18xe5AGARwtp_rSfFbUY', 'g': [4.4, 231],
              'tip': '호텔 닛코 간사이 에어포트, 에어로플라자와 연결. 점심 11:30~14:30. 평일 점심 뷔페 3,500엔 후기 (확인 필요)',
              'pro': ['조용해서 천천히 먹기 좋음', '점심 시간이 3시간으로 넉넉함', '양식, 일식, 디저트까지 정갈하다는 평'],
              'con': ['가격이 높은 편', '요리 가짓수는 많지 않다는 의견']},
             {'name': '나카우 (덮밥, 우동)', 'pid': 'ChIJP4ltIcO5AGARnQ4pGUQeDd0', 'g': [3.7, 473],
              'tip': '에어로플라자 3층. 24시간. 키오스크로 주문하는 덮밥 체인',
              'pro': ['주문하면 2분 안에 나옴', '카츠동이 짜지 않고 담백하다는 후기', '메뉴가 다양', '가격이 합리적'],
              'con': ['체인 맛 그대로라는 평', '입맛에 안 맞는다는 후기']},
             {'name': '편의점 (패밀리마트)', 'pid': FAMIMA_KIX, 'g': [3.7, 85],
              'tip': '패밀리마트 간사이공항역점, 역 안. 24시간. 공항 근처에는 세븐일레븐이 승강장 매점뿐'},
             SKIP]}),
    move('무료 연결버스로 T2', '14:00', '에어로플라자 앞에서 T2행 무료 연결버스. 약 7~9분', 0,
         KIX_STA, 'Kansai Airport Station', KIX, 'Kansai International Airport', 'transit'),
    add({'name': '간사이 국제공항 T2 출국', 'pid': KIX, 'time': '14:15', 'g': [4.1, 24923],
         'note': '17:00 출발 (제주항공 7C1394). 체크인 마감 시각은 확인 필요',
         'tip': 'T2는 저가항공 전용 터미널. 출국장 안 식당이 적음'}),
]

base = lambda title, point, weather, sun, rain_note: {
    'title': title, 'point': point, 'weather': weather, 'sun': sun, 'rain': sun, 'rainNote': rain_note}

plan = {
    'trip': {'title': '오사카 동선', 'name': '오사카', 'period': '11월 13일 ~ 16일', 'timezone': 'Asia/Tokyo', 'currency': '엔'},
    'flights': [
        {'label': '가는 편', 'date': '11/13 (금)', 'dep': '14:10 인천 T1', 'arr': '16:00 간사이 T2'},
        {'label': '오는 편', 'date': '11/16 (월)', 'dep': '17:00 간사이 T2', 'arr': '19:10 인천 T1'}],
    'locations': {
        'osaka': {'name': '오사카', 'lat': 34.6448, 'lon': 135.5071},
        'nara': {'name': '나라', 'lat': 34.6851, 'lon': 135.8430},
        'kyoto': {'name': '교토', 'lat': 34.9858, 'lon': 135.7588}},
    'rainThreshold': 60,
    'days': [
        {'date': '2026-11-13', 'label': '13일 금', 'full': '11월 13일 금요일', 'default': 'base',
         'plans': {'base': base('도착', '숙소 근처 신세카이에서 저녁, 쓰텐카쿠. 걷는 거리 약 3km', 'osaka', d13, '실내 위주라 그대로. 우산 챙기기')}},
        {'date': '2026-11-14', 'label': '14일 토', 'full': '11월 14일 토요일', 'default': 'base',
         'plans': {'base': base('나라, 고베 투어', '07:40 집합. 도다이지, 사슴공원, 아리마 온천, 기타노 이진칸, 하버랜드', 'nara', d14, '투어는 비가 와도 진행. 우산 챙기기')}},
        {'date': '2026-11-15', 'label': '15일 일', 'full': '11월 15일 일요일', 'default': 'base',
         'plans': {'base': base('교토 투어', '07:40 집합. 후시미 이나리, 아라시야마, 금각사, 기요미즈데라', 'kyoto', d15, '투어는 비가 와도 진행. 우산 챙기기')}},
        {'date': '2026-11-16', 'label': '16일 월', 'full': '11월 16일 월요일', 'default': 'base',
         'plans': {'base': base('출국', '아침 일정 없음. 11시 체크아웃 후 공항에서 점심, 17:00 출발', 'osaka', d16, '실내 이동이라 그대로')}},
    ],
    'items': items,
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(plan, f, ensure_ascii=False, separators=(',', ':'))
print(len(items), 'items')
