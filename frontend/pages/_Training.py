# frontend/pages/_Training.py
import streamlit as st
import requests
import json
from datetime import datetime
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Training", page_icon="🎓", layout="wide")

# Add CSS for compact layout
st.markdown("""
<style>
    .element-container {
        margin-bottom: 0.5rem;
    }
    .stSelectbox > div > div > div {
        font-size: 14px;
    }
    .stMultiSelect > div > div > div {
        font-size: 14px;
    }
    .stTextArea > div > div > textarea {
        font-size: 14px;
    }
    .stMetric {
        font-size: 14px;
    }
    .stButton > button {
        font-size: 14px;
        padding: 0.25rem 0.5rem;
    }
    .stRadio > div {
        font-size: 14px;
    }
    .stNumberInput > div > div > input {
        font-size: 14px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎓 Training Management")

setup_authenticated_sidebar()

# Helper functions
def get_available_document_types():
    """Get available document types from KB collections"""
    try:
        response = requests.get(f"{BACKEND_URL}/kb/collections", headers=get_auth_headers())
        if response.status_code == 200:
            collections = response.json()
            # Extract document types from collection names
            document_types = []
            for collection in collections:
                name = collection.get('name', '')
                # Convert back from collection format to readable format
                doc_type = name.replace('_', ' ').title()
                if doc_type not in document_types:
                    document_types.append(doc_type)
            return sorted(document_types)
        return []
    except Exception as e:
        st.error(f"Error fetching document types: {e}")
        return []

def generate_learning_content(topics):
    """Request learning content generation from KB"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/training/learning",
            json={"topics": topics},
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}

def generate_assessment_questions(topics, num_questions=20):
    """Request assessment questions generation from KB"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/training/assessment",
            json={"topics": topics, "num_questions": num_questions},
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}

def submit_assessment(question_ids, answers):
    """Submit assessment answers for evaluation"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/training/assessment/submit",
            json={"question_ids": question_ids, "answers": answers},
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}

