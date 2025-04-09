import streamlit as st
import requests
import zipfile
import io
import os
import json
import random
from datetime import datetime
from PIL import Image
from openai import OpenAI
from utils import icon
from streamlit_image_select import image_select

# UI configurations
st.set_page_config(page_title="Aura Farm Image Transformer",
                   page_icon=":seedling:",
                   layout="wide")
icon.show_icon(":crystal_ball:")
st.markdown("# :rainbow[Aura Farm Image Transformer]")

# Placeholders for images and gallery
uploaded_image_placeholder = st.empty()
generated_images_placeholder = st.empty()
rainbow_rating_placeholder = st.empty()
gallery_placeholder = st.empty()

# File to store visitor data
VISITOR_DATA_FILE = "visitor_data.json"

def track_visitor():
    """
    Track unique visitors and update the visitor count.
    Returns total visitor count.
    """
    # Initialize visitor data structure
    if os.path.exists(VISITOR_DATA_FILE):
        try:
            with open(VISITOR_DATA_FILE, "r") as f:
                visitor_data = json.load(f)
        except json.JSONDecodeError:
            visitor_data = {"total_count": 0, "daily_counts": {}, "sessions": []}
    else:
        visitor_data = {"total_count": 0, "daily_counts": {}, "sessions": []}
    
    # Generate a unique session ID if not already set
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    
    session_id = st.session_state.session_id
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if this is a new session
    if session_id not in visitor_data["sessions"]:
        visitor_data["sessions"].append(session_id)
        visitor_data["total_count"] += 1
        
        # Update daily count
        if today in visitor_data["daily_counts"]:
            visitor_data["daily_counts"][today] += 1
        else:
            visitor_data["daily_counts"][today] = 1
        
        # Save the updated data
        with open(VISITOR_DATA_FILE, "w") as f:
            json.dump(visitor_data, f)
    
    return visitor_data["total_count"]

def generate_rainbow_rating():
    """
    Generate a fun rainbow rating on a scale of 1-10
    with colorful emojis and fun descriptions.
    """
    # Generate a random rating between 1-10
    rating = random.randint(1, 10)
    
    # Define fun descriptions for different rating ranges
    rating_descriptions = {
        (1, 3): "Needs a bit more magic ✨",
        (4, 6): "Looking good! 🌟",
        (7, 9): "Amazing creation! 🌈",
        (10, 10): "Absolute perfection! 🦄✨"
    }
    
    # Get the description for the current rating
    description = next((desc for range_tuple, desc in rating_descriptions.items() 
                        if range_tuple[0] <= rating <= range_tuple[1]), "")
    
    # Create a colorful rainbow progress bar
    rainbow_colors = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#8B00FF"]
    
    return rating, description, rainbow_colors

def get_prompt_for_transformation(style_type):
    """
    Returns the appropriate prompt for the selected transformation style.
    
    Args:
        style_type (str): The transformation style selected by the user.
        
    Returns:
        str: The prompt to be used for image transformation.
    """
    style_prompts = {
        "Ghibli": "Transform this image into Studio Ghibli animation style with vibrant colors, whimsical elements, and a dreamy atmosphere.",
        "Minecraft": "Transform this image into Minecraft style with blocky pixelated texture, bright colors, and cubic shapes.",
        "Chicken-Jockey": "Transform this image into a blocky Minecraft-style character cool green zombie riding a chicken.",
        "Humanize": "Transform this image into a realistic human-like representation with natural proportions, detailed features, and lifelike textures."
    }
    
    return style_prompts.get(style_type, "Transform this image in a creative way.")

def configure_sidebar():
    """
    Setup and display the sidebar elements.
    
    Returns:
        tuple: A tuple containing user inputs from the sidebar form.
    """
    # Track visitor and get count
    visitor_count = track_visitor()
    
    with st.sidebar:
        # Display visitor count
        st.markdown(f"### 👥 Visitors: {visitor_count}")
        st.divider()
        
        with st.form("transformation_form"):
            st.info("**Welcome to Aura Farm! Start here ↓**", icon="🌱")
            
            # API Key input
            openai_api_key = st.text_input("OpenAI API Key", type="password")
            
            # Simplified transformation style selector - dropdown only
            transformation_style = st.selectbox(
                "Choose your transformation style:",
                ["Ghibli", "Minecraft", "Chicken-Jockey", "Humanize"]
            )
            
            # Advanced options
            with st.expander(":rainbow[**Advanced options**]"):
                num_images = st.slider(
                    "Number of variations to generate", 
                    value=1, 
                    min_value=1, 
                    max_value=4
                )
                
                image_size = st.selectbox(
                    "Image size",
                    ["1024x1024", "512x512", "256x256"],
                    index=0
                )
            
            # Upload image
            uploaded_file = st.file_uploader("Upload an image to transform", type=["png", "jpg", "jpeg"])
            
            # The Submit Button
            submitted = st.form_submit_button(
                "Transform Image", type="primary", use_container_width=True
            )
            
        # Credits and resources
        st.divider()
        st.markdown(
            """
            ---
            ### About Aura Farm
            
            Transform your images into magical new styles using AI.
            
            ---
            Created with ❤️ by Aura Farm team
            """
        )
        
        return submitted, openai_api_key, transformation_style, num_images, image_size, uploaded_file

