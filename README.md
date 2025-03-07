# 영어 문장 분석기

이 프로젝트는 영어 문장을 입력하면 문장성분을 분석하여 시각적으로 보여주는 웹 애플리케이션입니다.

## 기능

- 영어 문장의 문법 요소 분석 (주어, 동사, 목적어, 보어 등)
- 다양한 문장 성분 식별 (가주어, 진주어, 간접목적어, 직접목적어, 주격보어, 목적격보어 등)
- 시각적 표현 (색상별 밑줄, 괄호, 레이블 등)
- 문단 입력 시 문장 단위 분석 지원
- JSON 형식의 상세 분석 결과 제공

## 설치 방법

1. 필요한 패키지 설치:
```
pip install -r requirements.txt
```

## 실행 방법

```
python app.py
```

웹 브라우저에서 `http://localhost:5000`으로 접속하여 사용할 수 있습니다.

## 사용 예시

1. 텍스트 입력 영역에 분석할 영어 문장을 입력합니다.
2. "분석하기" 버튼을 클릭합니다.
3. 시각화 탭에서 문장성분 분석 결과를 확인합니다.
4. JSON 탭에서 상세한 분석 결과를 확인할 수 있습니다.

## 문장 성분 표시 방법

- 주어(subject): 파란색 폰트, 파란색 밑줄, 'S' 표시
- 동사(verb): 빨간색 폰트, 빨간색 밑줄, 'V' 표시
- 목적어(object): 초록색 폰트, 초록색 밑줄, 'O' 표시
- 가주어(dummy subject): 남색 폰트, 남색 밑줄, '(가)S' 표시
- 진주어(real subject): 파란색 폰트, 파란색 밑줄, '(진)S' 표시
- 간접목적어(indirect object): 옅은 초록색 폰트, 옅은 초록색 밑줄, 'IO' 표시
- 직접목적어(direct object): 짙은 초록색 폰트, 짙은 초록색 밑줄, 'DO' 표시
- 주격보어(subject complement): 보라색 폰트, 보라색 밑줄, 'SC' 표시
- 목적격보어(object complement): 옅은 보라색 폰트, 옅은 보라색 밑줄, 'OC' 표시
- 전치사구: 주황색 괄호로 표시

## 기술 스택

- Backend: Flask
- Frontend: HTML, CSS, JavaScript, Bootstrap

## 라이선스

MIT 라이선스 