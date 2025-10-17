import os
import json
import re
import google.generativeai as genai

# ===============================
# KONFIGURĀCIJA
# ===============================
API_KEY = "AIzaSyD3o_sQ04RLG69sWcJCDl2zgT0Le5geiX4"  # <-- ŠEIT IEVADI SAVU GEMINI API ATSLĒGU
MODEL_NAME = "gemini-1.5-flash"
TEMPERATURE = 0.3

# ===============================
# FUNKCIJAS
# ===============================

def create_prompt(jd_text, cv_text):
    """Izveido Gemini promptu un saglabā to kā prompt.md."""
    prompt = f"""
Tu esi HR speciālists, kas analizē darba aprakstu un kandidāta CV.

### Darba apraksts (JD):
{jd_text}

### Kandidāta CV:
{cv_text}

Uzdevums:
Izvērtē kandidāta atbilstību darba aprakstam un atgriez rezultātu **tikai JSON formātā** ar šo struktūru:
{{
  "match_score": 0-100,
  "summary": "Īss apraksts, cik labi CV atbilst JD.",
  "strengths": ["Galvenās prasmes/pieredze no CV, kas atbilst JD"],
  "missing_requirements": ["Svarīgas JD prasības, kas CV nav redzamas"],
  "verdict": "strong match | possible match | not a match"
}}
"""
    with open("prompt.md", "w", encoding="utf-8") as f:
        f.write(prompt)
    return prompt

def call_gemini(prompt):
    """Izsauc Gemini Flash 2.5 un atgriež strukturētu JSON rezultātu."""
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(prompt, generation_config={"temperature": TEMPERATURE})
    text = response.text.strip()

    try:
        # Ja modelis atgriež tīru JSON
        return json.loads(text)
    except json.JSONDecodeError:
        # Ja atbildē ir papildu teksta rindas
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        print("⚠️ Neizdevās parsēt JSON no atbildes.")
        print("Atbilde no modeļa:", text)
        return {}

def save_json(data, filepath):
    """Saglabā JSON failu ar UTF-8 kodējumu."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_report(data, output_path):
    """Ģenerē īsu Markdown pārskatu no JSON rezultāta."""
    report = f"""
# Kandidāta novērtējums

**Atbilstības punktu skaits:** {data.get('match_score', 'N/A')}  
**Kopsavilkums:** {data.get('summary', '')}

## Stiprās puses
- {"\n- ".join(data.get("strengths", []))}

## Trūkstošās prasības
- {"\n- ".join(data.get("missing_requirements", []))}

**Verdikts:** `{data.get('verdict', '')}`
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

# ===============================
# GALVENĀ PROGRAMMA
# ===============================

def main():
    os.makedirs("outputs", exist_ok=True)
    print("📄 --- DARBA APRĀKSTA UN CV SALĪDZINĀŠANA ---\n")

    print("Ievadi vai ielīmē darba aprakstu (JD). Beidz ar tukšu rindu:")
    jd_lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        jd_lines.append(line)
    jd_text = "\n".join(jd_lines)

    print("\n✅ JD saglabāts.\n")

    num_cv = int(input("Cik CV vēlies salīdzināt? (piemēram, 3): "))

    for i in range(1, num_cv + 1):
        print(f"\nIevadi vai ielīmē kandidāta {i} CV tekstu. Beidz ar tukšu rindu:")
        cv_lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            cv_lines.append(line)
        cv_text = "\n".join(cv_lines)

        print(f"\n➡️ Analizēju CV{i}...")

        prompt = create_prompt(jd_text, cv_text)
        result = call_gemini(prompt)

        json_path = f"outputs/cv{i}.json"
        report_path = f"outputs/cv{i}_report.md"

        save_json(result, json_path)
        generate_report(result, report_path)

        print(f"✅ Saglabāts: {json_path} un {report_path}\n")

    print("🎉 Visi kandidāti ir novērtēti!")

# ===============================
# STARTS
# ===============================
if __name__ == "__main__":
    main()
