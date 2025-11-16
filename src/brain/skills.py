"""
Agent Skills - Prompt Templates for AI Agent
Provides static methods for generating specialized prompts
"""


class Skills:
    """Collection of prompt templates for agent tasks"""
    
    @staticmethod
    def summarize(text):
        """Generate a prompt to summarize text into key bullet points"""
        return f"""Please summarize the following text into clear, concise bullet points.
Focus on the most important information and key takeaways.

TEXT TO SUMMARIZE:
{text}

SUMMARY (bullet points):"""
    
    @staticmethod
    def paraphrase(text):
        """Generate a prompt to paraphrase text professionally"""
        return f"""Please paraphrase the following text to be more professional and polished.
Maintain the original meaning but improve clarity and tone.

ORIGINAL TEXT:
{text}

PARAPHRASED VERSION:"""
    
    @staticmethod
    def get_router_prompt(user_query, selected_text=None):
        """
        Generate a routing prompt for the fast model to choose the right tool.
        This is the MOST IMPORTANT method - it determines which tool to use.
        """
        has_selected_text = selected_text and len(str(selected_text).strip()) > 20
        
        prompt = f"""You are a routing agent. Choose ONE tool from this list to handle the user's query:

AVAILABLE TOOLS:
[WEB_SEARCH] - Use for news, current events, research, "latest" information, or any query requiring up-to-date web data
[WIKIPEDIA] - Use for factual information, definitions, historical facts, or encyclopedic knowledge
[SUMMARIZE] - Use ONLY if the user has selected text and wants to summarize it
[PARAPHRASE] - Use ONLY if the user has selected text and wants to paraphrase/rewrite it
[GENERAL_QA] - Use for simple questions that don't need external data

USER QUERY: {user_query}

SELECTED TEXT AVAILABLE: {"YES - User has highlighted text" if has_selected_text else "NO - No text selected"}

CRITICAL RULES:
1. For queries with "latest", "news", "current", "today", "recent" → always use [WEB_SEARCH]
2. For "summarize" or "paraphrase" → ONLY use [SUMMARIZE] or [PARAPHRASE] if selected text exists
3. For factual/historical questions → use [WIKIPEDIA]
4. For simple questions → use [GENERAL_QA]

Reply with ONLY the tool name in brackets, like: [WEB_SEARCH]

YOUR CHOICE:"""
        
        return prompt
