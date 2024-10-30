import streamlit as st
import pandas as pd
import json
from openai import OpenAI
import os
import altair as alt
import re

# Load CSV file with country data
uploaded_file = st.file_uploader("Upload CSV file with country data", type="csv")

supported_chart_types = ["GeoMap", "BarChart", "LineChart", "PieChart"]

supported_generic_chart_types = ["BarChart", "LineChart", "PieChart"]

chart_type_mapping = {
    "BarChart": "bar",
    "LineChart": "line",
    "PieChart": "pie"
}

# Define chart templates for each chart type
chart_templates = {
    "bar": """
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('{x_field}', title='{x_field}'),
        y=alt.Y('{y_field}', title='{y_field}')
    ).properties(
        width=600,
        height=400,
        title='Bar chart of {y_field} vs {x_field}'
    )
    st.altair_chart(chart, use_container_width=True)
    """,
    "line": """
    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('{x_field}', title='{x_field}'),
        y=alt.Y('{y_field}', title='{y_field}'),
        color=alt.Color('{color_field}', title='{color_field}')  # Color field to distinguish lines if multiple attributes
    ).properties(
        width=600,
        height=400,
        title='Line chart of {y_field} vs {x_field}'
    )
    st.altair_chart(chart, use_container_width=True)
    """,
    "pie":""" 
    chart = alt.Chart(df).mark_arc().encode(
        theta=alt.Theta('{y_field}', type='quantitative'),
        color=alt.Color('{x_field}', type='nominal')
    ).properties(
        width=600,
        height=400,
        title='Pie chart of {y_field} by {x_field}'
    )
    st.altair_chart(chart, use_container_width=True)
    """
}

def generate_chart(chart_type, x_field, y_field):
    # Use the chart template for the given chart type
    chart_syntax = chart_templates[chart_type]

    # Use LLM to fill in the placeholders for x_field and y_field
    fill_prompt = f"""Give me a completed code for generating a {chart_type} graph. Do not add any text not python. I already have df dataframe so no need to initialize that. x_field is '{x_field}', y_field is '{y_field}'."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            fill_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"""given the template streamlit code: {chart_syntax}. {fill_prompt}"""
                    }
                ],
                model="gpt-4"
            )
            
            response_string = fill_completion.choices[0].message.content.strip()
            match = re.search(r"```(.*?)```", response_string, re.DOTALL)

            if match:
                code_between_quotes = match.group(1)
            else:
                code_between_quotes = response_string

            # Execute the filled code (carefully!)
            exec(code_between_quotes)
            break
        except Exception as e:
            st.error(f"Error: Attempt {attempt + 1} failed with error: {e}. Retrying...")
            if attempt == max_retries - 1:
                st.error("Maximum retry attempts reached. Unable to execute the generated code.")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    country_options = df.columns[1:]
    
    # Natural language question input
    user_question = st.text_input("Ask a question about the data (e.g., 'Show me population by state'):")

    my_api_key = os.environ.get("OPENAI_API_KEY")
  
    # Determine which column to visualize based on user question
    if 'last_error' in st.session_state:
        del st.session_state['last_error']

    if user_question:
        client = OpenAI(
            # This is the default and can be omitted
            api_key = my_api_key
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""Given the following columns: {', '.join([col for col in df.columns if col.lower()])},
                    which are the 2 columns that the user referring to in this question: '{user_question}'? 
                    Reply in valid JSON only as follows: 
                    {{\"field1\": \"one of State, Country or column_name or none\", \"field2\": \"column_name or none\", \"chart_type\": \"only one of {', '.join([s for s  in supported_chart_types]) } }} \"}}""",
                }
            ],
            model="gpt-3.5-turbo"
        )
        response_string = chat_completion.choices[0].message.content.strip()
        response = json.loads(response_string)
        selected_field_1 = response["field1"]
        selected_field_2 = response["field2"]
        chart_type = response["chart_type"]
        # Store in session state

        # Store in session state
        if selected_field_1 in df.columns and selected_field_2 in df.columns and chart_type in supported_chart_types:
            st.session_state.selected_field_1 = selected_field_1
            st.session_state.selected_field_2 = selected_field_2
            st.session_state.chart_type = chart_type
            st.write(f"Selected field for visualization: {selected_field_1} and {selected_field_2}")
        else:
            if 'last_error' in st.session_state:
                del st.session_state['last_error']
            st.error(f"Could not determine a valid column from the response '{response_string}'. Please try again.")
    
    
        # If we have the selected field and map type in session state, allow for visualization
        if "selected_field_1" in st.session_state and "selected_field_2" in st.session_state and "chart_type" in st.session_state:
            selected_field_1 = st.session_state.selected_field_1
            selected_field_2 = st.session_state.selected_field_2
            chart_type = st.session_state.chart_type

            if chart_type == "GeoMap":
                # Display selected field and allow user to adjust if necessary
                selected_field_2 = st.selectbox("Select the field to visualize", df.columns[1:], index=max(0, df.columns.get_loc(selected_field_2)-1))
                st.write(f"Selected field for visualization: {selected_field_2}")

                # Select the type of GeoJSON to use, set the default value from AI response
                selected_field_1 = st.selectbox("Select Map Type", ["Country", "State"], index=["Country", "State"].index(selected_field_1))

                # Prepare data for visualization
                try:
                    if selected_field_1 == "Country":
                        data = df.set_index('Country')[selected_field_2].to_dict()
                        geojson_file = "world_countries.json"
                        scale = 100
                        top_margin = 50
                        left_margin = 20
                        translate = [750 / 2, 500 / 1.5]
                    else:
                        data = df.set_index('State')[selected_field_2].to_dict()
                        geojson_file = "us-states.json"
                        scale = 500
                        top_margin = 350
                        left_margin = 800
                        translate = [750 / 2, 500 / 2]
                except KeyError as e:
                    st.error(f"Missing expected column: {e}. Please select appropriate Map type and make sure your data contains the corresponding column ('Country' or 'State').")
                else:
                    with open("d3_template.html", "r") as file:
                        d3_html_template = file.read()

                    # Replace placeholders in the template with actual data
                    d3_html = d3_html_template.replace("{{data}}", json.dumps(data))
                    d3_html = d3_html.replace("{{geoJson}}", json.dumps(json.load(open(geojson_file))))
                    d3_html = d3_html.replace("{{title}}", f"{selected_field_1} by {selected_field_2}")
                    d3_html = d3_html.replace("{{scale}}", str(scale))
                    d3_html = d3_html.replace("{{top_margin}}", str(top_margin))
                    d3_html = d3_html.replace("{{left_margin}}", str(left_margin))
                    d3_html = d3_html.replace("{{translate}}", json.dumps(translate))

                    # Embed the HTML that includes the D3 code in Streamlit
                    st.components.v1.html(d3_html, height=700, scrolling=True)
            elif chart_type in supported_generic_chart_types:
                generate_chart(chart_type_mapping[chart_type], selected_field_1, selected_field_2)