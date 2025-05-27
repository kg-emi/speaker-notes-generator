# AI prompts for each processing step with verbosity control

def get_verbosity_instructions(verbosity_level):
    """Returns verbosity-specific instructions for prompts."""
    if verbosity_level == "Brief":
        return """
IMPORTANT: Keep all outputs extremely concise. Use short bullet points only.
- Maximum 5-7 words per bullet point
- No explanatory text or elaboration
- Focus only on the most critical information
- Aim for 2-3 bullet points per slide maximum
"""
    elif verbosity_level == "Detailed":
        return """
Provide comprehensive analysis with full context and explanations.
- Include detailed reasoning and implications
- Provide thorough data analysis
- Add context and background where helpful
- Aim for 5-7 bullet points per slide
"""
    else:  # Standard
        return """
Provide balanced, professional notes with essential information.
- Keep bullet points to 10-15 words
- Include key data and insights
- Focus on actionable information
- Aim for 3-5 bullet points per slide
"""

def get_timing_instructions(timing):
    """Returns timing-specific instructions for speaker notes."""
    minutes = int(timing.split()[0])
    if minutes <= 10:
        return "CRITICAL: This is a very short presentation. Include only the most essential points. Maximum 2-3 brief bullet points per slide."
    elif minutes <= 20:
        return "Keep notes concise. Focus on key messages only. Maximum 3-4 bullet points per slide."
    elif minutes <= 30:
        return "Provide standard coverage with key points and essential data. Maximum 4-5 bullet points per slide."
    else:
        return "You have time for comprehensive coverage. Include important details and context. Maximum 5-6 bullet points per slide."

# 1. Prompt for "Outline" Component (Model: Palmyra X 004)
def get_outline_prompt(verbosity_level="Standard"):
    base_prompt = """
Your job is to analyse the structure of the presentation by examining each slide and identifying its title or creating a brief description when no title is present.

{verbosity_instructions}

For each slide, provide:
 - Slide number
 - The exact title OR a brief description (5-10 words max)

Format exactly as:
Slide 1: [Title or brief description]
Slide 2: [Title or brief description]

Process slides sequentially. Extract exact titles when present, otherwise create minimal descriptive phrases.

Presentation content:
"""
    return base_prompt.format(verbosity_instructions=get_verbosity_instructions(verbosity_level))

# 2. Prompt for "Visual Presentation Outline" Component
def get_visual_outline_prompt(verbosity_level="Standard"):
    if verbosity_level == "Brief":
        return """
Analyze {{InputDocument}} visuals. For each slide with charts/graphs/tables:

Slide X: [Visual Title]
- Type: [Chart/Graph/Table/Image]
- Key insight: [What story does this data tell? Max 10 words]
- Action item: [What should we do with this information?]

Focus on insights and implications, not descriptions.
"""
    elif verbosity_level == "Detailed":
        # Return the detailed prompt (VISUAL_OUTLINE_PROMPT already has {{InputDocument}})
        return VISUAL_OUTLINE_PROMPT
    else:  # Standard
        return """
Analyze {{InputDocument}} visuals with focus on insights, not just description.

For each slide with data visuals:

Slide X: [Visual Title or Description]
- Visual Type: [Specific chart/graph/table type]
- The Story: [What narrative does this data tell? 15-20 words]
- Key Insights:
  • [Primary finding with specific number]
  • [Trend or pattern that matters]
  • [Comparison or outlier worth noting]
- Strategic Implication: [What action this data suggests we take]

Focus on the "so what" - why this data matters for decision-making.
Extract insights that drive action, not just observations.
"""

# 3. Prompt for "Key Information from the Briefing" Component
def get_briefing_info_prompt(verbosity_level="Standard"):
    if verbosity_level == "Brief":
        return """
Extract only the most critical points from {{Briefing(s)}}:

Key Statistics (max 3):
• [Stat with context, max 10 words]

Key Findings (max 3):
• [Finding, max 10 words]

Strategic Actions (max 2):
• [Action, max 10 words]

Be extremely selective. Only include game-changing insights.
"""
    elif verbosity_level == "Detailed":
        return BRIEFING_INFO_PROMPT  # Use original detailed prompt
    else:  # Standard
        return """
Extract key insights from {{Briefing(s)}} for client presentation:

Key Statistics:
• [Important data point with brief context]
• [Growth rate or comparison]
• [Market size or share]

Key Findings:
• [Most important discovery or trend]
• [Critical market insight]
• [Competitive advantage or challenge]

Strategic Recommendations:
• [Primary action to take]
• [Secondary priority]

Keep each point under 15 words. Focus on actionable, decision-driving information.
"""

