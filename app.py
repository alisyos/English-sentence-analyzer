from flask import Flask, render_template, request, jsonify
import json
import traceback
import logging
import re

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# 데모용 HTML 시각화 템플릿
HTML_TEMPLATE = """
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
        margin-bottom: 30px; /* 문장성분 표시를 위한 여백 추가 */
    }}
    .collapseSyntaxAnalysis {{
        padding-top: 0px;
        padding-bottom: 30px;
        position: relative;
    }}
    /* 주어 스타일 */
    .s {{
        color: #0066cc;
        border-bottom: 2px solid #0066cc;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .s::after {{
        content: "S";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #0066cc;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 동사 스타일 */
    .v {{
        color: #cc0000;
        border-bottom: 2px solid #cc0000;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .v::after {{
        content: "V";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #cc0000;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 목적어 스타일 */
    .o {{
        color: #009900;
        border-bottom: 2px solid #009900;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .o::after {{
        content: "O";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #009900;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 간접 목적어 스타일 */
    .io {{
        color: #66cc66; /* 옅은 초록색 */
        border-bottom: 2px solid #66cc66;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .io::after {{
        content: "IO";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #66cc66;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 직접 목적어 스타일 */
    .do {{
        color: #006600; /* 짙은 초록색 */
        border-bottom: 2px solid #006600;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .do::after {{
        content: "DO";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #006600;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 명사절 스타일 */
    .nc {{
        color: #0066cc;
        position: relative;
    }}
    .nc::before {{
        content: "[";
        font-weight: bold;
        color: #0066cc;
    }}
    .nc::after {{
        content: "]";
        font-weight: bold;
        color: #0066cc;
    }}
    /* 전치사구 스타일 */
    .pp {{
        color: #ff9900; /* 주황색 */
        position: relative;
    }}
    .pp::before {{
        content: "(";
        font-weight: bold;
        color: #ff9900;
    }}
    .pp::after {{
        content: ")";
        font-weight: bold;
        color: #ff9900;
    }}
    /* 형용사 스타일 */
    .adj {{
        color: #ff6600;
        border-bottom: 2px dashed #ff6600;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .adj::after {{
        content: "ADJ";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #ff6600;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 부사 스타일 */
    .adv {{
        color: #cc00cc;
        border-bottom: 2px dotted #cc00cc;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .adv::after {{
        content: "ADV";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #cc00cc;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 주격 보어 스타일 */
    .sc {{
        color: #9900cc; /* 보라색 */
        border-bottom: 2px solid #9900cc;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .sc::after {{
        content: "SC";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #9900cc;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 목적격 보어 스타일 */
    .oc {{
        color: #cc99ff; /* 옅은 보라색 */
        border-bottom: 2px solid #cc99ff;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .oc::after {{
        content: "OC";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #cc99ff;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 가주어 스타일 */
    .ds {{
        color: #000080; /* 남색 */
        border-bottom: 2px solid #000080;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .ds::after {{
        content: "(가)S";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #000080;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
    /* 진주어 스타일 */
    .rs {{
        color: #0066cc; /* 파란색 */
        border-bottom: 2px solid #0066cc;
        display: inline-block;
        position: relative;
        margin-bottom: 5px;
    }}
    .rs::after {{
        content: "(진)S";
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: bold;
        color: #0066cc;
        background-color: #f5f5f5;
        padding: 1px 3px;
        border-radius: 3px;
    }}
</style>
<div class="parsed-syntax-image">
    <div class="parsed-text">
        <div class="collapseSyntaxAnalysis">
            {content}
        </div>
    </div>
</div>
"""

