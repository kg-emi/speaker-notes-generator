# --- START OF FILE main.py ---

import os
import logging
import re # Import regex for parsing
import time # Import time for temporary filenames
import io # Import io for in-memory streams
import writer as wf
import writer.ai
import pandas as pd
from typing import Literal, Any # Added Any for type hint
from prompts import (
    OUTLINE_PROMPT,
    VISUAL_OUTLINE_PROMPT,
    BRIEFING_INFO_PROMPT,
    MAP_MESSAGES_PROMPT,
    SPEAKER_NOTES_PROMPT,
)

try:
    from pptx import Presentation
    PPTX_SUPPORT = True
except ImportError:
    PPTX_SUPPORT = False

try:
    import docx
    from docx.shared import Inches, Pt
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if "WRITER_API_KEY" in os.environ:
    wf.api_key = os.getenv("WRITER_API_KEY")
else:
    logger.warning("WRITER_API_KEY environment variable not set. AI features will not work.")

# --- Custom Exception for Stopping ---
class GenerationStoppedError(Exception):
    """Custom exception for stopping the generation process."""
    pass

# --- Helper Functions ---
def _extract_text_from_file(file_path: str) -> str:
    """Extracts text from PDF or PPTX files."""
    logger.info(f"Attempting to extract text from: {file_path}")
    file_extension = os.path.splitext(file_path)[1].lower()
    base_filename = os.path.basename(file_path)
    sanitized_filename = base_filename.encode('ascii', 'ignore').decode('ascii')

    try:
        if file_extension == ".pdf":
            logger.info("Processing as PDF using writer.ai.tools.parse_pdf")
            with open(file_path, "rb") as f:
                file_data = f.read()

            if not wf.api_key:
                raise ConnectionError("WRITER_API_KEY is not set, cannot upload file.")

            uploaded_file = writer.ai.upload_file(
                data=file_data,
                type="application/pdf",
                name=sanitized_filename
            )
            file_id = uploaded_file.id
            logger.info(f"Uploaded PDF {sanitized_filename} with ID: {file_id}")

            extracted_text = writer.ai.tools.parse_pdf(file_id_or_file=file_id, format="text")
            logger.info(f"Extracted text from PDF {sanitized_filename}")
            # Optionally delete the file after parsing
            try:
                writer.ai.delete_file(file_id)
                logger.info(f"Deleted temporary file {file_id}")
            except Exception as del_e:
                logger.warning(f"Could not delete temporary file {file_id}: {del_e}")
            return extracted_text

        elif file_extension == ".pptx":
            if not PPTX_SUPPORT:
                 logger.warning(f"Skipping PPTX text extraction for {base_filename} as python-pptx is not installed. Please run 'pip install python-pptx'.")
                 return f"[Text extraction skipped for PPTX: {base_filename} - python-pptx not installed]"

            logger.info(f"Processing as PPTX locally using python-pptx")
            presentation = Presentation(file_path)
            full_text = []
            for slide in presentation.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text = shape.text.strip()
                        if text:
                            full_text.append(text)
            extracted_text = "\n".join(full_text)
            logger.info(f"Extracted text from PPTX {base_filename}")
            return extracted_text

        else:
            logger.warning(f"Unsupported file type for text extraction: {base_filename}. Returning placeholder.")
            return f"[Unsupported file type: {base_filename}]"

    except Exception as e:
        logger.error(f"Error extracting text from {base_filename}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to extract text from {base_filename}") from e

def _call_ai_model(prompt: str, model: str = "palmyra-x-004", temperature: float = 0.0) -> str:
    """Calls the Writer AI completion endpoint with a specific temperature."""
    if not wf.api_key:
        raise ConnectionError("WRITER_API_KEY is not set, cannot call AI model.")
    try:
        config = {"model": model, "temperature": temperature}
        response = writer.ai.complete(prompt, config=config)
        return response.strip()
    except Exception as e:
        logger.error(f"Error calling AI model {model} with temperature {temperature}: {e}")
        raise

