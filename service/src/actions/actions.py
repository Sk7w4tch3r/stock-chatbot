import logging
import os
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)


qa_model = AutoModelForQuestionAnswering.from_pretrained('../models')
qa_tokenizer = AutoTokenizer.from_pretrained('../models')
qa_nlp = pipeline('question-answering', model=qa_model, tokenizer=qa_tokenizer)

contexts = {}
for file in os.listdir('../data'):
    with open('../data/' + file, 'r', encoding='utf-8') as f:
        contexts[file.split('.')[0]] = f.read()


class ActionStockQA(Action):
    def name(self) -> Text:
        return "action_stock_qa"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:
        
        question = tracker.latest_message.get('text')
        intent = tracker.latest_message.get('intent').get('name')
        logger.info(f'intent: {intent}')
        # dispatcher.utter_message(text=f'intent: {intent}')
        
        QA_input = {
            'question': question,
            'context': contexts[intent]
        }

        res = qa_nlp(QA_input)

        dispatcher.utter_message(text=res['answer'])

        return []


class ActionCloseSession(Action):

    def name(self):
        return "action_close_session"

    
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="سپاس از همراهی شما!")

        return [AllSlotsReset()]
