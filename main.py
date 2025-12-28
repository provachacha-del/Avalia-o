
from ast import Import
from ast import Import
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
import json
import random
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDcOQJIrnQncUPVsluHIj3W4hwV2uMnLuE")
AI_ENABLED = bool(GOOGLE_API_KEY and GOOGLE_API_KEY.strip())
model = None
if AI_ENABLED:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        print(f"✅ API Key configurada: {GOOGLE_API_KEY[:8]}... (protegida)")
    except Exception as e:
        print(f"❌ Falha ao configurar genai: {type(e).__name__}: {str(e)[:200]}")
        AI_ENABLED = False
else:
    print("⚠️ ATENÇÃO: GOOGLE_API_KEY não encontrada. IA desabilitada. Use: export GOOGLE_API_KEY='sua_chave_aqui'")

questions_cache = []

QUESTIONS_DB = {
    1: [
        {"question": "Qual é o maior planeta do Sistema Solar?", "options": ["Marte", "Júpiter", "Saturno", "Netuno"], "correct": 1},
        {"question": "Qual é a capital da França?", "options": ["Londres", "Berlim", "Paris", "Roma"], "correct": 2},
        {"question": "Quantos continentes existem no mundo?", "options": ["5", "6", "7", "8"], "correct": 2},
        {"question": "Qual animal é conhecido como o rei da selva?", "options": ["Tigre", "Leão", "Elefante", "Leopardo"], "correct": 1},
        {"question": "Qual é a cor do céu em um dia claro?", "options": ["Verde", "Vermelho", "Azul", "Amarelo"], "correct": 2},
        {"question": "Quantos dias tem um ano?", "options": ["360", "365", "370", "366"], "correct": 1},
        {"question": "Qual é o planeta mais próximo do Sol?", "options": ["Vênus", "Terra", "Mercúrio", "Marte"], "correct": 2},
        {"question": "Quantas patas tem um cachorro?", "options": ["2", "4", "6", "8"], "correct": 1},
        {"question": "Qual é a capital do Brasil?", "options": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"], "correct": 2},
        {"question": "Qual animal põe ovos?", "options": ["Cachorro", "Gato", "Galinha", "Vaca"], "correct": 2},
        {"question": "Quantos lados tem um triângulo?", "options": ["2", "3", "4", "5"], "correct": 1},
        {"question": "Qual é a cor da grama?", "options": ["Azul", "Verde", "Amarelo", "Vermelho"], "correct": 1},
        {"question": "Em qual estação do ano faz mais calor?", "options": ["Inverno", "Outono", "Primavera", "Verão"], "correct": 3},
        {"question": "Quantos minutos tem uma hora?", "options": ["30", "45", "60", "90"], "correct": 2},
        {"question": "Qual é o animal mais rápido do mundo?", "options": ["Leão", "Cavalo", "Guepardo", "Coelho"], "correct": 2},
    ],
    2: [
        {"question": "Qual é a capital da Austrália?", "options": ["Sydney", "Melbourne", "Canberra", "Brisbane"], "correct": 2},
        {"question": "Quantos ossos tem o corpo humano adulto?", "options": ["206", "186", "216", "196"], "correct": 0},
        {"question": "Em que ano caiu o Muro de Berlim?", "options": ["1987", "1989", "1991", "1985"], "correct": 1},
        {"question": "Qual é o maior oceano do mundo?", "options": ["Atlântico", "Índico", "Pacífico", "Ártico"], "correct": 2},
        {"question": "Quem pintou a Mona Lisa?", "options": ["Michelangelo", "Leonardo da Vinci", "Rafael", "Donatello"], "correct": 1},
        {"question": "Quantos estados tem o Brasil?", "options": ["25", "26", "27", "28"], "correct": 2},
        {"question": "Qual é o metal mais abundante na Terra?", "options": ["Ferro", "Cobre", "Alumínio", "Ouro"], "correct": 2},
        {"question": "Em que continente fica o Egito?", "options": ["Ásia", "África", "Europa", "América"], "correct": 1},
        {"question": "Qual é a língua mais falada no mundo?", "options": ["Inglês", "Mandarim", "Espanhol", "Hindi"], "correct": 1},
        {"question": "Quantos jogadores tem um time de futebol?", "options": ["9", "10", "11", "12"], "correct": 2},
        {"question": "Qual é o rio mais extenso do mundo?", "options": ["Nilo", "Amazonas", "Yangtzé", "Mississipi"], "correct": 1},
        {"question": "Em que ano o homem pisou na Lua?", "options": ["1965", "1967", "1969", "1971"], "correct": 2},
        {"question": "Qual é a moeda do Japão?", "options": ["Won", "Yuan", "Yen", "Baht"], "correct": 2},
        {"question": "Quantos elementos tem a tabela periódica?", "options": ["98", "108", "118", "128"], "correct": 2},
        {"question": "Qual é o maior deserto do mundo?", "options": ["Saara", "Gobi", "Atacama", "Antártica"], "correct": 3},
    ],
    3: [
        {"question": "Qual é a constante de Avogadro?", "options": ["6,02 × 10²³", "3,14 × 10²³", "9,81 × 10²³", "1,60 × 10²³"], "correct": 0},
        {"question": "Em que ano Napoleão foi derrotado em Waterloo?", "options": ["1812", "1815", "1818", "1820"], "correct": 1},
        {"question": "Qual filósofo escreveu 'Crítica da Razão Pura'?", "options": ["Hegel", "Kant", "Nietzsche", "Schopenhauer"], "correct": 1},
        {"question": "Qual é a menor partícula de um elemento químico?", "options": ["Molécula", "Átomo", "Próton", "Elétron"], "correct": 1},
        {"question": "Quem formulou a Teoria da Relatividade?", "options": ["Isaac Newton", "Nikola Tesla", "Albert Einstein", "Stephen Hawking"], "correct": 2},
        {"question": "Qual é a velocidade da luz no vácuo?", "options": ["299.792 km/s", "300.000 km/s", "250.000 km/s", "350.000 km/s"], "correct": 0},
        {"question": "Em que ano foi assinada a Magna Carta?", "options": ["1205", "1215", "1225", "1235"], "correct": 1},
        {"question": "Qual é o elemento químico mais abundante no universo?", "options": ["Oxigênio", "Carbono", "Hidrogênio", "Hélio"], "correct": 2},
        {"question": "Quem escreveu 'A Divina Comédia'", "options": ["Dante Alighieri", "Petrarca", "Boccaccio", "Virgílio"], "correct": 0},
        {"question": "Qual é a capital do Cazaquistão?", "options": ["Almaty", "Astana", "Bishkek", "Tashkent"], "correct": 1},
        {"question": "Em que ano ocorreu a Revolução Francesa?", "options": ["1789", "1799", "1809", "1819"], "correct": 0},
        {"question": "Qual é o número atômico do carbono?", "options": ["4", "6", "8", "12"], "correct": 1},
        {"question": "Quem pintou 'A Noite Estrelada'", "options": ["Monet", "Van Gogh", "Picasso", "Dalí"], "correct": 1},
        {"question": "Qual é a montanha mais alta do mundo?", "options": ["K2", "Kangchenjunga", "Everest", "Lhotse"], "correct": 2},
        {"question": "Em que século viveu Shakespeare?", "options": ["XV", "XVI", "XVII", "XVIII"], "correct": 1},
    ]
}

def generate_ai_question(level: int, question_num: int, answered_questions: list) -> dict:

    if questions_cache:
        cached = questions_cache.pop(0)
        print(f"📦 Usando pergunta do cache (restam {len(questions_cache)} no cache)")
        return cached

    if not AI_ENABLED or model is None:
        print("⚠️ IA não configurada/indisponível — usando fallback do banco de perguntas.")
        return None

    level_names = {1: "fácil", 2: "médio", 3: "difícil"}
    level_descriptions = {
        1: "perguntas SIMPLES, de conhecimento geral básico que qualquer pessoa saberia",
        2: "perguntas de nível INTERMEDIÁRIO, que exigem conhecimento moderado",
        3: "perguntas DESAFIADORAS e específicas, que exigem conhecimento avançado"
    }

    temas = [
        "história mundial", "geografia", "ciências naturais", "matemática básica",
        "literatura", "arte e cultura", "tecnologia", "esportes", "cinema e TV",
        "música", "astronomia", "biologia", "química", "física", "política",
        "economia", "mitologia", "religião", "línguas", "culinária",
        "arquitetura", "filosofia", "psicologia", "meio ambiente", "saúde",
        "animais", "plantas", "oceanos", "países e capitais", "invenções"
    ]

    selected_themes = random.sample(temas, 3)

    prompt = f"""Crie 3 perguntas de quiz de conhecimentos gerais, nível {level_names[level]}.

Temas: {', '.join(selected_themes)}
Nível: {level_descriptions[level]}

Retorne APENAS este formato JSON exato:
[{"question":"Pergunta sobre {selected_themes[0]}?","options":["opcao A","opcao B","opcao C","opcao D"],"correct":0},{"question":"Pergunta sobre {selected_themes[1]}?","options":["opcao A","opcao B","opcao C","opcao D"],"correct":1},{"question":"Pergunta sobre {selected_themes[2]}?","options":["opcao A","opcao B","opcao C","opcao D"],"correct":2}]

IMPORTANTE: Use aspas duplas, sem quebras de linha nas perguntas."""

    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"🔄 Tentativa {attempt + 1}/{max_retries} - Gerando 3 perguntas (Nível {level})...")

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=1500,
                )
            )

            text = response.text.strip()
            print(f"📝 Resposta recebida ({len(text)} chars)")

            text = text.replace("```json", "").replace("```", "")
            text = text.replace("\n", " ").replace("\r", " ")

            if "[" in text and "]" in text:
                start = text.index("[")
                end = text.rindex("]") + 1
                text = text[start:end]

            import re
            text = re.sub(r'\s+', ' ', text)

            print(f"🧹 JSON limpo: {text[:200]}...")

            questions_array = json.loads(text)

            if not isinstance(questions_array, list):
                print(f"⚠️ Resposta não é um array")
                continue

            valid_questions = []
            for i, q in enumerate(questions_array):
                try:
                    if (isinstance(q, dict) and
                        "question" in q and
                        "options" in q and
                        "correct" in q and
                        isinstance(q["options"], list) and
                        len(q["options"]) == 4 and 
                        isinstance(q["correct"], int) and
                        0 <= q["correct"] <= 3 and
                        len(q["question"]) > 10):
                        valid_questions.append(q)
                        print(f"   ✓ Pergunta {i+1} válida")
                    else:
                        print(f"   ✗ Pergunta {i+1} inválida")
                except Exception as e:
                    print(f"   ✗ Erro na pergunta {i+1}: {e}")

            if len(valid_questions) >= 1:
                print(f"✅ {len(valid_questions)} perguntas válidas geradas!")

                if len(valid_questions) > 1:
                    questions_cache.extend(valid_questions[1:])
                    print(f"📦 {len(valid_questions) - 1} perguntas adicionadas ao cache")

                return valid_questions[0]

        except json.JSONDecodeError as e:
            print(f"❌ Erro JSON: {str(e)[:100]}")
            if attempt < max_retries - 1:
                print(f"   Tentando novamente...")
        except Exception as e:
            error_str = str(e)
            print(f"❌ Erro: {type(e).__name__}: {error_str[:100]}")

            if "quota" in error_str.lower() or "429" in error_str or "exceeded" in error_str.lower():
                print("⚠️ Limite de API atingido (429/quota). Usando banco de dados.")
            if "401" in error_str or "403" in error_str or "permission" in error_str.lower() or "unauthorized" in error_str.lower():
                print("⚠️ Erro de autorização (401/403). Verifique sua GOOGLE_API_KEY.")
                break

    print(f"⚠️ Usando pergunta fallback - Nível {level}")
    level_questions = QUESTIONS_DB[level]
    idx = question_num % len(level_questions)
    return level_questions[idx]

