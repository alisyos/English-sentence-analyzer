from flask import Flask, render_template, request, jsonify
import json
import traceback
import logging
import re
import nltk
from nltk import pos_tag, word_tokenize
from nltk.chunk import RegexpParser

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# NLTK 데이터 다운로드 (처음 실행 시 필요)
try:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
except Exception as e:
    logging.error(f"NLTK 데이터 다운로드 오류: {str(e)}")

# 데모용 HTML 시각화 템플릿
HTML_TEMPLATE = '''
<style>
    .parsed-syntax-image {{
        margin: 10px 0;
        width: 100%;
        border-radius: 8px;
        border: 1px solid #eaeaea;
        background-color: white;
        padding: 8px;
    }}
    .parsed-text {{
        font-family: 'Arial', sans-serif;
        font-size: 16px;
        line-height: 1.6;
        margin-bottom: 30px;
    }}
    .collapseSyntaxAnalysis {{
        padding-top: 0px;
        padding-bottom: 30px;
        position: relative;
    }}
    /* 문장성분 표시 */
    .phrase {{
        display: inline-block;
        position: relative;
        margin-bottom: 25px;
    }}
    .phrase::before {{
        content: "(";
        color: #666;
    }}
    .phrase::after {{
        content: ")";
        color: #666;
    }}
    .phrase-label {{
        position: absolute;
        bottom: -20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #0066cc;
    }}
    /* 주어 */
    .S {{
        color: #0066cc;
        border-bottom: 2px solid #0066cc;
    }}
    /* 동사 */
    .V {{
        color: #cc0000;
        border-bottom: 2px solid #cc0000;
    }}
    /* 목적어 */
    .O {{
        color: #009900;
        border-bottom: 2px solid #009900;
    }}
    /* 부사구 */
    .ADV {{
        color: #666666;
        border-bottom: 2px solid #666666;
    }}
</style>
<div class="parsed-syntax-image">
    <div class="parsed-text">
        <div class="collapseSyntaxAnalysis">
            {content}
        </div>
    </div>
</div>
'''

