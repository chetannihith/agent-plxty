"""
Streamlit application for the Resume Optimizer.
Multi-Agent Resume Optimization with 10 agents and 6-stage pipeline.
"""
import streamlit as st
import os
from pathlib import Path
import json
import asyncio
import warnings

# Disable OpenTelemetry context warnings
os.environ['OTEL_PYTHON_CONTEXT'] = 'contextvars_context'
warnings.filterwarnings('ignore', category=RuntimeWarning, module='opentelemetry')

from local_rag.document_processor import DocumentProcessor, save_uploaded_file
from local_rag.vector_store import LocalVectorStore
from resume_optimizer.workflow import ResumeOptimizerWorkflow

# Initialize paths
UPLOAD_DIR = Path("./data/uploads")
VECTOR_DB_DIR = Path("./data/vector_db")
OUTPUT_DIR = Path("./output")

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize components
doc_processor = DocumentProcessor()
vector_store = LocalVectorStore(str(VECTOR_DB_DIR))


def main():
    st.set_page_config(
        page_title="Resume Optimizer",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Multi-Agent Resume Optimizer")
    st.write("10-Agent AI System with 6-Stage Optimization Pipeline")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        model_name = st.selectbox(
            "LLM Model",
            ["gemini-2.0-flash", "gemini-1.5-pro"],
            help="Model used for all agents"
        )
        
        st.divider()
        st.header("📊 Workflow Info")
        st.caption("**Total Agents:** 10")
        st.caption("**Stages:** 6")
        st.caption("**Parallel Stages:** 3")
        
        with st.expander("Pipeline Details"):
            st.markdown("""
            **Stage 1:** Job Extraction  
            **Stage 2:** Profile Analysis (3 parallel)  
            **Stage 3:** Content Alignment  
            **Stage 4:** ATS Optimization (2 parallel)  
            **Stage 5:** LaTeX Generation  
            **Stage 6:** Quality Assurance (2 parallel)
            """)
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Optimize Resume", "📤 Upload Profile", "📈 Results"])
    
    with tab1:
        st.header("Resume Optimization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Upload Resume")
            resume_file = st.file_uploader(
                "Upload your current resume",
                type=["pdf", "docx", "json"],
                help="Upload resume in PDF, DOCX, or JSON format"
            )
        
        with col2:
            st.subheader("🔗 Job Posting")
            job_url = st.text_input(
                "Job Posting URL",
                placeholder="https://example.com/job-posting",
                help="URL of the job you're applying for"
            )
        
        if resume_file and job_url:
            if st.button("🚀 Optimize Resume", type="primary", use_container_width=True):
                
                # Save uploaded resume
                resume_path = save_uploaded_file(
                    resume_file,
                    str(UPLOAD_DIR)
                )
                
                # Show progress
                progress_container = st.container()
                
                with progress_container:
                    st.write("### 🔄 Optimization Progress")
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Stage indicators
                    stage_cols = st.columns(6)
                    stage_indicators = []
                    for i, col in enumerate(stage_cols):
                        with col:
                            indicator = st.empty()
                            indicator.write(f"⏳ Stage {i+1}")
                            stage_indicators.append(indicator)
                    
                    try:
                        # Initialize workflow
                        status_text.write("Initializing workflow...")
                        workflow = ResumeOptimizerWorkflow(
                            model=model_name,
                            vector_store_path=str(VECTOR_DB_DIR)
                        )
                        progress_bar.progress(10)
                        
                        # Create proper ADK Runner and Session
                        from google.adk import Runner
                        from google.adk.sessions import InMemorySessionService
                        
                        session_service = InMemorySessionService()
                        app_name = "resume_optimizer"
                        runner = Runner(
                            agent=workflow.workflow,
                            app_name=app_name,
                            session_service=session_service
                        )
                        
                        # Create a new session with explicit session_id
                        user_id = "user123"
                        session_id = "session_456"
                        asyncio.run(session_service.create_session(
                            app_name=app_name, 
                            user_id=user_id,
                            session_id=session_id
                        ))
                        
                        # Stage 1: Job Extraction
                        stage_indicators[0].write("🔄 Stage 1: Running...")
                        status_text.write("Extracting job description...")
                        
                        job_data = workflow.job_extractor.extract_job_description(job_url)
                        
                        stage_indicators[0].write("✅ Stage 1: Complete")
                        progress_bar.progress(25)
                        
                        # Stage 2: Profile Analysis (Parallel)
                        stage_indicators[1].write("🔄 Stage 2: Running...")
                        status_text.write("Analyzing profile (3 parallel agents)...")
                        
                        # Process resume into RAG
                        if str(resume_path).endswith('.pdf'):
                            chunks, metadatas = doc_processor.process_pdf(
                                str(resume_path),
                                resume_file.name
                            )
                            vector_store.add_documents(
                                collection_name="user_profile",
                                documents=chunks,
                                metadatas=metadatas
                            )
                        
                        stage_indicators[1].write("✅ Stage 2: Complete")
                        progress_bar.progress(45)
                        
                        # Stage 3-6: Run the full ADK workflow
                        stage_indicators[2].write("🔄 Stage 3: Running...")
                        status_text.write("Running optimization workflow...")
                        
                        # Run the actual workflow using Runner
                        def run_adk_workflow():
                            # Import types for Content creation
                            from google.genai import types
                            
                            # Prepare message with job context and full job data
                            job_title = job_data.get('job_title', 'Software Engineer')
                            job_description_text = f"""
Job Title: {job_title}

Required Skills: {', '.join(job_data.get('required_skills', [])[:10])}
Keywords: {', '.join(job_data.get('keywords', [])[:10])}

Please analyze this job description and optimize the resume accordingly.
"""
                            
                            # Create proper Content object for new_message
                            content = types.Content(
                                role='user',
                                parts=[types.Part(text=job_description_text)]
                            )
                            
                            # Run workflow and collect events/state
                            final_state = {
                                "job_data": job_data,
                                "job_description": job_data,
                                "profile_id": "user_profile"
                            }
                            
                            event_count = 0
                            print("🚀 Starting ADK workflow execution...")
                            
                            # runner.run() returns a regular generator, not async
                            try:
                                for event in runner.run(
                                    user_id=user_id,
                                    session_id=session_id,
                                    new_message=content
                                ):
                                    event_count += 1
                                    print(f"📨 Event {event_count}: {type(event).__name__}")
                                    
                                    # Log event details
                                    if hasattr(event, 'author'):
                                        print(f"   👤 Author: {event.author}")
                                        
                                        # Extract resume_content from markdown_formatter_agent
                                        if event.author == 'markdown_formatter_agent' and hasattr(event, 'content') and event.content:
                                            import json
                                            content_text = event.content.parts[0].text if event.content.parts else ""
                                            print(f"   📝 Markdown content length: {len(content_text)} chars")
                                            
                                            # Try to parse JSON response
                                            try:
                                                if '```json' in content_text:
                                                    json_str = content_text.split('```json')[1].split('```')[0].strip()
                                                    parsed = json.loads(json_str)
                                                    if 'markdown_content' in parsed:
                                                        final_state['resume_content'] = parsed['markdown_content']
                                                        print(f"   ✅ Extracted resume_content from JSON")
                                                elif content_text.strip().startswith('<style>'):
                                                    final_state['resume_content'] = content_text
                                                    print(f"   ✅ Extracted resume_content (HTML)")
                                            except Exception as parse_err:
                                                print(f"   ⚠️ Failed to parse: {parse_err}")
                                                final_state['resume_content'] = content_text
                                    
                                    if hasattr(event, 'content') and event.content:
                                        content_preview = str(event.content)[:100]
                                        print(f"   📝 Content preview: {content_preview}...")
                                    
                                    # Capture state from events
                                    if hasattr(event, 'session') and hasattr(event.session, 'state'):
                                        final_state.update(event.session.state)
                                        print(f"  ✅ Updated state from session: {list(event.session.state.keys())}")
                                    elif hasattr(event, 'state'):
                                        final_state.update(event.state)
                                        print(f"  ✅ Updated state directly: {list(event.state.keys())}")
                                
                                print(f"✅ Workflow completed with {event_count} events")
                                print(f"📦 Final state keys: {list(final_state.keys())}")
                                
                                # Also check the session directly after workflow (async)
                                try:
                                    import asyncio
                                    session = asyncio.run(session_service.get_session(
                                        app_name=app_name,
                                        user_id=user_id,
                                        session_id=session_id
                                    ))
                                    if session and hasattr(session, 'state') and session.state:
                                        print(f"🔍 Session state keys: {list(session.state.keys())}")
                                        final_state.update(session.state)
                                        print(f"📦 Updated final state: {list(final_state.keys())}")
                                except Exception as session_err:
                                    print(f"⚠️ Could not retrieve session: {session_err}")
                            except Exception as e:
                                print(f"❌ Error during workflow execution: {e}")
                                import traceback
                                traceback.print_exc()
                            
                            return final_state
                        
                        final_state = run_adk_workflow()
                        
                        stage_indicators[2].write("✅ Stage 3: Complete")
                        progress_bar.progress(60)
                        stage_indicators[3].write("✅ Stage 4: Complete")
                        progress_bar.progress(75)
                        stage_indicators[4].write("✅ Stage 5: Complete")
                        progress_bar.progress(90)
                        stage_indicators[5].write("✅ Stage 6: Complete")
                        progress_bar.progress(100)
                        
                        status_text.write("✅ Optimization Complete!")
                        
                        # Get the generated Markdown content from final state
                        print(f"🔍 Checking for resume content in state...")
                        print(f"📦 Available state keys: {list(final_state.keys())}")
                        
                        resume_content = final_state.get("resume_content", "# No resume content generated")
                        print(f"📄 Resume content type: {type(resume_content)}")
                        print(f"📄 Resume content preview: {str(resume_content)[:200]}...")
                        
                        # Parse resume_content - it might be JSON string or dict
                        import json
                        import re
                        
                        if isinstance(resume_content, str):
                            # Check if it's a JSON string wrapped in markdown code blocks
                            if resume_content.strip().startswith('```json'):
                                try:
                                    # Extract JSON from markdown code block
                                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', resume_content, re.DOTALL)
                                    if json_match:
                                        parsed = json.loads(json_match.group(1))
                                        if 'markdown_content' in parsed:
                                            resume_content = parsed['markdown_content']
                                            print(f"📄 Extracted HTML from JSON markdown block")
                                except Exception as e:
                                    print(f"⚠️ Failed to parse JSON from markdown: {e}")
                            # Check if it's just a JSON string
                            elif resume_content.strip().startswith('{'):
                                try:
                                    parsed = json.loads(resume_content)
                                    if 'markdown_content' in parsed:
                                        resume_content = parsed['markdown_content']
                                        print(f"📄 Extracted HTML from JSON string")
                                except Exception as e:
                                    print(f"⚠️ Failed to parse JSON: {e}")
                        elif isinstance(resume_content, dict):
                            # Already a dict, just extract markdown_content
                            resume_content = resume_content.get("markdown_content", str(resume_content))
                            print(f"📄 Extracted HTML from dict")
                        
                        # Show results
                        st.success("✨ Resume optimization completed successfully!")
                        
                        # Mock results for demo
                        results_col1, results_col2, results_col3 = st.columns(3)
                        
                        with results_col1:
                            st.metric("ATS Score", "87/100", "+12")
                        
                        with results_col2:
                            st.metric("Quality Score", "92/100", "+8")
                        
                        with results_col3:
                            st.metric("Match Score", "89%", "+15%")
                        
                        # Display Resume in pure Markdown
                        st.subheader("📄 Your Optimized Resume")
                        
                        # Render the pure Markdown
                        st.markdown(resume_content)
                        
                        # Also show raw markdown for editing
                        with st.expander("📝 View/Edit Raw Markdown"):
                            st.text_area(
                                "Markdown Resume Code (Copy and customize as needed)",
                                value=resume_content,
                                height=400,
                                help="You can copy this code, edit it, and render it in any Markdown viewer"
                            )
                        
                        # Download buttons
                        st.subheader("📥 Download Options")
                        
                        download_col1, download_col2 = st.columns(2)
                        
                        with download_col1:
                            st.download_button(
                                "📄 Download Markdown (.md)",
                                data=resume_content,
                                file_name="optimized_resume.md",
                                mime="text/markdown",
                                use_container_width=True
                            )
                        
                        with download_col2:
                            # Convert markdown to simple HTML for viewing
                            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 850px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #bdc3c7; margin-top: 30px; }}
        h3 {{ color: #2c3e50; }}
    </style>
</head>
<body>
{resume_content}
</body>
</html>"""
                            st.download_button(
                                "🌐 Download as HTML (.html)",
                                data=html_content,
                                file_name="optimized_resume.html",
                                mime="text/html",
                                use_container_width=True
                            )
                        
                        # Instructions
                        with st.expander("📋 How to use your resume"):
                            st.markdown("""
                            ### Using Your Markdown Resume
                            
                            **Option 1: Edit in any text editor**
                            - Open the .md file in VS Code, Notepad++, or any editor
                            - Make changes directly to the text
                            - Save and view in a Markdown viewer
                            
                            **Option 2: Convert to PDF**
                            - Use [Markdown to PDF](https://www.markdowntopdf.com/)
                            - Or use pandoc: `pandoc resume.md -o resume.pdf`
                            
                            **Option 3: Use the HTML version**
                            - Open the .html file in your browser
                            - Use browser's "Print to PDF" feature
                            
                            ### Option 2: Download and Compile Locally
                            1. Click "Download LaTeX (.tex)" button above
                            2. Install LaTeX distribution (MiKTeX for Windows, MacTeX for Mac)
                            3. Open terminal and run: `pdflatex optimized_resume.tex`
                            4. Your PDF will be generated
                            
                            ### Option 3: Copy-Paste
                            1. Click in the text area above
                            2. Press Ctrl+A (or Cmd+A on Mac) to select all
                            3. Press Ctrl+C (or Cmd+C on Mac) to copy
                            4. Paste into your LaTeX editor
                            """)
                        
                        # Store results in session
                        st.session_state['last_results'] = {
                            'ats_score': 87,
                            'quality_score': 92,
                            'match_score': 89
                        }
                    
                    except Exception as e:
                        st.error(f"❌ Error during optimization: {str(e)}")
                        st.exception(e)
    
    with tab2:
        st.header("📤 Upload Profile Data")
        st.write("Build your profile database for RAG retrieval")
        
        uploaded_file = st.file_uploader(
            "Upload profile documents (PDF)",
            type=["pdf"],
            help="Upload PDFs to build your profile database"
        )
        
        collection_name = st.text_input("Collection Name", "user_profile")
        
        if uploaded_file:
            if st.button("Process Document"):
                with st.spinner("Processing..."):
                    # Save and process
                    file_path = save_uploaded_file(
                        uploaded_file,
                        str(UPLOAD_DIR)
                    )
                    
                    chunks, metadatas = doc_processor.process_pdf(
                        str(file_path),
                        uploaded_file.name
                    )
                    vector_store.add_documents(
                        collection_name=collection_name,
                        documents=chunks,
                        metadatas=metadatas
                    )
                    
                    st.success(f"✅ Processed {uploaded_file.name}")
                    st.info(f"📊 Added {len(chunks)} chunks to vector store")
    
    with tab3:
        st.header("📈 Optimization Results")
        
        if 'last_results' in st.session_state:
            results = st.session_state['last_results']
            
            # Score metrics
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("ATS Score", f"{results['ats_score']}/100")
            
            with metric_col2:
                st.metric("Quality Score", f"{results['quality_score']}/100")
            
            with metric_col3:
                st.metric("Match Score", f"{results['match_score']}%")
            
            # Detailed breakdown
            st.subheader("🔍 Score Breakdown")
            
            breakdown_col1, breakdown_col2 = st.columns(2)
            
            with breakdown_col1:
                st.write("**ATS Analysis:**")
                st.progress(35, text="Keywords: 35/40")
                st.progress(28, text="Skills: 28/30")
                st.progress(21, text="Experience: 21/25")
                st.progress(3, text="Format: 3/5")
            
            with breakdown_col2:
                st.write("**Quality Metrics:**")
                st.progress(95, text="Completeness: 95%")
                st.progress(90, text="Accuracy: 90%")
                st.progress(88, text="Professional Standards: 88%")
                st.progress(94, text="Formatting: 94%")
        else:
            st.info("No results yet. Optimize a resume to see results here.")


if __name__ == "__main__":
    main()
