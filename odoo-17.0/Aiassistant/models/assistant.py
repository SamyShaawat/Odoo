from odoo import api, fields, models
# from langchain_google_genai import ChatGoogleGenerativeAI


class Agent(models.Model):
    _name = 'agent'
    _description = 'Agents'

    ai_assistant = fields.Html(string="AI Assistant Ask Any Thing")
    question = fields.Char(string="Question")
    answer = fields.Text(string="Answer", default="yes")

    @api.onchange("question")
    def get_answer(self):
        for rec in self:
            GOOGLE_API_KEY = "AIzaSyBk70TPMXgF7CMUMtHuv-YUt104NGGk_iw"
            llm = ChatGoogleGenerativeAI(api_key=GOOGLE_API_KEY, model="gemini-1.5-flash")
            if rec.question:
                print(rec.question)
                result = llm.invoke(rec.question)
                rec.ai_assistant += str("AI assistant :: \n" + str(result.content))
                rec.answer = result.content
