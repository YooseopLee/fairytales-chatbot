"""
conda activate textgen
cd fastapi
streamlit run HNLP_mini_project_full.py
"""


import streamlit as st
import json
from streamlit_chat import message  # chat UI
from HNLP_mini_project_prompt import *


##########################
# Preprocessing
##########################
import openai
openai.api_key = ""

import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

# import fairytaleQA dataset
import pandas as pd

the_ugly_duckling_s = pd.read_csv("the-ugly-duckling-story.csv")
the_ugly_duckling_q = pd.read_csv("the-ugly-duckling-questions.csv")
cinderella_s = pd.read_csv("cinderella-or-the-little-glass-slipper-story.csv")
cinderella_q = pd.read_csv("cinderella-or-the-little-glass-slipper-questions.csv")
happy_prince_s = pd.read_csv("happy-prince-story.csv")
happy_prince_q = pd.read_csv("happy-prince-questions.csv")

title = {0:"the ugly duckling", 1:"cinderella", 2:"happy prince"}
story = {0:the_ugly_duckling_s, 1:cinderella_s, 2:happy_prince_s}
question = {0:the_ugly_duckling_q, 1:cinderella_q, 2:happy_prince_q}

for i in range(len(story)):
    for j in range(len(story[i])):
        story[i]['text'][j] = sent_tokenize(story[i]['text'][j])


##########################
# Greeting
##########################

def greeting_chat(prompt_message, input_text):
    user_input = {"role": "user", "content": input_text}
    st.session_state['messages'].append(user_input)

    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages= prompt_message + st.session_state['messages'])

    bot_completion = completion.choices[0].message.content
    if "<selected>" in bot_completion:
        selected = int(bot_completion.split(':')[1])
        return selected
    
    bot_response = {"role": "assistant", "content": bot_completion}
    st.session_state['messages'].append(bot_response)

    return None


##########################
# Reading
##########################
def make_reading_prompt(selected_book:int, section:int):
    reading = ""
    for line in story[selected_book]['text'][section-1]:
        reading += line +"\n"
    df = question[selected_book].loc[question[selected_book]['cor_section']== str(section), ['question', 'ex-or-im1', 'attribute1','answer1']]
    df = df.loc[df['ex-or-im1'] == 'implicit', ['question', 'attribute1', 'answer1']]
    df = df.reset_index(drop=True)
    for i, row in df.iterrows():
        reading += f"\n#question {i + 1}: {row['question']}\n#answer {i + 1}: {row['answer1']}\n\n"

    return reading + reading_prompt

def reading(selected_book:int, section:int):
    if st.session_state['model'] == 'C':
        section_sentence = ""
        for line in story[selected_book]['text'][section-1]:
            section_sentence += (line + "\n")
        bot_response = {"role": "assistant", "content": section_sentence}
        st.session_state['messages'].append(bot_response)
        return None
    else :
        prompt = make_reading_prompt(selected_book, section) 
        
        completion = openai.completions.create(
            model = "text-davinci-003",
            prompt = prompt,
            max_tokens = 1000,
            temperature = 0
        )
        tokenized = sent_tokenize(completion.choices[0].text)
        
        section_sentence = ""
        for line in tokenized:
            section_sentence += line + "\n"
        bot_response = {"role": "assistant", "content": section_sentence}
        st.session_state['messages'].append(bot_response)
        return None


##########################
# Facilitating
##########################
def make_question_prompt(selected_book:int, section:int):
    reading = ""
    for line in story[selected_book]['text'][section-1]:
        reading += line +"\n"

    return reading + question_making_prompt


def question_making(selected_book:int, section:int):
    prompt = make_question_prompt(selected_book, section)

    completion = openai.completions.create(
        model = "text-davinci-003",
        prompt = prompt,
        max_tokens = 1000,
        temperature = 0
    )

    return completion.choices[0].text


def check_facilitating(selected_book:int, section:int):
    if st.session_state['model'] == 'A' or st.session_state['model'] == 'C':
        df = question[selected_book].loc[question[selected_book]['cor_section']== str(section), ['question', 'ex-or-im1', 'attribute1','answer1']]
        df = df.loc[df['ex-or-im1'] == 'implicit', ['question', 'attribute1', 'answer1']]
        df = df.reset_index(drop=True)
        if df.empty:
            return False
        else:
            return True
    
    elif st.session_state['model'] == 'B':
        if "#no question" in question_making(selected_book, section).lower():
            return False
        else:
            return True
        
    elif st.session_state['model'] == 'D':
        df = question[selected_book].loc[question[selected_book]['cor_section']== str(section), ['question', 'ex-or-im1', 'attribute1','answer1']]
        df = df.reset_index(drop=True)
        if df.empty:
            return False
        else:
            return True


