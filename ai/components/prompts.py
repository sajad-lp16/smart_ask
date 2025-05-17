ROUTER_PROMPT = """
Analyze the following client input and conversation history with STRICT PRIORITY:
1. **USER INPUT** - Primary source for intent and identifiers. A clear, new subject introduced here **overrides** any previous implicit subject context.
2. **HISTORY** - Consult only for *disambiguating ambiguous user input*. Prioritize the *immediately preceding turn* to understand the **Current Subject Context**. Use older history cautiously and only when the preceding turn is insufficient or the current input explicitly refers further back.

STRICT CATEGORIES:
1. **"summarize"** – ONLY If the client EXPLICITLY or IMPLICITLY requests a summary using words like "summarize", "recap", "brief", **OR** asks for the "main concern", "key point", or "what happened" in a ticket, conversation, or deal.
2. **"question"** – For CLEAR technical/platform functionality questions (password reset, features, purchases) OR requests for help responding to tickets OR requests for specific details about tickets (participants, status, history).
3. **"help"** – For bot usage help, greetings, or if the input is not related to chat history and is very unclear or generic.

CONVERSATION CONTINUITY & CONTEXT INHERITANCE RULES:
- The **Current Subject Context** for interpreting ambiguous follow-ups (like "more details", "about it") is primarily determined by the subject of the *immediately preceding user turn*.
- If a user input introduces a clear, new subject that is **unrelated** to the subject of the previous turn (e.g., asking "how can I reset my password?" after discussing a specific ticket), this establishes a NEW **Current Subject Context**. For the purpose of interpreting the *current turn's implicit references*, the context and identifiers from turns *before* the immediately preceding turn are discarded.
- If a user input is a follow-up using pronouns ("it", "this", "that") or generic references ("the ticket", "that request") AND the **Current Subject Context** (from the immediately preceding turn) was related to a ticket:
    - Classify based on the *new input's intent* (e.g., "question" for ticket details, "summarize" for explicit summary of that ticket).
    - Inherit the ticket_id and any other relevant identifiers from the immediately preceding turn's context.
- If a user input is a follow-up using pronouns or generic references AND the **Current Subject Context** (from the immediately preceding turn) was related to a **non-ticket subject** (e.g., password reset, feature details):
    - Classify as "question".
    - The follow-up refers to the **non-ticket subject** of the preceding turn. DO NOT inherit ticket identifiers from older history in this case.

CRITICAL RULES:
- Prioritize the **Current Subject Context** from the *immediately preceding turn* when interpreting ambiguous input or follow-ups.
- Any request about ticket details (participants, status, history, ...) is ALWAYS "question", NEVER "summarize".
- Ticket references ALWAYS inherit identifiers when:
    - Using pronouns ("it", "this ticket") *AND* the **Current Subject Context** (from the previous turn) is a ticket.
    - Using generic references ("the ticket", "that request") *AND* the **Current Subject Context** (from the previous turn) is a ticket.
- Explicit identifiers in the current input (e.g., "summarize ticket 789") ALWAYS establish the identifiers for the current turn, overriding any previous implicit or explicit context.
- Implicit ticket context is maintained through a conversation thread *only when the user's input continues to clearly refer to that ticket subject or its details*. A clear shift to a new, unrelated subject breaks this implicit ticket context chain for follow-ups.

HISTORY HANDLING RULES:
- Set `ignore_history` to `true` ONLY when:
  1. The query introduces a completely new, unrelated subject
  2. The query is a standalone question that doesn't need any context
  3. The query contains explicit identifiers that override any previous context
- Set `ignore_history` to `false` when:
  1. The query is a follow-up question using pronouns or references to previous context
  2. The query is asking for more details about the previous subject
  3. The query is related to the same ticket, person, or deal as the previous turn
  4. The query uses terms like "it", "this", "that", "the ticket", "that request" in reference to the previous context

RESPONSE FORMAT:
Make sure the response is in standard JSON deserializable format, with nothing before or after the json response. I want to deserialize your response directly with json.loads().
Avoid any backslashes before underscore, and any `\\n`s that are invalid in JSON.

```json
{
  "message_type": "summarize|question|help",
  "deal_ids": [<Extracted or inherited deal IDs used for response, ensure integer type and they can be mentioned in these formats (deal, dealID, deal_id, deal id, deal#)>],
  "emails": [<Extracted or inherited emails used for response>],
  "person_ids": [<Extracted or inherited person IDs used for response, ensure integer type and they can be mentioned in these formats (person, personID, person_id, person id, person#)>],
  "ticket_ids": [<Extracted or inherited ticket IDs used for response, ensure integer type and they can be mentioned in these formats (ticket, ticketID, ticket_id, ticket id, ticket#)>],
  "ignore_history": <boolean>  # Set to true ONLY for new, unrelated subjects or standalone questions
}
```

HERE IS THE CLIENT INPUT:

%s
"""

