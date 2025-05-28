## 📂 Directory
```
📁 ai_agent_system/
│
├── app.py                            # FastAPI 서버 엔트리포인트 (예: /chat 엔드포인트)
├── main.py                           # LangGraph 실행 진입점 (로컬 디버깅 등)
│
├── agents/                           # LangGraph의 노드 단위 Agent, ToolNode, Runnable 등
│   ├── __init__.py
│   ├── intent_classifier.py          # [의도 분류 노드] LLM 기반 또는 룰 기반 분류기
│   ├── loan_agent.py                 # 대출 추천 ToolNode or Runnable 노드 정의
│   ├── notice_agent.py               # 청약 공고문 RAG ToolNode or Runnable 노드 정의
│   └── agent_utils.py                # 공통 에이전트 유틸 (입력 정제, 예외 처리 등)
│
├── graphs/                           # LangGraph 흐름 정의
│   ├── __init__.py
│   ├── loan_graph.py                 # 대출 추천에 특화된 세부 LangGraph 정의
│   ├── notice_graph.py               # 공고문 RAG 워크플로우 정의
│   └── main_graph.py                 # 의도 분류 + 라우팅 포함한 전체 시스템 그래프
│
├── tools/                            # 실제 기능 수행하는 로직들 (함수 단위 툴)
│   ├── __init__.py
│   ├── recommend_loans.py            # 대출 상품 추천 함수
│   ├── user_utils.py                 # 사용자 입력 전처리, 정규화
│   ├── loan_utils.py                 # 대출 계산 (월 상환, LTV 등)
│   ├── region_rules.py               # 지역 규제 판단
│   └── rag_search.py                 # 청약 공고문 RAG 검색 함수
│
├── prompts/                          # 프롬프트 템플릿 모음
│   ├── __init__.py
│   ├── intent_prompt.py              # 의도 분류 프롬프트
│   ├── loan_prompt_template.py       # 대출 추천 설명 프롬프트
│   ├── notice_prompt_template.py     # 공고문 요약/출력 프롬프트
│   └── system_messages.py            # 시스템 전반에 쓰이는 메시지 템플릿
│
├── config/                           # 설정 관련 파일
│   ├── __init__.py
│   ├── rag_settings.py               # 벡터 검색 설정
│   └── config.py                     # API 키, 경로, 공통 상수
│
├── data/                             # 정적 데이터 파일
│   └── housing_loan_products.csv     # 대출 상품 기본 CSV
│
└── db/                               
    └── db.py                         # DB 연결 및 쿼리 함수

```