@app.get("/test_ai")
async def test_ai():
    if not AI_ENABLED or model is None:
        return JSONResponse({"status": "error", "message": "IA não configurada. Defina a variável de ambiente GOOGLE_API_KEY."}, status_code=400)
    try:
        print("🧪 Testando conexão com IA Gemini...")
        response = model.generate_content("Responda apenas: OK")
        return JSONResponse({"status": "success", "message": "IA está funcionando!", "response": response.text})
    except Exception as e:
        err = str(e)
        print(f"❌ Test AI falhou: {type(e).__name__}: {err[:300]}")
        status = 500
        if "401" in err or "403" in err or "unauthorized" in err.lower():
            status = 401
        if "429" in err or "quota" in err.lower():
            status = 429
        return JSONResponse({"status": "error", "message": f"Erro ao conectar com IA: {err}", "error_type": type(e).__name__}, status_code=status)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/get_question")
async def get_question(
    question_num: int = Form(...),
    use_ai: bool = Form(True),
    answered: str = Form("")
):
    try:
        answered_list = json.loads(answered) if answered else []

        if question_num < 10:
            level = 1
        elif question_num < 20:
            level = 2
        else:
            level = 3

        question = None
        if use_ai and not questions_cache:
            question = generate_ai_question(level, question_num, answered_list)
        elif use_ai and questions_cache:
            question = questions_cache.pop(0)
            print(f"📦 Usando pergunta do cache (restam {len(questions_cache)})")

        if not question:
            level_questions = QUESTIONS_DB[level]
            idx = question_num % len(level_questions)
            question = level_questions[idx]
            print(f"📚 Usando pergunta do banco - Nível {level}")

        print(f"📤 Enviando pergunta {question_num + 1} - Nível {level}")

        return JSONResponse({
            "question": question,
            "level": level,
            "question_num": question_num
        })
    except Exception as e:
        print(f"❌ Erro em get_question: {e}")
        return JSONResponse({
            "error": str(e),
            "question": QUESTIONS_DB[1][0],
            "level": 1,
            "question_num": question_num
        }, status_code=500)

