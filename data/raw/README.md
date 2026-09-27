# Raw Data

Place your own CSV here if you want to run ConsumerInsight-AI on real data.

Required columns (see src/data_loader.py:REQUIRED_COLUMNS):

    review_id     — unique id
    platform      — 小红书 / 微博 / 天猫 / ...
    user_id       — anonymised handle
    product       — product name
    rating        — 1-5 stars
    text          — review body
    timestamp     — ISO timestamp
    user_age_band — 18-23 / 24-30 / 31-40 / 40+
    user_segment  — 学生党 / 通勤族 / 成分党 / 精致妈妈 (any string)

Then run:

    python scripts/run_pipeline.py --csv data/raw/your_file.csv