ZAMMAD_QA_PROMPT = """I need to implement a RAG system to provide answers for users' questions. I'll provide you with a conversation where the client explains one or more problems, and the staff provides solutions. There might be multiple back-and-forth exchanges between the client and the staff before reaching a solution, or there might be internal notes between multiple staff members. You will receive all of these.

You must respect these rules:
1. For each ticket, provide an array of JSON objects, where each object contains two attributes: "problem" and "solution".
2. Only consider problems that are not about a specific account, person, or identifiable information (e.g., "Was my account Mike@sth created?" should be excluded).
3. The "problem" field should summarize the problem the client was asking about, transformed into a **general question form**. Do not mention specific emails, person names, account states, version numbers, app store timelines, or any identifiable information.
4. The "solution" field should provide the final solution the support staff provided, **generalized to address the "problem" field** without mentioning specific emails, person names, account states, version numbers, app store timelines, or any identifiable information. The solution should be phrased as a **general recommendation or action** (e.g., "Contact support to resolve this issue").
5. If the ticket involves multiple problems and solutions, the JSON array should contain multiple entries, one for each problem/solution set. Ensure that **all relevant problem-solution pairs** are included.
6. If the conversation is purely operational (e.g., ticket assignments or status updates), return an empty array.
7. If the conversation contains secret information like passwords, do not include them in the response.
8. Avoid any reference to account states (e.g., "active," "inactive," "exists," "does not exist") or any other details that could imply specific account information.
9. Avoid mentioning specific technical details like version numbers, app store timelines, or implementation specifics. Instead, provide **general solutions** like "it will happen soon" or "contact support for more information."
10. Ensure the "solution" field is phrased as a **general recommendation or action** that can be applied to any user facing a similar issue. For example, instead of "The support staff updated the account role," use "Contact support to update your account role."
11. Extract **as many question-answer sets as possible** from the conversation, ensuring that each problem-solution pair is distinct and addresses a unique issue.

Make sure the response in standard JSON deserializable format, nothing before or after the json response, wanna deserialize your response directly.
Avoid any backslashes before underscore, and any `\n`s that is invalid in JSON.
this is the conversation:

```
%s
```
"""

FORUM_QA_PROMPT = """I need to implement a RAG system to provide answers for users' questions. I'll provide you with conversations that may include:
1. Client problems and staff solutions
2. Feature announcements/updates
3. Internal staff discussions about features

You must respect these rules:

[Problem-Solution Extraction]
1. Output an array of JSON objects with "problem" (question form) and "solution" (detailed guide)
2. For client issues:
   - Generalize problems/solutions (remove personal/account info)
   - Phrase problems as questions ("How to...")
   - Include all technical details in solutions

[Update Notes Handling]
3. For update announcements:
   - Focus ONLY on new features/capabilities (ignore bug fixes unless they enable new functionality)
   - Convert feature announcements into "How to use X" format
   - Include detailed usage instructions when available
   - Skip trivial fixes (e.g., "fixed email composition bugs")

[Technical Details]
4. Solutions must include:
   - Step-by-step instructions for features
   - Configuration requirements
   - Technical parameters/settings
   - Usage examples when available

[Formatting]
5. Always provide:
   - Clear problem statements as questions
   - Complete, actionable solutions
   - Structured steps for complex features
   - Machine-readable JSON only (no commentary)

Example Output:
```json
[
  {
    "problem": "How to use the new export notification system?",
    "solution": "1. Enable notifications in Account Settings > Notifications\n2. Select preferred notification channels (email/SMS)\n3. Set notification triggers for export completion events"
  }
]
```
Avoid any backslashes before underscore, and any `\n`s that is invalid in JSON.
If you can't find any QA pairs just return empty array, nothing before or after it so it can be deserializable.
Current conversation:

```
%s
```
"""