def transform_image_with_openai(api_key, image_data, style, num_images=1, size="1024x1024"):
    """
    Transform an image using OpenAI's GPT-4o API.
    
    Args:
        api_key (str): OpenAI API key.
        image_data (bytes): The image data to transform.
        style (str): The transformation style selected.
        num_images (int): Number of image variations to generate.
        size (str): Size of the output image.
        
    Returns:
        list: URLs of the generated images.
    """
    client = OpenAI(api_key=api_key)
    
    try:
        # Get the appropriate prompt for the selected style
        prompt = get_prompt_for_transformation(style)
        
        response = client.images.edit(
            model="gpt-4o",  # Using GPT-4o model
            image=image_data,
            prompt=prompt,
            n=num_images,
            size=size
        )
        
        # Extract URLs from the response
        image_urls = [item.url for item in response.data]
        return image_urls
    
    except Exception as e:
        st.error(f"Error transforming image: {str(e)}")
        return []

def main_page(submitted, api_key, style, num_images, image_size, uploaded_file):
    """
    Main page layout and logic for transforming images.
    
    Args:
        submitted (bool): Flag indicating whether the form has been submitted.
        api_key (str): OpenAI API key.
        style (str): Selected transformation style.
        num_images (int): Number of image variations to generate.
        image_size (str): Size of the output image.
        uploaded_file: The uploaded image file.
    """
    # Display uploaded image if available
    if uploaded_file is not None:
        with uploaded_image_placeholder.container():
            st.image(uploaded_file, caption="Your Uploaded Image", use_column_width=True)
    
    if submitted and uploaded_file is not None and api_key:
        with st.status(f'🧙‍♂️ Transforming your image to {style} style...', expanded=True) as status:
            st.write("⚙️ Processing initiated")
            st.write(f"🔮 Applying {style} transformation")
            
            try:
                # Read the uploaded image as bytes
                image_bytes = uploaded_file.getvalue()
                
                # Call OpenAI API to transform the image
                transformed_image_urls = transform_image_with_openai(
                    api_key, 
                    image_bytes, 
                    style, 
                    num_images, 
                    image_size
                )
                
                if transformed_image_urls:
                    st.toast(f'Your {style} transformation is ready!', icon='✨')
                    
                    # Save generated image URLs to session state
                    st.session_state.transformed_images = transformed_image_urls
                    
                    # Display the images
                    with generated_images_placeholder.container():
                        all_images = []
                        
                        for i, image_url in enumerate(transformed_image_urls):
                            with st.container():
                                st.image(image_url, caption=f"{style} Transformation {i+1} ✨", use_column_width=True)
                                all_images.append(image_url)
                                
                                # Generate a rainbow rating for this image
                                rating, description, rainbow_colors = generate_rainbow_rating()
                                
                                # Create a colorful rating display
                                st.markdown(f"### Rainbow Rating: {rating}/10")
                                st.progress(rating / 10, f"Rainbow Rating: {rating}/10")
                                st.markdown(f"**{description}**")
                                
                                # Create a colorful separator
                                st.markdown(
                                    """
                                    <div style="text-align: center; margin: 10px 0;">
                                    🌈✨🌈✨🌈✨🌈✨🌈✨🌈✨🌈
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                    
                        # Save all generated images to session state
                        st.session_state.all_images = all_images
                        
                        # Create a BytesIO object for downloading images
                        zip_io = io.BytesIO()
                        
                        # Download option for each image
                        with zipfile.ZipFile(zip_io, 'w') as zipf:
                            for i, image_url in enumerate(all_images):
                                response = requests.get(image_url)
                                if response.status_code == 200:
                                    image_data = response.content
                                    # Write each image to the zip file with a name
                                    zipf.writestr(f"{style.lower()}_transform_{i+1}.png", image_data)
                                else:
                                    st.error(
                                        f"Failed to fetch image {i+1}. Error code: {response.status_code}", 
                                        icon="🚨"
                                    )
                        
                        # Create a download button for the zip file
                        st.download_button(
                            f"🔮 Download All {style} Transformations",
                            data=zip_io.getvalue(),
                            file_name=f"aura_farm_{style.lower()}_transformations.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                        
                status.update(label=f"✅ {style} transformation complete!", state="complete", expanded=False)
                
            except Exception as e:
                st.error(f'Error during transformation: {str(e)}', icon="🚨")
    elif submitted and not uploaded_file:
        st.warning("Please upload an image to transform.")
    elif submitted and not api_key:
        st.warning("Please provide your OpenAI API key.")

    # Gallery display for inspiration
    with gallery_placeholder.container():
        st.subheader("Transformation Examples")
        st.markdown("Check out these examples of our transformation styles:")
        
        # Create two rows with two columns each
        col1, col2 = st.columns(2)
        
        with col1:
            st.image("https://placekitten.com/500/300", caption="Original Image")
        
        with col2:
            st.image("https://placekitten.com/500/301", caption="Ghibli Style")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.image("https://placekitten.com/500/302", caption="Minecraft Style")
        
        with col4:
            st.image("https://placekitten.com/500/303", caption="Humanize Style")

def main():
    """
    Main function to run the Streamlit application.
    """
    submitted, api_key, style, num_images, image_size, uploaded_file = configure_sidebar()
    main_page(submitted, api_key, style, num_images, image_size, uploaded_file)

if __name__ == "__main__":
    main()