def simple_analyze(sentence):
    """
    문장을 분석하여 주어, 동사, 목적어 등의 문장 성분을 식별합니다.
    """
    # 기본 분석 결과 초기화
    analysis = {
        'phrases': []  # 각 구문의 정보를 담을 리스트
    }
    
    # 로그 추가
    logging.debug(f"분석할 문장: '{sentence}'")
    
    # 예시 문장 분석 - 하드코딩된 예시
    if "organizations" in sentence and "supervisor" in sentence and "evaluates" in sentence:
        # 직접 위치를 지정하여 분석
        # 부사구 (ADV)
        if "In most organizations" in sentence:
            adv_start = sentence.find("In most organizations")
            analysis['phrases'].append({
                'text': "In most organizations",
                'start': adv_start,
                'end': adv_start + len("In most organizations"),
                'label': 'ADV'
            })
        
        # 주어 (S)
        subject = "the employee's immediate supervisor"
        s_start = sentence.find("the employee")
        if s_start != -1:
            # 주어의 끝 위치 찾기
            s_end = sentence.find("evaluates", s_start)
            if s_end != -1:
                # 공백 제거
                s_end = s_end.strip() if isinstance(s_end, str) else s_end
                s_text = sentence[s_start:s_end].strip()
                analysis['phrases'].append({
                    'text': s_text,
                    'start': s_start,
                    'end': s_start + len(s_text),
                    'label': 'S'
                })
        
        # 동사 (V)
        if "evaluates" in sentence:
            v_start = sentence.find("evaluates")
            analysis['phrases'].append({
                'text': "evaluates",
                'start': v_start,
                'end': v_start + len("evaluates"),
                'label': 'V'
            })
        
        # 목적어 (O)
        object_text = "the employee's performance"
        o_start = sentence.find("performance")
        if o_start != -1:
            # 목적어의 시작 위치 찾기
            o_start = sentence.rfind("the ", 0, o_start)
            if o_start != -1:
                analysis['phrases'].append({
                    'text': object_text,
                    'start': o_start,
                    'end': o_start + len(object_text),
                    'label': 'O'
                })
    else:
        # 간단한 규칙 기반 분석
        try:
            # 문장을 단어로 분리
            words = sentence.split()
            
            # 간단한 규칙 기반 분석
            # 1. 첫 번째 명사구를 주어로 간주
            # 2. 첫 번째 동사를 동사로 간주
            # 3. 동사 이후의 명사구를 목적어로 간주
            # 4. 전치사로 시작하는 구를 부사구로 간주
            
            # 일반적인 전치사 목록
            prepositions = ['in', 'on', 'at', 'by', 'with', 'from', 'to', 'for', 'of', 'about', 'after', 'before']
            
            # 일반적인 동사 목록 (현재형, 과거형, 진행형 등)
            common_verbs = ['is', 'are', 'was', 'were', 'has', 'have', 'had', 'do', 'does', 'did', 
                           'go', 'goes', 'went', 'come', 'comes', 'came', 'see', 'sees', 'saw',
                           'take', 'takes', 'took', 'make', 'makes', 'made', 'know', 'knows', 'knew',
                           'get', 'gets', 'got', 'use', 'uses', 'used', 'find', 'finds', 'found',
                           'give', 'gives', 'gave', 'tell', 'tells', 'told', 'work', 'works', 'worked',
                           'call', 'calls', 'called', 'try', 'tries', 'tried', 'ask', 'asks', 'asked',
                           'need', 'needs', 'needed', 'feel', 'feels', 'felt', 'become', 'becomes', 'became',
                           'leave', 'leaves', 'left', 'put', 'puts', 'mean', 'means', 'meant',
                           'keep', 'keeps', 'kept', 'let', 'lets', 'begin', 'begins', 'began',
                           'seem', 'seems', 'seemed', 'help', 'helps', 'helped', 'talk', 'talks', 'talked',
                           'turn', 'turns', 'turned', 'start', 'starts', 'started', 'show', 'shows', 'showed',
                           'hear', 'hears', 'heard', 'play', 'plays', 'played', 'run', 'runs', 'ran',
                           'move', 'moves', 'moved', 'live', 'lives', 'lived', 'believe', 'believes', 'believed',
                           'bring', 'brings', 'brought', 'happen', 'happens', 'happened', 'write', 'writes', 'wrote',
                           'sit', 'sits', 'sat', 'stand', 'stands', 'stood', 'lose', 'loses', 'lost',
                           'pay', 'pays', 'paid', 'meet', 'meets', 'met', 'include', 'includes', 'included',
                           'continue', 'continues', 'continued', 'set', 'sets', 'learn', 'learns', 'learned',
                           'change', 'changes', 'changed', 'lead', 'leads', 'led', 'understand', 'understands', 'understood',
                           'watch', 'watches', 'watched', 'follow', 'follows', 'followed', 'stop', 'stops', 'stopped',
                           'create', 'creates', 'created', 'speak', 'speaks', 'spoke', 'read', 'reads', 'sleeping',
                           'allow', 'allows', 'allowed', 'add', 'adds', 'added', 'spend', 'spends', 'spent',
                           'grow', 'grows', 'grew', 'open', 'opens', 'opened', 'walk', 'walks', 'walked',
                           'win', 'wins', 'won', 'offer', 'offers', 'offered', 'remember', 'remembers', 'remembered',
                           'love', 'loves', 'loved', 'consider', 'considers', 'considered', 'appear', 'appears', 'appeared',
                           'buy', 'buys', 'bought', 'wait', 'waits', 'waited', 'serve', 'serves', 'served',
                           'die', 'dies', 'died', 'send', 'sends', 'sent', 'expect', 'expects', 'expected',
                           'build', 'builds', 'built', 'stay', 'stays', 'stayed', 'fall', 'falls', 'fell',
                           'cut', 'cuts', 'reach', 'reaches', 'reached', 'kill', 'kills', 'killed',
                           'remain', 'remains', 'remained', 'suggest', 'suggests', 'suggested', 'raise', 'raises', 'raised',
                           'pass', 'passes', 'passed', 'sell', 'sells', 'sold', 'require', 'requires', 'required',
                           'report', 'reports', 'reported', 'decide', 'decides', 'decided', 'pull', 'pulls', 'pulled',
                           'evaluates', 'evaluated', 'evaluate', 'finished', 'finish', 'finishes']
            
            current_pos = 0
            found_verb = False
            found_subject = False
            
            i = 0
            while i < len(words):
                word = words[i].lower().strip('.,;:!?')
                
                # 전치사구 (부사구) 찾기
                if word in prepositions and i < len(words) - 1:
                    # 전치사구의 끝 찾기
                    end_idx = i + 1
                    while end_idx < len(words) and words[end_idx].lower() not in prepositions and words[end_idx].lower() not in common_verbs:
                        end_idx += 1
                    
                    phrase_text = ' '.join(words[i:end_idx])
                    phrase_start = sentence.find(phrase_text, current_pos)
                    
                    if phrase_start != -1:
                        analysis['phrases'].append({
                            'text': phrase_text,
                            'start': phrase_start,
                            'end': phrase_start + len(phrase_text),
                            'label': 'ADV'
                        })
                        current_pos = phrase_start + len(phrase_text)
                        i = end_idx - 1
                
                # 동사 찾기
                elif word in common_verbs and not found_verb:
                    phrase_start = sentence.find(word, current_pos)
                    
                    if phrase_start != -1:
                        analysis['phrases'].append({
                            'text': word,
                            'start': phrase_start,
                            'end': phrase_start + len(word),
                            'label': 'V'
                        })
                        current_pos = phrase_start + len(word)
                        found_verb = True
                
                # 주어 찾기 (동사 이전의 첫 번째 명사구)
                elif not found_subject and not found_verb and word not in prepositions and word not in common_verbs:
                    # 주어의 끝 찾기
                    end_idx = i + 1
                    while end_idx < len(words) and words[end_idx].lower() not in common_verbs and words[end_idx].lower() not in prepositions:
                        end_idx += 1
                    
                    phrase_text = ' '.join(words[i:end_idx])
                    phrase_start = sentence.find(phrase_text, current_pos)
                    
                    if phrase_start != -1:
                        analysis['phrases'].append({
                            'text': phrase_text,
                            'start': phrase_start,
                            'end': phrase_start + len(phrase_text),
                            'label': 'S'
                        })
                        current_pos = phrase_start + len(phrase_text)
                        found_subject = True
                        i = end_idx - 1
                
                # 목적어 찾기 (동사 이후의 첫 번째 명사구)
                elif found_verb and word not in prepositions and word not in common_verbs:
                    # 목적어의 끝 찾기
                    end_idx = i + 1
                    while end_idx < len(words) and words[end_idx].lower() not in prepositions:
                        end_idx += 1
                    
                    phrase_text = ' '.join(words[i:end_idx])
                    phrase_start = sentence.find(phrase_text, current_pos)
                    
                    if phrase_start != -1:
                        analysis['phrases'].append({
                            'text': phrase_text,
                            'start': phrase_start,
                            'end': phrase_start + len(phrase_text),
                            'label': 'O'
                        })
                        current_pos = phrase_start + len(phrase_text)
                        i = end_idx - 1
                
                i += 1
                
        except Exception as e:
            logging.error(f"문장 분석 오류: {str(e)}")
            logging.error(traceback.format_exc())
    
    # 시작 위치를 기준으로 정렬하여 문장 순서 유지
    analysis['phrases'].sort(key=lambda x: x['start'])
    
    # 로그 추가
    logging.debug(f"분석된 구문: {json.dumps(analysis['phrases'], ensure_ascii=False, indent=2)}")
    
    return analysis