def _analyze_visuals(file_path: str, prompt: str) -> str:
    """Analyzes visuals (or text file content) in a presentation using Palmyra Vision."""
    if not wf.api_key:
        raise ConnectionError("WRITER_API_KEY is not set, cannot analyze visuals.")

    file_extension = os.path.splitext(file_path)[1].lower()
    base_filename = os.path.basename(file_path)
    sanitized_filename = base_filename.encode('ascii', 'ignore').decode('ascii')
    # Added .txt to supported types for the workaround
    supported_vision_types = [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt"]
    if file_extension not in supported_vision_types:
        logger.warning(f"File type {file_extension} not supported by Palmyra Vision. Skipping visual analysis for {base_filename}.")
        return "[Visual analysis skipped: Unsupported file type]"

    file_id = None # Initialize file_id to ensure it's available in finally block if upload fails
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()

        if file_extension == ".pdf":
            content_type = "application/pdf"
        elif file_extension == ".txt":
             content_type = "text/plain" # Correct content type for text files
        else:
            import mimetypes
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type or not content_type.startswith("image/"):
                content_type = "application/octet-stream"

        uploaded_file = writer.ai.upload_file(
            data=file_data,
            type=content_type,
            name=sanitized_filename
        )
        file_id = uploaded_file.id
        logger.info(f"Uploaded file for visual analysis {sanitized_filename} with ID: {file_id}")

        # Use the passed prompt here, replacing placeholder if needed
        variables = [{"name": "InputDocument", "file_id": file_id}] # Use a generic variable name
        # Adjust prompt to use the generic variable name if the original placeholder exists
        prompt_with_variable = prompt.replace("{{Presentation Deck}}", "{{InputDocument}}")

        client = writer.ai.WriterAIManager.acquire_client()
        response = client.vision.analyze(
            model="palmyra-vision",
            prompt=prompt_with_variable, # <-- Use the modified prompt
            variables=variables
        )
        logger.info(f"Visual analysis completed for {sanitized_filename}")

        # Delete the uploaded file after successful analysis
        try:
            writer.ai.delete_file(file_id)
            logger.info(f"Deleted temporary file {file_id} after visual analysis")
        except Exception as del_e:
            logger.warning(f"Could not delete temporary file {file_id} after visual analysis: {del_e}")

        return response.data
    except Exception as e:
        logger.error(f"Error analyzing visuals in {base_filename}: {e}", exc_info=True)
        # Ensure temporary file ID is deleted even on error if it exists
        if file_id:
             try:
                 writer.ai.delete_file(file_id)
                 logger.info(f"Deleted temporary file {file_id} after analysis error")
             except Exception as del_e:
                 logger.warning(f"Could not delete temporary file {file_id} after analysis error: {del_e}")
        return f"[Error during visual analysis: {type(e).__name__}]"

# --- Helper function to handle inline formatting ---
def _add_formatted_text_to_paragraph(paragraph: Any, text: str):
    """Adds text to a paragraph, applying bold and italic formatting based on Markdown."""
    # Regex to find **bold** or _italic_ or *italic* text, handling potential overlaps simply
    # It captures the marker and the content separately.
    # Prioritize bold first to handle cases like **bold *italic*** correctly (though nested isn't fully supported here)
    parts = re.split(r'(\*\*.*?\*\*|[*_].*?[*_])', text) # Split by bold or italic markers

    for part in parts:
        if not part: # Skip empty strings resulting from split
            continue

        run = paragraph.add_run()
        if part.startswith('**') and part.endswith('**'):
            run.text = part[2:-2] # Add text without markers
            run.bold = True
        elif (part.startswith('*') and part.endswith('*')) or \
             (part.startswith('_') and part.endswith('_')):
            run.text = part[1:-1] # Add text without markers
            run.italic = True
        else:
            run.text = part # Add as normal text

# --- Modified function to generate DOCX bytes ---
def _generate_docx_bytes(content: str) -> bytes:
    """Creates a DOCX file in memory from markdown-like text content and returns its bytes."""
    if not DOCX_SUPPORT:
        logger.error("python-docx library not found. Cannot create DOCX file.")
        raise ImportError("python-docx is required for DOCX generation. Please install it.")

    document = docx.Document()
    # Optional: Set default font if needed
    # style = document.styles['Normal']
    # font = style.font
    # font.name = 'Calibri'
    # font.size = Pt(11)

    for line in content.split('\n'):
        stripped_line = line.strip()

        # Handle Headings (Markdown Style: #, ##, ### etc.)
        heading_match = re.match(r"^(#+)\s+(.*)", stripped_line)
        if heading_match:
            level = len(heading_match.group(1))
            text_content = heading_match.group(2)
            level = max(1, min(level, 9)) # Ensure level is within Word's range
            heading = document.add_heading(level=level)
            _add_formatted_text_to_paragraph(heading, text_content) # Apply inline formatting
        # Handle Speaker Notes specific "Slide X:" format as Heading 1
        elif stripped_line.startswith("Slide ") and ":" in stripped_line:
             try:
                 # Attempt to extract text after "Slide X:"
                 heading_text = stripped_line.split(":", 1)[1].strip()
                 heading = document.add_heading(level=1)
                 _add_formatted_text_to_paragraph(heading, heading_text) # Apply inline formatting
             except IndexError: # Handle case like "Slide 1" with no colon
                 heading = document.add_heading(level=1)
                 _add_formatted_text_to_paragraph(heading, stripped_line) # Apply inline formatting
        # Handle Lists (Markdown Style: * or -)
        elif stripped_line.startswith("* ") or stripped_line.startswith("- "):
            text_content = stripped_line[2:]
            if text_content:
                 paragraph = document.add_paragraph(style='List Bullet')
                 _add_formatted_text_to_paragraph(paragraph, text_content) # Apply inline formatting
            else:
                 document.add_paragraph(style='List Bullet') # Add empty bullet point
        # Handle Empty lines
        elif not stripped_line:
             document.add_paragraph()
        # Handle Regular Paragraphs
        else:
            paragraph = document.add_paragraph()
            _add_formatted_text_to_paragraph(paragraph, stripped_line) # Apply inline formatting

    # Save to an in-memory buffer
    buffer = io.BytesIO()
    try:
        document.save(buffer)
        logger.info("Generated DOCX content in memory.")
        buffer.seek(0) # Rewind the buffer to the beginning
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Failed to save DOCX to memory buffer: {e}")
        raise # Re-raise the error

# --- Modified download helper ---
def _download_content_as_docx(state, content_key: str):
    """Helper to generate and download content as DOCX."""
    logger.info(f"Attempting to download content for key: {content_key}")
    if not state["results"] or content_key not in state["results"] or not state["results"][content_key]:
        message = f"!Content for '{content_key}' not available for download."
        state["processing_message"] = message
        logger.warning(message)
        return

    content = state["results"][content_key]
    if not isinstance(content, str):
        content = str(content) # Ensure content is string

    try:
        filename_docx = f"{content_key}_notes.docx"
        docx_bytes = _generate_docx_bytes(content) # Generate bytes directly
        state.file_download(
            wf.pack_bytes(docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            filename_docx
        )
        state["processing_message"] = f"+Download initiated for {filename_docx}."
    except Exception as e:
        message = f"-Error preparing DOCX download for '{content_key}': {e}"
        state["processing_message"] = message
        logger.error(message, exc_info=True)

def _get_input_text(state, input_type: Literal["deck", "briefing"]) -> str:
    """Gets the text content based on the selected input method."""
    if input_type == "deck":
        method = state["deck_input_method"]
        if method == "Upload File":
            if state["deck_file"]["path"]:
                if state["deck_file"]["text_content"] is None: # Extract if not already done
                     state["processing_message"] = "%Extracting text from presentation deck..."
                     state["deck_file"]["text_content"] = _extract_text_from_file(state["deck_file"]["path"])
                return state["deck_file"]["text_content"] or ""
            else:
                return "" # No file uploaded
        elif method == "Enter Text":
            return state["deck_file"]["text_content"] or "" # Use saved text
        else:
            return ""
    elif input_type == "briefing":
        method = state["briefing_input_method"]
        if method == "Upload File":
            briefing_texts = []
            for i, briefing_file in enumerate(state["briefing_files"]):
                if briefing_file["path"]:
                    if briefing_file["text_content"] is None: # Extract if not already done
                        state["processing_message"] = f"%Extracting text from briefing document {i+1}/{len(state['briefing_files'])}..."
                        briefing_file["text_content"] = _extract_text_from_file(briefing_file["path"])
                    briefing_texts.append(briefing_file["text_content"] or "")
            return "\n\n---\n\n".join(briefing_texts)
        elif method == "Enter Text":
            return state["briefing_manual_text"] or "" # Use saved text
        else:
            return ""
    return ""

def _update_generate_button_state(state):
    """Updates the disabled state of the generate button based on inputs."""
    deck_ready = False
    if state["deck_input_method"] == "Upload File":
        deck_ready = bool(state["deck_file"]["path"])
    elif state["deck_input_method"] == "Enter Text":
        deck_ready = bool(state["deck_file"]["text_content"])

    briefing_ready = False
    if state["briefing_input_method"] == "Upload File":
        briefing_ready = len(state["briefing_files"]) > 0
    elif state["briefing_input_method"] == "Enter Text":
        briefing_ready = bool(state["briefing_manual_text"])

    # Disable generate button if generation is already in progress OR inputs are not ready
    state["ui_controls"]["generate_disabled"] = "yes" if (state["is_generating"] or not (deck_ready and briefing_ready)) else "no"


# --- State Initialization ---
os.makedirs("data", exist_ok=True) # Keep this for potential temporary file needs (like uploads)
placeholder_data = {'Description': [], 'Label': []}
initial_df = pd.DataFrame(placeholder_data)

initial_state = wf.init_state({
    "app_title": "Speaker Notes Generator",
    "logo_path": "static/writer_logo.svg",
    "deck_file": {"name": None, "path": None, "id": None, "text_content": None}, # Added text_content
    "briefing_files": [],
    "settings": {
        "timing": "30 Minutes",
        "style": "Informative"
    },
    "metrics": {"new_features": 0, "caveats": 0, "fixed_issues": 0, "total": 0},
    "processing_step": "idle", # idle, text_extraction, step1, step2, step3, step4, step5, done, error
    "processing_message": "Upload your presentation deck and briefing document(s).",
    "results": {
        "outline": None,
        "visuals": None,
        "briefing_info": None,
        "mapping": None,
        "speaker_notes": None,
    },
    "ui_controls": {
        "generate_disabled": "yes",
        "download_disabled": "yes",
        # --- Add visibility flags ---
        "show_deck_upload": True,
        "show_deck_text_input": False,
        "show_briefing_upload": True,
        "show_briefing_text_input": False,
        # --- End Add ---
    },
    # New state variables for input method and text
    "deck_input_method": "Upload File", # "Upload File" or "Enter Text"
    "briefing_input_method": "Upload File", # "Upload File" or "Enter Text"
    "deck_text_input": "", # Temporary storage for deck text area
    "briefing_text_input": "", # Temporary storage for briefing text area
    "briefing_manual_text": "", # Saved manual briefing text
    # --- Add generation tracking flags ---
    "is_generating": False,
    "stop_requested": False,
    # --- End Add ---
})
initial_state.import_stylesheet("custom_styles", "/static/custom.css")

# --- Event Handlers ---
def handle_deck_upload(state, payload):
    """Handles the presentation deck upload."""
    if not payload:
        state["processing_message"] = "-No deck file uploaded."
        return
    try:
        uploaded_file = payload[0]
        name = uploaded_file.get("name")
        file_data = uploaded_file.get("data")

        # Save temporarily to disk for text extraction
        temp_path = os.path.join("data", f"deck_{name}")
        with open(temp_path, "wb") as file_handle:
            file_handle.write(file_data)

        if state["deck_file"] is None: state["deck_file"] = {}
        state["deck_file"]["name"] = name
        state["deck_file"]["path"] = temp_path # Store path for potential later use (e.g., vision)
        state["deck_file"]["id"] = None
        state["deck_file"]["text_content"] = None # Reset text content, will be extracted on demand
        state["processing_message"] = f"+Deck '{name}' uploaded."
        _update_generate_button_state(state)
        logger.info(f"Deck file uploaded: {name}")
    except Exception as e:
        state["processing_message"] = f"-Error uploading deck: {e}"
        logger.error(f"Error in handle_deck_upload: {e}", exc_info=True)

def handle_briefing_upload(state, payload):
    """Handles briefing document uploads."""
    if not payload:
        state["processing_message"] = "-No briefing file(s) uploaded."
        return
    try:
        new_files_info = []
        for uploaded_file in payload:
            name = uploaded_file.get("name")
            file_data = uploaded_file.get("data")
            # Save temporarily to disk for text extraction
            temp_path = os.path.join("data", f"briefing_{name}")
            with open(temp_path, "wb") as file_handle:
                file_handle.write(file_data)
            # Store path and reset text content
            new_files_info.append({"name": name, "path": temp_path, "id": None, "text_content": None})
            logger.info(f"Briefing file uploaded: {name}")

        if state["briefing_files"] is None: state["briefing_files"] = []
        state["briefing_files"] += new_files_info
        state["briefing_manual_text"] = "" # Clear manual text if files are uploaded
        state["processing_message"] = f"+{len(payload)} briefing file(s) added."
        _update_generate_button_state(state)

    except Exception as e:
        state["processing_message"] = f"-Error uploading briefing(s): {e}"
        logger.error(f"Error in handle_briefing_upload: {e}", exc_info=True)

# --- New Handlers for Input Method Change ---
def handle_deck_method_change(state, payload):
    state["deck_input_method"] = payload
    # --- Update visibility flags ---
    state["ui_controls"]["show_deck_upload"] = (payload == "Upload File")
    state["ui_controls"]["show_deck_text_input"] = (payload == "Enter Text")
    # --- End Update ---
    # Clear the other input method's data
    if payload == "Upload File":
        state["deck_file"]["text_content"] = None
    else: # Enter Text
        state["deck_file"]["path"] = None
        state["deck_file"]["name"] = None
        state["deck_file"]["id"] = None
    _update_generate_button_state(state)

def handle_briefing_method_change(state, payload):
    state["briefing_input_method"] = payload
    # --- Update visibility flags ---
    state["ui_controls"]["show_briefing_upload"] = (payload == "Upload File")
    state["ui_controls"]["show_briefing_text_input"] = (payload == "Enter Text")
    # --- End Update ---
    # Clear the other input method's data
    if payload == "Upload File":
        state["briefing_manual_text"] = ""
    else: # Enter Text
        state["briefing_files"] = []
    _update_generate_button_state(state)

# --- New Handlers for Saving Text Input ---
def handle_save_deck_text(state):
    state["deck_file"]["text_content"] = state["deck_text_input"]
    state["deck_file"]["path"] = None # Ensure path is cleared
    state["deck_file"]["name"] = "Manual Text Input"
    state["deck_file"]["id"] = None
    state["processing_message"] = "+Deck text saved."
    _update_generate_button_state(state)

def handle_save_briefing_text(state):
    state["briefing_manual_text"] = state["briefing_text_input"]
    state["briefing_files"] = [] # Ensure file list is cleared
    state["processing_message"] = "+Briefing text saved."
    _update_generate_button_state(state)

# --- Stop Handler ---
def handle_stop_generate(state):
    """Sets the stop flag to interrupt the generation process."""
    if state["is_generating"]:
        state["stop_requested"] = True
        state["processing_message"] = "!Stopping generation..."
        logger.info("Stop generation requested by user.")
    else:
        state["processing_message"] = "!Generation is not currently running."

def handle_generate(state):
    """Orchestrates the AI processing pipeline."""
    # Check if inputs are ready based on selected methods
    deck_ready = False
    if state["deck_input_method"] == "Upload File":
        deck_ready = bool(state["deck_file"]["path"])
    elif state["deck_input_method"] == "Enter Text":
        deck_ready = bool(state["deck_file"]["text_content"])

    briefing_ready = False
    if state["briefing_input_method"] == "Upload File":
        briefing_ready = len(state["briefing_files"]) > 0
    elif state["briefing_input_method"] == "Enter Text":
        briefing_ready = bool(state["briefing_manual_text"])

    if not deck_ready or not briefing_ready:
        state["processing_message"] = "!Please provide input for both the deck and briefing documents."
        return

    if not wf.api_key:
         state["processing_message"] = "-WRITER_API_KEY is not set. Cannot proceed with AI generation."
         logger.error("WRITER_API_KEY not set.")
         return

    # --- Start Generation ---
    state["is_generating"] = True
    state["stop_requested"] = False # Reset stop flag
    state["ui_controls"]["generate_disabled"] = "yes" # Disable generate button
    state["ui_controls"]["download_disabled"] = "yes"
    state["processing_step"] = "idle"
    state["results"] = {} # Clear previous results
    # --- End Start ---

    try:
        # --- Step 0: Get Text Content ---
        state["processing_step"] = "text_extraction"
        state["processing_message"] = "%Getting text content..."
        deck_text = _get_input_text(state, "deck")
        combined_briefing_text = _get_input_text(state, "briefing")

        if not deck_text:
             raise ValueError("Presentation deck content is empty.")
        if not combined_briefing_text:
             raise ValueError("Briefing document content is empty.")

        # --- Check Stop Flag ---
        if state["stop_requested"]: raise GenerationStoppedError()

        # --- Step 1: Extract Outline ---
        state["processing_step"] = "step1"
        state["processing_message"] = "%Generating presentation outline using vision model..."
        # --- START: Modified logic for Step 1 using vision model ---
        temp_text_filename = f"temp_deck_text_{int(time.time())}.txt"
        temp_text_path = os.path.join("data", temp_text_filename)
        outline = "[Error generating outline with vision model]" # Default error message
        temp_file_id = None # Initialize to handle potential upload errors
        try:
            # Save extracted text to a temporary file
            with open(temp_text_path, "w", encoding="utf-8") as f:
                f.write(deck_text)
            logger.info(f"Saved extracted deck text to temporary file: {temp_text_path}")

            # --- Check Stop Flag ---
            if state["stop_requested"]: raise GenerationStoppedError()

            # Call _analyze_visuals with the text file path and the outline prompt
            # _analyze_visuals handles uploading and deleting the temp file ID
            outline = _analyze_visuals(temp_text_path, OUTLINE_PROMPT) # Pass the original OUTLINE_PROMPT

        except GenerationStoppedError:
             raise # Re-raise to be caught by the main handler
        except Exception as e:
            logger.error(f"Error in Step 1 using vision model: {e}", exc_info=True)
            state["processing_message"] = f"-Error generating outline: {type(e).__name__}"
            # Ensure cleanup even if analysis fails before file deletion in helper
            if temp_file_id:
                 try:
                     writer.ai.delete_file(temp_file_id)
                     logger.info(f"Cleaned up temporary text file {temp_file_id} after error.")
                 except Exception as del_e:
                     logger.warning(f"Could not delete temporary text file {temp_file_id} after error: {del_e}")
        finally:
            # Clean up the temporary text file from local disk
            if os.path.exists(temp_text_path):
                try:
                    os.remove(temp_text_path)
                    logger.info(f"Removed temporary text file from disk: {temp_text_path}")
                except OSError as e:
                    logger.error(f"Error removing temporary text file {temp_text_path}: {e}")
        # --- END: Modified logic for Step 1 ---
        state["results"]["outline"] = outline
        logger.info("Step 1 (Outline with Vision Model) completed.")

        # --- Check Stop Flag ---
        if state["stop_requested"]: raise GenerationStoppedError()

        # --- Step 2: Analyze Visuals (Only if deck was uploaded) ---
        state["processing_step"] = "step2"
        if state["deck_input_method"] == "Upload File" and state["deck_file"]["path"]:
            state["processing_message"] = "%Analyzing presentation visuals..."
            # Pass the specific visual prompt here
            visual_analysis = _analyze_visuals(state["deck_file"]["path"], VISUAL_OUTLINE_PROMPT)
            state["results"]["visuals"] = visual_analysis
            logger.info("Step 2 (Visuals) completed.")
        else:
            state["results"]["visuals"] = "[Visual analysis skipped: Text input provided for deck]"
            logger.info("Step 2 (Visuals) skipped as text input was used for deck.")

        # --- Check Stop Flag ---
        if state["stop_requested"]: raise GenerationStoppedError()

        # --- Step 3: Extract Briefing Info ---
        state["processing_step"] = "step3"
        state["processing_message"] = "%Extracting key information from briefing..."
        prompt3 = BRIEFING_INFO_PROMPT.replace("{{Briefing(s)}}", combined_briefing_text)
        briefing_info = _call_ai_model(prompt3, temperature=0.0)
        state["results"]["briefing_info"] = briefing_info
        logger.info("Step 3 (Briefing Info) completed.")

        # --- Check Stop Flag ---
        if state["stop_requested"]: raise GenerationStoppedError()

        # --- Step 4: Map Messages ---
        state["processing_step"] = "step4"
        state["processing_message"] = "%Mapping messages to slides..."
        prompt4 = MAP_MESSAGES_PROMPT.replace("{{Presentation Outline}}", outline)
        prompt4 = prompt4.replace("{{Visual Presentation Outline}}", state["results"]["visuals"] or "")
        prompt4 = prompt4.replace("{{Key Information from the Briefing}}", briefing_info)
        mapping = _call_ai_model(prompt4, temperature=0.0)
        state["results"]["mapping"] = mapping
        logger.info("Step 4 (Mapping) completed.")

        # --- Check Stop Flag ---
        if state["stop_requested"]: raise GenerationStoppedError()

        # --- Step 5: Generate Speaker Notes ---
        state["processing_step"] = "step5"
        state["processing_message"] = "%Generating speaker notes..."
        prompt5 = SPEAKER_NOTES_PROMPT.replace("{{Map Messages to Each Slide}}", mapping)
        prompt5 = prompt5.replace("{{Presentation Outline}}", outline)
        prompt5 = prompt5.replace("{{Visual Presentation Outline}}", state["results"]["visuals"] or "")
        prompt5 = prompt5.replace("{{Timing}}", state["settings"]["timing"])
        prompt5 = prompt5.replace("{{Presentation Style}}", state["settings"]["style"])
        speaker_notes_text = _call_ai_model(prompt5, temperature=0.0)
        state["results"]["speaker_notes"] = speaker_notes_text
        logger.info("Step 5 (Speaker Notes) completed.")

        state["processing_message"] = "+Generation complete!"
        state["processing_step"] = "done"
        state["ui_controls"]["download_disabled"] = "no"

    except GenerationStoppedError:
         state["processing_message"] = "!Generation stopped by user."
         state["processing_step"] = "error" # Or a new 'stopped' state if preferred
         logger.info("Generation process stopped by user request.")
    except Exception as e:
        error_message = f"-An error occurred during step '{state['processing_step']}': {type(e).__name__}"
        state["processing_message"] = error_message
        state["processing_step"] = "error"
        logger.error(f"Pipeline error at step {state['processing_step']}: {e}", exc_info=True)
    finally:
        # --- End Generation ---
        state["is_generating"] = False
        state["stop_requested"] = False # Reset stop flag regardless of outcome
        _update_generate_button_state(state) # Re-evaluate generate button state
        # --- End End ---

# --- Download Handlers ---
def handle_download_outline(state):
    _download_content_as_docx(state, "outline")

def handle_download_visuals(state):
    _download_content_as_docx(state, "visuals")

def handle_download_briefing(state):
    _download_content_as_docx(state, "briefing_info")

def handle_download_mapping(state):
    _download_content_as_docx(state, "mapping")

def handle_download_notes(state):
    _download_content_as_docx(state, "speaker_notes")

# --- END OF FILE main.py ---