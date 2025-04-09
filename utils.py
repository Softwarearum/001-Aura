import streamlit as st

class icon:
    """
    Utility class for displaying icons in Streamlit apps
    """
    @staticmethod
    def show_icon(emoji_icon):
        """
        Display an emoji icon in the app
        
        Args:
            emoji_icon (str): The emoji to display as icon
        """
        st.markdown(
            f"""
            <style>
            .icon-container {{
                display: flex;
                justify-content: center;
                margin: 1rem 0;
            }}
            
            .emoji-icon {{
                font-size: 3rem;
                animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
                0% {{
                    transform: scale(1);
                    opacity: 1;
                }}
                50% {{
                    transform: scale(1.1);
                    opacity: 0.8;
                }}
                100% {{
                    transform: scale(1);
                    opacity: 1;
                }}
            }}
            </style>
            
            <div class="icon-container">
                <div class="emoji-icon">{emoji_icon}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