@app.post("/check_answer")
async def check_answer(
    question_data: str = Form(...),
    selected: int = Form(...)
):
   
    try:
        question = json.loads(question_data)
        is_correct = selected == question["correct"]

        return JSONResponse({
            "correct": is_correct,
            "correct_answer": question["correct"]
        })
    except Exception as e:
        print(f"❌ Erro em check_answer: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/get_ai_explanation")
async def get_ai_explanation(
    question: str = Form(...), 
    answer: str = Form(...)
):
    
    prompt = f"""Explique de forma breve (máximo 2 frases) por que a resposta para a pergunta abaixo é '{answer}':

 Pergunta: {question}

 Seja educativo e direto."""

    try:
        if not AI_ENABLED or model is None:
            print("⚠️ get_ai_explanation: IA não configurada, retornando explicação simples.")
            return JSONResponse({"explanation": f"A resposta correta é '{answer}'."})
        response = model.generate_content(prompt)
        return JSONResponse({"explanation": response.text.strip()})
    except Exception as e:
        print(f"❌ Erro ao gerar explicação: {type(e).__name__}: {str(e)[:200]}")
        return JSONResponse({"explanation": f"A resposta correta é '{answer}'."})

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🦋 QUIZ DA BORBOLETA - SISTEMA INFINITO")
    print("=" * 60)
    print("📊 Mecânica:")
    print("   🎯 Acerte 10 perguntas para libertar a borboleta")
    print("   🔄 Perguntas infinitas até completar")
    print("   📈 Níveis aumentam a cada 10 perguntas")
    print("=" * 60)
    print("🌐 Servidor rodando em: http://127.0.0.1:8000")
    print("🧪 Teste a IA em: http://127.0.0.1:8000/test_ai")
    print("=" * 60)

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
