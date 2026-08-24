# AI Note

## Did I Use AI?

Yes. I used AI to help me:

1. **Parse and load the dataset** — I had AI read the raw CSV from the GitHub repo so I could see the structure without manual copy-paste.
2. **Brainstorm the artifact scope** — I discussed what a "small useful artifact" means in this context (CLI report vs. notebook vs. Streamlit app) and settled on a self-contained Python script because it is the fastest to run and the easiest for a teammate to understand.
3. **Structure the README and AI note** — AI suggested the template sections based on the challenge requirements.

## One Prompt/Workflow Where AI Helped

I asked: *"What data quality issues should I look for in this small CSV, and which ones are worth handling vs. ignoring?"*

AI suggested checking for duplicates, missing values, casing issues, and outliers. I then verified each one manually by scanning the CSV. The most valuable suggestion was flagging the Aug 7 "review policy changed mid-day" row as non-comparable — I might have missed that if I had just averaged everything together.

## One Thing I Verified/Decided Myself

**Whether to exclude the Aug 5 demo spike from the fair comparison.**

AI suggested excluding it because it is an outlier. I agreed, but I made the call to *keep* it in the raw data and only exclude it from the pre/post comparison. My reasoning: the demo spike is real data that the team should know about (a demo account generated 140 sessions in one day), but it should not distort the prompt-change evaluation. I also decided to create a separate "with demo spike" view so the teammate can see how much it skews the numbers. That trade-off (transparency vs. fairness) was my judgment call.

Similarly, I decided that **user rating is the most trusted metric** and **model confidence is the least trusted** — based on the Aug 7 data where confidence was 0.91 and rating was 2.1. AI did not flag that specific contradiction; I noticed it while scanning the cleaned data and elevated it to a top-level warning.