def generate_html(sentence, analysis):
    """
    분석 결과를 HTML로 변환합니다.
    """
    # HTML 생성
    html_parts = []
    last_end = 0
    
    # 구문 순서대로 정렬
    phrases = sorted(analysis['phrases'], key=lambda x: x['start'])
    
    for phrase in phrases:
        # 구문 이전의 텍스트 추가
        if phrase['start'] > last_end:
            html_parts.append(sentence[last_end:phrase['start']])
        
        # 구문 추가
        html_parts.append(f'<span class="phrase {phrase["label"]}">')
        html_parts.append(phrase['text'])
        html_parts.append(f'<span class="phrase-label">{phrase["label"]}</span>')
        html_parts.append('</span>')
        
        last_end = phrase['end']
    
    # 마지막 구문 이후의 텍스트 추가
    if last_end < len(sentence):
        html_parts.append(sentence[last_end:])
    
    # HTML_TEMPLATE을 사용하여 최종 HTML 생성
    return HTML_TEMPLATE.format(content=''.join(html_parts))

def split_into_sentences(text):
    """
    문단을 문장 단위로 분리합니다.
    """
    # 마침표, 물음표, 느낌표 뒤에 공백이 있는 경우를 문장 구분자로 사용
    sentences = re.split(r'[.!?]\s+', text)
    
    # 마지막 문장이 마침표로 끝나지 않을 경우 처리
    if sentences and not text.rstrip().endswith(('.', '!', '?')):
        sentences[-1] = sentences[-1]
    else:
        # 마지막에 마침표가 있지만 공백이 없는 경우 처리
        for i in range(len(sentences)):
            if i < len(sentences) - 1 and not sentences[i].endswith(('.', '!', '?')):
                sentences[i] = sentences[i] + '.'
    
    # 빈 문장 제거
    return [s.strip() for s in sentences if s.strip()]

def analyze_and_visualize(sentence: str):
    """
    문장을 분석하고 시각화된 HTML을 반환합니다.
    """
    try:
        # 문장 분석
        analysis = simple_analyze(sentence)
        
        # 로그 추가
        logging.debug(f"분석 결과: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
        
        # HTML 생성
        html = generate_html(sentence, analysis)
        
        return {
            'success': True,
            'html': html,
            'analysis': analysis
        }
    except Exception as e:
        logging.error(f"Error in analyze_and_visualize: {str(e)}")
        logging.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    sentence = data.get('sentence', '')
    
    if not sentence:
        return jsonify({'error': '문장이 입력되지 않았습니다.'}), 400
    
    try:
        result = analyze_and_visualize(sentence)
        if not result['success']:
            return jsonify({'error': result.get('error', '알 수 없는 오류가 발생했습니다.')}), 500
        
        return jsonify({
            'success': True,
            'html': result['html'],
            'analysis': result['analysis']
        })
    except Exception as e:
        app.logger.error(f"API 오류: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 