QA_COMBINATION_PROMPT = """
I will provide you with multiple JSON arrays containing question-answer pairs extracted from different chunks of the same conversation. Your task is to:

1. Combine all the question-answer pairs into a single JSON array
2. Remove any duplicate entries (where both the problem and solution are identical)
3. Maintain all the original formatting rules:
   - Keep problems in general question form
   - Keep solutions as general recommendations
   - Exclude any specific identifiers
   - Follow all the extraction rules from the original prompt

Input format:
[
    [
      {"problem": "general question 1", "solution": "general solution 1"},
      {"problem": "general question 2", "solution": "general solution 2"}
    ],
    [
      {"problem": "general question 3", "solution": "general solution 3"},
      {"problem": "general question 4", "solution": "general solution 4"}
    ]
]

Output format:
[
  {"problem": "general question 1", "solution": "general solution 1"},
  {"problem": "general question 2", "solution": "general solution 2"},
  {"problem": "general question 3", "solution": "general solution 3"}
  {"problem": "general question 4", "solution": "general solution 4"}
]

Rules:
- Preserve the order of questions as they appeared in the conversation
- Only remove exact duplicates (where both problem and solution text are identical)
- Do not modify the wording of any existing questions or solutions
- If two entries have similar but not identical problems/solutions, keep both
- Return only the final merged JSON array, with no additional text
- Make sure the response in standard JSON deserializable format, nothing before or after the json response, wanna deserialize your response directly.
Avoid any backslashes before underscore, and any `\n`s that is invalid in JSON.


Here are the JSON chunks to merge:
```
%s
```
"""
SUMMARIZE_PROMPT = """Analyze the following conversation and provide:
I need the response to follow the example below, Make sure the response in standard JSON deserializable format, nothing before or after the json response, wanna deserialize your response directly.
Avoid any backslashes before underscore, and any `\n`s that is invalid in JSON.

{
  "emails" (type=list of valid emails string): [""All valid emails you can find"" ],
  "summary" (type=string): "Extract a structured and detailed summary from the following unstructured email conversation.
                ### **Instructions:**  
                1. **Sort all messages by Date & Time** before structuring the summary.  
                2. Output **only** the structured summary with **no extra explanations before or after**.  
                3. Use the following format:  

                ---
                #### **1. Who Said What (Sort by Date & Time)**  

                - **[Person A] (Role, Company) – [Date & Time]:**  
                - Key contributions  
                - Important details  
                - *Key quote:* "*Relevant statement from email*"  

                - **[Person B] (Role, Company) – [Date & Time]:**  
                - Key contributions  
                - High-priority and medium-priority details
                - *Key quote:* "*Relevant statement from email*"  

                #### **2. Timeline**  
                - **[Date]:** Event description  
                - **[Date]:** Event description  

                #### **3. Key Events/Issues**  
                - **Issue 1:** Summary of the problem and resolution  
                - **Feedback Submission:** Summary of feedback given  
                - **Access/Login Issues:** Summary of troubleshooting and resolution  

                #### **4. Action Items**  
                - **Pending:**  
                - Task 1 (assigned to [Person/Team])  
                - Task 2 (assigned to [Person/Team])  
                - **Completed:**  
                - Task 1  
                - Task 2  

                #### **5. Technical Details (if applicable)**  
                - **Account/Login Info:** Details  
                - **Study ID/Project Code:** Details  

                #### **6. Next Steps**  
                - **Action 1:** Description and responsible person  
                - **Action 2:** Description and responsible person"
}
```
%s
```
"""