# 4. Prompt for "Mapping Key Messages to Each Slide" Component
def get_map_messages_prompt(verbosity_level="Standard"):
    if verbosity_level == "Brief":
        return """
Map insights to slides from {{Presentation Outline}}, {{Visual Presentation Outline}}, and {{Key Information from the Briefing}}.

For each slide:

Slide [Number]: [Title]
Type: [Identify if it's intro/data/comparison/conclusion]
Key Message: [One essential point from briefing/visual that fits this slide]

Only include the most critical, actionable information.
"""
    elif verbosity_level == "Detailed":
        return """
You are a strategic presentation advisor. Map insights intelligently from {{Presentation Outline}}, {{Visual Presentation Outline}}, and {{Key Information from the Briefing}}.

For each slide:

Slide [Number]: [Title]

Slide Intelligence:
- Purpose: [What role does this slide play in the narrative?]
- Type: [Title/Intro/Data/Comparison/Transition/Conclusion]
- Audience Need: [What question is this slide answering?]

Strategic Mapping:
From Briefing:
• [Most relevant strategic insight for this slide's purpose]
• [Supporting evidence or context]
• [Implication that connects to this slide's message]

From Visuals:
• [Key data story that supports the slide's objective]
• [Specific insight or trend worth highlighting]
• [Action item derived from the visual analysis]

Storytelling Connection:
- Link to Previous: [How this builds on what came before]
- Core Message: [The one thing audience must understand]
- Bridge to Next: [How this sets up what follows]

Intelligence Notes:
- If intro slide: Focus on framing the problem/opportunity
- If data slide: Emphasize insights over descriptions
- If comparison: Highlight decision criteria and recommendation
- If conclusion: Synthesize journey and crystallize action items

Remember: Every slide should advance the story. Map information that moves the narrative forward, not just fills space.
"""
    else:  # Standard
        return """
Strategically map insights to each slide using {{Presentation Outline}}, {{Visual Presentation Outline}}, and {{Key Information from the Briefing}}.

For each slide, consider its role in the story:

Slide [Number]: [Title]
Slide Type: [Intro/Content/Data/Comparison/Conclusion]

Relevant Insights:
• [Primary insight from briefing that aligns with slide purpose]
• [Supporting data or trend from visuals if applicable]
• [Strategic implication or action item]

Story Flow:
- What question this slide answers
- How it connects to overall narrative
- Transition thought to next slide

Focus on mapping insights that:
1. Match the slide's purpose
2. Advance the presentation story
3. Drive toward action or decision

Skip purely transitional slides. Prioritize substance over description.
"""

# 5. Prompt for "Generate Bullet Point Speaker Notes per Slide" Component
def get_speaker_notes_prompt(verbosity_level="Standard", timing="30 Minutes", style="Informative"):
    timing_instruction = get_timing_instructions(timing)
    
    if verbosity_level == "Brief":
        return f"""
Create ultra-concise speaker notes from {{Map Messages to Each Slide}}, {{Presentation Outline}}, and {{Visual Presentation Outline}}.

{timing_instruction}

For each slide, identify its purpose (introduction/data/comparison/conclusion) and adapt your notes accordingly:

Title/Intro slides:
• Core message only

Data slides:
• Key finding + implication

Comparison slides:
• Winner + reason

Conclusion slides:
• Main takeaway + action

Style: {style} - adjust tone but maintain brevity.
Maximum 3 bullets per slide. Focus on insights, not descriptions.
"""
    elif verbosity_level == "Detailed":
        return f"""
Generate comprehensive speaker notes from {{Map Messages to Each Slide}}, {{Presentation Outline}}, and {{Visual Presentation Outline}}.

{timing_instruction}
{get_verbosity_instructions('Detailed')}

For each slide:

Slide [Number]: [Exact Title from Presentation Outline]

Analyze the slide type and purpose:
- Title/Introduction: Set context, establish credibility, preview main points
- Data/Visual: Explain context, highlight key findings, analyze trends/outliers, draw strategic implications
- Comparison: Set up options, analyze strengths/weaknesses, provide clear recommendation with rationale
- Conclusion: Synthesize journey, crystallize insights, provide clear next steps

Structure your notes to tell a story:
• Opening: Why this matters to the audience
• Evidence: Data, examples, or comparisons that support your point
• Analysis: What the evidence reveals (trends, outliers, implications)
• So What: The strategic or practical implication
• Transition: Natural bridge to the next slide's topic

For data slides, go beyond description:
- Identify the "aha" moment in the data
- Explain what's surprising or confirmatory
- Connect to broader business implications
- Suggest what action this data demands

Presentation Style: {style}
Timing: {timing}

Include speaking cues like (pause for emphasis), (ask audience), or (show with gesture) where impactful.
"""
    else:  # Standard
        return f"""
Generate clear, insightful speaker notes from {{Map Messages to Each Slide}}, {{Presentation Outline}}, and {{Visual Presentation Outline}}.

{timing_instruction}
{get_verbosity_instructions('Standard')}

For each slide, recognize its type and adapt your approach:

Slide [Number]: [Exact Title]

INTRO/AGENDA SLIDES:
• Set the stage - why this topic matters now
• Preview the journey - what you'll discover
• Create anticipation for key insights

DATA/VISUAL SLIDES:
• The story behind the numbers - what's really happening
• The "so what" - why this data changes things
• The implication - what we should do differently

COMPARISON SLIDES:
• Frame the choice - what we're evaluating
• Key differentiator - the decisive factor
• Clear recommendation - which path forward

CONTENT SLIDES:
• Main insight - the core message
• Evidence - what proves this point
• Application - how this changes our approach

CONCLUSION SLIDES:
• Synthesis - connecting the dots
• Key takeaway - what to remember
• Call to action - specific next steps

Style: {style}
- Formal: Data-driven, authoritative language
- Informal: Conversational, relatable examples
- Persuasive: Benefit-focused, action-oriented
- Informative: Clear explanations, educational tone
- Storytelling: Narrative arc, emotional connection

Focus on insights and interpretation, not just description. Help the presenter tell a compelling story that drives action.
"""

