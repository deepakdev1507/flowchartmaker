import streamlit as st
import datetime
import pandas as pd
import PyPDF2
from docx import Document
import io
from openai import OpenAI
import os
import json
from streamlit.components.v1 import html


def main():
    if "page" not in st.session_state:
        st.session_state.page = "form"

    if st.session_state.page == "form":
        expense_form()
    elif st.session_state.page == "result":
        display_results()

def display_results():
    st.title("Result")
    
    with open("OrgChart.pdf", "rb") as file:
        st.download_button(label="Download Organization Chart", data=file, file_name="OrgChart.pdf", mime="application/octet-stream")
    with open("Reimbursement  Policy - updated.pdf", "rb") as file:
        st.download_button(label="Download Reimbursement Policy", data=file, file_name="Reimbursement  Policy - updated.pdf", mime="application/octet-stream")
    reset = st.button("reset")
    if reset:
        st.session_state.page = "form"
        st.session_state.form_data = None
        st.session_state.api_key = None
        main()
    if "api_key" in st.session_state and "form_data" in st.session_state:
        code, explanation = process_data(st.session_state.form_data)
        st.subheader("Code")
        st.markdown(code)
        st.subheader("Explanation")
        st.write(explanation)
        display_mermaid_diagram(code)
        # Resetting the state for new input
        # reset_state()
    

def process_data(form_data):
    temp_text= ''
    
    
    structure=extract_text_from_file("Organization Chart.txt")
    temp_text=extract_text_from_file("reimursepolicy.txt")
    # print(temp_text,structure,form_data)
    message=[
        {"role": "system", "content": "you are a expert text to diagram bot , you are excellent and capable of writing mermaid js script to generate diagram from text, "},
        {"role": "system", "content": "below given is the expense policy of a company and you have to use it as a source of your knowledge"+temp_text},
        {"role":"system", "content": "Also use below given organization structure as your knowledge base and ALWAYS INCLUDE PERSONS name along with designation while making approval workflow diagrams for example if you are saying CEO or CTO please include there name as well in the diagram for sure use the given below org structure \n\n"+str(structure)},
        {"role":"system", "content": "Always use org structure and try to use names along with position or department name"},
        {"role": "system", "content": str(form_data)+ " \n this is the current request, use the above policy to generate a diagram from the text showing the approval process for the expense request and respond back in json format with code as key and mermaid code as value, another key value pair should be explaination and it should contain the explaination of the diagram"}
        ]
    # print(message)
    client = OpenAI(api_key=st.session_state.api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=message,
        response_format={ "type": "json_object" },
        temperature=0.1
            
        )

    
    response=json.loads(completion.choices[0].message.content)
    # print(response)
    code=response.get("code")
    explaination=response.get("explanation")
    # print(code)
    # print(explaination)
    st.session_state.page = "result"
    return code,explaination

def expense_form():
    st.title("Expense Form")
    
    with st.form("Approval workflow"):
        requestor = st.text_input("Requestor", "")
        position= st.text_input("Position", "")
        amount = st.number_input("Amount in Rupees", min_value=0.0, format="%.2f")
        date = st.date_input("Date", datetime.date.today())
        expense_type = st.text_input("Type of Expense", "")
        merchant_name = st.text_input("Merchant Name", "")
        comments = st.text_area("Comments", "")
        api_key = st.text_input("API Key", "")

        submitted = st.form_submit_button("Submit")
        
        if submitted:
            form_data = {
                "requestor": requestor,
                "position": position,
                "amount": amount,
                "date": date,
                "expense_type": expense_type,
                "merchant_name": merchant_name,
                "comments": comments
                
            }
            if api_key=='':
                st.write("Please enter a valid API key")
                st.session_state.page = "form"
            else:
                check=False
                try:
                    client=OpenAI(api_key=api_key)
                    response = client.moderations.create(input="Sample text goes here.")
                    check=True
                except:
                    st.write("Please enter a valid API key")
                    st.session_state.page = "form"
                                    
                if check:
                    st.session_state.api_key = api_key
                    st.session_state.form_data = form_data
                    
                    st.session_state.page = "result"
                    
            


# def document_upload():
#             st.title("Result")
#             code,explaination = process_data(st.session_state.form_data)
#             st.write(str(code))
#             st.write(explaination)
#             # print(code)
#             display_mermaid_diagram(code)
#             st.session_state.page = "form"
#             st.session_state.form_data = None
#             st.session_state.form_data2 = None
#             st.session_state.api_key = None
            
    
            

def display_mermaid_diagram(code):
    code = code.replace("\\n", "\n").replace("\\", "").replace(";", "").replace("mermaid", "").replace("```", "")
    
    # HTML and JS to render the Mermaid diagram
    mermaid_html = f"""
        <div class="mermaid" style="max-width: 100%; max-height: 800px; overflow: auto;">
            {code}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@8.13.5/dist/mermaid.min.js"></script>
        <script>
        function loadMermaid() {{
            if (typeof mermaid === 'undefined') {{
                setTimeout(loadMermaid, 100);
            }} else {{
                mermaid.initialize({{ startOnLoad: true }});
            }}
        }}
        loadMermaid();
        </script>
    """
    html(mermaid_html,width=1000,height=1000)


        


def extractText(file):
    file_type = file.name.split('.')[-1].lower()
    if file_type == 'txt':
        file_content = file.getvalue().decode("utf-8")
        # print("File Content:\n", file_content)
        temp_text = file_content
        
    elif file_type == 'csv':
        file.seek(0)  # Move to the start of the file
        df = pd.read_csv(file)
        # print("CSV File Content:\n", df)
        temp_text = df.to_string()
        
    elif file_type == 'pdf':
        file.seek(0)  # Move to the start of the file
        pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(file.getvalue()))
        pdf_text = ''
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            pdf_text += page.extractText()
        # print("PDF File Content:\n", pdf_text)
        temp_text = pdf_text
        
    elif file_type == 'docx':
        file.seek(0)  # Move to the start of the file
        doc = Document(io.BytesIO(file.getvalue()))
        docx_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        # print("DOCX File Content:\n", docx_text)
        temp_text = docx_text
    else:
        print("Unsupported file type:", file_type)
    return temp_text

def extract_text_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            text = file.read()
        return text
    except FileNotFoundError:
        return "The file was not found."
    except Exception as e:
        return f"An error occurred: {e}"

if "page" not in st.session_state:
    st.session_state.page = "form"

def reset_state():
    st.session_state.page = "form"
    st.session_state.form_data = None
    st.session_state.api_key = None

main()