import streamlit as st
import pandas as pd
import json
from openai import OpenAI
import os




# Load CSV file with country data
uploaded_file = st.file_uploader("Upload CSV file with country data", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    country_options = df.columns[1:]
    
    # Natural language question input
    user_question = st.text_input("Ask a question about the data (e.g., 'Show me population by state'):")

    my_api_key = os.environ.get("OPENAI_API_KEY")
  
    # Determine which column to visualize based on user question
    if user_question:
        client = OpenAI(
            # This is the default and can be omitted
            api_key = my_api_key
        )
        chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Given the following columns: {', '.join([col for col in df.columns if col.lower() not in ['country', 'state']])},
                which column is the user referring to in this question: '{user_question}'? 
                Reply in valid JSON only as follows: {{\"field\": \"column_name or none\", \"map_type\": \"Country or State\"}}""",
            }
        ],
        model="gpt-3.5-turbo"
        )
        response_string = chat_completion.choices[0].message.content.strip()
        response = json.loads(response_string)
        selected_field = response["field"]
        map_type = response["map_type"]
        # Store in session state
        if selected_field in df.columns and map_type in ["Country", "State"]:
            st.session_state.selected_field = selected_field
            st.session_state.map_type = map_type
        else:
            st.error(f"Could not determine a valid column from the response '{response_string}'. Please try again.")
    
        # If we have the selected field and map type in session state, allow for visualization
        if "selected_field" in st.session_state and "map_type" in st.session_state:
            selected_field = st.session_state.selected_field
            map_type = st.session_state.map_type

            # Display selected field and allow user to adjust if necessary
            selected_field = st.selectbox("Select the field to visualize", df.columns[1:], index=max(0, df.columns.get_loc(selected_field) - 1))
            st.write(f"Selected field for visualization: {selected_field}")

            # Select the type of GeoJSON to use, set the default value from AI response
            map_type = st.selectbox("Select Map Type", ["Country", "State"], index=["Country", "State"].index(map_type))


                # Prepare data for visualization
            try:
                if map_type == "Country":
                    data = df.set_index('Country')[selected_field].to_dict()
                    geojson_file = "world_countries.json"
                    scale = 100
                    top_margin = 50
                    left_margin = 20
                    translate = [750 / 2, 500 / 1.5]
                else:
                    data = df.set_index('State')[selected_field].to_dict()
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
                d3_html = d3_html.replace("{{title}}", f"{selected_field} by {map_type}")
                d3_html = d3_html.replace("{{scale}}", str(scale))
                d3_html = d3_html.replace("{{top_margin}}", str(top_margin))
                d3_html = d3_html.replace("{{left_margin}}", str(left_margin))
                d3_html = d3_html.replace("{{translate}}", json.dumps(translate))
                

                # Embed the HTML that includes the D3 code in Streamlit
                st.components.v1.html(d3_html, height=700, scrolling=True)