def simple_analyze(sentence):
    """
    간단한 규칙 기반 분석을 수행합니다.
    """
    words = sentence.strip('.').split()
    result = {
        "subject": [],
        "verb": [],
        "object": [],
        "prepositional_phrase": [],
        "adverb": [],
        "adjective": [],
        "noun_clause": [],
        "dummy_subject": [],
        "real_subject": [],
        "indirect_object": [],
        "direct_object": [],
        "subject_complement": [],
        "object_complement": [],
    }
    
    # 매우 간단한 규칙 기반 분석
    if len(words) > 0:
        # 가주어 및 진주어 처리
        if words[0].lower() == "it" and "to" in words:
            result["dummy_subject"].append(words[0])
            # "to" 이후의 단어들을 진주어로 간주
            to_index = words.index("to")
            result["real_subject"].append(" ".join(words[to_index:]))
            
            # 동사 찾기
            verb_start = 1
            verb_end = 2
            while verb_end < to_index and words[verb_end].lower() not in ["to"]:
                verb_end += 1
            if verb_start < len(words):
                result["verb"] = words[verb_start:verb_end]
        else:
            # 일반 주어 처리
            subject_end = 1
            # 관사, 소유격 등이 있는 경우 주어 범위 확장
            while subject_end < len(words) and words[subject_end].lower() in ["a", "an", "the", "my", "your", "his", "her", "their", "our"]:
                subject_end += 1
            # 형용사가 있는 경우 주어 범위 확장 (간단한 규칙)
            if subject_end < len(words) and words[subject_end].lower().endswith(("ful", "ous", "ive", "able", "ible", "al", "ial", "ic", "ical")):
                subject_end += 1
            # 명사가 있는 경우 주어 범위 확장
            if subject_end < len(words):
                subject_end += 1
            result["subject"] = words[:subject_end]
            
            # 동사 찾기
            verb_start = subject_end
            verb_end = verb_start + 1
            # 조동사, 부정어 등이 있는 경우 동사 범위 확장
            while verb_end < len(words) and words[verb_end].lower() in ["not", "n't", "have", "has", "had", "been", "be", "being"]:
                verb_end += 1
            if verb_start < len(words):
                result["verb"] = words[verb_start:verb_end]
        
        # 동사 이후 분석
        if result["verb"]:
            verb_text = " ".join(result["verb"]).lower()
            last_verb_index = verb_end - 1
            
            # 보어 확인 (be 동사류)
            is_linking_verb = any(v in verb_text for v in ["is", "are", "was", "were", "be", "been", "being", "am", "seem", "appear", "look", "sound", "smell", "taste", "feel", "become", "get"])
            
            # 간접 목적어를 가질 수 있는 동사 확인
            is_ditransitive = any(v in verb_text for v in ["give", "offer", "show", "tell", "send", "hand", "pass", "buy", "get", "bring", "teach", "promise", "write", "pay", "sell"])
            
            # 목적격 보어를 가질 수 있는 동사 확인
            has_obj_complement = any(v in verb_text for v in ["make", "call", "name", "consider", "find", "think", "elect", "choose", "appoint", "declare", "keep", "leave"])
            
            # 전치사 찾기
            prep_indices = [i for i, word in enumerate(words) if i >= verb_end and word.lower() in ["in", "on", "at", "by", "with", "for", "to", "from", "of", "about"]]
            
            # 연결사 찾기
            conj_indices = [i for i, word in enumerate(words) if i >= verb_end and word.lower() in ["and", "but", "or", "nor", "yet", "so"]]
            
            # 링킹 동사인 경우 (주격 보어)
            if is_linking_verb:
                if verb_end < len(words):
                    if prep_indices and prep_indices[0] > verb_end:
                        result["subject_complement"] = words[verb_end:prep_indices[0]]
                    else:
                        result["subject_complement"] = words[verb_end:]
            
            # 이중 타동사인 경우 (간접 목적어 + 직접 목적어)
            elif is_ditransitive and verb_end < len(words) - 1:
                # 'to' 또는 'for' 전치사가 있는 경우 (give something to someone)
                to_for_indices = [i for i in prep_indices if words[i].lower() in ["to", "for"]]
                
                if to_for_indices:
                    # 전치사 앞까지가 직접 목적어
                    to_for_index = to_for_indices[0]
                    if verb_end < to_for_index:
                        result["direct_object"] = words[verb_end:to_for_index]
                    
                    # 전치사 뒤가 간접 목적어
                    if to_for_index + 1 < len(words):
                        end_index = next((i for i in prep_indices if i > to_for_index), len(words))
                        result["indirect_object"] = words[to_for_index:end_index]
                else:
                    # 전치사 없는 경우 (give someone something)
                    # 첫 번째 명사구는 간접 목적어, 두 번째는 직접 목적어로 간주
                    if conj_indices:
                        mid_point = conj_indices[0]
                    else:
                        # 간단한 규칙: 중간 지점 추정
                        mid_point = verb_end + (len(words) - verb_end) // 2
                    
                    if verb_end < mid_point:
                        result["indirect_object"] = words[verb_end:mid_point]
                    
                    if mid_point < len(words):
                        if prep_indices and prep_indices[0] > mid_point:
                            result["direct_object"] = words[mid_point:prep_indices[0]]
                        else:
                            result["direct_object"] = words[mid_point:]
            
            # 목적격 보어를 가진 동사인 경우
            elif has_obj_complement and verb_end < len(words) - 1:
                # 간단한 규칙: 마지막 단어나 구를 목적격 보어로 간주
                if prep_indices:
                    # 전치사 앞까지가 목적어
                    result["object"] = words[verb_end:prep_indices[0]]
                    
                    # 전치사구가 목적격 보어인 경우
                    if words[prep_indices[0]].lower() == "as":
                        end_index = next((i for i in prep_indices if i > prep_indices[0]), len(words))
                        result["object_complement"] = words[prep_indices[0]:end_index]
                else:
                    # 마지막 형용사나 명사를 목적격 보어로 간주
                    last_word_index = len(words) - 1
                    if last_word_index > verb_end:
                        result["object"] = words[verb_end:last_word_index]
                        result["object_complement"] = [words[last_word_index]]
            
            # 일반 타동사인 경우 (단순 목적어)
            else:
                if verb_end < len(words):
                    if prep_indices and prep_indices[0] > verb_end:
                        # 전치사 앞까지를 목적어로 간주
                        result["object"] = words[verb_end:prep_indices[0]]
                    else:
                        # 나머지를 목적어로 간주
                        result["object"] = words[verb_end:]
            
            # 전치사구 추출
            for i in prep_indices:
                if i+1 < len(words):
                    phrase_end = i+1
                    while phrase_end < len(words) and phrase_end not in prep_indices and (not conj_indices or phrase_end not in conj_indices):
                        phrase_end += 1
                    result["prepositional_phrase"].append(" ".join(words[i:phrase_end]))
        
        # "that"이 있으면 명사절로 간주
        if "that" in words:
            that_index = words.index("that")
            result["noun_clause"].append(" ".join(words[that_index:]))
    
    return result

