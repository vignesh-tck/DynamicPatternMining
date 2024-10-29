import streamlit as st
import pandas as pd
import json

# Load CSV file with country data
uploaded_file = st.file_uploader("Upload CSV file with country data", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    country_options = df.columns[1:]
    
    # Select the field to visualize
    selected_field = st.selectbox("Select the field to visualize", country_options)
    
    # Prepare data for visualization
    # Select the type of GeoJSON to use
    map_type = st.selectbox("Select Map Type", ["Countries", "States"])

    # Prepare data for visualization
    if map_type == "Countries":
        data = df.set_index('Country')[selected_field].to_dict()
        geojson_file = "world_countries.json"
    else:
        data = df.set_index('State')[selected_field].to_dict()
        geojson_file = "us-states.json"

    # Create the button in Streamlit
    if st.button("Show Visualization"):
        # Load the HTML template from an external file
        with open("d3_template.html", "r") as file:
            d3_html_template = file.read()

        # Replace placeholders in the template with actual data
        d3_html = d3_html_template.replace("{{data}}", json.dumps(data))
        d3_html = d3_html.replace("{{geoJson}}", json.dumps(json.load(open(geojson_file))))
        d3_html = d3_html.replace("{{title}}", f"{selected_field} by {map_type}")
        

        # Embed the HTML that includes the D3 code in Streamlit
        st.components.v1.html(d3_html, height=700, scrolling=True)