SUMMARIZE_COMBINATION_PROMPT = """
You have multiple JSON objects, each containing a structured analysis of a chunk of a conversation. Your task is to combine these analyses into a single, cohesive JSON object with the same format as the individual chunk responses. Ensure the following:
Please make sure to:
- Sort all messages by Date & Time from all chunks combined.
- Maintain the structure and format for each section in the final response.
- If any action items, issues, or next steps appear in multiple chunks, merge them appropriately, ensuring the tasks are not duplicated.
Make sure the response in standard JSON deserializable format, nothing before or after the json response, wanna deserialize your response directly.
Avoid any backslashes before underscore, and any `\n`s that is invalid in JSON.

{
  "emails": ["All valid emails from all chunks"],
  "summary": "Extract a structured and detailed summary from the following unstructured email conversation. 
                ### **Instructions:**  
                1. **Sort all messages by Date & Time** before structuring the summary.  
                2. Output **only** the structured summary with **no extra explanations before or after**.  
                3. Use the following format:  

                #### **1. Who Said What (Sort by Date & Time)**  
                - **[Person A] (Role, Company) – [Date & Time]:**  
                - Key contributions  
                - Important details  
                - *Key quote:* "*Relevant statement from email*"  

                - **[Person B] (Role, Company) – [Date & Time]:**  
                - Key contributions  
                - High-priority and medium-priority details
                - *Key quote:* "*Relevant statement from email*"  

                #### **2. Timeline**  
                - **[Date]:** Event description  
                - **[Date]:** Event description  

                #### **3. Key Events/Issues**  
                - **Issue 1:** Summary of the problem and resolution  
                - **Feedback Submission:** Summary of feedback given  
                - **Access/Login Issues:** Summary of troubleshooting and resolution  

                #### **4. Action Items**  
                - **Pending:**  
                - Task 1 (assigned to [Person/Team])  
                - Task 2 (assigned to [Person/Team])  
                - **Completed:**  
                - Task 1  
                - Task 2  

                #### **5. Technical Details (if applicable)**  
                - **Account/Login Info:** Details  
                - **Study ID/Project Code:** Details  

                #### **6. Next Steps**  
                - **Action 1:** Description and responsible person  
                - **Action 2:** Description and responsible person"
}
```
Analysis json objects as a list to combine:

```json
%s
```
"""

WELCOME_MESSAGE = """### 👋 Welcome to **Avicenna Assistant Bot**! 🤖✨

Here's what I can help you with:

---

### 🛠️ What I can do:

1. 🧠 **Answer technical questions** about the platform.
   👉 Just ask me anything!

2. 📝 **Summarize tickets and conversations**  
   📌 I can:
   - Summarize a specific ticket (just give me the **ticket ID** 🎟️)
   - Summarize all conversations related to a **person** or a **deal**
   - Answer questions based on those conversations

   🧾 Just provide any of the following:
   - **person email** 📧  
   - **person ID** 🆔  
   - **deal ID** 💼  
   - or a combination of them!

---

### 🧪 Try asking me things like:

- ❓ _“can I try the application before I purchase a license?”_  
- 📄 _“Summarize ticket `#12345`”_  
- 🗣️ _“Summarize conversations with `john.doe@example.com` and `foo.bar@example.com`”_  
- 🤔 _“What’s the main concern from `deal_456` conversations?”_

---

🧭 I’m here to guide you — just tell me what you need! 🚀💬"""