def make_facilitating_prompt(selected_book:int, section:int):
    facilitating = "#section :\n"
    for line in story[selected_book]['text'][section-1]:
        facilitating += line +"\n"
    facilitating += "\n"
    df = question[selected_book].loc[question[selected_book]['cor_section']== str(section), ['question', 'ex-or-im1', 'attribute1','answer1']]
    df = df.loc[df['ex-or-im1'] == 'implicit', ['question', 'attribute1', 'answer1']]
    df = df.reset_index(drop=True)
    for i, row in df.iterrows():
        facilitating += f"#question {i + 1}: {row['question']}\n#answer {i + 1}: {row['answer1']}\n\n"
    if df.empty:
        return "#no question"

    return facilitating_prompt1 + facilitating + facilitating_prompt2


def make_auto_facilitating_prompt(selected_book:int, section:int):
    facilitating = "#section :\n"
    for line in story[selected_book]['text'][section-1]:
        facilitating += line +"\n"
    facilitating += question_making(selected_book, section)
    if "#no question" in facilitating.lower():
        return "#no question"

    return auto_facilitating_prompt1 + facilitating + auto_facilitating_prompt2


def make_all_facilitating_prompt(selected_book:int, section:int):
    facilitating = "#section :\n"
    for line in story[selected_book]['text'][section-1]:
        facilitating += line +"\n"
    facilitating += "\n"
    df = question[selected_book].loc[question[selected_book]['cor_section']== str(section), ['question', 'ex-or-im1', 'attribute1','answer1']]
    df = df.reset_index(drop=True)
    for i, row in df.iterrows():
        facilitating += f"#question {i + 1}: {row['question']}\n#answer {i + 1}: {row['answer1']}\n\n"
    if df.empty:
        return "#no question"

    return ab2_facilitating_prompt1 + facilitating + ab2_facilitating_prompt2


def facilitating(selected_book:int, section:int, user_input:str):
    if st.session_state['model'] == 'B':
        system_instruction = make_auto_facilitating_prompt(selected_book, section)
    elif st.session_state['model'] == 'D':
        system_instruction = make_all_facilitating_prompt(selected_book, section)
    else:
        system_instruction = make_facilitating_prompt(selected_book, section)
    prompt_message = [{"role": "system", "content": system_instruction}] # chat persona

    # skip
    if user_input == "skip":
        st.session_state['facilitating_history'] = []
        st.session_state['phase'] = 'reading'
        st.session_state['section'] += 1
        st.session_state['read'] = False
        return None

    else:
        user_input = {"role": "user", "content": user_input}
        st.session_state['facilitating_history'].append(user_input)

        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt_message + st.session_state['facilitating_history'])

        bot_completion = completion.choices[0].message.content
        if user_input == {"role": "user", "content": '<sos>'}:
            bot_completion = '❓' + bot_completion
    
        # select
        if "<end>" in bot_completion:
            st.session_state['messages'].append(user_input) 
            st.session_state['facilitating_history'] = []
            st.session_state['phase'] = 'reading'
            st.session_state['section'] += 1
            st.session_state['read'] = False
        else :
            if user_input != {"role": "user", "content": '<sos>'}:
                st.session_state['messages'].append(user_input) 
            bot_response = {"role": "assistant", "content": bot_completion}
            st.session_state['facilitating_history'].append(bot_response) 
            st.session_state['messages'].append(bot_response) 

    return None


##########################
# Wrapup
##########################
def make_wrapup_prompt(selected_book:int):
    return "[book] : " + title[selected_book] + "\n" + "[history]\n" + wrapup_prompt1


def wrapup_chat(text, messages):
    user_input = {"role": "user", "content": text}
    messages.append(user_input)

    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages)

    bot_completion = completion.choices[0].message.content
    bot_response = {"role": "assistant", "content": bot_completion}
    messages.append(bot_response)

    return bot_completion

def wrapup(selected_book:int, user_input:str):
    system_instruction = make_wrapup_prompt(selected_book)
    prompt_message = [{"role": "system", "content": system_instruction}] # chat persona

    # skip
    if user_input == "skip":
        st.session_state['wrapup_history'] = []
        st.session_state['phase'] = 'end'
        return None

    else:
        user_input = {"role": "user", "content": user_input}
        st.session_state['wrapup_history'].append(user_input)

        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt_message + st.session_state['wrapup_history'])

        bot_completion = completion.choices[0].message.content
        if user_input == {"role": "user", "content": '<sos>'}:
            bot_completion = '🚩' + bot_completion
    
        # select
        if "<end>" in bot_completion:
            st.session_state['messages'].append(user_input) 
            st.session_state['wrapup_history'] = []
            st.session_state['phase'] = 'end'
            return None
        else :
            if user_input != {"role": "user", "content": '<sos>'}:
                st.session_state['messages'].append(user_input) 
            bot_response = {"role": "assistant", "content": bot_completion}
            st.session_state['wrapup_history'].append(bot_response) 
            st.session_state['messages'].append(bot_response) 


