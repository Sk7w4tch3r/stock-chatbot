import streamlit as st
from bokeh.models import CustomJS
from bokeh.models.widgets import Button
from streamlit_bokeh_events import streamlit_bokeh_events
import requests
import json
from tokenizers import tokenizer
import os
from streamlit.report_thread import get_report_ctx


def _get_session():
    import streamlit.report_thread as ReportThread
    from streamlit.server.server import Server
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_info.session



SESSION = _get_session()
HOST = os.environ.get('HOST', '127.0.0.1')

url = f'http://{HOST}:5005/webhooks/rest/webhook'
headers = {
    "Content-type": "application/json"
}

stt_button = Button(label="Speak", width=100)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.lang = 'fa-IR';
    recognition.continuous = false;
    recognition.interimResults = true;
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
    """))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

if result:
    if "GET_TEXT" in result:
        st.write(result.get("GET_TEXT"))

        # post to Rasa:
        data = {
            'sender': SESSION.id,
            'message': tokenizer.tokenize(result.get("GET_TEXT"))
        }
        
        response = requests.post(
                                url = url,
                                data = json.dumps(data),
                                headers = headers
        )
        
        for i in json.loads(response.content):
            st.write(i['text'])