def get_user_training_results():
    """Get training results for current user"""
    try:
        print(f"DEBUG Frontend: Requesting training results for authenticated user")
        
        response = requests.get(
            f"{BACKEND_URL}/training/results",
            headers=get_auth_headers()
        )
        
        print(f"DEBUG Frontend: Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
            except:
                error_detail = response.text[:200] if hasattr(response, 'text') else ""
            return {"success": False, "error": f"Server error {response.status_code}: {error_detail}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}

# Test endpoint connectivity
def test_training_endpoint():
    """Test if training endpoints are accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/training/test", headers=get_auth_headers())
        return response.status_code == 200
    except:
        return False

# Main interface
st.markdown("**Training System** - Generic learning and assessment platform using Knowledge Base content")

# Main navigation tabs
main_tabs = st.tabs(["Learning", "Assessment", "Results"])

# === LEARNING TAB ===
with main_tabs[0]:
    
    # Topics selection
    document_types = get_available_document_types()
    
    if not document_types:
        st.warning("⚠️ No topics available. Please ensure Knowledge Base collections are populated.")
        st.stop()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_topics = st.multiselect(
            "Select Topics for Learning",
            document_types,
            help="Choose one or more topics to generate learning content from"
        )
    
    with col2:
        if st.button("🚀 Generate Learning Content", type="primary"):
            if selected_topics:
                with st.spinner("Generating comprehensive learning content from Knowledge Base..."):
                    result = generate_learning_content(selected_topics)
                
                if result.get("success"):
                    st.session_state.learning_content = result.get("learning_content", "")
                    st.session_state.learning_topics = selected_topics
                    st.session_state.learning_source_count = result.get("source_documents", 0)
                    st.success(f"✅ Learning content generated from {result.get('source_documents', 0)} source documents")
                else:
                    st.error(f"❌ Failed to generate learning content: {result.get('error', 'Unknown error')}")
            else:
                st.warning("⚠️ Please select at least one topic.")
    
    # Display learning content if available
    if hasattr(st.session_state, 'learning_content') and st.session_state.learning_content:
        st.markdown("---")
        topics_display = ", ".join(st.session_state.learning_topics) if hasattr(st.session_state, 'learning_topics') else "Multiple Topics"
        st.markdown(f"*Generated from {st.session_state.learning_source_count} source documents*")
        
        # Display learning content in markdown format
        with st.container():
            st.markdown("**Learning Content:**")
            # Create a styled container for the content
            content_container = st.container()
            with content_container:
                # Display as markdown for better readability
                st.markdown(st.session_state.learning_content)
            
            # Also provide raw content in a text area for reference
            with st.expander("📄 View Raw Content"):
                st.text_area(
                    "Learning Content (Markdown)",
                    value=st.session_state.learning_content,
                    height=400,
                    disabled=True,
                    key="learning_content_raw"
                )
        
        # Additional learning options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Take Assessment"):
                st.session_state.active_tab = 1  # Switch to assessment tab
                st.rerun()
        
        with col2:
            # Download learning content
            topics_filename = "_".join([t.replace(' ', '_').lower() for t in st.session_state.learning_topics])[:50]  # Limit length
            if st.download_button(
                label="📄 Download Learning Content",
                data=st.session_state.learning_content,
                file_name=f"learning_{topics_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            ):
                st.success("📁 Learning content downloaded!")

# === ASSESSMENT TAB ===
with main_tabs[1]:
    
    # Topics selection for assessment
    if not document_types:
        st.warning("⚠️ No topics available. Please ensure Knowledge Base collections are populated.")
        st.stop()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        assessment_topics = st.multiselect(
            "Select Topics for Assessment",
            document_types,
            help="Choose one or more topics to generate questions from"
        )
    
    with col2:
        num_questions = st.number_input(
            "Number of Questions",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Choose between 5-50 questions"
        )
    
    with col3:
        if st.button("🎯 Generate Assessment", type="primary"):
            if assessment_topics:
                with st.spinner(f"Generating {num_questions} True/False questions from Knowledge Base..."):
                    result = generate_assessment_questions(assessment_topics, num_questions)
                
                if result.get("success"):
                    st.session_state.assessment_questions = result.get("questions", [])
                    st.session_state.assessment_topics = assessment_topics
                    st.session_state.user_answers = [None] * len(result.get("questions", []))
                    topics_display = ", ".join(assessment_topics)
                    st.success(f"✅ Generated {len(result.get('questions', []))} questions for {topics_display}")
                else:
                    st.error(f"❌ Failed to generate assessment: {result.get('error', 'Unknown error')}")
            else:
                st.warning("⚠️ Please select at least one topic.")
    
    # Display assessment questions if available
    if hasattr(st.session_state, 'assessment_questions') and st.session_state.assessment_questions:
        st.markdown("---")
        assessment_topics_display = ", ".join(st.session_state.assessment_topics) if hasattr(st.session_state, 'assessment_topics') else "Multiple Topics"
        st.markdown(f"**Instructions:** Answer each question as True or False. You need 80% or higher to pass.")
        
        questions = st.session_state.assessment_questions
        
        # Assessment form
        with st.form("assessment_form"):
            st.markdown("**Questions:**")
            
            for i, question in enumerate(questions):
                st.markdown(f"**Question {i+1}:**")
                st.markdown(question.get('question', ''))
                
                answer = st.radio(
                    f"Answer for Question {i+1}",
                    options=[True, False],
                    format_func=lambda x: "True" if x else "False",
                    key=f"question_{i}",
                    horizontal=True
                )
                st.session_state.user_answers[i] = answer
                st.markdown("---")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit_assessment_btn = st.form_submit_button("📊 Submit Assessment", type="primary")
            with col2:
                if st.form_submit_button("🔄 Clear Answers"):
                    st.session_state.user_answers = [None] * len(questions)
                    st.rerun()
        
        # Process assessment submission
        if submit_assessment_btn:
            if None in st.session_state.user_answers:
                st.error("❌ Please answer all questions before submitting.")
            else:
                with st.spinner("Evaluating your assessment..."):
                    question_ids = [q.get('id') for q in questions]
                    result = submit_assessment(question_ids, st.session_state.user_answers)
                
                if result.get("success"):
                    # Clear the assessment questions after successful submission
                    if 'assessment_questions' in st.session_state:
                        del st.session_state.assessment_questions
                    if 'user_answers' in st.session_state:
                        del st.session_state.user_answers
                    if 'assessment_topics' in st.session_state:
                        del st.session_state.assessment_topics
                    
                    # Display results
                    st.markdown("---")
                    
                    score = result.get("score", 0)
                    total = result.get("total_questions", 0)
                    percentage = result.get("percentage", 0)
                    passed = result.get("passed", False)
                    
                    # Results summary
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Score", f"{score}/{total}")
                    with col2:
                        st.metric("Percentage", f"{percentage}%")
                    with col3:
                        st.metric("Result", "PASS" if passed else "FAIL")
                    with col4:
                        st.metric("Required", "80%")
                    
                    # Pass/Fail indicator
                    if passed:
                        st.success("🎉 **Congratulations!** You passed the assessment!")
                    else:
                        st.error("📚 **Study More Required** - You need 80% or higher to pass. Review the learning content and try again.")
                    
                    # Detailed results
                    if st.checkbox("Show Detailed Results"):
                        st.markdown("**Question-by-Question Results:**")
                        
                        questions_with_answers = result.get("questions_with_answers", [])
                        for i, qa in enumerate(questions_with_answers):
                            question_text = questions[i].get('question', f'Question {i+1}')
                            user_answer = qa.get("user_answer")
                            correct_answer = qa.get("correct_answer")
                            is_correct = qa.get("is_correct", False)
                            
                            icon = "✅" if is_correct else "❌"
                            st.markdown(f"**{icon} Question {i+1}:** {question_text}")
                            st.markdown(f"Your answer: **{user_answer}** | Correct answer: **{correct_answer}**")
                            
                            if i < len(questions_with_answers) - 1:
                                st.markdown("---")
                    
                    # Clear assessment after completion
                    if st.button("🆕 Take New Assessment"):
                        if 'assessment_questions' in st.session_state:
                            del st.session_state.assessment_questions
                        if 'user_answers' in st.session_state:
                            del st.session_state.user_answers
                        st.rerun()
                        
                else:
                    st.error(f"❌ Failed to evaluate assessment: {result.get('error', 'Unknown error')}")

# === RESULTS TAB ===
with main_tabs[2]:
    
    # Fetch and display training results
    with st.spinner("Loading your training results..."):
        results = get_user_training_results()
    
    if results.get("success"):
        user_id = results.get("user_id")
        total_assessments = results.get("total_assessments", 0)
        average_score = results.get("average_score", 0)
        assessments = results.get("assessments", [])
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Assessments", total_assessments)
        with col2:
            st.metric("Average Score", f"{average_score}%")
        with col3:
            passed_count = sum(1 for a in assessments if a.get('passed', False))
            st.metric("Passed Assessments", f"{passed_count}/{total_assessments}")
        with col4:
            pass_rate = (passed_count / total_assessments * 100) if total_assessments > 0 else 0
            st.metric("Pass Rate", f"{pass_rate:.1f}%")
        
        if total_assessments > 0:
            st.markdown("---")
            
            # Display assessments in a table
            import pandas as pd
            
            assessment_data = []
            for assessment in assessments:
                assessment_data.append({
                    "Date": assessment.get("assessment_date", ""),
                    "Document Type": assessment.get("document_type", ""),
                    "Score": f"{assessment.get('score', 0)}/{assessment.get('total_questions', 0)}",
                    "Percentage": f"{assessment.get('percentage', 0)}%",
                    "Result": "PASS" if assessment.get('passed', False) else "FAIL"
                })
            
            if assessment_data:
                df = pd.DataFrame(assessment_data)
                
                # Color code the results
                def color_result(val):
                    color = 'background-color: #d4edda' if val == 'PASS' else 'background-color: #f8d7da'
                    return color
                
                styled_df = df.style.applymap(color_result, subset=['Result'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Performance analysis
                if len(assessments) > 1:
                    
                    # Show improvement over time
                    recent_scores = [a.get('percentage', 0) for a in assessments[:5]]  # Last 5 assessments
                    if len(recent_scores) >= 2:
                        trend = "📈 Improving" if recent_scores[0] > recent_scores[-1] else "📉 Declining" if recent_scores[0] < recent_scores[-1] else "➡️ Stable"
                        st.markdown(f"**Recent Trend:** {trend}")
                    
                    # Document type performance
                    doc_type_performance = {}
                    for assessment in assessments:
                        doc_type = assessment.get('document_type', 'Unknown')
                        if doc_type not in doc_type_performance:
                            doc_type_performance[doc_type] = []
                        doc_type_performance[doc_type].append(assessment.get('percentage', 0))
                    
                    if len(doc_type_performance) > 1:
                        st.markdown("**Performance by Document Type:**")
                        for doc_type, scores in doc_type_performance.items():
                            avg_score = sum(scores) / len(scores)
                            st.markdown(f"- **{doc_type}**: {avg_score:.1f}% average ({len(scores)} assessments)")
        else:
            st.info("📚 No assessments completed yet. Take your first assessment to see results here!")
            
    else:
        st.error(f"❌ Failed to load training results: {results.get('error', 'Unknown error')}")

# Footer
st.markdown("---")
st.info("🎓 **Training System**: Generic learning and assessment platform leveraging Knowledge Base collections for comprehensive education and evaluation.")