def generate_html(sentence, analysis):
    """
    분석 결과를 기반으로 HTML 시각화를 생성합니다.
    """
    words = sentence.strip('.').split()
    html_parts = []
    
    # 주어 처리
    if analysis["dummy_subject"]:
        html_parts.append(f'<span class="ds">{" ".join(analysis["dummy_subject"])}</span>')
    elif analysis["subject"]:
        html_parts.append(f'<span class="s">{" ".join(analysis["subject"])}</span>')
    
    # 동사 처리
    if analysis["verb"]:
        html_parts.append(f' <span class="v">{" ".join(analysis["verb"])}</span>')
    
    # 간접 목적어 처리
    if analysis["indirect_object"]:
        html_parts.append(f' <span class="io">{" ".join(analysis["indirect_object"])}</span>')
    
    # 직접 목적어 처리
    if analysis["direct_object"]:
        html_parts.append(f' <span class="do">{" ".join(analysis["direct_object"])}</span>')
    
    # 일반 목적어 처리
    elif analysis["object"]:
        obj_text = " ".join(analysis["object"])
        if analysis["noun_clause"] and obj_text.startswith(analysis["noun_clause"][0].split()[0]):
            html_parts.append(f' <span class="o nc">{obj_text}</span>')
        else:
            html_parts.append(f' <span class="o">{obj_text}</span>')
    
    # 주격 보어 처리
    if analysis["subject_complement"]:
        html_parts.append(f' <span class="sc">{" ".join(analysis["subject_complement"])}</span>')
    
    # 목적격 보어 처리
    if analysis["object_complement"]:
        html_parts.append(f' <span class="oc">{" ".join(analysis["object_complement"])}</span>')
    
    # 전치사구 처리
    for phrase in analysis["prepositional_phrase"]:
        html_parts.append(f' <span class="pp">{phrase}</span>')
    
    # 진주어 처리
    if analysis["real_subject"]:
        html_parts.append(f' <span class="rs">{analysis["real_subject"][0]}</span>')
    
    # 마침표 추가
    if not sentence.endswith('.'):
        html_parts.append('.')
    
    return HTML_TEMPLATE.format(content="".join(html_parts))

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
    문장 또는 문단을 분석하고 시각화합니다.
    """
    try:
        # 문단을 문장으로 분리
        sentences = split_into_sentences(sentence)
        
        if not sentences:
            return {"error": "분석할 문장이 없습니다."}, "<p>분석할 문장이 없습니다.</p>"
        
        # 각 문장 분석 결과 저장
        all_analyses = []
        all_html_results = []
        
        for single_sentence in sentences:
            # 문장 분석
            analysis = simple_analyze(single_sentence)
            all_analyses.append({"sentence": single_sentence, "analysis": analysis})
            
            # HTML 생성
            html_result = generate_html(single_sentence, analysis)
            all_html_results.append(html_result)
        
        # 전체 HTML 결과 합치기
        combined_html = "".join(all_html_results)
        
        return {"sentences": all_analyses}, combined_html
    except Exception as e:
        app.logger.error(f"분석 오류: {str(e)}")
        app.logger.error(traceback.format_exc())
        return {"error": str(e)}, f"<p>분석 중 오류가 발생했습니다: {str(e)}</p>"

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
        json_result, html_result = analyze_and_visualize(sentence)
        if "error" in json_result:
            return jsonify({'error': json_result["error"]}), 500
        return jsonify({
            'analysis': json_result,
            'visualization': html_result
        })
    except Exception as e:
        app.logger.error(f"API 오류: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 