# For backward compatibility, keep original prompt constants but update them
OUTLINE_PROMPT = """
Your job is to analyse the structure of the presentation by examining each slide and identifying its title or creating a brief description when no title is present. For each slide, provide:
 - Slide number
 - The exact title of the slide if one exists
 - A concise (10 - 20 word) description of the slide content if no title is present
I am going to show you an example now.
<example>
Slide 1: Probiotics and botanicals: the next healthy food in Asia
Slide 2: Today's insights
Slide 3: introduction
Slide 4: key data about Probiotics and botanicals
Slide 5: Naturally functional ingredients hold vast potential in foods
</example>

Here are some special instructions to follow as you analyse the presentation:
 - Process the presentation sequentially, slide by slide
 - For each slide, first determine if there is a clear, formatted title
 - Look for text that is larger, bolded or otherwise distinguished
 - Look for text at the top of the slide that appears to function as a header
 - If a title exists, extract it exactly as written
 - If no clear title exists, create a brief descriptive phrase based on:
The main visual element (chart, image, table)
The primary topic being discussed
The apparent purpose of the slide
 - Number each slide sequentially starting with 1
 - Do not make up any slide
Here are some Additional Guidelines to follow as you analyse the presentation:
 - Maintain the exact wording of titles when they exist
 - Keep descriptions factual rather than interpretive
 - For slides with only images or data, describe the type of visual content
 - If slide numbers are included in the original, verify them but use your own sequential numbering in the output

Presentation content:
"""
VISUAL_OUTLINE_PROMPT = """
You are an AI with expertise in analysing presentation visuals and extracting actionable insights from the data presented. Your task is to thoroughly review the {{InputDocument}} and identify the core data and messages conveyed by all visuals, including charts, graphs, tables, and images. For each slide, provide the following:
 - Slide number
 - The exact title of the visual (charts, graphs, infographics, images, and tables) if one exists.
 - Type of Visual: Clearly state the type of visual (e.g., bar chart, line graph, pie chart, table, photograph, infographic).
 - What the visual represents: Provide a concise explanation of what the visual is depicting (e.g., "Market share of competitors in 2023," "Sales trends over the last five years," "Key features of the product").
 - Key Data Points and Messages Conveyed: This is crucial. Systematically identify and list the most important data points presented in the visual. For charts and graphs, mention specific values, trends, comparisons, and significant outliers, explaining why these are key. When identifying the highest or lowest values in a comparison, double-check each entity mentioned against the data presented to ensure only the correct entities are listed. For tables, highlight key figures and relationships, analysing their significance. For images and infographics, describe the core message or information being visually communicated, identifying the underlying insights. Be specific and quantify where possible.
 - Interpretation of the Visual's Message: This section is critical. Go beyond simply describing the visual. Analyse the visual by explaining its meaning in the context of the presentation and the briefing. Highlight key takeaways, conclusions from the data, and how it reinforces the overall narrative or supports the slide's objective. Identify any trends, patterns, or relationships revealed by the visual and explain their significance. Consider the potential implications of the visual's message for the client's objectives or strategic decisions. Use analytical language to articulate your interpretation.

I am going to show you an example now.
<example>
Slide 1: There isn't a formal charts, graphs, infographics, images, or tables title in the traditional sense. The main title is the presentation title itself.
Slide 2: There are no charts, graphs, or infographics in this image. The only title is "Today's insights" which acts as an overarching title for the presentation slide's agenda. The image on the right is a photograph, not a titled chart.
Slide 3: The image itself doesn't have a formal title beyond the text displayed. The text displayed is "Introduction".
Slide 4: There is no formal title for the image; it's a collection of data points presented visually.
* Type of Visual: Visual representation of data points.
* What the visual represents: Market size and prevalence of herbal/traditional remedies and probiotic/botanical ingredients in the Asia-Pacific region.
* Key Data Points and Messages Conveyed:
 -  Herbal/Traditional Remedies: USD 35b market size in 2023.
 - OTC medicine market size is nearly equal to Herbal/Traditional Remedies.
 - Probiotic culture ingredients are used in 68% of packaged food in the Asia-Pacific region in 2024. This indicates widespread adoption of probiotic ingredients.
 - Botanical ingredients are used in 40% of packaged food in the Asia-Pacific region in 2024. This also shows a significant presence of botanical ingredients.
* Interpretation of the Visual's Message: The visual strongly indicates a significant market for herbal/traditional remedies, comparable to over-the-counter medicine, and highlights the widespread use of probiotic and botanical ingredients in packaged foods within the Asia-Pacific region. This data suggests a strong consumer interest and market opportunity for products containing these ingredients in this region. This visual provides compelling data points early in the presentation, establishing the significant market presence and potential of natural and functional food ingredients in Asia-Pacific, likely supporting the presentation's central theme.
Slide 5: Top Three Biggest Consumer Health Categories in Asia Pacific Market Size 2023 and CAGR 2023-2028.
* Type of Visual: Bar chart with accompanying data.
* What the visual represents: Market size in 2023 and projected Compound Annual Growth Rate (CAGR) from 2023 to 2028 for the top three consumer health categories in the Asia Pacific.
* Key Data Points and Messages Conveyed:
 - Vitamins and Dietary Supplements: Largest market size in 2023 (specific value not explicitly stated in the title but implied). This establishes vitamins and supplements as the leading category.
 - OTC medications: Second largest market size in 2023. This indicates a substantial market for traditional pharmaceutical products.
 - Herbal/Traditional Products: Third largest market size in 2023.
 - Vitamins and Dietary Supplements: Highest projected CAGR of approximately 3.3% (2023-2028). This suggests continued strong growth in the vitamins and supplements sector.
* Interpretation of the Visual's Message: The chart clearly demonstrates that Vitamins and Dietary Supplements dominate the consumer health market in the Asia Pacific in terms of size and are expected to maintain the highest growth rate. This suggests a key area of focus and opportunity within the consumer health market. This visual provides crucial market context, highlighting the leading categories and their growth potential, which could be relevant for positioning probiotic and botanical products within this broader landscape.
</example>
Here are some special instructions to follow as you analyse the presentation:
 - Process the presentation sequentially, slide by slide.
 - If a visual's title exists, extract it exactly as written.
 - If no clear visual's title exists, create a brief descriptive phrase based on:
What the visual represents
The key messages it conveys
How it supports the overall narrative of the presentation
 - Pay very close attention to individual data points and ensure accuracy in identifying the highest values or specific attributes mentioned.
 - Before stating a 'Key Data Point,' cross-reference it directly with the data presented in the visual to ensure complete accuracy. If you get it wrong (e.g., "South Korea has the highest growth rate in retail value and volume of pickled products compared to other Asian Pacific countries" INSTEAD OF "Vietnam has the highest growth rate in retail value and volume of pickled products compared to other Asian Pacific countries"), you will be grounded.
 - Thoroughly analyse the data presented in each visual to identify key trends, values, and comparisons.
 - When identifying the highest or lowest values in a comparison, double-check each entity mentioned against the data presented to ensure only the correct entities are listed.
 - Clearly articulate the main message or takeaway that the audience should glean from each visual.
 - Remember that the focus of the 'exact title of the visual' is on titles specifically associated with charts, graphs, tables, and other data-driven visuals, not overarching slide titles.
 - Ensure that every slide has an 'Interpretation of the Visual's Message' section.
"""
BRIEFING_INFO_PROMPT = get_briefing_info_prompt()
MAP_MESSAGES_PROMPT = get_map_messages_prompt()
SPEAKER_NOTES_PROMPT = get_speaker_notes_prompt()