"""Part 1: your first tool call.  Run: python tool_call.py
The steps are in README.md. Each one adds a few lines to the bottom of this file."""
import csv, io, json, os, sys
import requests
from dotenv import load_dotenv

load_dotenv()
if not os.environ.get("GROQ_API_KEY"):
    raise SystemExit("No GROQ_API_KEY found. Make a file called .env next to tool_call.py with one line: GROQ_API_KEY=your key")

# ---------- THE SHEET (given) ----------
# Plain code, no model: one lecture of the course sheet, looked up by its number.
SHEET = "https://docs.google.com/spreadsheets/d/1Kg6T-dJWaYx_JCPiRk3u0nBuAQcsCVRDPj1NFKP4WzM/gviz/tq?tqx=out:csv&headers=0&gid=368290478"

def get_lecture(number):
    for row in csv.reader(io.StringIO(requests.get(SHEET).text)):
        if row[1].startswith(f"{number}. "):
            return {"date": row[0], "title": row[1], "type": row[2], "tools": row[3]}
    return {"error": f"There is no lecture {number}. Lectures run from 1 to 19."}

# ---------- THE MODEL (given) ----------
# One message to Groq, one message back. Nothing is added that you do not send.
def ask_model(messages, tools=None):
    body = {"model": "openai/gpt-oss-120b", "messages": messages}
    if tools:
        body["tools"] = tools
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]}, json=body)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]

# ---------- YOUR SERVER (yours to write) ----------
# python tool_call.py                      asks the question below
# python tool_call.py "What is an API?"    asks your own
question = " ".join(sys.argv[1:]) or "When is Lecture 12 of 100xEngineers Cohort 8, and what is it about?"
messages = [{"role": "user", "content": question}]

# Step 2. The card: fill in the two empty strings.
card = {"type": "function", "function": {
    "name": "get_lecture",
    "description": "gets the lecture details for the given lecture number",                                                    # Use it when
    "parameters": {"type": "object",
                   "properties": {"number": {"type": "integer",
                                             "description": "The lecture number to retrieve"}},         # It needs
                   "required": ["number"]},
}}

reply = ask_model(messages,[card])                 # Step 2: send the card too
print(json.dumps(reply, indent=2, ensure_ascii=False))



# # Step 3. Run the request the model wrote.
# argument=json.loads(reply["tool_calls"][0]["function"]["arguments"])
# get_lecture_result = get_lecture(argument["number"])
# print(json.dumps(get_lecture_result, indent=2, ensure_ascii=False))


# # Step 4. Hand the result back to the model and print its answer.
# messages.append(reply)
# messages.append({"role": "tool", "tool_call_id": reply["tool_calls"][0]["id"], "name": "get_lecture", "content": json.dumps(get_lecture_result)})
# reply2 = ask_model(messages,[card])
# print(json.dumps(reply2, indent=2, ensure_ascii=False))

# Step 5. Turn steps 3 and 4 into a loop.
while reply.get("tool_calls"):
    messages.append(reply)
    for tool_call in reply["tool_calls"]:
        if tool_call["function"]["name"] == "get_lecture":
            argument=json.loads(tool_call["function"]["arguments"])
            get_lecture_result = get_lecture(argument["number"])
            print(json.dumps(get_lecture_result, indent=2, ensure_ascii=False))
            messages.append({"role": "tool", "tool_call_id": tool_call["id"], "name": "get_lecture", "content": json.dumps(get_lecture_result)})
    reply = ask_model(messages,[card])

print(json.dumps(reply, indent=2, ensure_ascii=False))