QA_PROMPT_TEMPLATE = r"""
You are an expert assistant. The user will ask a question and you'll try to determine if the documents provided contain enough relevant information to answer it.

IMPORTANT INSTRUCTION ON USING CONTEXT:
Analyze the provided context thoroughly to answer the user's question.
- If the context contains specific details, steps, or facts that directly answer the question, synthesize a **comprehensive answer** using **all relevant information** from those parts of the context. Include as many pertinent details as possible to fully address the query based on the provided text.
- If the context includes a phrase like "contact support", "refer to customer service", or similar instructions:
    - DO NOT immediately default to this instruction.
    - First, check if *other* parts of the provided context contain information to answer the question directly.
    - Only include the instruction to "contact support" (or the equivalent phrase found in the context) in your final answer IF AND ONLY IF the provided context contains ABSOLUTELY NO OTHER relevant information to answer the user's question. In this specific case, clearly state that according to the provided information, the user should contact support.
- If ABSOLUTELY NO relevant information (including any 'contact support' instructions) is found in the context, state in the `answer` field that you could not find the answer in the provided context.

Respond strictly in JSON format with exactly two keys: "related" and "answer".
- Set the value of "related" to `true` (boolean) IF and only IF you were able to find and use relevant information from the provided context to populate the `answer` field (this includes the specific case where the only relevant information found was a 'contact support' instruction).
- Set the value of "related" to `false` (boolean) IF the provided context contained no relevant information at all to answer the question.
- The value of "answer" should be the synthesized answer based on the context (if `related` is true) or a concise statement indicating that the information was not found in the context (if `related` is false).

Ensure the JSON is valid and can be parsed by json.loads(). Specifically, make sure string values are properly quoted and escaped (e.g., backslashes `\\`, quotes `\"`, and newlines `\n` within the "answer" string must be correctly escaped according to JSON rules). Avoid any non-standard backslashes (like before underscores `\_` unless they are part of an escaped sequence) or unescaped newlines outside of string values.

Question:
{query_str}

Context:
{context_str}
"""

QA_BASED_PROMPT_TEMPLATE = """
You are an expert assistant helping users extract as much relevant information as possible from ticket documents.

You will be given a user question and a context from a ticket. Your task is to interpret the question naturally and answer it using all applicable information found in the ticket. 

- If the question asks about people, extract **all individuals** mentioned and include their **full details** (name, role, affiliation, actions taken, questions asked, and responses).
- Include **quotes, timestamps, technical references, and next steps** where relevant.
- Return the response using **Markdown formatting** for clarity (e.g., use lists, bold, headers).
- Your answer should be **as complete and detailed as possible** based on the context provided.

If the ticket does **not contain enough information** to answer the question, respond with:
**"Sorry, the question you asked is not covered in this ticket."**

---

**Question:**  
{query_str}

**Context:**  
{context_str}

"""
AVICENNA_LEARN_PROMPT = """DOCUMENT PROCESSING PROMPT:
Transform the input documentation into an optimized RAG-ready format by following these exact steps:

1. STRUCTURE THE CONTENT:
- Create clear hierarchical headings (## Section, ### Subsection)
- Group related information logically
- Maintain original document flow while improving scannability

2. CONTENT OPTIMIZATION:
- Remove redundant explanations but preserve all key concepts
- Maintain technical terms, proper nouns, and brand terminology
- Preserve code snippets, commands, and UI elements exactly
- Keep numbered steps/procedures in original order

3. LINK PROCESSING:
- Preserve ALL external links exactly as-is
- For internal links without domain (e.g., "/reference/surveys"):
  * Prepend with "https://learn.avicennaresearch.com"
  * Example: "/reference/surveys" → "https://learn.avicennaresearch.com/reference/surveys"
- Never modify:
  * Anchor text
  * Query parameters (#versions-import-and-export)
  * File extensions (.pdf, .html, etc.)

4. IMAGE PROCESSING:
- Ensure all image URLs use domain: "https://learn.avicennaresearch.com"
- Convert relative paths (e.g., "/assets/images/...") to absolute URLs
- Maintain original alt text and image descriptions
- Keep exact image formatting: ![alt text](https://learn.avicennaresearch.com/path/to/image.png)

5. FORMATTING RULES:
- Use strict Markdown syntax
- Bold UI elements like *Menu Name* or *Button Text*
- Code-related text in `monospace`
- Bullet points for feature lists
- Preserve all line breaks between sections

6. PROTECTED CONTENT (never modify):
- API endpoints and code samples
- CLI commands and config parameters
- Error messages and version numbers
- Warning/note boxes
- Any content between ```code blocks```
- External URLs (always keep original)

7. OUTPUT REQUIREMENTS:
- Return only processed content (no commentary)
- Maintain original line breaks between sections
- Preserve exact capitalization of technical terms
- Keep warnings/notes verbatim
- Ensure all internal links/images use correct domain
- Never alter external links

Process this document according to these rules:
```
%s
```
"""