##########################
# Integrate
##########################
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'read' not in st.session_state:
    st.session_state['read'] = False
if 'section' not in st.session_state:
    st.session_state['section'] = 1
if 'phase' not in st.session_state:
    st.session_state['phase'] = 'greeting'
if 'selected_book' not in st.session_state:
    st.session_state['selected_book'] = None    
if 'facilitating_history' not in st.session_state:
    st.session_state['facilitating_history'] = []
if 'wrapup_history' not in st.session_state:
    st.session_state['wrapup_history'] = []
if 'model' not in st.session_state:
    st.session_state['model'] = None
# user
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

st.title("Fairytale-Reading Chatbot")
st.write('❗Please write your name in ENGLISH without space, then press Enter.  ex: yooseop')
user_id = st.text_input('Your name : ', '', key='name')
st.session_state['user_id'] = user_id
st.write('User name : ', st.session_state['user_id'])
st.write('❗Choose a model first before starting a conversation. DO NOT change the model during a conversation!')
st.session_state['model'] = st.selectbox('Model', ('A', 'B', 'C', 'D'))
st.write('Selected model : ', st.session_state['model'])
st.markdown('#')
st.markdown('#')

row1 = st.container()
row2 = st.form('form', clear_on_submit=True)

def click_read():
    st.session_state['read'] = True

with row2:
    user_input = st.text_input('You: ', '', key='input')
    #submitted = st.form_submit_button('SEND')
    st.form_submit_button('READ >>', on_click=click_read)

# greeting
if user_input and st.session_state['phase'] == 'greeting':
    prompt_message = [{"role": "system", "content": greeting_prompt}] # chat persona
    st.session_state['selected_book'] = greeting_chat(prompt_message, user_input)
    if st.session_state['selected_book'] != None:
        st.session_state['phase'] = 'reading'

# reading
if st.session_state['phase'] == 'reading' and st.session_state['read']:
    max_section = len(story[st.session_state['selected_book']]['text'])

    if st.session_state['section'] > max_section:
        wrapup(st.session_state['selected_book'], '<sos>')
        st.session_state['phase'] = 'wrapup'
    else:
        reading(st.session_state['selected_book'], st.session_state['section'])
        if check_facilitating(st.session_state['selected_book'], st.session_state['section']):
            st.session_state['phase'] = 'facilitating'
            # <sos>
            facilitating(st.session_state['selected_book'], st.session_state['section'], '<sos>')
            user_input = False
            st.session_state['read'] = False
        else:
            st.session_state['section'] += 1
            st.session_state['read'] = False
    
# facilitating
if user_input and st.session_state['phase'] == 'facilitating':
    facilitating(st.session_state['selected_book'], st.session_state['section'], user_input)

# wrapup
if user_input and st.session_state['phase'] == 'wrapup':
    wrapup(st.session_state['selected_book'], user_input)


with row1:
    if st.session_state['messages']:
        for i in range(len(st.session_state['messages'])):
            msg = st.session_state['messages'][i]['content']

            is_user = False
            if st.session_state['messages'][i]['role'] == 'user':
                is_user = True
            
            message(msg, is_user=is_user,key=str(i)+str(is_user))


if st.session_state['phase'] == 'greeting':
    st.write("💬Please select the book you want to read. Type your chat and press Enter")
if st.session_state['phase'] == 'reading':
    st.write("👆Please press 'READ' button to continue!")
    st.write("reading :", title[st.session_state['selected_book']], ", section : ", st.session_state['section']-1)
if st.session_state['phase'] == 'facilitating' or st.session_state['phase'] == 'wrapup':
    st.write("❓Please answer the question! Type your answer and press Enter")
if st.session_state['phase'] == 'end':
    st.write("✅Finished!")
    # save history
    dic = {}
    dic['user_id'] = st.session_state['user_id']
    dic['selected_model'] = st.session_state['model']
    dic['messages'] = st.session_state['messages']
    #st.write(dic)
    filename = st.session_state['user_id'] + "_" + st.session_state['model'] + "_history.json"
    with open(filename, 'w') as file:                                                                                                                                                                                                                                                                                                                                
        file.write(json.dumps(dic, indent=2)) # use `json.loads` to do the reverse                                                                                                                                           


st.write("phase : ", st.session_state['phase'])
#st.write(st.session_state['facilitating_history'])
