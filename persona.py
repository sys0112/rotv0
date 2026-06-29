def normalize_input(s: str):
    s = s.strip().lower()
    if s in ("y", "예", "ㅇ", "네"):
        return "yes"
    if s in ("n", "아니오", "ㄴ", "아니"):
        return "no"
    return None


TREE = {
    "question": "생각하신 것이 살아있나요?",
    "yes": {
        "question": "동물인가요?",
        "yes": {
            "question": "날 수 있나요?",
            "yes": {
                "question": "곤충인가요?",
                "yes": {
                    "question": "아름다운 날개를 가지고 있나요?",
                    "yes": {"answer": "나비"},
                    "no": {
                        "question": "꿀을 만드나요?",
                        "yes": {"answer": "꿀벌"},
                        "no": {"answer": "잠자리"},
                    },
                },
                "no": {
                    "question": "새인가요?",
                    "yes": {
                        "question": "사냥하는 맹금류인가요?",
                        "yes": {"answer": "독수리"},
                        "no": {
                            "question": "남극에 사나요?",
                            "yes": {"answer": "펭귄"},
                            "no": {
                                "question": "화려한 깃털을 자랑하나요?",
                                "yes": {"answer": "공작"},
                                "no": {"answer": "타조"},
                            },
                        },
                    },
                    "no": {"answer": "박쥐"},
                },
            },
            "no": {
                "question": "물속에서 사나요?",
                "yes": {
                    "question": "포유류인가요?",
                    "yes": {
                        "question": "몸길이가 5미터 이상인가요?",
                        "yes": {"answer": "고래"},
                        "no": {"answer": "돌고래"},
                    },
                    "no": {
                        "question": "다리가 여덟 개인가요?",
                        "yes": {"answer": "문어"},
                        "no": {
                            "question": "매우 위험한 포식자인가요?",
                            "yes": {"answer": "상어"},
                            "no": {
                                "question": "몸이 투명한가요?",
                                "yes": {"answer": "해파리"},
                                "no": {"answer": "금붕어"},
                            },
                        },
                    },
                },
                "no": {
                    "question": "몸집이 소보다 큰가요?",
                    "yes": {
                        "question": "코가 매우 긴가요?",
                        "yes": {"answer": "코끼리"},
                        "no": {
                            "question": "목이 매우 긴가요?",
                            "yes": {"answer": "기린"},
                            "no": {
                                "question": "검은 흰 줄무늬가 있나요?",
                                "yes": {"answer": "얼룩말"},
                                "no": {"answer": "하마"},
                            },
                        },
                    },
                    "no": {
                        "question": "고양이과 동물인가요?",
                        "yes": {
                            "question": "줄무늬가 있나요?",
                            "yes": {"answer": "호랑이"},
                            "no": {
                                "question": "점박이 무늬가 있나요?",
                                "yes": {"answer": "치타"},
                                "no": {"answer": "사자"},
                            },
                        },
                        "no": {
                            "question": "흑백 색상인가요?",
                            "yes": {
                                "question": "대나무를 먹나요?",
                                "yes": {"answer": "판다"},
                                "no": {"answer": "얼룩말"},
                            },
                            "no": {
                                "question": "나무 위에서 주로 생활하나요?",
                                "yes": {
                                    "question": "호주에 사나요?",
                                    "yes": {"answer": "코알라"},
                                    "no": {"answer": "고릴라"},
                                },
                                "no": {
                                    "question": "딱딱한 등딱지가 있나요?",
                                    "yes": {"answer": "거북이"},
                                    "no": {
                                        "question": "색을 바꿀 수 있나요?",
                                        "yes": {"answer": "카멜레온"},
                                        "no": {
                                            "question": "무리 지어 사나요?",
                                            "yes": {"answer": "개미"},
                                            "no": {"answer": "악어"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "no": {
            "question": "실존 인물인가요? (가상 캐릭터가 아닌)",
            "yes": {
                "question": "한국인인가요?",
                "yes": {
                    "question": "100년 이상 전에 활동한 역사적 인물인가요?",
                    "yes": {
                        "question": "왕이었나요?",
                        "yes": {"answer": "세종대왕"},
                        "no": {
                            "question": "군인/장군인가요?",
                            "yes": {"answer": "이순신"},
                            "no": {"answer": "유관순"},
                        },
                    },
                    "no": {
                        "question": "운동선수인가요?",
                        "yes": {"answer": "손흥민"},
                        "no": {
                            "question": "가수/아이돌인가요?",
                            "yes": {
                                "question": "BTS 멤버인가요?",
                                "yes": {"answer": "BTS 정국"},
                                "no": {"answer": "이효리"},
                            },
                            "no": {
                                "question": "기업인인가요?",
                                "yes": {"answer": "이재용"},
                                "no": {"answer": "봉준호"},
                            },
                        },
                    },
                },
                "no": {
                    "question": "과학자인가요?",
                    "yes": {
                        "question": "물리학자인가요?",
                        "yes": {"answer": "아인슈타인"},
                        "no": {
                            "question": "발명가로도 유명한가요?",
                            "yes": {"answer": "에디슨"},
                            "no": {"answer": "마리 퀴리"},
                        },
                    },
                    "no": {
                        "question": "예술가(화가, 음악가)인가요?",
                        "yes": {
                            "question": "음악가인가요?",
                            "yes": {"answer": "모차르트"},
                            "no": {"answer": "레오나르도 다빈치"},
                        },
                        "no": {
                            "question": "IT/기술 분야 유명인인가요?",
                            "yes": {"answer": "스티브 잡스"},
                            "no": {
                                "question": "군인/황제인가요?",
                                "yes": {"answer": "나폴레옹"},
                                "no": {"answer": "셰익스피어"},
                            },
                        },
                    },
                },
            },
            "no": {
                "question": "슈퍼히어로인가요?",
                "yes": {
                    "question": "마블 캐릭터인가요?",
                    "yes": {
                        "question": "슈트를 입고 싸우나요?",
                        "yes": {"answer": "아이언맨"},
                        "no": {
                            "question": "거미 능력이 있나요?",
                            "yes": {"answer": "스파이더맨"},
                            "no": {"answer": "헐크"},
                        },
                    },
                    "no": {
                        "question": "어두운 도시를 지키는 히어로인가요?",
                        "yes": {"answer": "배트맨"},
                        "no": {"answer": "슈퍼맨"},
                    },
                },
                "no": {
                    "question": "애니메이션 캐릭터인가요?",
                    "yes": {
                        "question": "일본 애니메이션인가요?",
                        "yes": {
                            "question": "해적인가요?",
                            "yes": {"answer": "루피 (원피스)"},
                            "no": {
                                "question": "닌자인가요?",
                                "yes": {"answer": "나루토"},
                                "no": {
                                    "question": "로봇 고양이인가요?",
                                    "yes": {"answer": "도라에몽"},
                                    "no": {"answer": "손오공 (드래곤볼)"},
                                },
                            },
                        },
                        "no": {
                            "question": "디즈니 공주인가요?",
                            "yes": {"answer": "엘사"},
                            "no": {"answer": "호머 심슨"},
                        },
                    },
                    "no": {
                        "question": "마법을 쓸 수 있나요?",
                        "yes": {"answer": "해리 포터"},
                        "no": {
                            "question": "게임 캐릭터인가요?",
                            "yes": {"answer": "마리오"},
                            "no": {"answer": "셜록 홈즈"},
                        },
                    },
                },
            },
        },
    },
    "no": {
        "question": "손으로 들 수 있는 크기인가요?",
        "yes": {
            "question": "전자기기인가요?",
            "yes": {
                "question": "전화 통화가 주 기능인가요?",
                "yes": {"answer": "스마트폰"},
                "no": {
                    "question": "화면이 있나요?",
                    "yes": {
                        "question": "키보드가 달려 있나요?",
                        "yes": {"answer": "노트북"},
                        "no": {"answer": "카메라"},
                    },
                    "no": {
                        "question": "컴퓨터 제어에 사용하나요?",
                        "yes": {"answer": "마우스"},
                        "no": {"answer": "이어폰"},
                    },
                },
            },
            "no": {
                "question": "글을 쓰거나 읽는 데 사용하나요?",
                "yes": {
                    "question": "종이로 되어 있나요?",
                    "yes": {"answer": "책"},
                    "no": {"answer": "연필"},
                },
                "no": {
                    "question": "몸에 착용하나요?",
                    "yes": {
                        "question": "눈에 착용하나요?",
                        "yes": {"answer": "안경"},
                        "no": {
                            "question": "발에 신나요?",
                            "yes": {"answer": "신발"},
                            "no": {"answer": "시계"},
                        },
                    },
                    "no": {
                        "question": "액체를 담는 데 사용하나요?",
                        "yes": {"answer": "컵"},
                        "no": {
                            "question": "자르는 데 사용하나요?",
                            "yes": {"answer": "가위"},
                            "no": {
                                "question": "돈을 보관하나요?",
                                "yes": {"answer": "지갑"},
                                "no": {
                                    "question": "문을 여는 데 사용하나요?",
                                    "yes": {"answer": "열쇠"},
                                    "no": {
                                        "question": "비를 막아주나요?",
                                        "yes": {"answer": "우산"},
                                        "no": {"answer": "칫솔"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "no": {
            "question": "인간이 만든 것인가요?",
            "yes": {
                "question": "탈 수 있는 교통수단인가요?",
                "yes": {
                    "question": "하늘을 나나요?",
                    "yes": {"answer": "비행기"},
                    "no": {
                        "question": "레일 위를 달리나요?",
                        "yes": {"answer": "기차"},
                        "no": {"answer": "자동차"},
                    },
                },
                "no": {
                    "question": "건물인가요?",
                    "yes": {
                        "question": "세계적으로 유명한 랜드마크인가요?",
                        "yes": {"answer": "에펠탑"},
                        "no": {
                            "question": "배우는 곳인가요?",
                            "yes": {"answer": "학교"},
                            "no": {"answer": "병원"},
                        },
                    },
                    "no": {
                        "question": "음식을 보관하는 데 사용하나요?",
                        "yes": {"answer": "냉장고"},
                        "no": {
                            "question": "음악을 연주하는 악기인가요?",
                            "yes": {"answer": "피아노"},
                            "no": {"answer": "텔레비전"},
                        },
                    },
                },
            },
            "no": {
                "question": "우주에 있나요?",
                "yes": {
                    "question": "스스로 빛을 내나요?",
                    "yes": {"answer": "태양"},
                    "no": {"answer": "지구"},
                },
                "no": {
                    "question": "물로 이루어진 곳인가요?",
                    "yes": {"answer": "한강"},
                    "no": {
                        "question": "산인가요?",
                        "yes": {"answer": "한라산"},
                        "no": {"answer": "사막"},
                    },
                },
            },
        },
    },
}


def traverse(node: dict) -> str:
    while "answer" not in node:
        print(f"\n  {node['question']}")
        while True:
            raw = input("  (y/n) > ")
            answer = normalize_input(raw)
            if answer:
                break
            print("  y 또는 n으로 답해주세요.")
        node = node[answer]
    return node["answer"]
