



How to run this program:
1. Update .env file located on root so that ANTHROPIC_API_KEY is defined with a valid Anthropic Key 
2. Activate .venv virtual environment for the project: source .venv/bin/activate  
3. Run the program: 
ython -m research_coordinator "Artificial Intelligence"
4. Fill free to play with max_iterations and min_subtopics (and related prompts and methods, e.g. from decomposition.py, refinement.py, research.py and coverage.py)
The output will be something like this:

================================================================================
RESEARCH REPORT: Artificial Intelligence
================================================================================

Coverage: 2/3 subtopics sufficient after 1 refinement iteration(s)

--- History and evolution of AI [INSUFFICIENT] ---
  (remaining gaps: lacks timelines and milestones; lacks societal impact)
  Artificial Intelligence traces its origins to the mid-20th century, with early
  pioneers like Alan Turing laying the groundwork for machine intelligence through
  theoretical concepts such as the Turing Test. The field witnessed periods of
  both optimism and disillusionment, often referred to as "AI winters," as
  expectations outpaced technological capabilities. Key milestones include the
  development of expert systems in the 1980s, the rise of machine learning, and
  the recent deep learning revolution, which has enabled breakthroughs in areas
  like computer vision and natural language processing. Early AI research was
  largely symbolic and rule-based, relying on human-coded knowledge rather than
  data-driven learning, but the availability of massive datasets and increased
  computational power have shifted the paradigm toward machine learning and deep
  learning. Societal impacts have evolved alongside the technology, with early
  concerns about job displacement and ethical implications giving way to broader
  discussions about bias, accountability, and the future of human-AI interaction.

  Sources:
    * https://en.wikipedia.org/wiki/History_of_artificial_intelligence
    * https://www.ibm.com/topics/artificial-intelligence-history
    * https://builtin.com/data-science/history-of-ai

--- Contemporary AI landscape and applications [SUFFICIENT] ---
  Contemporary AI spans a wide array of applications, from virtual assistants like
  Siri and Alexa to recommendation systems on platforms such as Netflix and
  Amazon, as well as fraud detection in finance and predictive maintenance in
  manufacturing. Machine learning, particularly deep learning with neural networks,
  has enabled significant advances in computer vision, allowing machines to
  recognize objects and faces in images, and in natural language processing (NLP),
  powering chatbots like ChatGPT and translation services. Generative AI, capable
  of creating text, images, and code, represents a major recent development, with
  models like GPT-4 and DALL-E 2 showcasing unprecedented capabilities. In
  healthcare, AI is used for medical image analysis and drug discovery, while in
  autonomous vehicles, it enables perception and decision-making. The economic
  impact is substantial, with AI driving productivity gains and creating new
  business models across industries, while also raising concerns about market
  concentration and the digital divide.

  Sources:
    * https://www.simplilearn.com/what-is-artificial-intelligence-ai-article
    * https://www.techtarget.com/what-is/definition/Artificial-Intelligence-AI
    * https://www.sas.com/en_us/insights/analytics/what-is-artificial-intelligence.html

--- Challenges and risks of modern AI [SUFFICIENT] ---
  Modern AI systems face significant challenges and risks, including issues of bias,
  fairness, and transparency. Because AI models learn from historical data, they
  can perpetuate and even amplify existing societal biases related to race, gender,
  and socioeconomic status, leading to discriminatory outcomes in areas like hiring
  and loan applications. The "black box" nature of deep learning models makes it
  difficult to understand how they arrive at decisions, raising concerns about
  accountability when things go wrong. Security risks include adversarial attacks
  that can fool AI systems, such as tricking autonomous vehicles into misinterpreting
  road signs. Job displacement due to automation is another major concern, as AI
  capabilities expand into areas previously requiring human labor. Furthermore, the
  potential for misuse in surveillance, autonomous weaponry, and the spread of
  disinformation through AI-generated content poses serious ethical and societal
  risks, prompting calls for regulation and international agreements to govern
  AI development and deployment.

  Sources:
    * https://www.ibm.com/topics/ai-risks-and-challenges
    * https://www.brookings.edu/articles/challenges-and-risks-of-ai-innovation/
    * https://www.weforum.org/agenda/2023/03/ai-risks-solutions-ethics/