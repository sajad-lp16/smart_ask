ROUTER_PROMPT = """
Analyze the following client input and determine its intent based on these STRICT categories:
1. **"summarize"** – ONLY if the client EXPLICITLY asks to summarize (using words like "summarize", "recap", "brief") a ticket, conversation, or deal.
2. **"question"** – For CLEAR technical/platform functionality questions (password reset, features, purchases) OR requests for help responding to tickets.
3. **"help"** – For bot usage help, greetings, or unclear requests.

ENHANCED CLASSIFICATION RULES:
For ticket response assistance ("help me respond to this ticket"):
- Classify as "question" if the request involves platform functionality
- Extract ALL relevant identifiers (email/person_id/deal_id/ticket_id) from:
  a) The direct request ("using conversation from X")
  b) The client’s message (if the client requests action using an identifier)
- Do **NOT** extract any identifiers if they are merely mentioned and not directly referenced for action.
- **IGNORE** the ticket content entirely in case of ticket response assistance and focus on the client’s direct request.

STRICT EXTRACTION RULES:
1. **ALWAYS** extract identifiers when:
   - They are preceded by action verbs like "using", "based on", "from" and are clearly referenced for response/summary purposes.
2. **NEVER** extract identifiers that are merely mentioned without an explicit request for action.
3. **IGNORE** any irrelevant content such as mere mentions of "person id", "ticket id", or "deal id" unless explicitly referenced for a specific action.

RESPONSE FORMAT:

```json
{
  "message_type": "summarize|question|help",
  "deal_ids": [<Extracted deal IDs used for response>],
  "emails": [<Extracted emails used for response>], 
  "person_ids": [<Extracted person IDs used for response>],
  "ticket_ids": [<Extracted ticket IDs used for response>]
}
```

Here is the client input:
```
what should be qwewefwf```
"""

QA_PROMPT = """I need to implement a RAG system to provide answers for users' questions. I'll provide you with a conversation where the client explains one or more problems, and the staff provides solutions. There might be multiple back-and-forth exchanges between the client and the staff before reaching a solution, or there might be internal notes between multiple staff members. You will receive all of these.

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

Make sure the response in standard JSON deserializable format, nothing before or after the json response.
this is the conversation:

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
- Make sure the response in standard JSON deserializable format, nothing before or after the json response.

Here are the JSON chunks to merge:
```
%s
```
"""
SUMMARIZE_PROMPT = """Analyze the following conversation and provide:
I need the response to follow the example below, Make sure the response in standard JSON deserializable format, nothing before or after the json response.
{
  "emails": [""All valid emails you can find""],
  "summary": "Extract a structured and detailed summary from the following unstructured email conversation.
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
Make sure the response in standard JSON deserializable format, nothing before or after the json response.

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

Analysis json objects as a list to combine:

```json
%s
```
"""
