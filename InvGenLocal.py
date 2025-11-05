import os

from groq import Groq

from groq.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam
from openai import OpenAI

#client = Groq(api_key=os.getenv("API_KEY"))



client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)




def getInvariant() -> str:


    progPoint_prompt3 = ''' You are given a Solidity smart contract. First, meticulously reason step by step and identify possible invariants (such as supply conservation, non-negative balances, or ownership conditions) using detailed, silent chain-of-thought reasoning. Do not display your reasoning. Next, give me only the invariant statements to be inserted at the critical program points and in which line. no explanation or extra text.
            Output format: line_number: invariant_statement; example: 20: assert(funcA2(funcA1())==12); '''


    # Usa direttamente il template del prompt come system message
    system_prompt = ChatCompletionSystemMessageParam(
        role="system",
        content=progPoint_prompt3
    )

    # Metti il contratto come user message
    user_prompt = ChatCompletionUserMessageParam(
        role="user",
        content=f"\n\n=== CONTRACT START ===\n{solidity_code}\n=== CONTRACT END ==="
    )

    # Chiamata al modello Groq
    response = client.chat.completions.create(
        model="llama-3.2-1b-instruct",
        messages=[system_prompt, user_prompt],
        temperature=0.7,
    )

    return response.choices[0].message.content


def run_pipeline_on_folder(folder_path="contracts_input"):
    invariants_dir = "invariants_generated"
    numerated_dir = "contracts_input_numerated"
    os.makedirs(invariants_dir, exist_ok=True)
    os.makedirs(numerated_dir, exist_ok=True)

    for root, dirs, files in os.walk(folder_path):
        rel_dir = os.path.relpath(root, folder_path)
        if rel_dir == ".":
            rel_dir = ""
        out_num_dir = os.path.join(numerated_dir, rel_dir)
        out_inv_dir = os.path.join(invariants_dir, rel_dir)
        os.makedirs(out_num_dir, exist_ok=True)
        os.makedirs(out_inv_dir, exist_ok=True)

        for filename in files:
            if not filename.endswith(".sol"):
                continue

            file_path = os.path.join(root, filename)
            print(f"\n Processing contract: {os.path.join(rel_dir, filename)}")
            print("=" * 60)

            # Leggi e numeri il contratto
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()
            numbered_code = enumerate_contract_lines(original_code)

            # Salva il contratto numerato nello stesso path relativo
            numerated_path = os.path.join(out_num_dir, filename)
            with open(numerated_path, "w", encoding="utf-8") as nf:
                nf.write(numbered_code)

            # Usa il contratto numerato nella pipeline
            global solidity_code
            solidity_code = numbered_code

            # Step 2: Critical Program Points
            progPoints = getInvariant()
            print(" Risposta 2 (Critical Program Points):")
            print(progPoints)
            print("-" * 60)

            # Salva output invariants mantenendo la stessa struttura
            contract_name = os.path.splitext(filename)[0]
            output_path = os.path.join(out_inv_dir, f"{contract_name}-inv.txt")
            with open(output_path, "w", encoding="utf-8") as out:
                out.write(progPoints if progPoints else "")


def enumerate_contract_lines(content: str) -> str:
    numbered_lines = []
    counter = 1
    for line in content.splitlines():
        if line.strip():
            numbered_lines.append(f"{counter} {line}")
            counter += 1
        else:
            numbered_lines.append("")
    return "\n".join(numbered_lines)


if __name__ == "__main__":
    run_pipeline_on_folder("contracts_input")
