import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers.platpharm import PlatpharmScraper

CATEGORIES = [
    "거즈/붕대/탈지면",
    "건강기능식품",
    "건강음료/드링크/숙취해소",
    "구강청량제",
    "금연보조용품",
    "기능성/트러블",
    "눈/코/입/귀",
    "다이어트/변비",
    "마스크/방한대",
    "마스크팩/코팩",
    "물리치료/재활용품",
    "바디/다리/풋/제모",
    "반창고/밴드/파스",
    "발관리/수액시트",
    "벌꿀/프로폴리스",
    "베이비(baby)",
    "보호대/교정용품",
    "비타민/소아영양",
    "생식/영양식",
    "석류/콜라겐",
    "시럽병/용기",
    "식품/과자류",
    "얼굴(face)",
    "여성전용용품",
    "위생/화공",
    "유소아용품",
    "의료용구",
    "임산부용",
    "진단키트",
    "측정기기",
    "치아/구강용품",
    "콘돔/러브젤/청결제",
    "한방제제",
    "해충퇴치용품",
    "헤어(hair)",
    "홍삼/버섯",
    "기타건강식품",
    "기타의약외상품",
    "기타제품",
]

scraper = PlatpharmScraper()
scraper.run(CATEGORIES)
